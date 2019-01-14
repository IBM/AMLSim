import sys
import networkx as nx
import matplotlib.pyplot as plt
import csv


def load_log(fname):

  rf = open(fname, "r")
  reader = csv.reader(rf)
  header = next(reader)

  idx_step = -1
  idx_amount = -1
  idx_orig = -1
  idx_dest = -1
  idx_fraud = -1
  idx_alert = -1

  for i, k in enumerate(header):
    if k == "step":
      idx_step = i
    elif k == "amount":
      idx_amount = i
    elif k == "nameOrig":
      idx_orig = i
    elif k == "nameDest":
      idx_dest = i
    elif k == "isFraud":
      idx_fraud = i
    elif k == "alertID":
      idx_alert = i

  g = nx.MultiDiGraph()

  for row in reader:
    step = int(row[idx_step])
    amount = float(row[idx_amount])
    orig = int(row[idx_orig])
    dest = int(row[idx_dest])
    isFraud = row[idx_fraud] == "1"
    alertID = int(row[idx_alert])

    g.add_edge(orig, dest, step=step, amount=amount, isFraud=isFraud, alertID=alertID)

  rf.close()

  return g


def get_alert_graph(g, alertID):
  edge_alerts = nx.get_edge_attributes(g, "alertID")
  edges = [k for k, v in edge_alerts.iteritems() if v == alertID]
  # g_ = nx.MultiDiGraph()
  # g_.add_edges_from(edges)
  g_ = g.edge_subgraph(edges)
  return g_


def plot_graph(g):
  # weights = nx.get_edge_attributes(g, "amount").values()
  pos = nx.spring_layout(g)
  nx.draw_networkx_nodes(g, pos, node_size=100)
  nx.draw_networkx_edges(g, pos)

  steps = {(src, dst): v for (src, dst, k), v in nx.get_edge_attributes(g, "step").iteritems()}
  amounts = {(src, dst): v for (src, dst, k), v in nx.get_edge_attributes(g, "amount").iteritems()}
  # print steps, amounts
  edge_labels = {e: "{:d}:{:.2f}".format(st, amounts[e]) for e, st in steps.iteritems()}
  labels = nx.draw_networkx_edge_labels(g, pos, edge_labels)
  # print labels
  plt.show()


if __name__ == "__main__":
  argv = sys.argv
  if len(argv) < 3:
    print("Usage: python %s [TxLog] [AlertID]" % argv[0])
    exit(1)

  log_name = argv[1]
  alertID = int(argv[2])
  g = load_log(log_name)
  g_ = get_alert_graph(g, alertID)
  plot_graph(g_)




