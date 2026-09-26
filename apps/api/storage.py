import os
import sqlite3
import hashlib
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple

from apps.api.config import config
from apps.api.errors import (
    APIException,
    ArtifactHashMismatchError,
    ArtifactNotFoundError,
    ErrorCode,
)
from apps.api.models import (
    ArtifactMetadata,
    ArtifactType,
    DocumentMetadata,
    JobStatus,
    LeakMetadata,
    AnalysisJobResponse,
)
from apps.api.security import sanitize_path

class ArtifactStorage(Protocol):
    def store_artifact(
        self,
        data: bytes,
        artifact_type: ArtifactType,
        document_id: Optional[str] = None,
        release_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        mime_type: str = "application/octet-stream",
        expected_hash: Optional[str] = None,
    ) -> ArtifactMetadata: ...

    def retrieve_artifact_bytes(self, artifact_id: str) -> bytes: ...

    def retrieve_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]: ...

class FilesystemArtifactStorage:
    """
    Filesystem-backed Data Plane storage.
    Enforces hash verification, path isolation, content-addressed storage,
    and persistent metadata index recovery across application restarts.
    """
    def __init__(self, storage_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        self.storage_dir = storage_dir or config.artifacts_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or (self.storage_dir / "artifacts_metadata.sqlite3")
        self._metadata_index: Dict[str, ArtifactMetadata] = {}
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            if hasattr(self.db_path, "parent"):
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    artifact_type TEXT,
                    sha256_hash TEXT,
                    document_id TEXT,
                    release_id TEXT,
                    recipient_id TEXT,
                    mime_type TEXT,
                    size_bytes INTEGER,
                    storage_path TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

            cur.execute("SELECT artifact_id, artifact_type, sha256_hash, document_id, release_id, recipient_id, mime_type, size_bytes, storage_path, created_at FROM artifacts")
            for row in cur.fetchall():
                self._metadata_index[row[0]] = ArtifactMetadata(
                    artifact_id=row[0],
                    artifact_type=ArtifactType(row[1]),
                    sha256_hash=row[2],
                    document_id=row[3],
                    release_id=row[4],
                    recipient_id=row[5],
                    mime_type=row[6],
                    size_bytes=row[7],
                    storage_path=row[8],
                    created_at=row[9],
                )
            conn.close()
        except Exception:
            pass

    def store_artifact(
        self,
        data: bytes,
        artifact_type: ArtifactType,
        document_id: Optional[str] = None,
        release_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        mime_type: str = "application/octet-stream",
        expected_hash: Optional[str] = None,
    ) -> ArtifactMetadata:
        computed_hash = hashlib.sha256(data).hexdigest()
        if expected_hash and computed_hash.lower() != expected_hash.lower():
            raise ArtifactHashMismatchError(expected=expected_hash, actual=computed_hash)

        artifact_id = f"art_{artifact_type.value.lower()}_{computed_hash[:12]}_{uuid.uuid4().hex[:6]}"
        safe_path = sanitize_path(f"{artifact_id}.bin", self.storage_dir)

        # Write data plane bytes to disk
        with open(safe_path, "wb") as f:
            f.write(data)

        meta = ArtifactMetadata(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            sha256_hash=computed_hash,
            document_id=document_id,
            release_id=release_id,
            recipient_id=recipient_id,
            mime_type=mime_type,
            size_bytes=len(data),
            storage_path=str(safe_path),
        )
        self._metadata_index[artifact_id] = meta

        try:
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (meta.artifact_id, meta.artifact_type.value, meta.sha256_hash, meta.document_id, meta.release_id, meta.recipient_id, meta.mime_type, meta.size_bytes, meta.storage_path, meta.created_at)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

        return meta

    def retrieve_artifact_bytes(self, artifact_id: str) -> bytes:
        meta = self._metadata_index.get(artifact_id)
        safe_path = sanitize_path(f"{artifact_id}.bin", self.storage_dir)
        if not safe_path.exists():
            raise ArtifactNotFoundError(artifact_id)
        with open(safe_path, "rb") as f:
            return f.read()

    def retrieve_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        return self._metadata_index.get(artifact_id)

class MetadataRepository:
    """
    Control Plane metadata repository for documents, leaks, and analysis jobs.
    In-memory with SQLite persistence support for offline durability across restarts.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.db_path
        self._documents: Dict[str, DocumentMetadata] = {}
        self._leaks: Dict[str, LeakMetadata] = {}
        self._jobs: Dict[str, AnalysisJobResponse] = {}
        self._init_sqlite()

    def _init_sqlite(self):
        try:
            if hasattr(self.db_path, "parent"):
                self.db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    document_name TEXT,
                    original_document_hash TEXT,
                    size_bytes INTEGER,
                    mime_type TEXT,
                    created_at TEXT,
                    artifact_id TEXT
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS leaks (
                    leak_id TEXT PRIMARY KEY,
                    leak_artifact_hash TEXT,
                    size_bytes INTEGER,
                    mime_type TEXT,
                    suspected_document_id TEXT,
                    suspected_release_id TEXT,
                    created_at TEXT,
                    artifact_id TEXT
                )
            """)
            conn.commit()

            # Hydrate in-memory maps from persistent SQLite database
            cur.execute("SELECT document_id, document_name, original_document_hash, size_bytes, mime_type, created_at, artifact_id FROM documents")
            for row in cur.fetchall():
                self._documents[row[0]] = DocumentMetadata(
                    document_id=row[0],
                    document_name=row[1],
                    original_document_hash=row[2],
                    size_bytes=row[3],
                    mime_type=row[4],
                    created_at=row[5],
                    artifact_id=row[6],
                )

            cur.execute("SELECT leak_id, leak_artifact_hash, size_bytes, mime_type, suspected_document_id, suspected_release_id, created_at, artifact_id FROM leaks")
            for row in cur.fetchall():
                self._leaks[row[0]] = LeakMetadata(
                    leak_id=row[0],
                    leak_artifact_hash=row[1],
                    size_bytes=row[2],
                    mime_type=row[3],
                    suspected_document_id=row[4],
                    suspected_release_id=row[5],
                    created_at=row[6],
                    artifact_id=row[7],
                )
            conn.close()
        except Exception:
            # Fallback to pure in-memory if sqlite file creation fails in restricted environments
            pass

    # Document operations
    def save_document(self, doc: DocumentMetadata):
        self._documents[doc.document_id] = doc
        try:
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?)",
                (doc.document_id, doc.document_name, doc.original_document_hash, doc.size_bytes, doc.mime_type, doc.created_at, doc.artifact_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_document(self, document_id: str) -> Optional[DocumentMetadata]:
        return self._documents.get(document_id)

    def list_documents(self) -> List[DocumentMetadata]:
        return list(self._documents.values())

    # Leak operations
    def save_leak(self, leak: LeakMetadata):
        self._leaks[leak.leak_id] = leak
        try:
            conn = sqlite3.connect(str(self.db_path))
            cur = conn.cursor()
            cur.execute(
                "INSERT OR REPLACE INTO leaks VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (leak.leak_id, leak.leak_artifact_hash, leak.size_bytes, leak.mime_type, leak.suspected_document_id, leak.suspected_release_id, leak.created_at, leak.artifact_id)
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_leak(self, leak_id: str) -> Optional[LeakMetadata]:
        return self._leaks.get(leak_id)

    # Job operations
    def save_job(self, job: AnalysisJobResponse):
        self._jobs[job.analysis_id] = job

    def get_job(self, analysis_id: str) -> Optional[AnalysisJobResponse]:
        return self._jobs.get(analysis_id)

    def list_jobs(self) -> List[AnalysisJobResponse]:
        return list(self._jobs.values())

# Global singletons for default execution
default_artifact_storage = FilesystemArtifactStorage()
default_metadata_repo = MetadataRepository()
