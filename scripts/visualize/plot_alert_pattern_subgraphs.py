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


def load_alerts(_conf_json):
    _g = nx.DiGraph()
    _bank_accts = defaultdict(list)

    with open(_conf_json, "r") as rf:
        conf = json.load(rf)
    
    data_dir = os.path.join(conf["output"]["directory"], conf["general"]["simulation_name"])
    acct_csv = os.path.join(data_dir, conf["output"]["alert_members"])
    tx_csv = os.path.join(data_dir, conf["output"]["alert_transactions"])

    input_dir = conf["input"]["directory"]
    schema_json = os.path.join(input_dir, conf["input"]["schema"])
    with open(schema_json, "r") as rf:
        schema = json.load(rf)

    acct_idx = None
    bank_idx = None
    orig_idx = None
    bene_idx = None
    amt_idx = None
    date_idx = None
    for i, col in enumerate(schema["alert_member"]):
        if col.get("dataType") == "account_id":
            acct_idx = i
        elif col.get("dataType") == "bank_id":
            bank_idx = i
    for i, col in enumerate(schema["alert_tx"]):
        if col.get("dataType") == "orig_id":
            orig_idx = i
        elif col.get("dataType") == "dest_id":
            bene_idx = i
        elif col.get("dataType") == "amount":
            amt_idx = i
        elif col.get("dataType") == "timestamp":
            date_idx = i

    with open(acct_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            acct_id = row[acct_idx]
            bank_id = row[bank_idx]
            _g.add_node(acct_id, bank_id=bank_id)
            _bank_accts[bank_id].append(acct_id)

    with open(tx_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            orig_id = row[orig_idx]
            bene_id = row[bene_idx]
            amount = row[amt_idx]
            date = row[date_idx].split("T")[0]  # Extract only the date
            label = amount + "\n" + date
            _g.add_edge(orig_id, bene_id, amount=amount, date=date, label=label)

    return _g, _bank_accts


def plot_alerts(_g, _bank_accts, _output_png):
    bank_ids = _bank_accts.keys()
    cmap = plt.get_cmap("tab10")
    pos = nx.nx_agraph.graphviz_layout(_g)

    plt.figure(figsize=(12.0, 8.0))
    plt.axis('off')

    for i, bank_id in enumerate(bank_ids):
        color = cmap(i)
        members = _bank_accts[bank_id]
        nx.draw_networkx_nodes(_g, pos, members, node_size=300, node_color=color, label=bank_id)
        nx.draw_networkx_labels(_g, pos, {n: n for n in members}, font_size=10)

    edge_labels = nx.get_edge_attributes(_g, "label")
    nx.draw_networkx_edges(_g, pos)
    nx.draw_networkx_edge_labels(_g, pos, edge_labels, font_size=6)

    plt.legend(numpoints=1)
    plt.subplots_adjust(left=0, right=1, bottom=0, top=1)
    plt.savefig(_output_png, dpi=120)


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 3:
        print("Usage: python3 %s [ConfJSON] [OutputPNG]" % argv[0])
        exit(1)

    conf_json = argv[1]
    output_png = argv[2]
    g, bank_accts = load_alerts(conf_json)
    plot_alerts(g, bank_accts, output_png)
