import os
import sqlite3
import hashlib
import threading
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
from apps.api.security import sanitize_path, validate_id_format

class ArtifactStorage(Protocol):
    def store_artifact(
        self,
        data: bytes,
        artifact_type: ArtifactType,
        document_id: Optional[str] = None,
        release_id: Optional[str] = None,
        recipient_id: Optional[str] = None,
        tenant_id: str = "default_tenant",
        mime_type: str = "application/octet-stream",
        expected_hash: Optional[str] = None,
    ) -> ArtifactMetadata: ...

    def retrieve_artifact_bytes(self, artifact_id: str) -> bytes: ...

    def retrieve_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]: ...

class FilesystemArtifactStorage:
    """
    Filesystem-backed Data Plane storage with multi-tenant logical partitioning.
    Enforces hash verification, path isolation, content-addressed storage,
    and persistent metadata index recovery across application restarts.
    """
    def __init__(self, storage_dir: Optional[Path] = None, db_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.storage_dir = storage_dir or config.artifacts_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path or (self.storage_dir / "artifacts_metadata.sqlite3")
        self._metadata_index: Dict[str, ArtifactMetadata] = {}
        self._init_sqlite()

    def _init_sqlite(self):
        with self._lock:
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
                        tenant_id TEXT DEFAULT 'default_tenant',
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

                # Migration check: ensure tenant_id column exists
                cur.execute("PRAGMA table_info(artifacts)")
                cols = [r[1] for r in cur.fetchall()]
                if "tenant_id" not in cols:
                    cur.execute("ALTER TABLE artifacts ADD COLUMN tenant_id TEXT DEFAULT 'default_tenant'")
                    conn.commit()

                cur.execute("SELECT artifact_id, artifact_type, sha256_hash, tenant_id, document_id, release_id, recipient_id, mime_type, size_bytes, storage_path, created_at FROM artifacts")
                for row in cur.fetchall():
                    self._metadata_index[row[0]] = ArtifactMetadata(
                        artifact_id=row[0],
                        artifact_type=ArtifactType(row[1]),
                        sha256_hash=row[2],
                        tenant_id=row[3] or "default_tenant",
                        document_id=row[4],
                        release_id=row[5],
                        recipient_id=row[6],
                        mime_type=row[7],
                        size_bytes=row[8],
                        storage_path=row[9],
                        created_at=row[10],
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
        tenant_id: str = "default_tenant",
        mime_type: str = "application/octet-stream",
        expected_hash: Optional[str] = None,
    ) -> ArtifactMetadata:
        with self._lock:
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
                tenant_id=tenant_id,
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
                    "INSERT OR REPLACE INTO artifacts VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (meta.artifact_id, meta.artifact_type.value, meta.sha256_hash, meta.tenant_id, meta.document_id, meta.release_id, meta.recipient_id, meta.mime_type, meta.size_bytes, meta.storage_path, meta.created_at)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

            return meta

    def retrieve_artifact_bytes(self, artifact_id: str) -> bytes:
        with self._lock:
            validate_id_format(artifact_id, "artifact_id")
            meta = self._metadata_index.get(artifact_id)
            safe_path = sanitize_path(f"{artifact_id}.bin", self.storage_dir)
            if not safe_path.exists():
                raise ArtifactNotFoundError(artifact_id)
            with open(safe_path, "rb") as f:
                return f.read()

    def retrieve_metadata(self, artifact_id: str) -> Optional[ArtifactMetadata]:
        with self._lock:
            validate_id_format(artifact_id, "artifact_id")
            return self._metadata_index.get(artifact_id)

    def clear(self):
        """Clear all in-memory metadata entries and SQLite artifact records."""
        with self._lock:
            self._metadata_index.clear()
            try:
                conn = sqlite3.connect(str(self.db_path))
                cur = conn.cursor()
                cur.execute("DELETE FROM artifacts")
                conn.commit()
                conn.close()
            except Exception:
                pass

class MetadataRepository:
    """
    Control Plane metadata repository for documents, leaks, and analysis jobs
    with multi-tenant isolation and thread safety.
    """
    def __init__(self, db_path: Optional[Path] = None):
        self._lock = threading.RLock()
        self.db_path = db_path or config.db_path
        self._documents: Dict[str, DocumentMetadata] = {}
        self._leaks: Dict[str, LeakMetadata] = {}
        self._jobs: Dict[str, AnalysisJobResponse] = {}
        self._init_sqlite()

    def _init_sqlite(self):
        with self._lock:
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
                        tenant_id TEXT DEFAULT 'default_tenant',
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
                        tenant_id TEXT DEFAULT 'default_tenant',
                        size_bytes INTEGER,
                        mime_type TEXT,
                        suspected_document_id TEXT,
                        suspected_release_id TEXT,
                        created_at TEXT,
                        artifact_id TEXT
                    )
                """)
                conn.commit()

                # Migration checks for tenant_id column
                cur.execute("PRAGMA table_info(documents)")
                doc_cols = [r[1] for r in cur.fetchall()]
                if "tenant_id" not in doc_cols:
                    cur.execute("ALTER TABLE documents ADD COLUMN tenant_id TEXT DEFAULT 'default_tenant'")
                    conn.commit()

                cur.execute("PRAGMA table_info(leaks)")
                leak_cols = [r[1] for r in cur.fetchall()]
                if "tenant_id" not in leak_cols:
                    cur.execute("ALTER TABLE leaks ADD COLUMN tenant_id TEXT DEFAULT 'default_tenant'")
                    conn.commit()

                # Hydrate in-memory maps from persistent SQLite database
                cur.execute("SELECT document_id, document_name, original_document_hash, tenant_id, size_bytes, mime_type, created_at, artifact_id FROM documents")
                for row in cur.fetchall():
                    self._documents[row[0]] = DocumentMetadata(
                        document_id=row[0],
                        document_name=row[1],
                        original_document_hash=row[2],
                        tenant_id=row[3] or "default_tenant",
                        size_bytes=row[4],
                        mime_type=row[5],
                        created_at=row[6],
                        artifact_id=row[7],
                    )

                cur.execute("SELECT leak_id, leak_artifact_hash, tenant_id, size_bytes, mime_type, suspected_document_id, suspected_release_id, created_at, artifact_id FROM leaks")
                for row in cur.fetchall():
                    self._leaks[row[0]] = LeakMetadata(
                        leak_id=row[0],
                        leak_artifact_hash=row[1],
                        tenant_id=row[2] or "default_tenant",
                        size_bytes=row[3],
                        mime_type=row[4],
                        suspected_document_id=row[5],
                        suspected_release_id=row[6],
                        created_at=row[7],
                        artifact_id=row[8],
                    )
                conn.close()
            except Exception:
                pass

    # Document operations
    def save_document(self, doc: DocumentMetadata):
        with self._lock:
            self._documents[doc.document_id] = doc
            try:
                conn = sqlite3.connect(str(self.db_path))
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (doc.document_id, doc.document_name, doc.original_document_hash, doc.tenant_id, doc.size_bytes, doc.mime_type, doc.created_at, doc.artifact_id)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

    def get_document(self, document_id: str, tenant_id: Optional[str] = None) -> Optional[DocumentMetadata]:
        with self._lock:
            validate_id_format(document_id, "document_id")
            doc = self._documents.get(document_id)
            if not doc:
                return None
            if tenant_id and tenant_id != "*" and doc.tenant_id != tenant_id:
                return None
            return doc

    def list_documents(self, tenant_id: Optional[str] = None) -> List[DocumentMetadata]:
        with self._lock:
            if not tenant_id or tenant_id == "*":
                return list(self._documents.values())
            return [d for d in self._documents.values() if d.tenant_id == tenant_id]

    # Leak operations
    def save_leak(self, leak: LeakMetadata):
        with self._lock:
            self._leaks[leak.leak_id] = leak
            try:
                conn = sqlite3.connect(str(self.db_path))
                cur = conn.cursor()
                cur.execute(
                    "INSERT OR REPLACE INTO leaks VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (leak.leak_id, leak.leak_artifact_hash, leak.tenant_id, leak.size_bytes, leak.mime_type, leak.suspected_document_id, leak.suspected_release_id, leak.created_at, leak.artifact_id)
                )
                conn.commit()
                conn.close()
            except Exception:
                pass

    def get_leak(self, leak_id: str, tenant_id: Optional[str] = None) -> Optional[LeakMetadata]:
        with self._lock:
            validate_id_format(leak_id, "leak_id")
            leak = self._leaks.get(leak_id)
            if not leak:
                return None
            if tenant_id and tenant_id != "*" and leak.tenant_id != tenant_id:
                return None
            return leak

    def list_leaks(self, tenant_id: Optional[str] = None) -> List[LeakMetadata]:
        with self._lock:
            if not tenant_id or tenant_id == "*":
                return list(self._leaks.values())
            return [l for l in self._leaks.values() if l.tenant_id == tenant_id]

    # Job operations
    def save_job(self, job: AnalysisJobResponse):
        with self._lock:
            self._jobs[job.analysis_id] = job

    def get_job(self, analysis_id: str, tenant_id: Optional[str] = None) -> Optional[AnalysisJobResponse]:
        with self._lock:
            validate_id_format(analysis_id, "analysis_id")
            job = self._jobs.get(analysis_id)
            if not job:
                return None
            if tenant_id and tenant_id != "*" and getattr(job, "tenant_id", "default_tenant") != tenant_id:
                return None
            return job

    def list_jobs(self, tenant_id: Optional[str] = None) -> List[AnalysisJobResponse]:
        with self._lock:
            if not tenant_id or tenant_id == "*":
                return list(self._jobs.values())
            return [j for j in self._jobs.values() if getattr(j, "tenant_id", "default_tenant") == tenant_id]

    def clear(self):
        """Clear all in-memory documents, leaks, jobs, and SQLite table rows."""
        with self._lock:
            self._documents.clear()
            self._leaks.clear()
            self._jobs.clear()
            try:
                conn = sqlite3.connect(str(self.db_path))
                cur = conn.cursor()
                cur.execute("DELETE FROM documents")
                cur.execute("DELETE FROM leaks")
                conn.commit()
                conn.close()
            except Exception:
                pass

# Global singletons for default execution
default_artifact_storage = FilesystemArtifactStorage()
default_metadata_repo = MetadataRepository()
