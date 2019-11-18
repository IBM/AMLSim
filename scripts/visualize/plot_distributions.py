"""
Plot statistical distributions from the transaction graph.
"""

import os
import sys
import csv
import json
from collections import Counter, defaultdict
import networkx as nx
import powerlaw
from datetime import datetime, timedelta

import matplotlib
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore', category=matplotlib.cbook.deprecation.MatplotlibDeprecationWarning)


def get_date_list(_g):
    all_dates = list(nx.get_edge_attributes(_g, "date").values())
    start_date = min(all_dates)
    end_date = max(all_dates)
    days = (end_date - start_date).days + 1
    date_list = [start_date + timedelta(days=n) for n in range(days)]
    return date_list


def construct_graph(_acct_csv, _tx_csv, _schema):
    """Load transaction CSV file and construct Graph
    :param _acct_csv: Account CSV file (e.g. output/accounts.csv)
    :param _tx_csv: Transaction CSV file (e.g. output/transactions.csv)
    :param _schema: Dict for schema from JSON file
    :return: Transaction Graph
    :rtype: nx.MultiDiGraph
    """
    _g = nx.MultiDiGraph()

    id_idx = None
    bank_idx = None
    sar_idx = None

    acct_schema = _schema["account"]
    for i, col in enumerate(acct_schema):
        data_type = col.get("dataType")
        if data_type == "account_id":
            id_idx = i
        elif data_type == "bank_id":
            bank_idx = i
        elif data_type == "sar_flag":
            sar_idx = i

    orig_idx = None
    bene_idx = None
    type_idx = None
    amt_idx = None
    date_idx = None

    with open(_acct_csv, "r") as _rf:
        reader = csv.reader(_rf)
        next(reader)  # Skip header

        for row in reader:
            acct_id = row[id_idx]
            bank_id = row[bank_idx]
            is_sar = row[sar_idx].lower() == "true"
            _g.add_node(acct_id, bank_id=bank_id, is_sar=is_sar)

    tx_schema = _schema["transaction"]
    for i, col in enumerate(tx_schema):
        data_type = col.get("dataType")
        if data_type == "orig_id":
            orig_idx = i
        elif data_type == "dest_id":
            bene_idx = i
        elif data_type == "transaction_type":
            type_idx = i
        elif data_type == "amount":
            amt_idx = i
        elif data_type == "timestamp":
            date_idx = i
        elif data_type == "sar_flag":
            sar_idx = i

    with open(_tx_csv, "r") as _rf:
        reader = csv.reader(_rf)
        next(reader)  # Skip header

        for row in reader:
            orig = row[orig_idx]
            bene = row[bene_idx]
            tx_type = row[type_idx]
            amount = float(row[amt_idx])
            date = datetime.strptime(row[date_idx].split("T")[0], "%Y-%m-%d")
            is_sar = row[sar_idx].lower() == "true"
            _g.add_edge(orig, bene, amount=amount, date=date, type=tx_type, is_sar=is_sar)

    return _g


def plot_degree_distribution(_g, plot_img):
    """Plot degree distribution for accounts (vertices)
    :param _g: Transaction graph
    :param plot_img: Degree distribution image (log-log plot)
    :return:
    """
    degrees = list(_g.degree().values())
    deg_seq = sorted(set(degrees), reverse=True)
    deg_hist = [degrees.count(x) for x in deg_seq]

    pw_result = powerlaw.Fit(degrees)
    alpha = pw_result.power_law.alpha
    alpha_text = "alpha = %f" % alpha
    print(alpha_text)

    plt.clf()
    fig, ax = plt.subplots(1, 1)
    ax.loglog(deg_seq, deg_hist, 'bo-')
    plt.text(0.1, 0.1, alpha_text, transform=ax.transAxes)
    plt.title("Degree Distribution")
    plt.xlabel("Degree")
    plt.ylabel("Number of accounts")
    plt.savefig(plot_img)


def plot_wcc_distribution(_g, plot_img):
    """Plot weakly connected components size distributions
    :param _g: Transaction graph
    :param plot_img: WCC size distribution image (log-log plot)
    :return:
    """
    all_wcc = nx.weakly_connected_components(_g)
    wcc_sizes = Counter([len(wcc) for wcc in all_wcc])
    size_seq = sorted(wcc_sizes.keys())
    size_hist = [wcc_sizes[x] for x in size_seq]

    plt.clf()
    plt.loglog(size_seq, size_hist, 'ro-')
    plt.title("WCC Size Distribution")
    plt.xlabel("Size")
    plt.ylabel("Number of WCCs")
    plt.savefig(plot_img)


def plot_aml_rule(aml_csv, plot_img):
    """Plot the number of AML typologies
    :param aml_csv: AML typology pattern parameter CSV file
    :param plot_img: Output image file (bar plot)
    """
    aml_types = Counter()
    num_idx = None
    type_idx = None

    with open(aml_csv, "r") as _rf:
        reader = csv.reader(_rf)
        header = next(reader)
        for i, k in enumerate(header):
            if k == "count":
                num_idx = i
            elif k == "type":
                type_idx = i

        for row in reader:
            if "#" in row[0]:
                continue
            num = int(row[num_idx])
            aml_type = row[type_idx]
            aml_types[aml_type] += num

    x = list()
    y = list()
    for aml_type, num in aml_types.items():
        x.append(aml_type)
        y.append(num)

    plt.clf()
    plt.bar(range(len(x)), y, tick_label=x)
    plt.title("AML typologies")
    plt.xlabel("Typology name")
    plt.ylabel("Number of patterns")
    plt.savefig(plot_img)


def plot_tx_count(_g, plot_img):
    """Plot the number of normal and SAR transactions (excludes cash transactions)
    :param _g: Transaction graph
    :param plot_img: Output image file path
    """
    date_list = get_date_list(_g)
    normal_tx_count = Counter()
    sar_tx_count = Counter()

    for _, _, attr in _g.edges(data=True):
        is_sar = attr["is_sar"]
        date = attr["date"]
        if is_sar:
            sar_tx_count[date] += 1
        else:
            normal_tx_count[date] += 1

    normal_tx_list = [normal_tx_count[d] for d in date_list]
    sar_tx_list = [sar_tx_count[d] for d in date_list]

    plt.clf()
    p_n = plt.plot(date_list, normal_tx_list, "b")
    p_f = plt.plot(date_list, sar_tx_list, "r")
    plt.yscale('log')
    plt.legend((p_n[0], p_f[0]), ("Normal", "SAR"))
    plt.title("Number of transactions per step")
    plt.xlabel("Simulation step")
    plt.ylabel("Number of transactions")
    plt.savefig(plot_img)


def plot_clustering_coefficient(_g, plot_img, interval=10):
    """Plot the clustering coefficient transition
    :param _g: Transaction graph
    :param plot_img: Output image file
    :param interval: Simulation step interval for plotting (it takes too much time to compute clustering coefficient)
    :return:
    """
    date_list = get_date_list(_g)

    gg = nx.Graph()
    edges = defaultdict(list)
    for k, v in nx.get_edge_attributes(_g, "date").items():
        e = (k[0], k[1])
        edges[v].append(e)

    sample_dates = list()
    values = list()
    for i, t in enumerate(date_list):
        gg.add_edges_from(edges[t])
        if i % interval == 0:
            v = nx.average_clustering(gg) if gg.number_of_nodes() else 0.0
            # date_str = datetime.strftime(t, "%Y-%m-%d")
            # print("Date: %s, Coefficient: %f" % (date_str, v))
            sample_dates.append(t)
            values.append(v)

    plt.clf()
    plt.plot(sample_dates, values, 'bo-')
    plt.title("Clustering Coefficient Transition")
    plt.xlabel("date")
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

    with open(dia_csv, "r") as _rf:
        reader = csv.reader(_rf)
        next(reader)
        for row in reader:
            step = int(row[0])
            d = float(row[1])
            a = float(row[2])
            x.append(step)
            dia.append(d)
            aver.append(a)

    plt.clf()
    plt.ylim(0, max(dia) + 1)
    p_d = plt.plot(x, dia, "r")
    p_a = plt.plot(x, aver, "b")
    plt.legend((p_d[0], p_a[0]), ("Diameter", "Average"))
    plt.title("Diameter and Average Distance")
    plt.xlabel("Simulation step")
    plt.ylabel("Distance")
    plt.savefig(plot_img)


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    conf_json = argv[1]
    with open(conf_json, "r") as rf:
        conf = json.load(rf)

    input_dir = conf["input"]["directory"]
    schema_json = conf["input"]["schema"]
    schema_path = os.path.join(input_dir, schema_json)

    with open(schema_path, "r") as rf:
        schema = json.load(rf)

    data_dir = conf["output"]["directory"]
    acct_csv = conf["output"]["accounts"]
    tx_csv = conf["output"]["transactions"]
    acct_path = os.path.join(data_dir, acct_csv)
    tx_path = os.path.join(data_dir, tx_csv)

    tmp_dir = conf["temporal"]["directory"]
    output_dir = conf["output"]["directory"]
    sim_name = conf["general"]["simulation_name"]
    if not os.path.exists(tx_path):
        print("Transaction list CSV file %s not found." % tx_path)
        exit(1)

    g = construct_graph(acct_path, tx_path, schema)
    output_path = os.path.join(output_dir, sim_name)
    if os.path.isdir(output_path):
        print("Warning: this output directory %s already exists." % output_path)
    else:
        os.makedirs(output_path)

    v_conf = conf["visualizer"]
    deg_plot = v_conf["degree"]
    wcc_plot = v_conf["wcc"]
    alert_plot = v_conf["alert"]
    count_plot = v_conf["count"]
    cc_plot = v_conf["clustering"]
    dia_plot = v_conf["diameter"]

    plot_degree_distribution(g, os.path.join(output_path, deg_plot))
    plot_wcc_distribution(g, os.path.join(output_path, wcc_plot))

    param_dir = conf["input"]["directory"]
    alert_param = conf["input"]["alert_patterns"]
    plot_aml_rule(os.path.join(param_dir, alert_param), os.path.join(output_path, alert_plot))

    plot_tx_count(g, os.path.join(output_path, count_plot))

    plot_clustering_coefficient(g, os.path.join(output_path, cc_plot))

    dia_log = conf["output"]["diameter_log"]
    if os.path.exists(dia_log):
        plot_diameter(os.path.join(tmp_dir, sim_name, dia_log), os.path.join(output_path, dia_plot))
    else:
        print("Diameter log file %s not found." % dia_log)
