"""
AegisTrace Forensic Correlation Graph Model.

Implements a directed forensic property graph preserving uncertainty,
causal lineage, and strict separation between accounts, devices, networks,
and physical identities.

10 Node Types:
  DOCUMENT, COPY, IDENTITY, ACCOUNT, DEVICE, SESSION, EVENT, NETWORK,
  EXTERNAL_ARTIFACT, LOCATION

10 Edge Types:
  RELEASED_TO, ACCESSED_BY, RENDERED_ON, EXPORTED_BY, COPIED_BY, WRITTEN_TO,
  TRANSMITTED_TO, UPLOADED_FROM, CORRESPONDS_TO, DERIVED_FROM
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List, Set, Tuple
from pydantic import BaseModel, Field
import json


class ForensicNodeType(str, Enum):
    DOCUMENT = "DOCUMENT"
    COPY = "COPY"
    IDENTITY = "IDENTITY"
    ACCOUNT = "ACCOUNT"
    DEVICE = "DEVICE"
    SESSION = "SESSION"
    EVENT = "EVENT"
    NETWORK = "NETWORK"
    EXTERNAL_ARTIFACT = "EXTERNAL_ARTIFACT"
    LOCATION = "LOCATION"


class ForensicEdgeType(str, Enum):
    RELEASED_TO = "RELEASED_TO"
    ACCESSED_BY = "ACCESSED_BY"
    RENDERED_ON = "RENDERED_ON"
    EXPORTED_BY = "EXPORTED_BY"
    COPIED_BY = "COPIED_BY"
    WRITTEN_TO = "WRITTEN_TO"
    TRANSMITTED_TO = "TRANSMITTED_TO"
    UPLOADED_FROM = "UPLOADED_FROM"
    CORRESPONDS_TO = "CORRESPONDS_TO"
    DERIVED_FROM = "DERIVED_FROM"


class ForensicGraphNode(BaseModel):
    node_id: str
    node_type: ForensicNodeType
    label: str
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ForensicGraphEdge(BaseModel):
    source_id: str
    target_id: str
    edge_type: ForensicEdgeType
    weight: float = 1.0
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    timestamp: Optional[datetime] = None
    provenance: str = "SYSTEM"
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ForensicCorrelationGraph:
    """
    Forensic correlation graph tracking artifact provenance, custody transitions,
    and external operational events.
    """

    def __init__(self):
        self._nodes: Dict[str, ForensicGraphNode] = {}
        # Adjacency list: node_id -> list of outgoing ForensicGraphEdge
        self._out_edges: Dict[str, List[ForensicGraphEdge]] = {}
        # Inverted adjacency: node_id -> list of incoming ForensicGraphEdge
        self._in_edges: Dict[str, List[ForensicGraphEdge]] = {}

    def add_node(
        self,
        node_id: str,
        node_type: ForensicNodeType,
        label: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ForensicGraphNode:
        if node_id in self._nodes:
            # Update attributes if needed
            if attributes:
                self._nodes[node_id].attributes.update(attributes)
            return self._nodes[node_id]

        node = ForensicGraphNode(
            node_id=node_id,
            node_type=node_type,
            label=label or f"{node_type.value}:{node_id}",
            attributes=attributes or {},
        )
        self._nodes[node_id] = node
        self._out_edges.setdefault(node_id, [])
        self._in_edges.setdefault(node_id, [])
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: ForensicEdgeType,
        weight: float = 1.0,
        confidence: float = 1.0,
        timestamp: Optional[datetime] = None,
        provenance: str = "SYSTEM",
        attributes: Optional[Dict[str, Any]] = None,
    ) -> ForensicGraphEdge:
        if source_id not in self._nodes:
            raise ValueError(f"Source node '{source_id}' does not exist in graph.")
        if target_id not in self._nodes:
            raise ValueError(f"Target node '{target_id}' does not exist in graph.")

        edge = ForensicGraphEdge(
            source_id=source_id,
            target_id=target_id,
            edge_type=edge_type,
            weight=weight,
            confidence=confidence,
            timestamp=timestamp,
            provenance=provenance,
            attributes=attributes or {},
        )
        self._out_edges[source_id].append(edge)
        self._in_edges[target_id].append(edge)
        return edge

    def get_node(self, node_id: str) -> Optional[ForensicGraphNode]:
        return self._nodes.get(node_id)

    def get_out_edges(self, node_id: str) -> List[ForensicGraphEdge]:
        return self._out_edges.get(node_id, [])

    def get_in_edges(self, node_id: str) -> List[ForensicGraphEdge]:
        return self._in_edges.get(node_id, [])

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def edge_count(self) -> int:
        return sum(len(edges) for edges in self._out_edges.values())

    def find_all_paths(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 10,
    ) -> List[List[ForensicGraphEdge]]:
        """
        Find all directed paths from start_id to end_id up to max_depth.
        """
        if start_id not in self._nodes or end_id not in self._nodes:
            return []

        paths: List[List[ForensicGraphEdge]] = []

        def dfs(curr_id: str, current_path: List[ForensicGraphEdge], visited_nodes: Set[str]):
            if curr_id == end_id:
                paths.append(list(current_path))
                return
            if len(current_path) >= max_depth:
                return

            for edge in self._out_edges.get(curr_id, []):
                next_id = edge.target_id
                if next_id not in visited_nodes:
                    visited_nodes.add(next_id)
                    current_path.append(edge)
                    dfs(next_id, current_path, visited_nodes)
                    current_path.pop()
                    visited_nodes.remove(next_id)

        dfs(start_id, [], {start_id})
        return paths

    def find_shortest_path(
        self,
        start_id: str,
        end_id: str,
    ) -> Optional[List[ForensicGraphEdge]]:
        """
        Breadth-first search for the shortest causal edge path.
        """
        if start_id not in self._nodes or end_id not in self._nodes:
            return None
        if start_id == end_id:
            return []

        from collections import deque
        queue = deque([(start_id, [])])
        visited = {start_id}

        while queue:
            curr_id, path = queue.popleft()
            for edge in self._out_edges.get(curr_id, []):
                next_id = edge.target_id
                new_path = path + [edge]
                if next_id == end_id:
                    return new_path
                if next_id not in visited:
                    visited.add(next_id)
                    queue.append((next_id, new_path))
        return None

    def detect_custody_gaps(self, path: List[ForensicGraphEdge]) -> List[str]:
        """
        Identify missing causal steps or unaccounted boundaries along an edge path.
        Returns descriptions of identified gaps.
        """
        gaps = []
        for i in range(len(path) - 1):
            e1 = path[i]
            e2 = path[i + 1]
            t1 = self.get_node(e1.target_id)
            if not t1:
                continue

            # Gap check: e.g. Device directly to External Artifact without an export/upload event
            if t1.node_type == ForensicNodeType.DEVICE and e2.edge_type == ForensicEdgeType.TRANSMITTED_TO:
                if not any(k in e2.attributes for k in ("observed_upload", "event_id")):
                    gaps.append(f"Unobserved transmission transition between device '{t1.node_id}' and '{e2.target_id}'")

            # Timestamp order violation check (predecessor causality)
            if e1.timestamp and e2.timestamp:
                if e2.timestamp < e1.timestamp:
                    diff_sec = (e1.timestamp - e2.timestamp).total_seconds()
                    gaps.append(
                        f"Temporal reversal: step {i+1} ({e2.edge_type}) occurred {diff_sec:.1f}s "
                        f"BEFORE step {i} ({e1.edge_type})"
                    )

        return gaps

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to dictionary."""
        nodes_list = []
        for n in self._nodes.values():
            nodes_list.append({
                "node_id": n.node_id,
                "node_type": n.node_type.value,
                "label": n.label,
                "attributes": n.attributes,
            })
        edges_list = []
        for edges in self._out_edges.values():
            for e in edges:
                edges_list.append({
                    "source_id": e.source_id,
                    "target_id": e.target_id,
                    "edge_type": e.edge_type.value,
                    "weight": e.weight,
                    "confidence": e.confidence,
                    "timestamp": e.timestamp.isoformat() if e.timestamp else None,
                    "provenance": e.provenance,
                    "attributes": e.attributes,
                })
        return {"nodes": nodes_list, "edges": edges_list}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ForensicCorrelationGraph":
        """Deserialize graph from dictionary."""
        graph = cls()
        for nd in data.get("nodes", []):
            graph.add_node(
                node_id=nd["node_id"],
                node_type=ForensicNodeType(nd["node_type"]),
                label=nd.get("label"),
                attributes=nd.get("attributes", {}),
            )
        for ed in data.get("edges", []):
            ts = ed.get("timestamp")
            if ts:
                ts = datetime.fromisoformat(ts)
            graph.add_edge(
                source_id=ed["source_id"],
                target_id=ed["target_id"],
                edge_type=ForensicEdgeType(ed["edge_type"]),
                weight=float(ed.get("weight", 1.0)),
                confidence=float(ed.get("confidence", 1.0)),
                timestamp=ts,
                provenance=ed.get("provenance", "SYSTEM"),
                attributes=ed.get("attributes", {}),
            )
        return graph
