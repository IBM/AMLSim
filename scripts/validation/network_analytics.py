"""
Load output files from AMLSim and create NetworkX graph for analytics
"""
import os
import sys
import csv
from datetime import datetime, timedelta
from dateutil.parser import parse
from collections import Counter
import networkx as nx
import json


# Account (vertex) and transaction (edge) attribute keys
ACCT_SAR = "sar"
TX_AMOUNT = "amount"
TX_DATE = "date"

DEGREE_STEP = 5  # Interval of degrees


def load_base_csv(acct_csv, tx_csv, schema_data):
    """Load account and transaction list CSV from the transaction graph generator (before running AMLSim)
    :param acct_csv: Account list CSV
    :param tx_csv: Transaction list CSV
    :param schema_data: Schema data from JSON file
    :return: Base transaction network as a NetworkX graph object
    """
    return None


def load_result_csv(acct_csv: str, tx_csv: str, schema_data) -> nx.MultiDiGraph:
    """Load account list CSV and transaction list CSV from AMLSim and generate transaction graph
    :param acct_csv: Account list CSV
    :param tx_csv: Transaction list CSV
    :param schema_data: Schema data from JSON
    :return: Transaction network as a NetworkX graph object
    """
    acct_id_idx = None
    acct_sar_idx = None
    tx_src_idx = None
    tx_dst_idx = None
    tx_amt_idx = None
    tx_date_idx = None
    is_date_type = False
    base_date = datetime(1970, 1, 1)

    for idx, col in enumerate(schema_data["account"]):
        data_type = col.get("dataType")
        if data_type == "account_id":
            acct_id_idx = idx
        elif data_type == "sar_flag":
            acct_sar_idx = idx
    for idx, col in enumerate(schema_data["transaction"]):
        data_type = col.get("dataType")
        if data_type == "orig_id":
            tx_src_idx = idx
        elif data_type == "dest_id":
            tx_dst_idx = idx
        elif data_type == "amount":
            tx_amt_idx = idx
        elif data_type == "timestamp":
            tx_date_idx = idx
            is_date_type = col.get("valueType") == "date"

    _g = nx.MultiDiGraph()
    num_accts = 0
    num_sar = 0
    num_txs = 0
    # Load account list CSV
    print("Load account list CSV file", acct_csv)
    with open(acct_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)  # Skip header
        for row in reader:
            acct_id = row[acct_id_idx]  # Account ID
            is_sar = row[acct_sar_idx].lower() == "true"  # SAR flag
            attr = {ACCT_SAR: is_sar}
            _g.add_node(acct_id, **attr)
            num_accts += 1
            if is_sar:
                num_sar += 1
    print("Number of total accounts: %d" % num_accts)
    print("Number of SAR accounts: %d (%.2f%%)" % (num_sar, num_sar/num_accts*100))

    # Load transaction list CSV
    print("Loading transaction list CSV file", tx_csv)
    with open(tx_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)  # Skip header
        for row in reader:
            src_id = row[tx_src_idx]  # Originator account ID
            dst_id = row[tx_dst_idx]  # Beneficiary account ID
            amount = float(row[tx_amt_idx])  # TX_AMOUNT
            date = parse(row[tx_date_idx]) if is_date_type else base_date + timedelta(int(row[tx_date_idx]))
            date_str = date.strftime("%Y-%m-%d")
            attr = {TX_AMOUNT: amount, TX_DATE: date_str}
            _g.add_edge(src_id, dst_id, **attr)
            num_txs += 1
            if num_txs % 100000 == 0:
                print("Loaded %d transactions" % num_txs)
    print("Number of transactions: %d" % num_txs)
    return _g


def load_alert_csv(_g, alert_acct_csv, alert_tx_csv, schema_data):
    """Load alert member and transaction lists
    """
    acct_id_idx = None


class __TransactionGraphLoader:

    def __init__(self, _conf_json):
        with open(_conf_json, "r") as rf:
            self.conf = json.load(rf)
        schema_json = os.path.join(self.conf["input"]["directory"], self.conf["input"]["schema"])
        with open(schema_json, "r") as rf:
            self.schema = json.load(rf)
        self.output_conf = self.conf["output"]
        self.g = nx.MultiDiGraph()
        self.sim_name = self.conf["general"]["simulation_name"]

    def get_graph(self):
        return self.g

    def count_hub_accounts(self, min_degree=DEGREE_STEP, max_degree=10):
        """Count number of "hub" accounts by degree
        """
        in_deg = Counter(self.g.in_degree().values())  # in-degree, count
        out_deg = Counter(self.g.out_degree().values())  # out-degree, count
        for th in range(min_degree, max_degree + 1, DEGREE_STEP):
            num_fan_in = sum([c for d, c in in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in out_deg.items() if d >= th])
            print("\tNumber of fan-in / fan-out patterns with", th, "or more neighbors:", num_fan_in, "/", num_fan_out)


class BaseGraphLoader(__TransactionGraphLoader):

    def __init__(self, _conf_json):
        super(BaseGraphLoader, self).__init__(_conf_json)


class ResultGraphLoader(__TransactionGraphLoader):

    def __init__(self, _conf_json):
        super(ResultGraphLoader, self).__init__(_conf_json)

        # Create a transaction graph from output files
        output_dir = os.path.join(self.output_conf["directory"], self.sim_name)
        acct_file = self.output_conf["accounts"]
        tx_file = self.output_conf["transactions"]
        alert_acct_file = self.output_conf["alert_members"]
        alert_tx_file = self.output_conf["alert_transactions"]

        acct_path = os.path.join(output_dir, acct_file)
        tx_path = os.path.join(output_dir, tx_file)
        self.g = load_result_csv(acct_path, tx_path, self.schema)
        self.num_normal_accts = len([n for n, flag in nx.get_node_attributes(self.g, ACCT_SAR).items() if not flag])
        self.num_sar_accts = len([n for n, flag in nx.get_node_attributes(self.g, ACCT_SAR).items() if flag])

    def count_hub_accounts(self, min_degree=DEGREE_STEP, max_degree=10):
        super(ResultGraphLoader, self).count_hub_accounts(min_degree, max_degree)

        # Extract the same statistical data for normal and alert account vertices
        normal_in_deg = Counter([v for k, v in self.g.in_degree().items() if not self.g.node[k][ACCT_SAR]])
        normal_out_deg = Counter([v for k, v in self.g.out_degree().items() if not self.g.node[k][ACCT_SAR]])
        sar_in_deg = Counter([v for k, v in self.g.in_degree().items() if self.g.node[k][ACCT_SAR]])
        sar_out_deg = Counter([v for k, v in self.g.out_degree().items() if self.g.node[k][ACCT_SAR]])

        print("Number of fan-in / fan-out patterns for %d normal accounts" % self.num_normal_accts)
        for th in range(min_degree, max_degree + 1, DEGREE_STEP):
            num_fan_in = sum([c for d, c in normal_in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in normal_out_deg.items() if d >= th])
            ratio_fan_in = num_fan_in / self.num_normal_accts
            ratio_fan_out = num_fan_out / self.num_normal_accts
            print("\tNumber of fan-in / fan-out patterns with %d or more neighbors: %d (%.2f%%)/ %d (%.2f%%)" %
                  (th, num_fan_in, ratio_fan_in * 100, num_fan_out, ratio_fan_out * 100))

        print("Number of fan-in / fan-out patterns for %d SAR accounts" % self.num_sar_accts)
        for th in range(min_degree, max_degree + 1, DEGREE_STEP):
            num_fan_in = sum([c for d, c in sar_in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in sar_out_deg.items() if d >= th])
            ratio_fan_in = num_fan_in / self.num_sar_accts
            ratio_fan_out = num_fan_out / self.num_sar_accts
            print("\tNumber of fan-in / fan-out patterns with %d or more neighbors: %d (%.2f%%)/ %d (%.2f%%)" %
                  (th, num_fan_in, ratio_fan_in * 100, num_fan_out, ratio_fan_out * 100))


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    conf_json = argv[1]

    # Base transaction network (as input of the simulator) analytics
    # bgl = BaseGraphLoader(conf_json)

    # Generated transaction network analysis as the final result
    rgl = ResultGraphLoader(conf_json)
    rgl.count_hub_accounts(5, 25)
