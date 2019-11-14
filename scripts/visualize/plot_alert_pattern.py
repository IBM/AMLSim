import os
import sys
import csv
import json
import networkx as nx
from collections import defaultdict

import matplotlib
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore', category=matplotlib.cbook.deprecation.MatplotlibDeprecationWarning)


def plot_alerts(_conf_json, _output_png):
    g = nx.DiGraph()
    bank_accts = defaultdict(list)

    with open(_conf_json, "r") as rf:
        conf = json.load(rf)
    data_dir = conf["output"]["directory"]
    acct_csv = os.path.join(data_dir, conf["output"]["alert_members"])
    tx_csv = os.path.join(data_dir, conf["output"]["alert_transactions"])

    with open(acct_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)

        for row in reader:
            acct_id = row[3]
            bank_id = row[9]
            g.add_node(acct_id, bank_id=bank_id)
            bank_accts[bank_id].append(acct_id)

    with open(tx_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)

        for row in reader:
            orig_id = row[4]
            bene_id = row[5]
            amount = row[7]
            date = row[8].split("T")[0]  # Extract only the date
            label = amount + "\n" + date
            g.add_edge(orig_id, bene_id, amount=amount, date=date, label=label)

    bank_ids = bank_accts.keys()
    cmap = plt.get_cmap("tab10")
    # pos = nx.spring_layout(g)
    pos = nx.nx_agraph.graphviz_layout(g)

    plt.figure(figsize=(12.0, 8.0))
    plt.axis('off')

    for i, bank_id in enumerate(bank_ids):
        color = cmap(i)
        accts = bank_accts[bank_id]
        nx.draw_networkx_nodes(g, pos, accts, node_size=300, node_color=color, label=bank_id)
        nx.draw_networkx_labels(g, pos, {n: n for n in accts}, font_size=10)

    edge_labels = nx.get_edge_attributes(g, "label")
    nx.draw_networkx_edges(g, pos)
    nx.draw_networkx_edge_labels(g, pos, edge_labels, font_size=6)

    plt.legend(numpoints = 1)
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    plt.savefig(_output_png, dpi=120)


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 3:
        print("Usage: python3 %s [ConfJSON] [OutputPNG]" % argv[0])
        exit(1)

    conf_json = argv[1]
    output_png = argv[2]
    plot_alerts(conf_json, output_png)
