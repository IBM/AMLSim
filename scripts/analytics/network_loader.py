"""
Load output files from AMLSim and create NetworkX graph for analytics
"""
import os
import csv
from datetime import datetime, timedelta
from dateutil.parser import parse
from collections import Counter
import networkx as nx
import json


ACCT_SAR = "sar"
TX_AMOUNT = "amount"
TX_DATE = "date"


def load_base_csv(acct_csv, tx_csv, schema_data):
    pass


def load_result_csv(acct_csv: str, tx_csv: str, schema_data) -> nx.Graph:
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
        elif data_type == "fraud_flag":
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
            acct_id = row[acct_id_idx]  # ACCOUNT_ID
            is_sar = row[acct_sar_idx].lower() == "true"  # IS_FRAUD
            attr = {"sar": is_sar}
            _g.add_node(acct_id, **attr)
            num_accts += 1
            if is_sar:
                num_sar += 1
    print("Number of total accounts: %d" % num_accts)
    print("Number of SAR accounts: %d (%.2f%%)" % (num_sar, num_sar/num_accts*100))

    # Load transaction list CSV
    print("Load transaction list CSV file", tx_csv)
    with open(tx_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)  # Skip header
        for row in reader:
            src_id = row[tx_src_idx]  # SENDER_ACCOUNT_ID
            dst_id = row[tx_dst_idx]  # RECEIVER_ACCOUNT_ID
            amount = float(row[tx_amt_idx])  # TX_AMOUNT
            date = parse(row[tx_date_idx]) if is_date_type else base_date + timedelta(int(row[tx_date_idx]))
            date_str = date.strftime("%Y-%m-%d")
            attr = {"amount": amount, "date": date_str}
            _g.add_edge(src_id, dst_id, **attr)
            num_txs += 1
    print("Number of transactions: %d" % num_txs)
    return _g


def load_alerts(_g, alert_acct_csv, alert_tx_csv, schema_data):
    """Load alert member and transaction lists
    """
    pass


class __TransactionGraphLoader:

    def __index__(self, conf_json):
        with open(conf_json, "r") as rf:
            self.conf = json.load(rf)
        schema_json = self.conf["input"]["schema"]
        with open(schema_json, "r") as rf:
            self.schema = json.load(rf)
        self.output_conf = self.conf["output"]
        self.g = nx.MultiDiGraph()

    def get_graph(self):
        return self.g

    def count_hub_accounts(self, min_degree=2, max_degree=10):
        """Count number of "hub" accounts by degree
        """
        in_deg = Counter(self.g.in_degree().values())  # in-degree, count
        out_deg = Counter(self.g.out_degree().values())  # out-degree, count
        for th in range(min_degree, max_degree + 1):
            num_fan_in = sum([c for d, c in in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in out_deg.items() if d >= th])
            print("\tNumber of fan-in / fan-out patterns with", th, "neighbors:", num_fan_in, "/", num_fan_out)


class BaseGraphLoader(__TransactionGraphLoader):

    def __init__(self, conf_json):
        super(BaseGraphLoader, self).__init__(conf_json)


class ResultGraphLoader(__TransactionGraphLoader):

    def __init__(self, conf_json):
        super(ResultGraphLoader, self).__init__(conf_json)

        # Create a transaction graph from output files
        output_dir = self.output_conf["directory"]
        acct_file = self.output_conf["accounts"]
        tx_file = self.output_conf["transactions"]
        alert_acct_file = self.output_conf["alert_members"]
        alert_tx_file = self.output_conf["alert_transactions"]

        acct_path = os.path.join(output_dir, acct_file)
        tx_path = os.path.join(output_dir, tx_file)
        self.g = load_result_csv(acct_path, tx_path, self.schema)
        # TODO: Add alert attributes to account vertices and transaction edges

    def count_hub_accounts(self, min_degree=2, max_degree=10):
        super(ResultGraphLoader, self).count_hub_accounts(min_degree, max_degree)
        # TODO: Extract the same statistical data for normal and alert account vertices
