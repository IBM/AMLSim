import sys
import networkx as nx
import matplotlib.pyplot as plt
import csv


def load_log(tx_log):
    rf = open(tx_log, "r")
    reader = csv.reader(rf)
    header = next(reader)

    idx_step = -1
    idx_amount = -1
    idx_orig = -1
    idx_dest = -1
    idx_sar = -1
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
        elif k == "isSAR":
            idx_sar = i
        elif k == "alertID":
            idx_alert = i

    g = nx.MultiDiGraph()

    for row in reader:
        step = int(row[idx_step])
        amount = float(row[idx_amount])
        orig = int(row[idx_orig])
        dest = int(row[idx_dest])
        is_sar = row[idx_sar] == "1"
        alert_id = int(row[idx_alert])
        g.add_edge(orig, dest, step=step, amount=amount, isSAR=is_sar, alertID=alert_id)

    rf.close()

    return g


def get_alert_graph(g, aid):
    g_ = nx.MultiDiGraph()
    for e in g.edges(keys=True, data=True):
        src, dst, key, data = e
        if data.get("alertID") == aid:
            g_.add_edge(src, dst, key=key, attr_dict=data)
    # print(g_.edges(data=True))
    return g_


def plot_graph(g):
    # weights = nx.get_edge_attributes(g, "amount").values()
    pos = nx.spring_layout(g)
    nx.draw_networkx_nodes(g, pos, node_size=100)
    nx.draw_networkx_edges(g, pos)

    steps = {(src, dst): v for (src, dst, k), v in nx.get_edge_attributes(g, "step").iteritems()}
    amounts = {(src, dst): v for (src, dst, k), v in nx.get_edge_attributes(g, "amount").iteritems()}
    edge_labels = {e: "{:d}:{:.2f}".format(st, amounts[e]) for e, st in steps.items()}
    labels = nx.draw_networkx_edge_labels(g, pos, edge_labels)
    plt.show()


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 3:
        print("Usage: python3 %s [TxLog] [AlertID]" % argv[0])
        exit(1)

    log_name = argv[1]
    alert = int(argv[2])
    print("Plot alert transaction subgraph (%d) from %s" % (alert, log_name))
    g = load_log(log_name)
    g_ = get_alert_graph(g, alert)
    plot_graph(g_)
