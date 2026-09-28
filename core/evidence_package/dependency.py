"""
AegisTrace Evidence Dependency DAG & Topological Grounding Validator.

Builds and verifies the directed acyclic graph (DAG) connecting forensic claims,
receipts, observations, and attribution conclusions.
Guarantees:
1. Strict acyclicity (no recursive/circular evidence loops).
2. Conclusion grounding: every attribution decision must trace to root evidence.
3. No orphaned evidence influencing decisions.
"""

from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict, deque

from core.evidence_package.models import (
    BaseEvidenceObject,
    DependencyEdge,
    AttributionDecisionObject,
    EvidenceObjectType
)


class EvidenceDAGError(ValueError):
    """Raised when evidence DAG violates acyclicity or grounding rules."""
    pass


class EvidenceDependencyDAG:
    """
    Directed Acyclic Graph over package evidence objects.
    Edges represent directed evidentiary dependencies (source depends on / is grounded in target).
    """
    def __init__(self):
        self.nodes: Dict[str, BaseEvidenceObject] = {}
        self.adjacency: Dict[str, Set[str]] = defaultdict(set)  # u -> set(v) where u depends on v
        self.reverse_adjacency: Dict[str, Set[str]] = defaultdict(set)  # v -> set(u) where v is dependency of u
        self.edges: List[DependencyEdge] = []

    def add_node(self, node: BaseEvidenceObject) -> None:
        self.nodes[node.object_id] = node

    def add_edge(self, edge: DependencyEdge) -> None:
        self.edges.append(edge)
        self.adjacency[edge.source_id].add(edge.target_id)
        self.reverse_adjacency[edge.target_id].add(edge.source_id)

    def validate_acyclic(self) -> List[str]:
        """
        Validates that graph is a DAG using topological sorting (Kahn's algorithm).
        Returns topological ordering of object IDs.
        Raises EvidenceDAGError if a cycle is detected.
        """
        in_degree = {u: 0 for u in self.nodes}
        for u in self.adjacency:
            for v in self.adjacency[u]:
                if v in in_degree:
                    in_degree[v] += 1

        queue = deque([u for u, deg in in_degree.items() if deg == 0])
        order = []

        while queue:
            u = queue.popleft()
            order.append(u)
            for v in self.adjacency.get(u, set()):
                if v in in_degree:
                    in_degree[v] -= 1
                    if in_degree[v] == 0:
                        queue.append(v)

        if len(order) != len(self.nodes):
            remaining = set(self.nodes.keys()) - set(order)
            raise EvidenceDAGError(f"Evidence dependency cycle detected involving nodes: {sorted(list(remaining))}")

        return order

    def verify_grounding(self, decision_object_id: str) -> Tuple[bool, List[str]]:
        """
        Verifies that a decision object is grounded in valid root evidence nodes
        and does not reference missing objects.
        Returns: (is_grounded, list_of_errors)
        """
        errors = []
        if decision_object_id not in self.nodes:
            return False, [f"Decision object '{decision_object_id}' not found in DAG"]

        visited = set()
        queue = deque([decision_object_id])
        ground_nodes = set()

        while queue:
            curr_id = queue.popleft()
            if curr_id in visited:
                continue
            visited.add(curr_id)

            curr_node = self.nodes.get(curr_id)
            if not curr_node:
                errors.append(f"Missing referenced dependency node '{curr_id}'")
                continue

            # Check if root evidence type
            if curr_node.object_type in (
                EvidenceObjectType.ARTIFACT,
                EvidenceObjectType.WATERMARK_EVIDENCE,
                EvidenceObjectType.DECRYPTION_RECEIPT,
                EvidenceObjectType.LEDGER_PROOF,
                EvidenceObjectType.TELEMETRY_EVIDENCE,
                EvidenceObjectType.DEVICE_EVIDENCE,
                EvidenceObjectType.LINEAGE_EVIDENCE,
            ):
                ground_nodes.add(curr_id)

            for dep_id in self.adjacency.get(curr_id, set()):
                if dep_id not in visited:
                    queue.append(dep_id)

        if not ground_nodes:
            errors.append(f"Decision '{decision_object_id}' has no grounding in empirical evidence nodes")

        return (len(errors) == 0, errors)
