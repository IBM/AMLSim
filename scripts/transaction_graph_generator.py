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
from collections import Counter, defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Attribute keys
MAIN_ACCT_KEY = "main_acct"
IS_SAR_KEY = "is_sar"

DEFAULT_MARGIN_RATIO = 0.1  # Each member will keep this ratio of the received amount


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


def parse_float(value):
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


def get_positive_or_none(value):
    """ Get positive value or None
    :param value: Numerical value or None
    :return: If the value is positive, return this value. Otherwise, return None.
    """
    if value is None:
        return None
    else:
        return value if value > 0 else None


def directed_configuration_model(_in_deg, _out_deg, seed=0):
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
    if in_len != out_len:
        raise ValueError("The length of in-degree (%d) and out-degree (%d) sequences must be same." % (in_len, out_len))

    total_in_deg, total_out_deg = sum(_in_deg), sum(_out_deg)
    if total_in_deg != total_out_deg:
        raise ValueError("The sum of in-degree (%d) and out-degree (%d) must be same." % (total_in_deg, total_out_deg))

    total_v = in_len
    if num_v % total_v != 0:
        raise ValueError("The number of total accounts (%d) "
                         "must be a multiple of the degree sequence length (%d)." % (num_v, total_v))

    repeats = num_v // total_v
    _in_deg = _in_deg * repeats
    _out_deg = _out_deg * repeats

    assert sum(_in_deg) == sum(_out_deg), "Sequences must have equal sums."
    return _in_deg, _out_deg


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
        # self.degrees = dict()  # Degree distribution
        self.hubs = list()  # Hub vertices
        self.main_acct_candidates = set()  # Set of the main account candidates of AML typology subgraphs
        self.attr_names = list()  # Additional account attribute names
        self.bank_to_accts = defaultdict(set)  # Bank ID -> account set
        self.acct_to_bank = dict()  # Account ID -> bank ID

        with open(conf_file, "r") as rf:
            self.conf = json.load(rf)

        general_conf = self.conf["general"]

        # Set random seed
        seed = general_conf.get("random_seed")
        env_seed = os.getenv("RANDOM_SEED")
        if env_seed is not None:
            seed = env_seed  # Overwrite random seed if specified as an environment variable
        self.seed = seed if seed is None else int(seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        print("Random seed:", self.seed)

        # Get simulation name
        sim_name = os.getenv("SIMULATION_NAME")
        if sim_name is None:
            sim_name = general_conf["simulation_name"]
        print("Simulation name:", sim_name)

        self.total_steps = parse_int(general_conf["total_steps"])

        # Set default amounts, steps and model ID
        default_conf = self.conf["default"]
        self.default_min_amount = parse_float(default_conf.get("min_amount"))
        self.default_max_amount = parse_float(default_conf.get("max_amount"))
        self.default_min_balance = parse_float(default_conf.get("min_balance"))
        self.default_max_balance = parse_float(default_conf.get("max_balance"))
        self.default_start_step = parse_int(default_conf.get("start_step"))
        self.default_end_step = parse_int(default_conf.get("end_step"))
        self.default_start_range = parse_int(default_conf.get("start_range"))
        self.default_end_range = parse_int(default_conf.get("end_range"))
        self.default_model = parse_int(default_conf.get("transaction_model"))

        self.margin_ratio = parse_float(default_conf.get("margin_ratio", DEFAULT_MARGIN_RATIO))
        if not 0.0 <= self.margin_ratio <= 1.0:
            raise ValueError("Margin ratio in AML typologies is %f, must be within [0.0, 1.0]" % self.margin_ratio)

        self.default_bank_id = default_conf.get("bank_id")  # Default bank ID if not specified at parameter files

        # Get input file names and properties
        input_conf = self.conf["input"]
        self.input_dir = input_conf["directory"]  # Directory name of input files
        self.account_file = input_conf["accounts"]  # Account list file
        self.alert_file = input_conf["alert_patterns"]
        self.degree_file = input_conf["degree"]
        self.type_file = input_conf["transaction_type"]
        self.is_aggregated = input_conf["is_aggregated_accounts"]

        # Get output file names
        output_conf = self.conf["temporal"]  # The output directory of this graph generator is the temporal directory
        self.output_dir = os.path.join(output_conf["directory"], sim_name)
        self.out_tx_file = output_conf["transactions"]
        self.out_account_file = output_conf["accounts"]
        self.out_alert_member_file = output_conf["alert_members"]

        # Other properties for the transaction graph generator
        other_conf = self.conf["graph_generator"]
        self.degree_threshold = parse_int(other_conf["degree_threshold"])
        high_risk_countries_str = other_conf.get("high_risk_countries", "")
        high_risk_business_str = other_conf.get("high_risk_business", "")
        self.high_risk_countries = set(high_risk_countries_str.split(","))
        self.high_risk_business = set(high_risk_business_str.split(","))

        self.tx_id = 0  # Transaction ID
        self.alert_id = 0  # Alert ID from the alert parameter file
        self.alert_groups = dict()  # Alert ID and alert transaction subgraph
        # TODO: Move the mapping of AML pattern to configuration JSON file
        self.alert_types = {"fan_out": 1, "fan_in": 2, "cycle": 3, "bipartite": 4, "stack": 5,
                            "random": 6, "scatter_gather": 7, "gather_scatter": 8}  # Pattern name and model ID

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
        """Choose hub accounts with larger degree than the specified threshold
        as the main account candidates of alert transaction sets
        """
        # degrees = self.g.in_degree()
        self.hubs = [n for n in self.g.nodes() if self.degree_threshold <= self.g.in_degree(n) + self.g.out_degree(n)]
        # self.degrees = self.g.degree(self.g.nodes())
        # self.hubs = [n for n in self.g.nodes() if self.degree_threshold <= self.degrees[n]]
        self.main_acct_candidates = set(self.hubs)

    def add_normal_sar_edges(self, ratio=1.0):
        """Add extra edges from normal accounts to SAR accounts to adjust transaction graph features
        """
        orig_candidates = [n for n in self.main_acct_candidates if not self.g.node[n].get(IS_SAR_KEY, False)]
        bene_candidates = [n for n, sar in nx.get_node_attributes(self.g, IS_SAR_KEY).items() if sar]
        num = int(len(bene_candidates) * ratio)
        if num <= 0:
            return

        orig_list = random.choices(orig_candidates, k=num)
        bene_list = random.choices(bene_candidates, k=num)
        for i in range(num):
            _orig = orig_list[i]
            _bene = bene_list[i]
            self.add_transaction(_orig, _bene)
        print("Added %d edges from normal accounts to sar accounts" % num)

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

    def get_all_bank_ids(self):
        return list(self.bank_to_accts.keys())

    def get_typology_members(self, num, bank_id=""):
        """Choose accounts randomly from one or multiple banks.
        :param num: Number of total account vertices
        :param bank_id: It chooses members from a single bank with the ID. If empty, it chooses members from all banks.
        :return: Main account and account ID list
        """
        if num <= 1:
            raise ValueError("The number of members must be more than 1")

        if bank_id in self.bank_to_accts:  # Choose members from the same bank as the main account
            bank_accts = self.bank_to_accts[bank_id]
            main_candidates = self.main_acct_candidates & bank_accts
            main_acct = random.sample(main_candidates, 1)[0]
            self.remove_typology_candidate(main_acct)
            sub_accts = random.sample(bank_accts, num - 1)
            for n in sub_accts:
                self.remove_typology_candidate(n)

            members = [main_acct] + sub_accts
            return main_acct, members

        elif bank_id == "":  # Choose members from all accounts
            main_acct = random.sample(self.main_acct_candidates, 1)[0]
            self.remove_typology_candidate(main_acct)

            sub_accts = random.sample(self.acct_to_bank.keys(), num - 1)
            for n in sub_accts:
                self.remove_typology_candidate(n)
            members = [main_acct] + sub_accts
            return main_acct, members

        else:
            raise KeyError("No such bank ID: %s" % bank_id)

    def load_account_list(self):
        """Load and add account vertices from a CSV file
        """
        acct_file = os.path.join(self.input_dir, self.account_file)
        if self.is_aggregated:
            self.load_account_list_param(acct_file)
        else:
            self.load_account_list_raw(acct_file)

    def load_account_list_raw(self, acct_file):
        """Load and add account vertices from a CSV file with raw account info
        header: uuid,seq,first_name,last_name,street_addr,city,state,zip,gender,phone_number,birth_date,ssn
        :param acct_file: Raw account list file path
        """
        if self.default_min_balance is None:
            raise KeyError("Option 'default_min_balance' is required to load raw account list")
        min_balance = self.default_min_balance

        if self.default_max_balance is None:
            raise KeyError("Option 'default_max_balance' is required to load raw account list")
        max_balance = self.default_max_balance

        start_day = get_positive_or_none(self.default_start_step)
        end_day = get_positive_or_none(self.default_end_step)
        start_range = get_positive_or_none(self.default_start_range)
        end_range = get_positive_or_none(self.default_end_range)
        default_model = self.default_model if self.default_model is not None else 1

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
                if row[0].startswith("#"):  # Comment line
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

    def load_account_list_param(self, acct_file):
        """Load and add account vertices from a CSV file with aggregated parameters
        Each row may represent two or more accounts
        :param acct_file: Account parameter file path
        """
        idx_num = None  # Number of accounts per row
        idx_min = None  # Minimum initial balance
        idx_max = None  # Maximum initial balance
        idx_start = None  # Start step
        idx_end = None  # End step
        idx_country = None  # Country
        idx_business = None  # Business type
        idx_model = None  # Transaction model
        idx_bank = None  # Bank ID

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
                elif k == "bank_id":
                    idx_bank = i
                else:
                    print("Warning: unknown key: %s" % k)

            acct_id = 0
            for row in reader:
                if row[0].startswith("#"):
                    continue
                num = int(row[idx_num])
                min_balance = parse_float(row[idx_min])
                max_balance = parse_float(row[idx_max])
                start_day = parse_int(row[idx_start]) if idx_start is not None else -1
                end_day = parse_int(row[idx_end]) if idx_end is not None else -1
                country = row[idx_country]
                business = row[idx_business]
                model_id = parse_int(row[idx_model])
                bank_id = row[idx_bank] if idx_bank is not None else self.default_bank_id

                for i in range(num):
                    init_balance = random.uniform(min_balance, max_balance)  # Generate amount
                    self.add_account(acct_id, init_balance, start_day, end_day, country, business, model_id, bank_id)
                    acct_id += 1

        self.num_accounts = acct_id
        print("Generated %d accounts." % self.num_accounts)

    def generate_normal_transactions(self):
        """Generate a base directed graph from degree sequences
        TODO: Add options to call scale-free generator functions directly instead of loading degree CSV files
        :return: Directed graph as the base transaction graph (not complete transaction graph)
        """
        deg_file = os.path.join(self.input_dir, self.degree_file)
        in_deg, out_deg = get_degrees(deg_file, self.num_accounts)
        g = directed_configuration_model(in_deg, out_deg, self.seed)

        print("Add %d base transactions" % g.number_of_edges())
        nodes = self.g.nodes()
        for src_i, dst_i in g.edges():
            assert (src_i != dst_i)
            src = nodes[src_i]
            dst = nodes[dst_i]
            self.add_transaction(src, dst)  # Add edges to transaction graph

    def add_account(self, acct_id, init_balance, start, end, country, business, model_id, bank_id=None, **attr):
        """Add an account vertex
        :param acct_id: Account ID
        :param init_balance: Initial amount
        :param start: The day when the account opened
        :param end: The day when the account closed
        :param country: Country name
        :param business: Business type
        :param model_id: Transaction model ID
        :param bank_id: Bank ID
        :param attr: Optional attributes
        :return:
        """
        if bank_id is None:
            bank_id = self.default_bank_id

        # Add an account vertex with an ID and attributes if and only if it is not yet added
        if self.check_account_absent(acct_id):
            self.g.add_node(acct_id, label="account", init_balance=init_balance, start=start, end=end,
                            country=country, business=business, is_sar=False,
                            model_id=model_id, bank_id=bank_id, **attr)
            self.bank_to_accts[bank_id].add(acct_id)
            self.acct_to_bank[acct_id] = bank_id

    def remove_typology_candidate(self, acct):
        """Remove an account vertex from AML typology member candidates
        :param acct: Account ID
        """
        self.main_acct_candidates.discard(acct)
        bank_id = self.acct_to_bank[acct]
        del self.acct_to_bank[acct]
        self.bank_to_accts[bank_id].discard(acct)

    def add_transaction(self, orig, bene, amount=None, date=None, tx_type=None):
        """Add a transaction edge
        :param orig: Originator account ID
        :param bene: Beneficiary account ID
        :param amount: Transaction amount
        :param date: Transaction date
        :param tx_type: Transaction type description
        :return:
        """
        self.check_account_exist(orig)  # Ensure the originator and beneficiary accounts exist
        self.check_account_exist(bene)
        if orig == bene:
            raise ValueError("Self loop from/to %s is not allowed for transaction networks" % str(orig))
        self.g.add_edge(orig, bene, key=self.tx_id, label="transaction", amount=amount, date=date, ttype=tx_type)
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
        idx_schedule = None
        idx_min_accts = None
        idx_max_accts = None
        idx_min_amt = None
        idx_max_amt = None
        idx_min_period = None
        idx_max_period = None
        idx_bank = None
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
                elif k == "schedule_id":
                    idx_schedule = i
                elif k == "min_accounts":
                    idx_min_accts = i
                elif k == "max_accounts":
                    idx_max_accts = i
                elif k == "min_amount":
                    idx_min_amt = i
                elif k == "max_amount":
                    idx_max_amt = i
                elif k == "min_period":
                    idx_min_period = i
                elif k == "max_period":
                    idx_max_period = i
                elif k == "bank_id":  # Bank ID for internal-bank transactions
                    idx_bank = i
                elif k == "is_sar":  # SAR flag
                    idx_sar = i
                else:
                    print("Warning: unknown key: %s" % k)

            # Generate transaction set
            count = 0
            for row in reader:
                if len(row) == 0 or row[0].startswith("#"):
                    continue
                num_patterns = int(row[idx_num])  # Number of alert patterns
                typology_name = row[idx_type]
                schedule = int(row[idx_schedule])
                min_accts = int(row[idx_min_accts])
                max_accts = int(row[idx_max_accts])
                min_amount = parse_float(row[idx_min_amt])
                max_amount = parse_float(row[idx_max_amt])
                min_period = parse_int(row[idx_min_period])
                max_period = parse_int(row[idx_max_period])
                bank_id = row[idx_bank] if idx_bank is not None else ""
                is_sar = parse_flag(row[idx_sar])

                if typology_name not in self.alert_types:
                    print("Warning: pattern type name (%s) must be one of %s"
                          % (typology_name, str(self.alert_types.keys())))
                    continue

                for i in range(num_patterns):
                    num_accts = random.randrange(min_accts, max_accts + 1)
                    init_amount = random.uniform(min_amount, max_amount)
                    period = random.randrange(min_period, max_period + 1)
                    self.add_aml_typology(is_sar, typology_name, num_accts, init_amount, period, bank_id, schedule)
                    count += 1
                    if count % 1000 == 0:
                        print("Created %d alerts" % count)

    def add_aml_typology(self, is_sar, typology_name, num_accounts, init_amount, period, bank_id="", schedule=1):
        """Add an AML typology transaction set
        :param is_sar: Whether the alerted transaction set is SAR (True) or false-alert (False)
        :param typology_name: Name of pattern type
            ("fan_in", "fan_out", "cycle", "random", "stack", "scatter_gather" or "gather_scatter")
        :param num_accounts: Number of transaction members (accounts)
        :param init_amount: Initial individual amount
        :param period: Period (number of days) for all transactions
        :param bank_id: Bank ID which it chooses members from. If empty, it chooses members from all banks.
        :param schedule: AML pattern transaction schedule model ID
        """
        # main_acct, members = self.get_typology_members(num_accounts, bank_id)
        if bank_id == "" and len(self.bank_to_accts) >= 2:
            is_external = True
        elif bank_id != "" and bank_id not in self.bank_to_accts:  # Invalid bank ID
            raise KeyError("No such bank ID: %s" % bank_id)
        else:
            is_external = False

        start_date = random.randrange(0, self.total_steps - period)
        end_date = start_date + period - 1

        # Create subgraph structure with transaction attributes
        model_id = self.alert_types[typology_name]  # alert model ID
        sub_g = nx.MultiDiGraph(model_id=model_id, reason=typology_name, scheduleID=schedule,
                                start=start_date, end=end_date)  # Transaction subgraph for a typology

        # Set bank ID attribute to a member account
        def add_node(_n, _bank_id):
            sub_g.add_node(_n, bank_id=_bank_id)

        def add_edge(_orig, _bene, _amount, _date):
            """Add transaction edge to the AML typology subgraph as well as the whole transaction graph
            :param _orig: Originator account ID
            :param _bene: Beneficiary account ID
            :param _amount: Transaction amount
            :param _date: Transaction timestamp
            """
            sub_g.add_edge(_orig, _bene, amount=_amount, date=_date)
            self.add_transaction(_orig, _bene, amount=_amount, date=_date)

        if typology_name == "fan_in":  # fan_in pattern (multiple accounts --> single (main) account)
            main_acct = random.sample(self.main_acct_candidates, 1)[0]
            main_bank_id = self.acct_to_bank[main_acct]
            self.remove_typology_candidate(main_acct)
            add_node(main_acct, main_bank_id)

            if is_external:
                sub_bank_id = random.choice([b for b in self.get_all_bank_ids() if b != main_bank_id])
            else:
                sub_bank_id = main_bank_id
            sub_accts = random.sample(self.bank_to_accts[sub_bank_id], num_accounts - 1)
            for n in sub_accts:
                self.remove_typology_candidate(n)
                add_node(n, sub_bank_id)

            for orig in sub_accts:
                amount = init_amount
                date = random.randrange(start_date, end_date)
                add_edge(orig, main_acct, amount, date)

        elif typology_name == "fan_out":  # fan_out pattern (single (main) account --> multiple accounts)
            main_acct = random.sample(self.main_acct_candidates, 1)[0]
            main_bank_id = self.acct_to_bank[main_acct]
            self.remove_typology_candidate(main_acct)
            add_node(main_acct, main_bank_id)

            if is_external:
                sub_bank_id = random.choice([b for b in self.get_all_bank_ids() if b != main_bank_id])
            else:
                sub_bank_id = main_bank_id
            sub_accts = random.sample(self.bank_to_accts[sub_bank_id], num_accounts - 1)
            for n in sub_accts:
                self.remove_typology_candidate(n)
                add_node(n, sub_bank_id)

            for bene in sub_accts:
                amount = init_amount
                date = random.randrange(start_date, end_date)
                add_edge(main_acct, bene, amount, date)

        elif typology_name == "bipartite":  # bipartite (originators -> many-to-many -> beneficiaries)
            orig_bank_id = random.choice(self.get_all_bank_ids())
            if is_external:
                bene_bank_id = random.choice([b for b in self.get_all_bank_ids() if b != orig_bank_id])
            else:
                bene_bank_id = orig_bank_id

            num_orig_accts = num_accounts // 2  # The former half members are originator accounts
            num_bene_accts = num_accounts - num_orig_accts  # The latter half members are beneficiary accounts

            orig_accts = random.sample(self.bank_to_accts[orig_bank_id], num_orig_accts)
            for n in orig_accts:
                self.remove_typology_candidate(n)
                add_node(n, orig_bank_id)
            main_acct = orig_accts[0]

            bene_accts = random.sample(self.bank_to_accts[bene_bank_id], num_bene_accts)
            for n in bene_accts:
                self.remove_typology_candidate(n)
                add_node(n, bene_bank_id)

            for orig, bene in itertools.product(orig_accts, bene_accts):  # All-to-all transaction edges
                amount = init_amount
                date = random.randrange(start_date, end_date)
                add_edge(orig, bene, amount, date)

        elif typology_name == "stack":  # stacked bipartite layers
            if is_external:
                if len(self.get_all_bank_ids()) >= 3:
                    [orig_bank_id, mid_bank_id, bene_bank_id] = random.sample(self.get_all_bank_ids(), 3)
                else:
                    [orig_bank_id, mid_bank_id] = random.sample(self.get_all_bank_ids(), 2)
                    bene_bank_id = orig_bank_id
            else:
                orig_bank_id = mid_bank_id = bene_bank_id = random.sample(self.get_all_bank_ids(), 1)[0]

            # First and second 1/3 of members: originator and intermediate accounts
            num_orig_accts = num_mid_accts = num_accounts // 3
            # Last 1/3 of members: beneficiary accounts
            num_bene_accts = num_accounts - num_orig_accts * 2

            orig_accts = random.sample(self.bank_to_accts[orig_bank_id], num_orig_accts)
            for n in orig_accts:
                self.remove_typology_candidate(n)
                add_node(n, orig_bank_id)
            main_acct = orig_accts[0]

            mid_accts = random.sample(self.bank_to_accts[mid_bank_id], num_mid_accts)
            for n in mid_accts:
                self.remove_typology_candidate(n)
                add_node(n, mid_bank_id)
            bene_accts = random.sample(self.bank_to_accts[bene_bank_id], num_bene_accts)
            for n in bene_accts:
                self.remove_typology_candidate(n)
                add_node(n, bene_bank_id)

            for orig, bene in itertools.product(orig_accts, mid_accts):  # all-to-all transactions
                amount = init_amount
                date = random.randrange(start_date, end_date)
                add_edge(orig, bene, amount, date)

            for orig, bene in itertools.product(mid_accts, bene_accts):  # all-to-all transactions
                amount = init_amount
                date = random.randrange(start_date, end_date)
                add_edge(orig, bene, amount, date)

        elif typology_name == "random":  # Random transactions among members
            amount = init_amount
            date = random.randrange(start_date, end_date)

            if is_external:
                all_bank_ids = self.get_all_bank_ids()
                bank_id_iter = itertools.cycle(all_bank_ids)
                prev_acct = None
                main_acct = None
                for _ in range(num_accounts):
                    bank_id = next(bank_id_iter)
                    next_acct = random.sample(self.bank_to_accts[bank_id], 1)[0]
                    if prev_acct is None:
                        main_acct = next_acct
                    else:
                        add_edge(prev_acct, next_acct, amount, date)
                    self.remove_typology_candidate(next_acct)
                    add_node(next_acct, bank_id)
                    prev_acct = next_acct

            else:
                main_acct = random.sample(self.main_acct_candidates, 1)[0]
                bank_id = self.acct_to_bank[main_acct]
                self.remove_typology_candidate(main_acct)
                add_node(main_acct, bank_id)
                sub_accts = random.sample(self.bank_to_accts[bank_id], num_accounts - 1)
                for n in sub_accts:
                    self.remove_typology_candidate(n)
                    add_node(n, bank_id)
                prev_acct = main_acct
                for _ in range(num_accounts - 1):
                    next_acct = random.choice([n for n in sub_accts if n != prev_acct])
                    add_edge(prev_acct, next_acct, amount, date)
                    prev_acct = next_acct

        elif typology_name == "cycle":  # Cycle transactions
            amount = init_amount
            dates = sorted([random.randrange(start_date, end_date) for _ in range(num_accounts)])

            if is_external:
                all_accts = list()
                all_bank_ids = self.get_all_bank_ids()
                remain_num = num_accounts

                while all_bank_ids:
                    num_accts_per_bank = remain_num // len(all_bank_ids)
                    bank_id = all_bank_ids.pop()
                    new_members = random.sample(self.bank_to_accts[bank_id], num_accts_per_bank)
                    all_accts.extend(new_members)

                    remain_num -= len(new_members)
                    for n in new_members:
                        self.remove_typology_candidate(n)
                        add_node(n, bank_id)

                main_acct = all_accts[0]

            else:
                main_acct = random.sample(self.main_acct_candidates, 1)[0]
                bank_id = self.acct_to_bank[main_acct]
                self.remove_typology_candidate(main_acct)
                add_node(main_acct, bank_id)
                sub_accts = random.sample(self.bank_to_accts[bank_id], num_accounts - 1)
                for n in sub_accts:
                    self.remove_typology_candidate(n)
                    add_node(n, bank_id)
                all_accts = [main_acct] + sub_accts

            for i in range(num_accounts):
                orig_i = i
                bene_i = (i + 1) % num_accounts
                orig_acct = all_accts[orig_i]
                bene_acct = all_accts[bene_i]
                date = dates[i]

                add_edge(orig_acct, bene_acct, amount, date)
                margin = amount * self.margin_ratio  # Margin the beneficiary account can gain
                amount = amount - margin  # max(amount - margin, min_amount)

        elif typology_name == "scatter_gather":  # Scatter-Gather (fan-out -> fan-in)
            if is_external:
                if len(self.get_all_bank_ids()) >= 3:
                    [orig_bank_id, mid_bank_id, bene_bank_id] = random.sample(self.get_all_bank_ids(), 3)
                else:
                    [orig_bank_id, mid_bank_id] = random.sample(self.get_all_bank_ids(), 2)
                    bene_bank_id = orig_bank_id
            else:
                orig_bank_id = mid_bank_id = bene_bank_id = random.sample(self.get_all_bank_ids(), 1)[0]

            main_acct = orig_acct = random.sample(self.bank_to_accts[orig_bank_id], 1)[0]
            self.remove_typology_candidate(orig_acct)
            add_node(orig_acct, orig_bank_id)
            mid_accts = random.sample(self.bank_to_accts[mid_bank_id], num_accounts - 2)
            for n in mid_accts:
                self.remove_typology_candidate(n)
                add_node(n, mid_bank_id)
            bene_acct = random.sample(self.bank_to_accts[bene_bank_id], 1)[0]
            self.remove_typology_candidate(bene_acct)
            add_node(bene_acct, bene_bank_id)

            # The date of all scatter transactions must be performed before middle day
            mid_date = (start_date + end_date) // 2

            for i in range(len(mid_accts)):
                mid_acct = mid_accts[i]
                scatter_amount = init_amount
                margin = scatter_amount * self.margin_ratio  # Margin of the intermediate account
                amount = scatter_amount - margin
                scatter_date = random.randrange(start_date, mid_date)
                gather_date = random.randrange(mid_date, end_date)

                add_edge(orig_acct, mid_acct, scatter_amount, scatter_date)
                add_edge(mid_acct, bene_acct, amount, gather_date)

        elif typology_name == "gather_scatter":  # Gather-Scatter (fan-in -> fan-out)
            if is_external:
                if len(self.get_all_bank_ids()) >= 3:
                    [orig_bank_id, mid_bank_id, bene_bank_id] = random.sample(self.get_all_bank_ids(), 3)
                else:
                    [orig_bank_id, mid_bank_id] = random.sample(self.get_all_bank_ids(), 2)
                    bene_bank_id = orig_bank_id
            else:
                orig_bank_id = mid_bank_id = bene_bank_id = random.sample(self.get_all_bank_ids(), 1)[0]

            num_orig_accts = num_bene_accts = (num_accounts - 1) // 2

            orig_accts = random.sample(self.bank_to_accts[orig_bank_id], num_orig_accts)
            for n in orig_accts:
                self.remove_typology_candidate(n)
                add_node(n, orig_bank_id)
            main_acct = mid_acct = random.sample(self.bank_to_accts[mid_bank_id], 1)[0]
            self.remove_typology_candidate(mid_acct)
            add_node(mid_acct, mid_bank_id)
            bene_accts = random.sample(self.bank_to_accts[bene_bank_id], num_bene_accts)
            for n in bene_accts:
                self.remove_typology_candidate(n)
                add_node(n, bene_bank_id)

            accumulated_amount = 0.0
            mid_date = (start_date + end_date) // 2
            # print(start_date, mid_date, end_date)
            amount = init_amount

            for i in range(num_orig_accts):
                orig_acct = orig_accts[i]
                date = random.randrange(start_date, mid_date)
                add_edge(orig_acct, mid_acct, amount, date)
                accumulated_amount += amount
                # print(orig_acct, "->", date, "->", mid_acct)

            # margin = accumulated_amount * self.margin_ratio  # Margin of the intermediate (main) account
            # scatter_amount = (accumulated_amount - margin) / num_bene_accts

            for i in range(num_bene_accts):
                bene_acct = bene_accts[i]
                date = random.randrange(mid_date, end_date)
                add_edge(mid_acct, bene_acct, amount, date)
                # print(mid_acct, "->", date, "->", bene_acct)
            # print(orig_accts, mid_acct, bene_accts)

        # TODO: Please add user-defined typology implementations here

        else:
            print("Warning: unknown pattern type: %s" % typology_name)
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
                          "ACCOUNT_TYPE", "IS_SAR", "TX_BEHAVIOR_ID", "BANK_ID"]
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
                bank_id = prop["bank_id"]  # Bank ID
                values = [aid, cid, balance, start, end, country, business, is_sar, model_id, bank_id]
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
                tx_type = random.choice(self.tx_types)
                writer.writerow([tid, src, dst, tx_type])
        print("Exported %d transactions to %s" % (self.g.number_of_edges(), tx_file))

    def write_alert_account_list(self):
        def get_out_edge_attrs(g, vid, name):
            return [v for k, v in nx.get_edge_attributes(g, name).items() if (k[0] == vid or k[1] == vid)]

        acct_count = 0
        alert_member_file = os.path.join(self.output_dir, self.out_alert_member_file)
        print("Output alert member list to:", alert_member_file)
        with open(alert_member_file, "w") as wf:
            writer = csv.writer(wf)
            base_attrs = ["alertID", "reason", "accountID", "isMain", "isSAR", "modelID", "minAmount", "maxAmount",
                          "startStep", "endStep", "scheduleID", "bankID"]
            writer.writerow(base_attrs + self.attr_names)
            for gid, sub_g in self.alert_groups.items():
                main_id = sub_g.graph[MAIN_ACCT_KEY]
                model_id = sub_g.graph["model_id"]
                schedule_id = sub_g.graph["scheduleID"]
                reason = sub_g.graph["reason"]
                start = sub_g.graph["start"]
                end = sub_g.graph["end"]
                for n in sub_g.nodes():
                    is_main = "true" if n == main_id else "false"
                    is_sar = "true" if sub_g.graph[IS_SAR_KEY] else "false"
                    min_amt = '{:.2f}'.format(min(get_out_edge_attrs(sub_g, n, "amount")))
                    max_amt = '{:.2f}'.format(max(get_out_edge_attrs(sub_g, n, "amount")))
                    min_step = start
                    max_step = end
                    bank_id = sub_g.node[n]["bank_id"]
                    values = [gid, reason, n, is_main, is_sar, model_id, min_amt, max_amt,
                              min_step, max_step, schedule_id, bank_id]
                    prop = self.g.node[n]
                    for attr_name in self.attr_names:
                        values.append(prop[attr_name])
                    writer.writerow(values)
                    acct_count += 1

        print("Exported %d members for %d AML typologies to %s" %
              (acct_count, len(self.alert_groups), alert_member_file))

    def count_fan_in_out_patterns(self, threshold=2):
        """Count the number of fan-in and fan-out patterns in the generated transaction graph
        """
        in_deg = Counter(self.g.in_degree().values())  # in-degree, count
        out_deg = Counter(self.g.out_degree().values())  # out-degree, count
        for th in range(2, threshold + 1):
            num_fan_in = sum([c for d, c in in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in out_deg.items() if d >= th])
            print("\tNumber of fan-in / fan-out patterns with", th, "neighbors:", num_fan_in, "/", num_fan_out)

        main_in_deg = Counter()
        main_out_deg = Counter()
        for sub_g in self.alert_groups.values():
            main_acct = sub_g.graph[MAIN_ACCT_KEY]
            main_in_deg[self.g.in_degree(main_acct)] += 1
            main_out_deg[self.g.out_degree(main_acct)] += 1
        for th in range(2, threshold + 1):
            num_fan_in = sum([c for d, c in main_in_deg.items() if d >= threshold])
            num_fan_out = sum([c for d, c in main_out_deg.items() if d >= threshold])
            print("\tNumber of alerted fan-in / fan-out patterns with", th, "neighbors", num_fan_in, "/", num_fan_out)


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    _conf_file = argv[1]
    if len(argv) >= 3:
        _ratio = float(argv[2])
    else:
        _ratio = 1.0

    # Validation option for graph contractions
    deg_param = os.getenv("DEGREE")
    degree_threshold = 0 if deg_param is None else int(deg_param)

    txg = TransactionGenerator(_conf_file)
    txg.load_account_list()  # Load account list CSV file
    txg.generate_normal_transactions()  # Load a parameter CSV file for the base transaction types
    if degree_threshold > 0:
        print("Generated normal transaction network")
        txg.count_fan_in_out_patterns(degree_threshold)
    txg.set_main_acct_candidates()  # Load a parameter CSV file for degrees of the base transaction graph
    txg.load_alert_patterns()  # Load a parameter CSV file for AML typology subgraphs
    txg.add_normal_sar_edges(_ratio)

    if degree_threshold > 0:
        print("Added alert transaction patterns")
        txg.count_fan_in_out_patterns(degree_threshold)
    txg.write_account_list()  # Export accounts to a CSV file
    txg.write_transaction_list()  # Export transactions to a CSV file
    txg.write_alert_account_list()  # Export alert accounts to a CSV file
