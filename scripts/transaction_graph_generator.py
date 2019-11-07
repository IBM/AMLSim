"""
Generate a base transaction graph used in the simulator
"""

import networkx as nx
import numpy as np
import itertools
import random
import csv
import json
import os
import sys
import logging
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Attribute keys
MAIN_ACCT_KEY = "main_acct"
IS_SAR_KEY = "is_sar"


# Utility functions parsing values
def parse_int(value):
    """ Convert string to int
    :param value: string value
    :return: int value if the parameter can be converted to str, otherwise None
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_amount(value):
    """ Convert string to amount (float)
    :param value: string value
    :return: float value if the parameter can be converted to float, otherwise None
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def parse_flag(value):
    """ Convert string to boolean (True or false)
    :param value: string value
    :return: True if the value is equal to "true" (case insensitive), otherwise False
    """
    return type(value) == str and value.lower() == "true"


class InputSchema:

    def __init__(self, input_json):
        with open(input_json, "r") as rf:
            self.data = json.load(rf)

    def get_header(self, table_name):
        fields = self.data[table_name]
        return [f["name"] for f in fields]


class TransactionGenerator:

    def __init__(self, conf_file):
        """Initialize transaction network from parameter files.
        :param conf_file: JSON file as configurations
        """
        self.g = nx.MultiDiGraph()  # Transaction graph object
        self.num_accounts = 0  # Number of total accounts
        self.degrees = dict()  # Degree distribution
        self.hubs = list()  # Hub vertices
        self.main_acct_candidates = set()  # Set of the main account candidates
        self.attr_names = list()  # Additional account attribute names

        with open(conf_file, "r") as rf:
            self.conf = json.load(rf)

        general_conf = self.conf["general"]

        # Set random seed
        seed = general_conf.get("random_seed")
        self.seed = seed if seed is None else int(seed)
        np.random.seed(self.seed)
        random.seed(self.seed)

        self.total_steps = parse_int(general_conf["total_steps"])

        # Set default amounts, steps and model ID
        default_conf = self.conf["default"]
        self.default_min_amount = parse_amount(default_conf.get("min_amount"))
        self.default_max_amount = parse_amount(default_conf.get("max_amount"))
        self.default_min_balance = parse_amount(default_conf.get("min_balance"))
        self.default_max_balance = parse_amount(default_conf.get("max_balance"))
        self.default_start_step = parse_int(default_conf.get("start_step"))
        self.default_end_step = parse_int(default_conf.get("end_step"))
        self.default_start_range = parse_int(default_conf.get("start_range"))
        self.default_end_range = parse_int(default_conf.get("end_range"))
        self.default_model = parse_int(default_conf.get("transaction_model"))

        # Get input file names and properties
        input_conf = self.conf["input"]
        self.input_dir = input_conf["directory"]  # Directory name of input files
        self.account_file = input_conf["accounts"]  # Account list file
        self.alert_file = input_conf["alert_patterns"]
        self.degree_file = input_conf["degree"]
        self.type_file = input_conf["transaction_type"]
        self.is_aggregated = input_conf["is_aggregated_accounts"]

        # Get output file names
        output_conf = self.conf["temporal"]  # The destination directory is temporal
        self.output_dir = output_conf["directory"]
        self.out_tx_file = output_conf["transactions"]
        self.out_account_file = output_conf["accounts"]
        self.out_alert_member_file = output_conf["alert_members"]

        # Other properties for the transaction graph generator
        other_conf = self.conf["graph_generator"]
        self.degree_threshold = parse_int(other_conf["degree_threshold"])
        highrisk_countries_str = other_conf.get("high_risk_countries", "")
        highrisk_business_str = other_conf.get("high_risk_business", "")
        self.highrisk_countries = set(highrisk_countries_str.split(","))
        self.highrisk_business = set(highrisk_business_str.split(","))

        self.tx_id = 0  # Transaction ID
        self.alert_id = 0  # Alert ID from the alert parameter file
        self.alert_groups = dict()  # Alert ID and alert transaction subgraph
        # TODO: Move the mapping of AML pattern to configuration JSON file
        self.alert_types = {"fan_out": 1, "fan_in": 2, "cycle": 3, "bipartite": 4, "stack": 5,
                            "dense": 6, "scatter_gather": 7, "gather_scatter": 8}  # Pattern name and model ID

        def get_types(type_csv):
            tx_types = list()
            with open(type_csv, "r") as _rf:
                reader = csv.reader(_rf)
                next(reader)
                for row in reader:
                    if row[0].startswith("#"):
                        continue
                    ttype = row[0]
                    tx_types.extend([ttype] * int(row[1]))
            return tx_types

        self.tx_types = get_types(os.path.join(self.input_dir, self.type_file))

    def set_main_acct_candidates(self):
        """Choose the main account candidates of alert transaction sets
        Currently, it chooses hub accounts with larger degree than the specified threshold
        TODO: More options how to choose the main accounts
        """
        self.degrees = self.g.degree(self.g.nodes())
        self.hubs = [n for n in self.g.nodes() if self.degree_threshold <= self.degrees[n]]
        self.main_acct_candidates = set(self.g.nodes())

    def count_patterns(self, threshold=2):
        """Count the number of fan-in and fan-out patterns in the generated transaction graph
        """
        in_deg = Counter(self.g.in_degree().values())  # in-degree, count
        out_deg = Counter(self.g.out_degree().values())  # out-degree, count
        for th in range(2, threshold+1):
            num_fan_in = sum([c for d, c in in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in out_deg.items() if d >= th])
            print("\tNumber of fan-in / fan-out patterns with", th, "neighbors:", num_fan_in, "/", num_fan_out)

        main_in_deg = Counter()
        main_out_deg = Counter()
        for sub_g in self.alert_groups.values():
            main_acct = sub_g.graph[MAIN_ACCT_KEY]
            main_in_deg[self.g.in_degree(main_acct)] += 1
            main_out_deg[self.g.out_degree(main_acct)] += 1
        for th in range(2, threshold+1):
            num_fan_in = sum([c for d, c in main_in_deg.items() if d >= threshold])
            num_fan_out = sum([c for d, c in main_out_deg.items() if d >= threshold])
            print("\tNumber of alerted fan-in / fan-out patterns with", th, "neighbors", num_fan_in, "/", num_fan_out)

    # Highrisk country and business
    def is_highrisk_country(self, country):
        return country in self.highrisk_countries

    def is_highrisk_business(self, business):
        return business in self.highrisk_business

    # Account existence check
    def check_account_exist(self, aid):
        if not self.g.has_node(aid):
            raise KeyError("Account %s does not exist" % str(aid))

    def check_account_absent(self, aid):
        if self.g.has_node(aid):
            print("Warning: account %s already exists" % str(aid))
            return False
        else:
            return True

    def get_alert_members(self, num, is_sar):
        """Get account vertices randomly (high-degree vertices are likely selected)
        :param num: Number of total account vertices
        :param is_sar: Whether the alert is SAR (True) or false-alert (False)
        :return: Main account and account ID list
        """
        found = False
        main_acct = None
        members = list()

        while not found:
            candidates = set()
            while len(candidates) < num:  # Get sufficient alert members
                hub = random.choice(self.hubs)
                candidates.update([hub] + list(self.g.adj[hub].keys()))
            members = np.random.choice(list(candidates), num, False)
            candidates_set = set(members) & self.main_acct_candidates
            if not candidates_set:
                continue
            main_acct = random.choice(list(candidates_set))  # Choose one main account from members randomly
            found = True
            if is_sar:
                self.main_acct_candidates.remove(main_acct)
        return main_acct, members

    def get_account_vertices(self, num, suspicious=None):
        """Get account vertices randomly
        :param num: Number of total account vertices
        :param suspicious: If True, extract only suspicious accounts. If False, extract only non-suspicious accounts.
        If None (default), extract them from all accounts.
        :return: Account ID list
        """
        if suspicious is None:
            candidates = self.g.nodes()
        else:
            candidates = [n for n in self.g.nodes() if self.g.node[n]["suspicious"] == suspicious]  # True/False
        return random.sample(candidates, num)

    def load_account_list(self):
        """Load and add account vertices from a CSV file
        :return:
        """
        acct_file = os.path.join(self.input_dir, self.account_file)
        if self.is_aggregated:
            self.load_account_param(acct_file)
        else:
            self.load_account_raw(acct_file)

    def load_account_raw(self, acct_file):
        """Load and add account vertices from a CSV file with raw account info
        header: uuid,seq,first_name,last_name,street_addr,city,state,zip,gender,phone_number,birth_date,ssn
        :param acct_file: Account list file path
        :return:
        """
        if self.default_min_balance is None:
            raise KeyError("Option 'default_min_balance' is required to load raw account list")
        min_balance = self.default_min_balance

        if self.default_max_balance is None:
            raise KeyError("Option 'default_max_balance' is required to load raw account list")
        max_balance = self.default_max_balance

        if self.default_start_step is None or self.default_start_step < 0:
            start_day = None  # No limitation
        else:
            start_day = self.default_start_step

        if self.default_end_step is None or self.default_end_step <= 0:
            end_day = None  # No limitation
        else:
            end_day = self.default_end_step

        if self.default_start_range is None or self.default_start_range <= 0:
            start_range = None  # No limitation
        else:
            start_range = self.default_start_range

        if self.default_end_range is None or self.default_end_range <= 0:
            end_range = None  # No limitation
        else:
            end_range = self.default_end_range

        if self.default_model is None:
            default_model = 1
        else:
            default_model = self.default_model

        self.attr_names.extend(["first_name", "last_name", "street_addr", "city", "state", "zip",
                                "gender", "phone_number", "birth_date", "ssn", "lon", "lat"])

        with open(acct_file, "r") as rf:
            reader = csv.reader(rf)
            header = next(reader)
            name2idx = {n: i for i, n in enumerate(header)}
            idx_aid = name2idx["uuid"]
            idx_first_name = name2idx["first_name"]
            idx_last_name = name2idx["last_name"]
            idx_street_addr = name2idx["street_addr"]
            idx_city = name2idx["city"]
            idx_state = name2idx["state"]
            idx_zip = name2idx["zip"]
            idx_gender = name2idx["gender"]
            idx_phone_number = name2idx["phone_number"]
            idx_birth_date = name2idx["birth_date"]
            idx_ssn = name2idx["ssn"]
            idx_lon = name2idx["lon"]
            idx_lat = name2idx["lat"]

            default_country = "US"
            default_acct_type = "I"

            count = 0
            for row in reader:
                if row[0].startswith("#"):
                    continue
                aid = row[idx_aid]
                first_name = row[idx_first_name]
                last_name = row[idx_last_name]
                street_addr = row[idx_street_addr]
                city = row[idx_city]
                state = row[idx_state]
                zip_code = row[idx_zip]
                gender = row[idx_gender]
                phone_number = row[idx_phone_number]
                birth_date = row[idx_birth_date]
                ssn = row[idx_ssn]
                lon = row[idx_lon]
                lat = row[idx_lat]
                model = default_model
                start = start_day + random.randrange(start_range) if (
                        start_day is not None and start_range is not None) else -1
                end = end_day - random.randrange(end_range) if (end_day is not None and end_range is not None) else -1

                attr = {"first_name": first_name, "last_name": last_name, "street_addr": street_addr,
                        "city": city, "state": state, "zip": zip_code, "gender": gender, "phone_number": phone_number,
                        "birth_date": birth_date, "ssn": ssn, "lon": lon, "lat": lat}

                init_balance = random.uniform(min_balance, max_balance)  # Generate the initial balance
                self.add_account(aid, init_balance, start, end, default_country, default_acct_type, model, **attr)
                count += 1

    def load_account_param(self, acct_file):
        """Load and add account vertices from a CSV file with aggregated parameters
        Each row may represent two or more accounts
        :param acct_file: Account parameter file path
        :return:
        """

        idx_num = None  # Number of accounts per row
        idx_min = None  # Minimum initial balance
        idx_max = None  # Maximum initial balance
        idx_start = None  # Start step
        idx_end = None  # End step
        idx_country = None  # Country
        idx_business = None  # Business type
        idx_model = None  # Transaction model

        with open(acct_file, "r") as rf:
            reader = csv.reader(rf)
            # Parse header
            header = next(reader)
            for i, k in enumerate(header):
                if k == "count":
                    idx_num = i
                elif k == "min_balance":
                    idx_min = i
                elif k == "max_balance":
                    idx_max = i
                elif k == "start_day":
                    idx_start = i
                elif k == "end_day":
                    idx_end = i
                elif k == "country":
                    idx_country = i
                elif k == "business_type":
                    idx_business = i
                elif k == "model":
                    idx_model = i
                else:
                    print("Warning: unknown key: %s" % k)

            aid = 0
            for row in reader:
                if row[0].startswith("#"):
                    continue
                num = int(row[idx_num])
                min_balance = parse_amount(row[idx_min])
                max_balance = parse_amount(row[idx_max])
                start_day = parse_int(row[idx_start]) if idx_start is not None else -1
                end_day = parse_int(row[idx_end]) if idx_end is not None else -1
                country = row[idx_country]
                business = row[idx_business]
                model_id = parse_int(row[idx_model])

                for i in range(num):
                    init_balance = random.uniform(min_balance, max_balance)  # Generate amount
                    self.add_account(aid, init_balance, start_day, end_day, country, business, model_id)
                    aid += 1

        self.num_accounts = aid
        print("Created %d accounts." % self.num_accounts)

    # Generate base transactions from same degree sequences of transaction CSV
    def generate_normal_transactions(self):

        def get_degrees(deg_csv, num_v):
            """
            :param deg_csv: Degree distribution parameter CSV file
            :param num_v: Number of total account vertices
            :return: In-degree and out-degree sequence list
            """
            _in_deg = list()  # In-degree sequence
            _out_deg = list()  # Out-degree sequence
            with open(deg_csv, "r") as rf:  # Load in/out-degree sequences from parameter CSV file for each account
                reader = csv.reader(rf)
                next(reader)
                for row in reader:
                    if row[0].startswith("#"):
                        continue
                    nv = int(row[0])
                    _in_deg.extend(int(row[1]) * [nv])
                    _out_deg.extend(int(row[2]) * [nv])

            in_len, out_len = len(_in_deg), len(_out_deg)
            assert in_len == out_len, "In-degree (%d) and Out-degree (%d) Sequences must have equal length." \
                                      % (in_len, out_len)
            total_v = len(_in_deg)

            # If the number of total accounts from degree sequences is larger than specified, shrink degree sequence
            if total_v > num_v:
                diff = total_v - num_v  # The number of extra accounts to be removed
                in_tmp = list()
                out_tmp = list()
                for i in range(total_v):
                    num_in = _in_deg[i]
                    num_out = _out_deg[i]
                    if num_in == num_out and diff > 0:  # Remove extra elements with the same degree
                        diff -= 1
                    else:
                        in_tmp.append(num_in)
                        out_tmp.append(num_out)
                _in_deg = in_tmp
                _out_deg = out_tmp

            # If the number of total accounts from degree sequences is smaller than specified, extend degree sequence
            else:
                repeats = num_v // total_v  # Number of repetitions of degree sequences
                _in_deg = _in_deg * repeats
                _out_deg = _out_deg * repeats
                remain = num_v - total_v * repeats  # Number of extra accounts
                _in_deg.extend([1] * remain)  # Add 1-degree account vertices
                _out_deg.extend([1] * remain)

            assert sum(_in_deg) == sum(_out_deg), "Sequences must have equal sums."
            return _in_deg, _out_deg

        def _directed_configuration_model(_in_deg, _out_deg, seed=0):
            """Generate a directed random graph with the given degree sequences without self loop.
            Based on nx.generators.degree_seq.directed_configuration_model
            :param _in_deg: Each list entry corresponds to the in-degree of a node.
            :param _out_deg: Each list entry corresponds to the out-degree of a node.
            :param seed: Seed for random number generator
            :return: MultiDiGraph without self loop
            """
            if not sum(_in_deg) == sum(_out_deg):
                raise nx.NetworkXError('Invalid degree sequences. Sequences must have equal sums.')

            random.seed(seed)
            n_in = len(_in_deg)
            n_out = len(_out_deg)
            if n_in < n_out:
                _in_deg.extend((n_out - n_in) * [0])
            else:
                _out_deg.extend((n_in - n_out) * [0])

            num_nodes = len(_in_deg)
            _g = nx.empty_graph(num_nodes, nx.MultiDiGraph())
            if num_nodes == 0 or max(_in_deg) == 0:
                return _g  # No edges

            in_tmp_list = list()
            out_tmp_list = list()
            for n in _g.nodes():
                in_tmp_list.extend(_in_deg[n] * [n])
                out_tmp_list.extend(_out_deg[n] * [n])
            random.shuffle(in_tmp_list)
            random.shuffle(out_tmp_list)

            num_edges = len(in_tmp_list)
            for i in range(num_edges):
                _src = out_tmp_list[i]
                _dst = in_tmp_list[i]
                if _src == _dst:  # ID conflict causes self-loop
                    for j in range(i + 1, num_edges):
                        if _src != in_tmp_list[j]:
                            in_tmp_list[i], in_tmp_list[j] = in_tmp_list[j], in_tmp_list[i]  # Swap ID
                            break

            _g.add_edges_from(zip(out_tmp_list, in_tmp_list))
            for idx, (_src, _dst) in enumerate(_g.edges()):
                if _src == _dst:
                    print("Self loop from/to %d at %d" % (_src, idx))
            return _g

        # Generate a directed graph from degree sequences (not transaction graph)
        # TODO: Add options to call scale-free generator functions directly instead of loading degree CSV files
        deg_file = os.path.join(self.input_dir, self.degree_file)
        in_deg, out_deg = get_degrees(deg_file, self.num_accounts)
        g = _directed_configuration_model(in_deg, out_deg, self.seed)

        print("Add %d base transactions" % g.number_of_edges())
        nodes = self.g.nodes()
        for src_i, dst_i in g.edges():
            assert (src_i != dst_i)
            src = nodes[src_i]
            dst = nodes[dst_i]
            self.add_transaction(src, dst)  # Add edges to transaction graph

    def add_account(self, aid, init_balance, start, end, country, business, model_id, **attr):
        """Add an account vertex
        :param aid: Account ID
        :param init_balance: Initial amount
        :param start: The day when the account opened
        :param end: The day when the account closed
        :param country: Country name
        :param business: Business type
        :param model_id: Transaction model ID
        :param attr: Optional attributes
        :return:
        """
        # Add an account vertex with an ID and attributes if and only if an account with the same ID is not yet added
        if self.check_account_absent(aid):
            self.g.add_node(aid, label="account", init_balance=init_balance, start=start, end=end, country=country,
                            business=business, is_sar=False, model_id=model_id, **attr)

    def add_transaction(self, src, dst, amount=None, date=None, ttype=None):
        """Add a transaction edge
        :param src: Source account ID
        :param dst: Destination account ID
        :param amount: Transaction amount
        :param date: Transaction date
        :param ttype: Transaction type description
        :return:
        """
        self.check_account_exist(src)  # Ensure the source and destination accounts exist
        self.check_account_exist(dst)
        if src == dst:
            raise ValueError("Self loop from/to %s is not allowed for transaction networks" % str(src))
        self.g.add_edge(src, dst, key=self.tx_id, label="transaction", amount=amount, date=date, ttype=ttype)
        self.tx_id += 1
        if self.tx_id % 1000000 == 0:
            print("Added %d transactions" % self.tx_id)

    # Load Custom Topology Files
    def add_subgraph(self, members, topology):
        """Add subgraph from existing account vertices and given graph topology
        :param members: Account vertex list
        :param topology: Topology graph
        :return:
        """
        if len(members) != topology.number_of_nodes():
            raise nx.NetworkXError("The number of account vertices does not match")

        node_map = dict(zip(members, topology.nodes()))
        for e in topology.edges():
            src = node_map[e[0]]
            dst = node_map[e[1]]
            self.add_transaction(src, dst)

    def load_edgelist(self, members, csv_name):
        """Load edgelist and add edges with existing account vertices
        :param members: Account vertex list
        :param csv_name: Edgelist file name
        :return:
        """
        topology = nx.MultiDiGraph()
        topology = nx.read_edgelist(csv_name, delimiter=",", create_using=topology)
        self.add_subgraph(members, topology)

    def load_alert_patterns(self):
        """Load an AML typology parameter file
        :return:
        """
        alert_file = os.path.join(self.input_dir, self.alert_file)

        idx_num = None
        idx_type = None
        idx_accts = None
        idx_schedule = None
        idx_individual = None
        idx_aggregated = None
        idx_count = None
        idx_difference = None
        idx_period = None
        idx_rounded = None
        idx_orig_country = None
        idx_bene_country = None
        idx_orig_business = None
        idx_bene_business = None
        idx_sar = None

        with open(alert_file, "r") as rf:
            reader = csv.reader(rf)
            # Parse header
            header = next(reader)
            for i, k in enumerate(header):
                if k == "count":  # Number of pattern subgraphs
                    idx_num = i
                elif k == "type":
                    idx_type = i
                elif k == "accounts":
                    idx_accts = i
                elif k == "individual_amount":
                    idx_individual = i
                elif k == "schedule_id":
                    idx_schedule = i
                elif k == "aggregated_amount":
                    idx_aggregated = i
                elif k == "transaction_count":
                    idx_count = i
                elif k == "amount_difference":
                    idx_difference = i
                elif k == "period":
                    idx_period = i
                elif k == "amount_rounded":
                    idx_rounded = i
                elif k == "orig_country":
                    idx_orig_country = i
                elif k == "bene_country":
                    idx_bene_country = i
                elif k == "orig_business":
                    idx_orig_business = i
                elif k == "bene_business":
                    idx_bene_business = i
                elif k == "is_sar":  # SAR flag
                    idx_sar = i
                else:
                    print("Warning: unknown key: %s" % k)

            # Generate transaction set
            count = 0
            for row in reader:
                if row[0].startswith("#"):
                    continue
                num_patterns = int(row[idx_num])  # Number of alert patterns
                pattern_name = row[idx_type]
                num_accounts = int(row[idx_accts])
                schedule = int(row[idx_schedule])
                individual_amount = parse_amount(row[idx_individual])
                total_amount = parse_amount(row[idx_aggregated])
                num_transactions = parse_int(row[idx_count])
                amount_difference = parse_amount(row[idx_difference])
                period = parse_int(row[idx_period]) if idx_period is not None else self.total_steps
                amount_rounded = parse_amount(row[idx_rounded]) if idx_rounded is not None else 0.0
                orig_country = parse_flag(row[idx_orig_country]) if idx_orig_country is not None else False
                bene_country = parse_flag(row[idx_bene_country]) if idx_bene_country is not None else False
                orig_business = parse_flag(row[idx_orig_business]) if idx_orig_business is not None else False
                bene_business = parse_flag(row[idx_bene_business]) if idx_bene_business is not None else False
                is_sar = parse_flag(row[idx_sar ])

                if pattern_name not in self.alert_types:
                    print("Warning: pattern type name (%s) must be one of %s"
                          % (pattern_name, str(self.alert_types.keys())))
                    continue

                if num_transactions is not None and num_transactions < num_accounts:
                    print("Warning: number of transactions (%d) "
                          "is smaller than the number of accounts (%d)" % (num_transactions, num_accounts))
                    num_transactions = num_accounts

                for i in range(num_patterns):
                    # Add an AML typology
                    self.add_alert_pattern(is_sar, pattern_name, num_accounts, individual_amount, total_amount,
                                           num_transactions, schedule, amount_difference, period, amount_rounded,
                                           orig_country, bene_country, orig_business, bene_business)
                    count += 1
                    if count % 1000 == 0:
                        print("Write %d alerts" % count)

    def add_alert_pattern(self, is_sar, pattern_name, num_accounts, individual_amount, total_amount,
                          num_transactions=None, schedule=1, amount_difference=None, period=None, amount_rounded=None,
                          orig_country=False, bene_country=False, orig_business=False, bene_business=False):
        """Add an AML rule transaction set
        :param is_sar: Whether the alerted transaction set is SAR or false-alert
        :param pattern_name: Name of pattern type
            ("fan_in", "fan_out", "cycle", "dense", "mixed", "stack", "scatter_gather" or "gather_scatter")
        :param num_accounts: Number of transaction members (accounts)
        :param individual_amount: Initial individual amount
        :param total_amount: Minimum total amount
        :param num_transactions: Minimum number of transactions
        :param schedule: AML pattern transaction schedule model ID
        :param amount_difference: Proportion of maximum transaction difference (currently unused)
        :param period: Overall transaction period (days, currently unused)
        :param amount_rounded: Proportion of number of transactions with rounded amounts (currently unused)
        :param orig_country: Whether the originator country is suspicious (currently unused)
        :param bene_country: Whether the beneficiary country is suspicious (currently unused)
        :param orig_business: Whether the originator business type is suspicious (currently unused)
        :param bene_business: Whether the beneficiary business type is suspicious (currently unused)
        """
        main_acct, members = self.get_alert_members(num_accounts, is_sar)

        # Prepare parameters
        # if individual_amount is None:
        #     min_amount = self.default_min_amount
        #     max_amount = self.default_max_amount
        # else:
        #     min_amount = individual_amount
        #     max_amount = individual_amount * 2
        #
        # if total_amount is None:
        #     total_amount = 0

        start_date = 0
        end_date = self.total_steps

        # Create subgraph structure with transaction attributes
        model_id = self.alert_types[pattern_name]  # alert model ID
        sub_g = nx.MultiDiGraph(model_id=model_id, reason=pattern_name, scheduleID=schedule, start=start_date,
                                end=end_date)  # Transaction subgraph for a typology
        num_members = len(members)  # Number of accounts
        accumulated_amount = 0
        transaction_count = 0

        if pattern_name == "fan_in":  # fan_in pattern (multiple accounts --> single (main) account)
            src_list = [n for n in members if n != main_acct]
            dst = main_acct
            if num_transactions is None:
                num_transactions = num_members - 1
            for src in itertools.cycle(src_list):  # Generate transactions for the specified number
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(src, dst, amount=amount, date=date)
                self.g.add_edge(src, dst, amount=amount, date=date)
                transaction_count += 1
                accumulated_amount += amount
                if transaction_count >= num_transactions and accumulated_amount >= total_amount:
                    break

        elif pattern_name == "fan_out":  # fan_out pattern (single (main) account --> multiple accounts)
            src = main_acct
            dst_list = [n for n in members if n != main_acct]
            if num_transactions is None:
                num_transactions = num_members - 1
            for dst in itertools.cycle(dst_list):  # Generate transactions for the specified number
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(src, dst, amount=amount, date=date)
                self.g.add_edge(src, dst, amount=amount, date=date)

                transaction_count += 1
                accumulated_amount += amount
                if transaction_count >= num_transactions and accumulated_amount >= total_amount:
                    break

        elif pattern_name == "bipartite":  # bipartite (sender accounts --> all-to-all --> receiver accounts)
            src_list = members[:(num_members // 2)]  # The former half members are sender accounts
            dst_list = members[(num_members // 2):]  # The latter half members are receiver accounts
            if num_transactions is None:  # Number of transactions
                num_transactions = len(src_list) * len(dst_list)
            for src, dst in itertools.product(src_list, dst_list):  # All-to-all transactions
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(src, dst, amount=amount, date=date)
                self.g.add_edge(src, dst, amount=amount, date=date)

                transaction_count += 1
                accumulated_amount += amount
                if transaction_count > num_transactions and accumulated_amount >= total_amount:
                    break

        elif pattern_name == "mixed":  # fan_out -> bipartite -> fan_in
            src = members[0]  # Source account
            dst = members[num_members - 1]  # Destination account
            src_list = members[1:(num_members // 2)]  # First intermediate accounts
            dst_list = members[(num_members // 2):num_members - 1]  # Second intermediate accounts

            if num_transactions is None:
                num_transactions = len(src_list) + len(dst_list) + len(src_list) * len(dst_list)

            for _dst in src_list:  # Fan-out
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(src, _dst, amount=amount, date=date)
                self.g.add_edge(src, _dst, amount=amount, date=date)
                transaction_count += 1
                accumulated_amount += amount

            for _src, _dst in itertools.product(src_list, dst_list):  # Bipartite
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(_src, _dst, amount=amount, date=date)
                self.g.add_edge(_src, _dst, amount=amount, date=date)
                transaction_count += 1
                accumulated_amount += amount

            for _src in itertools.cycle(dst_list):  # Fan-in
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(_src, dst, amount=amount, date=date)
                self.g.add_edge(_src, dst, amount=amount, date=date)
                transaction_count += 1
                accumulated_amount += amount
                if transaction_count >= num_transactions and accumulated_amount >= total_amount:
                    break

        elif pattern_name == "stack":  # two dense bipartite layers
            src_list = members[:num_members // 3]  # First 1/3 of members: source accounts
            mid_list = members[num_members // 3:num_members * 2 // 3]  # Second 1/3 of members: intermediate accounts
            dst_list = members[num_members * 2 // 3:]  # Last 1/3 of members: destination accounts
            if num_transactions is None:  # Total number of transactions
                num_transactions = len(src_list) * len(mid_list) + len(mid_list) * len(dst_list)

            for src, dst in itertools.product(src_list, mid_list):  # all-to-all transactions
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(src, dst, amount=amount, date=date)
                self.g.add_edge(src, dst, amount=amount, date=date)
                transaction_count += 1
                accumulated_amount += amount
                if transaction_count > num_transactions and accumulated_amount >= total_amount:
                    break
            for src, dst in itertools.product(mid_list, dst_list):  # all-to-all transactions
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(src, dst, amount=amount, date=date)
                self.g.add_edge(src, dst, amount=amount, date=date)
                transaction_count += 1
                accumulated_amount += amount
                if transaction_count > num_transactions and accumulated_amount >= total_amount:
                    break

        elif pattern_name == "dense":  # Dense alert accounts (all-to-all)
            dst_list = [n for n in members if n != main_acct]
            for dst in dst_list:
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, end_date)
                sub_g.add_edge(main_acct, dst, amount=amount, date=date)
                self.g.add_edge(main_acct, dst, amount=amount, date=date)
            for dst in dst_list:
                nb1 = random.choice(dst_list)
                if dst != nb1:
                    amount = individual_amount  # random.uniform(min_amount, max_amount)
                    date = random.randrange(start_date, end_date)
                    sub_g.add_edge(dst, nb1, amount=amount, date=date)
                    self.g.add_edge(dst, nb1, amount=amount, date=date)
                nb2 = random.choice(dst_list)
                if dst != nb2:
                    amount = individual_amount  # random.uniform(min_amount, max_amount)
                    date = random.randrange(start_date, end_date)
                    sub_g.add_edge(nb2, dst, amount=amount, date=date)
                    self.g.add_edge(nb2, dst, amount=amount, date=date)

        elif pattern_name == "cycle":  # Cycle transactions
            start_index = list(members).index(main_acct)  # Index of member list indicates the main account
            num = len(members)  # Number of involved accounts
            amount = individual_amount  # max_amount  # Initial transaction amount
            dates = sorted([random.randrange(start_date, end_date) for _ in range(num)])  # Ordered transaction date
            for i in range(num):
                src_i = (start_index + i) % num
                dst_i = (src_i + 1) % num
                src = members[src_i]  # Source account ID
                dst = members[dst_i]  # Destination account ID
                date = dates[i]  # Transaction date (timestamp)

                sub_g.add_edge(src, dst, amount=amount, date=date)
                self.g.add_edge(src, dst, amount=amount, date=date)
                margin = amount * 0.1  # Margin the beneficiary account can gain
                amount = amount - margin  # max(amount - margin, min_amount)

        elif pattern_name == "scatter_gather":  # Scatter-Gather (fan-out -> fan-in)
            sub_accounts = [n for n in members if n != main_acct]
            dest = sub_accounts[0]  # Final destination account
            num = len(members)
            # The date of all scatter transactions must be performed before middle day
            middle_day = (start_date + end_date) // 2
            for i in range(1, num):
                acct = members[i]
                scatter_amount = individual_amount  # random.uniform(min_amount, max_amount)
                margin = scatter_amount * 0.1  # Margin of the intermediate account
                gather_amount = scatter_amount - margin
                scatter_date = random.randrange(start_date, middle_day)
                gather_date = random.randrange(middle_day, end_date)

                sub_g.add_edge(main_acct, acct, amount=scatter_amount, date=scatter_date)
                self.g.add_edge(main_acct, acct, amount=scatter_amount, date=scatter_date)
                sub_g.add_edge(acct, dest, amount=gather_amount, date=gather_date)
                self.g.add_edge(acct, dest, amount=gather_amount, date=gather_date)

        elif pattern_name == "gather_scatter":  # Gather-Scatter (fan-in -> fan-out)
            sub_accounts = [n for n in members if n != main_acct]
            num_orig_accounts = len(sub_accounts) // 2
            orig_accounts = sub_accounts[:num_orig_accounts]
            middle_day = (start_date + end_date) // 2

            accumulated_amount = 0.0
            for i in range(num_orig_accounts):
                acct = orig_accounts[i]
                amount = individual_amount  # random.uniform(min_amount, max_amount)
                date = random.randrange(start_date, middle_day)

                sub_g.add_edge(acct, main_acct, amount=amount, date=date)
                self.g.add_edge(acct, main_acct, amount=amount, date=date)
                accumulated_amount += amount

            margin = accumulated_amount * 0.1  # Margin of the intermediate (main) account
            bene_accounts = sub_accounts[num_orig_accounts:]
            num_bene_accounts = len(bene_accounts)
            scatter_amount = (accumulated_amount - margin) / num_bene_accounts

            for i in range(num_bene_accounts):
                acct = bene_accounts[i]
                date = random.randrange(middle_day, end_date)

                sub_g.add_edge(main_acct, acct, amount=scatter_amount, date=date)
                self.g.add_edge(main_acct, acct, amount=scatter_amount, date=date)

        else:
            print("Warning: unknown pattern type: %s" % pattern_name)
            return

        # Add the generated transaction edges to whole transaction graph
        sub_g.graph[MAIN_ACCT_KEY] = main_acct  # Main account ID
        sub_g.graph[IS_SAR_KEY] = is_sar  # SAR flag
        self.alert_groups[self.alert_id] = sub_g

        # Add the SAR flag to all member account vertices
        if is_sar:
            for n in sub_g.nodes():
                self.g.node[n][IS_SAR_KEY] = True
        self.alert_id += 1

    def write_account_list(self):
        os.makedirs(self.output_dir, exist_ok=True)
        acct_file = os.path.join(self.output_dir, self.out_account_file)
        with open(acct_file, "w") as wf:
            writer = csv.writer(wf)
            base_attrs = ["ACCOUNT_ID", "CUSTOMER_ID", "INIT_BALANCE", "START_DATE", "END_DATE", "COUNTRY",
                          "ACCOUNT_TYPE", "IS_SAR", "TX_BEHAVIOR_ID"]
            writer.writerow(base_attrs + self.attr_names)
            for n in self.g.nodes(data=True):
                aid = n[0]  # Account ID
                cid = "C_" + str(aid)  # Customer ID bounded to this account
                prop = n[1]  # Account attributes
                balance = "{0:.2f}".format(prop["init_balance"])  # Initial balance
                start = prop["start"]  # Start time (when the account is opened)
                end = prop["end"]  # End time (when the account is closed)
                country = prop["country"]  # Country
                business = prop["business"]  # Business type
                is_sar = "true" if prop[IS_SAR_KEY] else "false"  # Whether this account is involved in SAR
                model_id = prop["model_id"]  # Transaction behavior model ID
                values = [aid, cid, balance, start, end, country, business, is_sar, model_id]
                for attr_name in self.attr_names:
                    values.append(prop[attr_name])
                writer.writerow(values)
        print("Exported %d accounts to %s" % (self.g.number_of_nodes(), acct_file))

    def write_transaction_list(self):
        tx_file = os.path.join(self.output_dir, self.out_tx_file)
        with open(tx_file, "w") as wf:
            writer = csv.writer(wf)
            writer.writerow(["id", "src", "dst", "ttype"])
            for e in self.g.edges(data=True, keys=True):
                src = e[0]
                dst = e[1]
                tid = e[2]
                ttype = random.choice(self.tx_types)
                writer.writerow([tid, src, dst, ttype])
        print("Exported %d transactions to %s" % (self.g.number_of_edges(), tx_file))

    def write_alert_account_list(self):
        def get_out_edge_attrs(g, vid, name):
            return [v for k, v in nx.get_edge_attributes(g, name).items() if (k[0] == vid or k[1] == vid)]

        acct_count = 0
        alert_member_file = os.path.join(self.output_dir, self.out_alert_member_file)
        print("Output alert member list to:", alert_member_file)
        with open(alert_member_file, "w") as wf:
            writer = csv.writer(wf)
            base_attrs = ["alertID", "reason", "clientID", "isSAR", "modelID", "minAmount", "maxAmount",
                          "startStep", "endStep", "scheduleID"]
            writer.writerow(base_attrs + self.attr_names)
            for gid, sub_g in self.alert_groups.items():
                model_id = sub_g.graph["model_id"]
                schedule_id = sub_g.graph["scheduleID"]
                reason = sub_g.graph["reason"]
                start = sub_g.graph["start"]
                end = sub_g.graph["end"]
                for n in sub_g.nodes():
                    is_sar = "true" if sub_g.graph[IS_SAR_KEY] else "false"
                    min_amt = '{:.2f}'.format(min(get_out_edge_attrs(sub_g, n, "amount")))
                    max_amt = '{:.2f}'.format(max(get_out_edge_attrs(sub_g, n, "amount")))
                    min_step = start
                    max_step = end
                    values = [gid, reason, n, is_sar, model_id, min_amt, max_amt, min_step, max_step, schedule_id]
                    prop = self.g.node[n]
                    for attr_name in self.attr_names:
                        values.append(prop[attr_name])
                    writer.writerow(values)
                    acct_count += 1

        print("Exported %d members for %d alerts to %s" % (acct_count, len(self.alert_groups), alert_member_file))


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    _conf_file = argv[1]

    # Validation option for graph contractions
    deg_param = os.getenv("DEGREE")
    degree_threshold = 0 if deg_param is None else int(deg_param)

    txg = TransactionGenerator(_conf_file)
    txg.load_account_list()  # Load account list CSV file
    txg.generate_normal_transactions()  # Load a parameter CSV file for the base transaction types
    if degree_threshold > 0:
        print("Generated normal transaction network")
        txg.count_patterns(degree_threshold)
    txg.set_main_acct_candidates()  # Load a parameter CSV file for degrees of the base transaction graph
    txg.load_alert_patterns()  # Load a parameter CSV file for AML typology subgraphs
    if degree_threshold > 0:
        print("Added alert transaction patterns")
        txg.count_patterns(degree_threshold)
    txg.write_account_list()  # Export accounts to a CSV file
    txg.write_transaction_list()  # Export transactions to a CSV file
    txg.write_alert_account_list()  # Export alert accounts to a CSV file
