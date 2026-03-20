from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, Optional


class SkillAdjacencyGraph:
    """Lightweight, hand-crafted skill adjacency graph.

    This approximates relationships like C++ -> Rust or React -> Vue so that
    we can reason about how far a candidate is from a requirement.
    Distances are small integers (0 = same skill, 1 = very close, etc.).
    """

    def __init__(self) -> None:
        # Undirected adjacency list; edges imply strong transferability.
        self._adj: Dict[str, set[str]] = {}
        self._build_default_graph()

    def _add_edge(self, a: str, b: str) -> None:
        a = a.lower()
        b = b.lower()
        if a == b:
            return
        self._adj.setdefault(a, set()).add(b)
        self._adj.setdefault(b, set()).add(a)

    def _build_default_graph(self) -> None:
        # Languages
        for a, b in [
            ("c++", "rust"),
            ("c++", "c"),
            ("java", "kotlin"),
            ("javascript", "typescript"),
            ("python", "r"),
            ("python", "scala"),
            ("go", "rust"),
        ]:
            self._add_edge(a, b)

        # Web frameworks
        for a, b in [
            ("react", "vue"),
            ("react", "next.js"),
            ("vue", "nuxt"),
            ("django", "flask"),
            ("fastapi", "django"),
            ("express", "fastify"),
        ]:
            self._add_edge(a, b)

        # Data / ML
        for a, b in [
            ("pandas", "numpy"),
            ("pandas", "sql"),
            ("tensorflow", "pytorch"),
            ("scikit-learn", "pytorch"),
            ("mlops", "kubernetes"),
            ("mlops", "airflow"),
        ]:
            self._add_edge(a, b)

        # Cloud
        for a, b in [
            ("aws", "gcp"),
            ("aws", "azure"),
            ("docker", "kubernetes"),
        ]:
            self._add_edge(a, b)

        # General CS
        for a, b in [
            ("algorithms", "data structures"),
            ("system design", "distributed systems"),
        ]:
            self._add_edge(a, b)

    def neighbours(self, skill: str) -> Iterable[str]:
        return self._adj.get(skill.lower(), set())

    def shortest_distance(self, source: str, target: str, max_depth: int = 3) -> Optional[int]:
        """Return the hop distance between two skills if they are connected.

        Uses unweighted BFS up to max_depth to keep lookups cheap.
        Returns 0 if the names are identical, None if no path within max_depth.
        """

        s = source.lower().strip()
        t = target.lower().strip()
        if not s or not t:
            return None
        if s == t:
            return 0

        visited = {s}
        q: deque[tuple[str, int]] = deque([(s, 0)])

        while q:
            node, dist = q.popleft()
            if dist >= max_depth:
                continue
            for nb in self._adj.get(node, ()):  # type: ignore[arg-type]
                if nb == t:
                    return dist + 1
                if nb not in visited:
                    visited.add(nb)
                    q.append((nb, dist + 1))
        return None


# Singleton instance used across the app
GLOBAL_SKILL_GRAPH = SkillAdjacencyGraph()
