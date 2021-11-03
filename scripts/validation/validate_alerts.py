import os
import sys
import csv
import json
from collections import defaultdict
import networkx as nx
from datetime import datetime
import logging


def col2idx(cols):
    result = dict()  # Column name -> column index
    for i, col in enumerate(cols):
        result[col] = i
    return result


def load_alert_param(_alert_param_csv):
    """Load an alert parameter file
    :param _alert_param_csv: Alert parameter CSV file
    :return: dict of line number of the parameter file and parameter set as dict
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

        param_data = dict()
        line_num = 2
        for row in reader:
            count = int(row[count_idx])
            alert_type = row[type_idx]
            is_ordered = int(row[schedule_idx]) > 0
            accounts = (int(row[min_acct_idx]), int(row[max_acct_idx]))
            amount = (float(row[min_amt_idx]), float(row[max_amt_idx]))
            period = (int(row[min_period_idx]), int(row[max_period_idx]))
            is_multiple_banks = row[bank_idx] == ""
            is_sar = row[sar_idx].lower() == "true"
            params = {"count": count, "type": alert_type, "ordered": is_ordered,
                      "accounts": accounts, "amount": amount, "period": period,
                      "multiple_banks": is_multiple_banks, "sar": is_sar}
            param_data[line_num] = params
            line_num += 1

        return param_data


def load_alert_tx(_alert_tx_schema, _alert_tx_csv):
    """Load an alert-related transaction CSV file and construct subgraphs
    :param _alert_tx_schema:
    :param _alert_tx_csv:
    :return: dict of alert ID and alert transaction subgraph
    """
    alert_idx = None
    type_idx = None
    orig_idx = None
    bene_idx = None
    amt_idx = None
    date_idx = None
    for i, col in enumerate(_alert_tx_schema):
        data_type = col.get("dataType")
        if data_type == "alert_id":
            alert_idx = i
        elif data_type == "alert_type":
            type_idx = i
        elif data_type == "orig_id":
            orig_idx = i
        elif data_type == "dest_id":
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
            alert_type = row[type_idx]
            orig_id = row[orig_idx]
            bene_id = row[bene_idx]
            amount = float(row[amt_idx])
            date_str = row[date_idx].split("T")[0]
            date = datetime.strptime(date_str, "%Y-%m-%d")
            alert_graphs[alert_id].add_edge(orig_id, bene_id, amount=amount, date=date)
            alert_graphs[alert_id].graph["alert_id"] = alert_id
            alert_graphs[alert_id].graph["alert_type"] = alert_type

    return alert_graphs


def satisfies_params(alert_sub_g, param):
    """Check whether the given alert subgraph satisfies the given parameter
    :param alert_sub_g: Alert subgraph
    :param param: Alert parameters as dict from a parameter file
    :return: If the subgraph satisfies all of the given parameter, return True.
    """
    alert_id = alert_sub_g.graph["alert_id"]
    num_accounts = alert_sub_g.number_of_nodes()
    tx_attrs = [attr for _, _, attr in alert_sub_g.edges(data=True)]
    start_date = min([attr["date"] for attr in tx_attrs])
    end_date = max([attr["date"] for attr in tx_attrs])
    period = (end_date - start_date).days + 1
    init_amount = [attr["amount"] for attr in tx_attrs if attr["date"] == start_date][0]
    alert_type = param["type"]

    if alert_type == "cycle" and not is_cycle(alert_sub_g):
        return False
    elif alert_type == "scatter_gather" and not is_scatter_gather(alert_sub_g):
        return False
    elif alert_type == "gather_scatter" and not is_gather_scatter(alert_sub_g):
        return False

    min_acct, max_acct = param["accounts"]
    if not min_acct <= num_accounts <= max_acct:
        logging.info("Alert %s: The number of accounts %d is not within [%d, %d]"
                     % (alert_id, num_accounts, min_acct, max_acct))
        return False

    min_amt, max_amt = param["amount"]
    if not min_amt <= init_amount <= max_amt:
        logging.info("Alert %s: initial amount %f is not within [%f, %f]" % (alert_id, init_amount, min_amt, max_amt))
        return False

    min_period, max_period = param["period"]
    if not min_period <= period <= max_period:
        logging.info("Alert %s: period %d is not within [%d, %d]" % (alert_id, period, min_period, max_period))
        return False

    return True


def is_cycle(alert_sub_g: nx.DiGraph, is_ordered: bool = True):
    alert_id = alert_sub_g.graph["alert_id"]
    edges = alert_sub_g.edges(data=True)
    cycles = list(nx.simple_cycles(alert_sub_g))  # Use simple_cycles function directly (subgraph is small enough)
    if len(cycles) != 1:
        logging.info("Alert %s is not a cycle pattern" % alert_id)
        return False
    if is_ordered:
        edges.sort(key=lambda e: e[2]["date"])
        next_orig = None
        next_amt = sys.float_info.max
        next_date = datetime.strptime("1970-01-01", "%Y-%m-%d")
        for orig, bene, attr in edges:
            if next_orig is not None and orig != next_orig:
                logging.info("Alert %s is not a cycle pattern" % alert_id)
                return False
            else:
                next_orig = bene

            amount = attr["amount"]
            if amount == next_amt:
                logging.info("Alert %s cycle transaction amounts are unordered" % alert_id)
                return False
            else:
                next_amt = amount

            date = attr["date"]
            if date < next_date:
                logging.info("Alert %s cycle transactions are chronologically unordered" % alert_id)
                return False
            else:
                next_date = date
    return True


def is_scatter_gather(alert_sub_g: nx.DiGraph, is_ordered: bool = True):
    alert_id = alert_sub_g.graph["alert_id"]
    num_accts = alert_sub_g.number_of_nodes()
    num_mid = num_accts - 2
    out_degrees = alert_sub_g.out_degree()
    in_degrees = alert_sub_g.in_degree()
    orig = None
    bene = None
    mid_accts = list()
    for n, out_d in out_degrees.items():
        in_d = in_degrees[n]
        if out_d == num_mid:
            orig = n
            if in_d != 0:
                logging.info("Alert %s is not a scatter-gather pattern: invalid vertex degree %d -> [%s] -> %d"
                             % (alert_id, in_d, n, out_d))
                return False
        elif out_d == 0:
            bene = n
            if in_d != num_mid:
                logging.info("Alert %s is not a scatter-gather pattern: invalid vertex degree %d -> [%s] -> %d"
                             % (alert_id, in_d, n, out_d))
                return False
        elif out_d == 1:
            mid_accts.append(n)
            if in_d != 1:
                logging.info("Alert %s is not a scatter-gather pattern: invalid vertex degree %d -> [%s] -> %d"
                             % (alert_id, in_d, n, out_d))
                return False
        else:
            logging.info("Alert %s is not a scatter-gather pattern: invalid vertex degree %d -> [%s] -> %d"
                         % (alert_id, in_d, n, out_d))
            return False
    if len(mid_accts) != num_mid:  # Mismatched the number of intermediate accounts
        logging.info("Not a scatter-gather pattern: " + alert_id)
        return False

    if is_ordered:
        for mid in mid_accts:
            scatter_attr = alert_sub_g.get_edge_data(orig, mid)
            gather_attr = alert_sub_g.get_edge_data(mid, bene)
            if scatter_attr is None:
                logging.info("Alert %s is not a scatter-gather pattern: scatter edge %s -> %s not found"
                             % (alert_id, orig, mid))
                return False  # No scatter or gather edges found
            elif gather_attr is None:
                logging.info("Alert %s is not a scatter-gather pattern: gather edge %s -> %s not found"
                             % (alert_id, mid, bene))

            scatter_date = scatter_attr["date"]
            gather_date = gather_attr["date"]
            if scatter_date > gather_date:
                logging.info("Alert %s scatter-gather transactions are chronologically unordered" % alert_id)
                return False  # Chronologically unordered
            scatter_amount = scatter_attr["amount"]
            gather_amount = gather_attr["amount"]
            if scatter_amount <= gather_amount:
                logging.info("Alert %s scatter-gather transaction amounts are unordered" % alert_id)
                return False  # The intermediate account must get margin

    return True


def is_gather_scatter(alert_sub_g: nx.DiGraph, is_ordered: bool = True):
    alert_id = alert_sub_g.graph["alert_id"]
    num_accts = alert_sub_g.number_of_nodes()
    out_degrees = alert_sub_g.out_degree()
    in_degrees = alert_sub_g.in_degree()

    orig_accts = [n for n, d in out_degrees.items() if d == 1 and in_degrees[n] == 0]
    bene_accts = [n for n, d in in_degrees.items() if d == 1 and out_degrees[n] == 0]
    num_orig = len(orig_accts)
    num_bene = len(bene_accts)
    hub_accts = [n for n, d in out_degrees.items() if d == num_bene and in_degrees[n] == num_orig]
    if len(hub_accts) != 1 or (num_orig + num_bene + 1) != num_accts:
        logging.info("Alert %s is not a gather-scatter pattern" % alert_id)
        return False  # Mismatched the number of accounts

    hub = hub_accts[0]
    last_gather_date = datetime.strptime("1970-01-01", "%Y-%m-%d")
    total_gather_amount = 0.0
    for orig in orig_accts:
        attr = alert_sub_g.get_edge_data(orig, hub)
        if attr is None:
            logging.info("Alert %s is not a gather-scatter pattern: gather edge %s -> %s not found"
                         % (alert_id, orig, hub))
            return False  # No gather edges found
        date = attr["date"]
        amount = attr["amount"]
        last_gather_date = max(last_gather_date, date)
        total_gather_amount += amount

    if is_ordered:
        max_scatter_amount = total_gather_amount / num_bene
        for bene in bene_accts:
            attr = alert_sub_g.get_edge_data(hub, bene)
            if attr is None:
                return False
            date = attr["date"]
            amount = attr["amount"]
            if date < last_gather_date:
                logging.info("Alert %s gather-scatter transactions are chronologically unordered " % alert_id)
                return False
            elif max_scatter_amount <= amount:
                logging.info("Alert %s gather-scatter transaction amounts are unordered" % alert_id)
                return False

    return True


class AlertValidator:

    def __init__(self, conf_json, sim_name=None):
        with open(conf_json, "r") as rf:
            self.conf = json.load(rf)

        self.sim_name = sim_name if sim_name is not None else self.conf["general"]["simulation_name"]
        self.input_dir = self.conf["input"]["directory"]
        self.output_dir = os.path.join(self.conf["output"]["directory"], self.sim_name)
        schema_json = self.conf["input"]["schema"]
        schema_path = os.path.join(self.input_dir, schema_json)
        with open(schema_path, "r") as rf:
            self.schema = json.load(rf)

        log_file = os.path.join(self.output_dir, "alert_validations.log")
        logging.basicConfig(filename=log_file, filemode="w", level=logging.INFO)

        # Load an alert (AML typology) parameter file
        self.alert_param_file = self.conf["input"]["alert_patterns"]
        alert_param_path = os.path.join(self.input_dir, self.alert_param_file)
        schema_file = self.conf["input"]["schema"]
        schema_path = os.path.join(self.input_dir, schema_file)
        self.alert_params = load_alert_param(alert_param_path)

        # Load an alert transaction file
        alert_tx_file = self.conf["output"]["alert_transactions"]
        alert_tx_path = os.path.join(self.output_dir, alert_tx_file)
        with open(schema_path, "r") as _rf:
            schema = json.load(_rf)
        self.alert_graphs = load_alert_tx(schema["alert_tx"], alert_tx_path)

    def validate_single(self, alert_id):
        if alert_id not in self.alert_graphs:
            raise KeyError("No such alert ID: " + alert_id)
        sub_g = self.alert_graphs[alert_id]
        alert_type = sub_g.graph["alert_type"]
        for line_num, param in self.alert_params.items():
            if param["type"] != alert_type:
                continue
            if satisfies_params(sub_g, param):
                logging.info("The alert %s subgraph matches the parameter %s:%d, data %s" %
                             (alert_id, self.alert_param_file, line_num, str(param)))
                return True
        else:  # No match any parameter sets
            logging.warning("The alert subgraph (ID:%s, Type:%s) does not match any parameter sets"
                            % (alert_id, alert_type))
            return False

    def validate_all(self):
        num_alerts = len(self.alert_graphs)
        num_matched = 0
        for alert_id in self.alert_graphs.keys():
            if self.validate_single(alert_id):
                num_matched += 1
        num_unmatched = num_alerts - num_matched
        print("Total number of alerts: %d, matched: %d, unmatched: %d" % (num_alerts, num_matched, num_unmatched))


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: python3 %s [ConfJson] [SimName]" % argv[0])
        exit(1)

    _conf_json = argv[1]
    _sim_name = argv[2] if len(argv) >= 3 else None
    av = AlertValidator(_conf_json, _sim_name)
    av.validate_all()
