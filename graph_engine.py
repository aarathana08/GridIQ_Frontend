"""Power Grid Graph Isomorphism Analyzer — core graph engine.

Pure-logic module backed by NetworkX.  Every public function accepts plain
Python data (lists, dicts) and returns plain Python data so the Flask layer
can serialise the results directly to JSON.
"""

from __future__ import annotations

import copy
from typing import Any

import networkx as nx
from networkx.algorithms import isomorphism


# ---------------------------------------------------------------------------
# 1. Build an undirected graph from nodes & edges
# ---------------------------------------------------------------------------

def build_graph(nodes: list[Any], edges: list[tuple[Any, Any]]) -> nx.Graph:
    """Return an undirected ``nx.Graph`` built from *nodes* and *edges*.

    Parameters
    ----------
    nodes : list
        Node identifiers (strings, ints, …).
    edges : list[tuple]
        Each element is a ``(source, target)`` pair.
    """
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G


# ---------------------------------------------------------------------------
# 2. Graph isomorphism check with node mapping
# ---------------------------------------------------------------------------

def check_isomorphism(
    G1: nx.Graph,
    G2: nx.Graph,
) -> dict[str, Any]:
    """Check whether *G1* and *G2* are isomorphic.

    Returns
    -------
    dict
        ``{"is_isomorphic": bool, "mapping": dict | None}``
        When the graphs are isomorphic the *mapping* maps every node in
        *G1* to its corresponding node in *G2*.
    """
    gm = isomorphism.GraphMatcher(G1, G2)
    if gm.is_isomorphic():
        return {"is_isomorphic": True, "mapping": gm.mapping}
    return {"is_isomorphic": False, "mapping": None}


# ---------------------------------------------------------------------------
# 3. Basic graph metrics: vertices, edges, degree sequence
# ---------------------------------------------------------------------------

def graph_metrics(G: nx.Graph) -> dict[str, Any]:
    """Return vertex count, edge count, and per-node degrees.

    Returns
    -------
    dict
        ``{"num_vertices": int, "num_edges": int,
           "degrees": dict[node, int]}``
    """
    return {
        "num_vertices": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "degrees": dict(G.degree()),
    }


# ---------------------------------------------------------------------------
# 4. Adjacency matrix
# ---------------------------------------------------------------------------

def adjacency_matrix(G: nx.Graph) -> dict[str, Any]:
    """Return the adjacency matrix as a nested list together with the
    ordered list of node labels used as row / column headers.

    Returns
    -------
    dict
        ``{"nodes": list, "matrix": list[list[int]]}``
    """
    nodelist = sorted(G.nodes(), key=str)
    A = nx.adjacency_matrix(G, nodelist=nodelist)
    return {
        "nodes": [str(n) for n in nodelist],
        "matrix": A.todense().tolist(),
    }


# ---------------------------------------------------------------------------
# 5. Connected components & connectivity
# ---------------------------------------------------------------------------

def connectivity_info(G: nx.Graph) -> dict[str, Any]:
    """Return connectivity status and the list of connected components.

    Returns
    -------
    dict
        ``{"is_connected": bool, "num_components": int,
           "components": list[list]}``
        Each inner list is one connected component (sorted for
        deterministic output).
    """
    components = list(nx.connected_components(G))
    return {
        "is_connected": nx.is_connected(G) if G.number_of_nodes() > 0 else True,
        "num_components": len(components),
        "components": [sorted(c, key=str) for c in components],
    }


# ---------------------------------------------------------------------------
# 6. Simulate power-line failure (non-destructive)
# ---------------------------------------------------------------------------

def simulate_failure(
    G: nx.Graph,
    failed_edges: list[tuple[Any, Any]] | None = None,
    failed_nodes: list[Any] | None = None,
) -> dict[str, Any]:
    """Simulate the removal of edges and / or nodes **without** mutating *G*.

    Parameters
    ----------
    G : nx.Graph
        The original power-grid graph.
    failed_edges : list[tuple], optional
        Edges (transmission lines) to remove.
    failed_nodes : list, optional
        Nodes (substations / generators) to remove.

    Returns
    -------
    dict
        ``{"remaining_nodes": list, "remaining_edges": list,
           "is_connected": bool, "num_components": int,
           "components": list[list]}``
    """
    H = copy.deepcopy(G)

    if failed_edges:
        H.remove_edges_from(failed_edges)
    if failed_nodes:
        H.remove_nodes_from(failed_nodes)

    components = list(nx.connected_components(H))

    return {
        "remaining_nodes": sorted(H.nodes(), key=str),
        "remaining_edges": [list(e) for e in H.edges()],
        "is_connected": nx.is_connected(H) if H.number_of_nodes() > 0 else True,
        "num_components": len(components),
        "components": [sorted(c, key=str) for c in components],
    }

