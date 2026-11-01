"""Power Grid Graph Isomorphism Analyzer — Flask API server."""

from flask import Flask, jsonify, request
from flask_cors import CORS

import graph_engine as engine

app = Flask(__name__)
CORS(app)


# ── helpers ────────────────────────────────────────────────────────────────

def _parse_graph(payload: dict, prefix: str = ""):
    """Build an ``nx.Graph`` from the JSON *payload*.

    When *prefix* is provided (e.g. ``"graph1_"``), the keys looked up
    become ``graph1_nodes`` / ``graph1_edges`` so that a single request
    body can carry two graphs.
    """
    nodes = payload.get(f"{prefix}nodes", [])
    edges = payload.get(f"{prefix}edges", [])
    # Edges arrive as [[u, v], …] or [{"source": u, "target": v}, …]
    normalised: list[tuple] = []
    for e in edges:
        if isinstance(e, dict):
            normalised.append((e["source"], e["target"]))
        else:
            normalised.append(tuple(e))
    return engine.build_graph(nodes, normalised)


# ── endpoints ──────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health_check():
    """Return a simple health-check response."""
    return jsonify({"status": "ok", "message": "Backend is running"})


# 1 & 3. Build a graph and return its basic metrics
@app.route("/api/graph/metrics", methods=["POST"])
def graph_metrics():
    """Accept nodes & edges, return vertex/edge counts and degree map.

    Request body::

        {
          "nodes": ["A", "B", "C"],
          "edges": [["A", "B"], ["B", "C"]]
        }
    """
    data = request.get_json(force=True)
    G = _parse_graph(data)
    return jsonify(engine.graph_metrics(G))


# 2. Isomorphism check
@app.route("/api/graph/isomorphism", methods=["POST"])
def check_isomorphism():
    """Compare two graphs for isomorphism and return the node mapping.

    Request body::

        {
          "graph1_nodes": ["A", "B", "C"],
          "graph1_edges": [["A", "B"], ["B", "C"]],
          "graph2_nodes": ["X", "Y", "Z"],
          "graph2_edges": [["X", "Y"], ["Y", "Z"]]
        }
    """
    data = request.get_json(force=True)
    G1 = _parse_graph(data, prefix="graph1_")
    G2 = _parse_graph(data, prefix="graph2_")
    return jsonify(engine.check_isomorphism(G1, G2))


# 4. Adjacency matrix
@app.route("/api/graph/adjacency", methods=["POST"])
def adjacency_matrix():
    """Return the adjacency matrix for the given graph.

    Request body: same as ``/api/graph/metrics``.
    """
    data = request.get_json(force=True)
    G = _parse_graph(data)
    return jsonify(engine.adjacency_matrix(G))


# 5. Connectivity & connected components
@app.route("/api/graph/connectivity", methods=["POST"])
def connectivity():
    """Return connectivity status and component list.

    Request body: same as ``/api/graph/metrics``.
    """
    data = request.get_json(force=True)
    G = _parse_graph(data)
    return jsonify(engine.connectivity_info(G))


# 6. Simulate power-line / substation failure
@app.route("/api/graph/simulate-failure", methods=["POST"])
def simulate_failure():
    """Remove edges/nodes and report the resulting network state.

    Request body::

        {
          "nodes": ["A", "B", "C", "D"],
          "edges": [["A", "B"], ["B", "C"], ["C", "D"]],
          "failed_edges": [["B", "C"]],
          "failed_nodes": []
        }
    """
    data = request.get_json(force=True)
    G = _parse_graph(data)
    failed_edges = [tuple(e) for e in data.get("failed_edges", [])]
    failed_nodes = data.get("failed_nodes", [])
    return jsonify(engine.simulate_failure(G, failed_edges, failed_nodes))


if __name__ == "__main__":
    app.run(debug=True, port=5000)
