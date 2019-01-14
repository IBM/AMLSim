"""Generate and output scale-free graph as a degree-distribution CSV file

"""

import networkx as nx
from collections import Counter
import csv
import sys

argv = sys.argv
if len(argv) < 4:
  print("Usage: python %s [Vertices] [EdgeFactor] [DegCSV]" % argv[0])
  exit(1)

n = int(argv[1])
p = 0.1


factor = int(argv[2])
# g_ = nx.barabasi_albert_graph(n, factor, seed=0)
g_ = nx.scale_free_graph(n, seed=0)
g = nx.DiGraph(g_)  # Convert the generated to a directed graph without parallel edges

print g  # Graph Type
print g.number_of_nodes()  # Number of vertices (accounts)
print g.number_of_edges()  # Number of edges (transactions)

in_deg = Counter(g.in_degree().values())
out_deg = Counter(g.out_degree().values())

keys = set(sorted(in_deg.keys() + out_deg.keys()))

with open(argv[3], "w") as wf:
  writer = csv.writer(wf)
  writer.writerow(["Count","In-degree","Out-degree"])
  for k in keys:
    writer.writerow([k, in_deg[k], out_deg[k]])


