import os
import sys
import csv
import json
from collections import defaultdict
import networkx as nx
from datetime import datetime


def col2idx(cols):
    result = dict()  # Column name -> column index
    for i, col in enumerate(cols):
        result[col] = i
    return result


def load_alert_param(_alert_param_csv):
    """Load an alert parameter file
    :param _alert_param_csv: Alert parameter CSV file
    :return: List of alert parameter set as dict
    """
    with open(_alert_param_csv, "r") as _rf:
        reader = csv.reader(_rf)
        header = next(reader)
        name2idx = col2idx(header)
        count_idx = name2idx["count"]
        type_idx = name2idx["type"]
        schedule_idx = name2idx["schedule_id"]
        min_acct_idx = name2idx["min_accounts"]
        max_acct_idx = name2idx["max_accounts"]
        min_amt_idx = name2idx["min_amount"]
        max_amt_idx = name2idx["max_amount"]
        min_period_idx = name2idx["min_period"]
        max_period_idx = name2idx["max_period"]
        bank_idx = name2idx["bank_id"]
        sar_idx = name2idx["is_sar"]

        param_list = list()
        for row in reader:
            count = int(row[count_idx])
            alert_type = row[type_idx]
            is_ordered = int(row[schedule_idx]) > 0
            accounts = (int(row[min_acct_idx]), int(row[max_acct_idx]))
            amount = (float(row[min_amt_idx]), int(row[max_amt_idx]))
            period = (int(row[min_period_idx]), int(row[max_period_idx]))
            is_multiple_banks = row[bank_idx] == ""
            is_sar = row[sar_idx].lower() == "true"
            params = {"count": count, "type": alert_type, "ordered": is_ordered,
                      "accounts": accounts, "amount": amount, "period": period,
                      "multiple_banks": is_multiple_banks, "sar": is_sar}
            param_list.append(params)

        return param_list


def load_alert_tx(_alert_tx_schema, _alert_tx_csv):
    """Load an alert-related transaction CSV file and construct subgraphs
    :param _alert_tx_schema:
    :param _alert_tx_csv:
    :return: dict of alert ID and alert transaction subgraph
    """
    alert_idx = None
    orig_idx = None
    bene_idx = None
    amt_idx = None
    date_idx = None
    for i, col in enumerate(_alert_tx_schema):
        data_type = col.get("dataType")
        if data_type == "alert_id":
            alert_idx = i
        elif data_type == "orig_id":
            orig_idx = i
        elif data_type == "bene_id":
            bene_idx = i
        elif data_type == "amount":
            amt_idx = i
        elif data_type == "timestamp":
            date_idx = i

    alert_graphs = defaultdict(nx.DiGraph)
    with open(_alert_tx_csv, "r") as _rf:
        reader = csv.reader(_rf)
        next(reader)
        for row in reader:
            alert_id = row[alert_idx]
            orig_id = row[orig_idx]
            bene_id = row[bene_idx]
            amount = float(row[amt_idx])
            date_str = row[date_idx].split("T")[0]
            date = datetime.strptime(date_str, "%Y-%m-%d")
            alert_graphs[alert_id].add_edge(orig_id, bene_id, amount=amount, date=date)

    return alert_graphs


def satisfies_params(alert_sub_g, param):
    """Check whether the given alert subgraph satisfies the given parameter
    :param alert_sub_g: Alert subgraph
    :param param: Alert parameters as dict from a parameter file
    :return: If the subgraph satisfies all of the given parameter, return True.
    """
    num_accounts = alert_sub_g.number_of_nodes()
    tx_attrs = [attr for _, _, attr in alert_sub_g.edges(data=True)]
    start_date = min([attr["date"] for attr in tx_attrs])
    end_date = max([attr["date"] for attr in tx_attrs])
    period = (end_date - start_date).days + 1
    init_amount = [attr["amount"] for attr in tx_attrs if attr["date"] == start_date][0]
    alert_type = param["type"]

    min_acct, max_acct = param["accounts"]
    if not min_acct <= num_accounts <= max_acct:
        return False
    min_amt, max_amt = param["amount"]
    if not min_amt <= init_amount <= max_amt:
        return False
    min_period, max_period = param["period"]
    if not min_period <= period <= max_period:
        return False


class AlertValidator:

    def __init__(self, conf_json):
        with open(conf_json, "r") as rf:
            self.conf = json.load(rf)

        self.input_dir = self.conf["input"]["directory"]
        self.output_dir = self.conf["output"]["directory"]
        schema_json = self.conf["input"]["schema"]
        schema_path = os.path.join(self.input_dir, schema_json)
        with open(schema_path, "r") as rf:
            self.schema = json.load(rf)

        # Load an alert (AML typology) parameter file
        alert_param_file = self.conf["input"]["alert_patterns"]
        alert_param_path = os.path.join(self.input_dir, alert_param_file)
        schema_file = self.conf["input"]["schema"]
        schema_path = os.path.join(self.input_dir, schema_file)
        self.alert_params = load_alert_param(alert_param_path)

        # Load an alert transaction file
        alert_tx_file = self.conf["output"]["alert_transactions"]
        alert_tx_path = os.path.join(self.output_dir, alert_tx_file)
        self.alert_graphs = load_alert_tx(schema_path, alert_tx_path)

    def validate_all(self):
        for alert_id, sub_g in self.alert_graphs.items():
            for param in self.alert_params:
                if satisfies_params(sub_g, param):
                    if param["count"] == 0:
                        alert_type = param["type"]
                        min_acct, max_acct = param["accounts"]
                        min_amt, max_amt = param["amount"]
                        min_period, max_period = param["period"]
                        print("Too many alert subgraphs for the following parameters:",
                              "Type: %s, Accounts: [%d, %d], Amount: [%f, %f], Period: [%d, %d]" %
                              (alert_type, min_acct, max_acct, min_amt, max_amt, min_period, max_period))
                    param["count"] -= 1
                    break
            else:
                print("The alert subgraph with ID %s does not satisfy any parameters")


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: python3 %s [ConfJson]" % argv[0])
        exit(1)

    av = AlertValidator(argv[1])

