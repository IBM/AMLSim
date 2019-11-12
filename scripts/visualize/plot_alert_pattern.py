import sys
import csv
import networkx as nx
from collections import defaultdict

import matplotlib.pyplot as plt
from matplotlib import animation


def plot_alert(tx_csv):
    g = nx.Graph()
    edges = list()
    alert_st = dict()
    alert_ed = dict()
    acct_alert = defaultdict(set)
    e_suspicious = defaultdict(set)

    with open(tx_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)

        for row in reader:
            step = int(row[0])
            src = row[3]
            dst = row[6]
            isSAR = int(row[9]) > 0
            alertID = int(row[10])
            g.add_edge(src, dst)
            edges.append((step, src, dst))
            acct_alert[src].add(alertID)
            acct_alert[dst].add(alertID)

            if isSAR:
                if alertID not in alert_st:
                    alert_st[alertID] = step

                if alertID not in alert_ed or alert_ed[alertID] < step:
                    alert_ed[alertID] = step

                e_suspicious[step].add((src, dst))
                e_suspicious[step].add((dst, src))

    pos = nx.spring_layout(g)
    sub_g = nx.DiGraph()

    steps = list(range(30))  # sorted(set([e[0] for e in edges]))

    def show_graph(i):
        if i != 0:
            plt.cla()

        def within_acct(acct):
            alertIDs = acct_alert[acct]
            return True in [alert_st.get(alert, -1) <= i <= alert_ed.get(alert, -1) for alert in alertIDs]

        new_edges = [(_src, _dst) for (st, _src, _dst) in edges if st == steps[i]]
        sub_g.add_edges_from(new_edges)
        nodes = sub_g.nodes()
        all_edges = sub_g.edges()
        node_colors = ["r" if within_acct(n) else "b" for n in nodes]
        edge_colors = ["r" if e in e_suspicious[i] else "k" for e in all_edges]

        plt.title("Step %d" % steps[i])
        plt.xlim([-1.0, 1.0])
        plt.ylim([-1.0, 1.0])
        nx.draw_networkx_nodes(sub_g, pos, nodelist=nodes, node_color=node_colors, node_size=50)
        nx.draw_networkx_edges(sub_g, pos, edgelist=all_edges, edge_color=edge_colors, arrowsize=5, width=0.5)

    fig = plt.figure()
    anim = animation.FuncAnimation(fig, show_graph, frames=len(steps))
    anim.save('tx.gif', writer='imagemagick', fps=1)


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: python %s [TxCSV]" % argv[0])
        exit(1)

    plot_alert(argv[1])
