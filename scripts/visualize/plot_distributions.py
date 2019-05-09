"""
Plot statistical distributions from the transaction graph.
"""

import os
import sys
import csv
from ConfigParser import ConfigParser
from collections import Counter, defaultdict
import networkx as nx
import powerlaw

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


CASH_TYPE = {"CASH-IN", "CASH-OUT"}

def load_csv(tx_csv):
  """Load transaction CSV file and create Graph
  :param tx_csv: Input transaction CSV file (e.g. tx.csv)
  :return: Transaction Graph
  :rtype: nx.Graph
  """
  g = nx.DiGraph()
  with open(tx_csv, "r") as rf:
    reader = csv.reader(rf)
    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}
    src_idx = indices["SENDER_ACCOUNT_ID"]
    dst_idx = indices["RECEIVER_ACCOUNT_ID"]
    type_idx = indices["TX_TYPE"]
    time_idx = indices["TIMESTAMP"]

    for row in reader:
      src = row[src_idx]
      dst = row[dst_idx]
      ttype = row[type_idx]
      step = int(row[time_idx])
      if ttype in CASH_TYPE:
        continue
      g.add_edge(src, dst, step=step)
  return g

def plot_degree_distribution(g, plot_img):
  """Plot degree distribution for accounts (vertices)
  :param g: Transaction graph
  :param plot_img: Degree distribution image (log-log plot)
  :return:
  """
  degrees = g.degree().values()
  deg_seq = sorted(set(degrees),reverse=True)
  deg_hist = [degrees.count(x) for x in deg_seq]

  pw_result = powerlaw.Fit(degrees)
  alpha = pw_result.power_law.alpha
  alpha_text = "alpha = %f" % alpha
  print(alpha_text)

  plt.clf()
  fig, ax = plt.subplots(1,1)
  ax.loglog(deg_seq, deg_hist, 'bo-')
  plt.text(0.1, 0.1, alpha_text, transform=ax.transAxes)
  plt.title("Degree Distribution")
  plt.xlabel("Degree")
  plt.ylabel("Number of accounts")
  plt.savefig(plot_img)


def plot_wcc_distribution(g, plot_img):
  """Plot weakly connected components size distribution

  :param g: Transaction graph
  :param plot_img: WCC size distribution image (log-log plot)
  :return:
  """
  wccs = nx.weakly_connected_components(g)
  wcc_sizes = Counter([len(wcc) for wcc in wccs])
  sizes = wcc_sizes.keys()
  size_seq = sorted(set(sizes))
  size_hist = [wcc_sizes[x] for x in size_seq]

  plt.clf()
  plt.loglog(size_seq, size_hist, 'ro-')
  plt.title("WCC Size Distribution")
  plt.xlabel("Size")
  plt.ylabel("Number of WCCs")
  plt.savefig(plot_img)


def plot_aml_rule(aml_csv, plot_img):
  """Plot the number of fraud patterns

  :param aml_csv: Fraud pattern parameter CSV file
  :param plot_img: Output image file (bar plot)
  :return:
  """
  aml_types = Counter()

  with open(aml_csv, "r") as rf:
    reader = csv.reader(rf)
    next(reader)
    for row in reader:
      if "#" in row[0]:
        continue
      num = int(row[0])
      ttype = row[1]
      aml_types[ttype] += num

  x = list()
  y = list()
  for ttype, num in aml_types.iteritems():
    x.append(ttype)
    y.append(num)

  plt.clf()
  plt.bar(range(len(x)), y, tick_label=x)
  plt.title("Fraud patterns")
  plt.xlabel("Fraud type")
  plt.ylabel("Number of patterns")
  plt.savefig(plot_img)



def plot_tx_count(tx_step_csv, plot_img):
  """Plot the number of normal and fraud transactions (excludes cash transactions)

  :param tx_step_csv: Statistics CSV file
  :param plot_img: Output image file name
  :return:
  """

  x = list()
  normal = list()
  fraud = list()

  with open(tx_step_csv, "r") as rf:
    reader = csv.reader(rf)
    next(reader)
    for row in reader:
      step = int(row[0])
      if step > 0:
        num_n = int(row[1])
        num_f = int(row[2])
        x.append(step)
        normal.append(num_n)
        fraud.append(num_f)

  plt.clf()
  p_n = plt.plot(x, normal, "b")
  p_f = plt.plot(x, fraud, "r")
  plt.yscale('log')
  plt.legend((p_n[0], p_f[0]), ("Normal", "Fraud"))
  plt.title("Number of transactions per step")
  plt.xlabel("Simulation step")
  plt.ylabel("Number of transactions")
  plt.savefig(plot_img)


def plot_clustering_coefficient(g, plot_img, interval=10):
  """Plot the clustering coefficient transition

  :param g: Transaction graph
  :param plot_img: Output image file
  :param interval: Simulation step interval for plotting (it takes too much time to compute clustering coefficient)
  :return:
  """

  max_step = max(nx.get_edge_attributes(g, "step").values())
  steps = list(range(0, max_step, interval))
  values = list()

  gg = nx.Graph()
  edges = defaultdict(list)
  for k,v in nx.get_edge_attributes(g, "step").iteritems():
    edges[v].append(k)

  for t in range(max_step):
    gg.add_edges_from(edges[t])
    if t % interval == 0:
      v = nx.average_clustering(gg) if gg.number_of_nodes() else 0.0
      print("Step: %d, Coefficient: %f" % (t, v))
      values.append(v)

  plt.clf()
  plt.plot(steps, values, 'bo-')
  plt.title("Clustering Coefficient Transition")
  plt.xlabel("Step")
  plt.ylabel("Clustering Coefficient")
  plt.savefig(plot_img)



def plot_diameter(dia_csv, plot_img):
  """Plot the diameter and the average of largest distance transitions

  :param dia_csv: Diameter transition CSV file
  :param plot_img: Output image file
  :return:
  """
  x = list()
  dia = list()
  aver = list()

  with open(dia_csv, "r") as rf:
    reader = csv.reader(rf)
    next(reader)
    for row in reader:
      step = int(row[0])
      d = float(row[1])
      a = float(row[2])
      x.append(step)
      dia.append(d)
      aver.append(a)

  plt.clf()
  plt.ylim(0, max(dia)+1)
  p_d = plt.plot(x, dia, "r")
  p_a = plt.plot(x, aver, "b")
  plt.legend((p_d[0], p_a[0]), ("Diameter", "Average"))
  plt.title("Diameter and Average Distance")
  plt.xlabel("Simulation step")
  plt.ylabel("Distance")
  plt.savefig(plot_img)




if __name__ == "__main__":
  argv = sys.argv

  if len(argv) < 3:
    print("Usage: python %s [TxCSV] [PropINI] [AMLRuleCSV]" % argv[0])
    exit(1)

  tx_file = argv[1]
  conf_file = argv[2]

  if not os.path.exists(tx_file):
    print("Transaction file %s not found." % tx_file)
    exit(1)
  g = load_csv(tx_file)
  prop = ConfigParser()
  prop.read(conf_file)

  output_dir = prop.get("OutputFile", "directory")

  deg_plot = prop.get("PlotFile", "degree")
  wcc_plot = prop.get("PlotFile", "wcc")
  alert_plot = prop.get("PlotFile", "alert")
  count_plot = prop.get("PlotFile", "count")
  cc_plot = prop.get("PlotFile", "clustering")
  dia_plot = prop.get("PlotFile", "diameter")

  plot_degree_distribution(g, os.path.join(output_dir, deg_plot))
  plot_wcc_distribution(g, os.path.join(output_dir, wcc_plot))

  param_dir = prop.get("InputFile", "directory")
  amlrule = os.path.join(param_dir, prop.get("InputFile", "amlrule")) if len(argv) == 3 else argv[3]
  plot_aml_rule(amlrule, os.path.join(output_dir, alert_plot))

  tx_count = prop.get("OutputFile", "counter_log")
  plot_tx_count(os.path.join(output_dir, tx_count), os.path.join(output_dir, count_plot))

  plot_clustering_coefficient(g, os.path.join(output_dir, cc_plot))

  dia_log = prop.get("OutputFile", "diameter_log")
  if os.path.exists(dia_log):
    plot_diameter(os.path.join(output_dir, dia_log), os.path.join(output_dir, dia_plot))
  else:
    print("Diameter log file %s not found." % dia_log)


