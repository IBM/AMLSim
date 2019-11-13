"""
Generate scale-free graph and output degree-distribution CSV file
"""

import numpy as np
import networkx as nx
from collections import Counter
import csv
import sys


def kronecker_generator(scale, edge_factor):
    """Kronecker graph generator
  Ported from octave code in https://graph500.org/?page_id=12#alg:generator
  """
    N = 2 ** scale  # Number of vertices
    M = N * edge_factor  # Number of edges
    A, B, C = (0.57, 0.19, 0.19)  # Initiator probabilities
    ijw = np.ones((3, M))  # Index arrays

    ab = A + B
    c_norm = C / (1 - (A + B))
    a_norm = A / (A + B)

    for ib in range(scale):
        ii_bit = (np.random.rand(1, M) > ab).astype(int)
        ac = c_norm * ii_bit + a_norm * (1 - ii_bit)
        jj_bit = (np.random.rand(1, M) > ac).astype(int)
        ijw[:2, :] = ijw[:2, :] + 2 ** ib * np.vstack((ii_bit, jj_bit))

    ijw[2, :] = np.random.rand(1, M)
    ijw[:2, :] = ijw[:2, :] - 1
    q = range(M)
    np.random.shuffle(q)
    ijw = ijw[:, q]
    edges = ijw[:2, :].astype(int).T
    _g = nx.DiGraph()
    _g.add_edges_from(edges)
    return _g


def kronecker_generator_general(_n, _m):
    # TODO: Accept general number of nodes and edges
    A, B, C = (0.57, 0.19, 0.19)  # Initiator probabilities
    ijw = np.ones((3, _m))  # Index arrays
    ab = A + B
    c_norm = C / (1 - (A + B))
    a_norm = A / (A + B)
    tmp = _n
    while tmp > 0:
        tmp //= 2
        ii_bit = (np.random.rand(1, _m) > ab).astype(int)
        ac = c_norm * ii_bit + a_norm * (1 - ii_bit)
        jj_bit = (np.random.rand(1, _m) > ac).astype(int)
        ijw[:2, :] = ijw[:2, :] + tmp * np.vstack((ii_bit, jj_bit))
    ijw[2, :] = np.random.rand(1, _m)
    ijw[:2, :] = ijw[:2, :] - 1
    q = range(_m)
    np.random.shuffle(q)
    ijw = ijw[:, q]
    edges = ijw[:2, :].astype(int).T
    _g = nx.DiGraph()
    _g.add_edges_from(edges)
    return _g


def powerlaw_cluster_generator(_n, _edge_factor):
    edges = nx.barabasi_albert_graph(_n, _edge_factor, seed=0).edges()  # Undirected edges

    # Swap the direction of half edges to diffuse degree
    di_edges = [(edges[i][0], edges[i][1]) if i % 2 == 0 else (edges[i][1], edges[i][0]) for i in range(len(edges))]
    _g = nx.DiGraph()
    _g.add_edges_from(di_edges)  # Create a directed graph
    return _g


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 4:
        print("Usage: python3 %s [NumVertices] [EdgeFactor] [DegCSV]" % argv[0])
        exit(1)

    n = int(argv[1])
    factor = int(argv[2])
    g = powerlaw_cluster_generator(n, factor)

    print("Number of vertices: %d" % g.number_of_nodes())  # Number of vertices (accounts)
    print("Number of edges: %d" % g.number_of_edges())  # Number of edges (transactions)

    in_deg = Counter(g.in_degree().values())
    out_deg = Counter(g.out_degree().values())

    keys = set(sorted(list(in_deg.keys()) + list(out_deg.keys())))

    with open(argv[3], "w") as wf:
        writer = csv.writer(wf)
        writer.writerow(["Count", "In-degree", "Out-degree"])
        for k in keys:
            # Degree, number of vertices for in-degree, number of vertices for out-degree
            writer.writerow([k, in_deg[k], out_deg[k]])
