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

import cProfile


from collections import Counter, defaultdict
from amlsim.nominator import Nominator
from amlsim.normal_model import NormalModel

from amlsim.random_amount import RandomAmount
from amlsim.rounded_amount import RoundedAmount


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Attribute keys
MAIN_ACCT_KEY = "main_acct"  # Main account ID (SAR typology subgraph attribute)
IS_SAR_KEY = "is_sar"  # SAR flag (account vertex attribute)

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
    :return: True if the value is equal to "true" (case-insensitive), otherwise False
    """
    return type(value) == str and value.lower() == "true"


def get_positive_or_none(value):
    """ Get positive value or None (used to parse simulation step parameters)
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
        return _g  # No edges exist

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
            logger.warning("Self loop from/to %d at %d" % (_src, idx))
    return _g


def get_degrees(deg_csv, num_v):
    """
    :param deg_csv: Degree distribution parameter CSV file
    :param num_v: Number of total account vertices
    :return: In-degree and out-degree sequence list
    """
    with open(deg_csv, "r") as rf:  # Load in/out-degree sequences from parameter CSV file for each account
        reader = csv.reader(rf)
        next(reader)
        return get_in_and_out_degrees(reader, num_v)


def get_in_and_out_degrees(iterable, num_v):
    _in_deg = list()  # In-degree sequence
    _out_deg = list()  # Out-degree sequence
    
    for row in iterable:
        if row[0].startswith("#"):
            continue
        count = int(row[0])
        _in_deg.extend([int(row[1])] * count)
        _out_deg.extend([int(row[2])] * count)

    in_len, out_len = len(_in_deg), len(_out_deg)
    if in_len != out_len:
        raise ValueError("The length of in-degree (%d) and out-degree (%d) sequences must be same."
                         % (in_len, out_len))

    total_in_deg, total_out_deg = sum(_in_deg), sum(_out_deg)
    if total_in_deg != total_out_deg:
        raise ValueError("The sum of in-degree (%d) and out-degree (%d) must be same."
                         % (total_in_deg, total_out_deg))

    if num_v % in_len != 0:
        raise ValueError("The number of total accounts (%d) "
                         "must be a multiple of the degree sequence length (%d)."
                         % (num_v, in_len))

    repeats = num_v // in_len
    _in_deg = _in_deg * repeats
    _out_deg = _out_deg * repeats

    return _in_deg, _out_deg


class TransactionGenerator:

    def __init__(self, conf, sim_name=None):
        """Initialize transaction network from parameter files.
        :param conf_file: JSON file as configurations
        :param sim_name: Simulation name (overrides the content in the `conf_json`)
        """
        self.g = nx.DiGraph()  # Transaction graph object
        self.num_accounts = 0  # Number of total accounts
        self.hubs = set()  # Hub account vertices (main account candidates of AML typology subgraphs)
        self.attr_names = list()  # Additional account attribute names
        self.bank_to_accts = defaultdict(set)  # Bank ID -> account set
        self.acct_to_bank = dict()  # Account ID -> bank ID
        self.normal_model_counts = dict()
        self.normal_models = list()
        self.normal_model_id = 1

        self.conf = conf

        general_conf = self.conf["general"]

        # Set random seed
        seed = general_conf.get("random_seed")
        env_seed = os.getenv("RANDOM_SEED")
        if env_seed is not None:
            seed = env_seed  # Overwrite random seed if specified as an environment variable
        self.seed = seed if seed is None else int(seed)
        np.random.seed(self.seed)
        random.seed(self.seed)
        logger.info("Random seed: " + str(self.seed))

        # Get simulation name
        if sim_name is None:
            sim_name = general_conf["simulation_name"]
        logger.info("Simulation name: " + sim_name)

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

        # The ratio of amount intermediate accounts receive
        self.margin_ratio = parse_float(default_conf.get("margin_ratio", DEFAULT_MARGIN_RATIO))
        if not 0.0 <= self.margin_ratio <= 1.0:
            raise ValueError("Margin ratio in AML typologies (%f) must be within [0.0, 1.0]" % self.margin_ratio)

        self.default_bank_id = default_conf.get("bank_id")  # Default bank ID if not specified at parameter files

        # Get input file names and properties
        input_conf = self.conf["input"]
        self.input_dir = input_conf["directory"]  # The directory name of input files
        self.account_file = input_conf["accounts"]  # Account list file
        self.alert_file = input_conf["alert_patterns"]  # AML typology definition file
        self.normal_models_file = input_conf["normal_models"] # Normal models definition file
        self.degree_file = input_conf["degree"]  # Degree distribution file
        self.type_file = input_conf["transaction_type"]  # Transaction type
        self.is_aggregated = input_conf["is_aggregated_accounts"]  # Flag whether the account list is aggregated

        # Get output file names
        output_conf = self.conf["temporal"]  # The output directory of the graph generator is temporal one
        self.output_dir = os.path.join(output_conf["directory"], sim_name)  # The directory name of temporal files
        self.out_tx_file = output_conf["transactions"]  # All transaction list CSV file
        self.out_account_file = output_conf["accounts"]  # All account list CSV file
        self.out_alert_member_file = output_conf["alert_members"]  # Account list of AML typology members CSV file
        self.out_normal_models_file = output_conf["normal_models"] # List of normal models CSV file
 
        # Other properties for the transaction graph generator
        other_conf = self.conf["graph_generator"]
        self.degree_threshold = parse_int(other_conf["degree_threshold"])  # Degree for candidates of main accounts
        high_risk_countries_str = other_conf.get("high_risk_countries", "")
        high_risk_business_str = other_conf.get("high_risk_business", "")
        self.high_risk_countries = set(high_risk_countries_str.split(","))  # List of high-risk country codes
        self.high_risk_business = set(high_risk_business_str.split(","))  # List of high-risk business types

        self.edge_id = 0  # Edge ID. Formerly Transaction ID
        self.alert_id = 0  # Alert ID from the alert parameter file
        self.alert_groups = dict()  # Alert ID and alert transaction subgraph
        # TODO: Move the mapping of AML pattern to configuration JSON file
        self.alert_types = {"fan_out": 1, "fan_in": 2, "cycle": 3, "bipartite": 4, "stack": 5,
                            "random": 6, "scatter_gather": 7, "gather_scatter": 8}  # Pattern name and model ID

        self.acct_file = os.path.join(self.input_dir, self.account_file)

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

    def check_hub_exists(self):
        """Validate whether one or more hub accounts exist as main accounts of AML typologies
        """
        if not self.hubs:
            raise ValueError("No main account candidates found. "
                             "Please try again with smaller value of the 'degree_threshold' parameter in conf.json.")

    def set_main_acct_candidates(self):
        """ Set self.hubs to be a set of hub nodes
            Throw an error if not done successfully.
        """
        hub_list = self.hub_nodes()
        self.hubs = set(hub_list)
        self.check_hub_exists()


    def hub_nodes(self):
        """Choose hub accounts with larger degree than the specified threshold
        as the main account candidates of alert transaction sets
        """
        nodes = [n for n in self.g.nodes()  # Hub vertices (with large in/out degrees)
                 if self.degree_threshold <= self.g.in_degree(n)
                 or self.degree_threshold <= self.g.out_degree(n)]
        return nodes


    def check_account_exist(self, aid):
        """Validate an existence of a specified account. If absent, it raises KeyError.
        :param aid: Account ID
        """
        if not self.g.has_node(aid):
            raise KeyError("Account %s does not exist" % str(aid))

    def check_account_absent(self, aid):
        """Validate an absence of a specified account
        :param aid: Account ID
        :return: True if an account of the specified ID is not yet added
        """
        if self.g.has_node(aid):
            logger.warning("Account %s already exists" % str(aid))
            return False
        else:
            return True

    def get_all_bank_ids(self):
        """Get a list of all bank IDs
        :return: Bank ID list
        """
        return list(self.bank_to_accts.keys())

    def get_typology_members(self, num, bank_id=""):
        """Choose accounts randomly as members of AML typologies from one or multiple banks.
        :param num: Number of total account vertices (including the main account)
        :param bank_id: If specified, it chooses members from a single bank with the ID.
        If empty (default), it chooses members from all banks randomly.
        :return: Main account and list of member account IDs
        """
        if num <= 1:
            raise ValueError("The number of members must be more than 1")

        if bank_id in self.bank_to_accts:  # Choose members from the same bank as the main account
            bank_accts = self.bank_to_accts[bank_id]
            main_candidates = self.hubs & bank_accts
            main_acct = random.sample(main_candidates, 1)[0]
            self.remove_typology_candidate(main_acct)
            sub_accts = random.sample(bank_accts, num - 1)
            for n in sub_accts:
                self.remove_typology_candidate(n)

            members = [main_acct] + sub_accts
            return main_acct, members

        elif bank_id == "":  # Choose members from all accounts
            self.check_hub_exists()
            main_acct = random.sample(self.hubs, 1)[0]
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
        if self.is_aggregated:
            self.load_account_list_param()
        else:
            self.load_account_list_raw()

    def load_account_list_raw(self):
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

        with open(self.acct_file, "r") as rf:
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

                if start_day is not None and start_range is not None:
                    start = start_day + random.randrange(start_range)
                else:
                    start = -1

                if end_day is not None and end_range is not None:
                    end = end_day - random.randrange(end_range)
                else:
                    end = -1

                attr = {"first_name": first_name, "last_name": last_name, "street_addr": street_addr,
                        "city": city, "state": state, "zip": zip_code, "gender": gender,
                        "phone_number": phone_number, "birth_date": birth_date, "ssn": ssn, "lon": lon, "lat": lat}

                init_balance = random.uniform(min_balance, max_balance)  # Generate the initial balance
                self.add_account(aid, init_balance=init_balance, country=default_country, business=default_acct_type, is_sar=False, **attr)
                count += 1

    def set_num_accounts(self):
        with open(self.acct_file, "r") as rf:
            reader = csv.reader(rf)
            # Parse header
            header = next(reader)

            count = 0
            for row in reader:
                if row[0].startswith("#"):
                    continue
                num = int(row[header.index('count')])
                count += num

        self.num_accounts = count


    def load_account_list_param(self):

        """Load and add account vertices from a CSV file with aggregated parameters
        Each row may represent two or more accounts
        :param acct_file: Account parameter file path
        """

        with open(self.acct_file, "r") as rf:
            reader = csv.reader(rf)
            # Parse header
            header = next(reader)

            acct_id = 0
            for row in reader:
                if row[0].startswith("#"):
                    continue
                num = int(row[header.index('count')])
                min_balance = parse_float(row[header.index('min_balance')])
                max_balance = parse_float(row[header.index('max_balance')])
                country = row[header.index('country')]
                business = row[header.index('business_type')]
                bank_id = row[header.index('bank_id')] 
                if bank_id is None:
                    bank_id = self.default_bank_id

                for i in range(num):
                    init_balance = random.uniform(min_balance, max_balance)  # Generate amount
                    self.add_account(acct_id, init_balance=init_balance, country=country, business=business, bank_id=bank_id, is_sar=False, normal_models=list())
                    acct_id += 1

        logger.info("Generated %d accounts." % self.num_accounts)

    def generate_normal_transactions(self):
        """Generate a base directed graph from degree sequences
        TODO: Add options to call scale-free generator functions directly instead of loading degree CSV files
        :return: Directed graph as the base transaction graph (not complete transaction graph)
        """
        deg_file = os.path.join(self.input_dir, self.degree_file)
        in_deg, out_deg = get_degrees(deg_file, self.num_accounts)
        G = directed_configuration_model(in_deg, out_deg, self.seed)
        G = nx.DiGraph(G)
        self.g = G

        logger.info("Add %d base transactions" % self.g.number_of_edges())
        nodes = self.g.nodes()
        for src_i, dst_i in self.g.edges():
            src = nodes[src_i]
            dst = nodes[dst_i]
            self.add_edge_info(src, dst)  # Add edge info.

    def add_account(self, acct_id, **attr):
        """Add an account vertex
        :param acct_id: Account ID
        :param init_balance: Initial amount
        :param start: The day when the account opened
        :param end: The day when the account closed
        :param country: Country name
        :param business: Business type
        :param bank_id: Bank ID
        :param attr: Optional attributes-
        :return:
        """
        
        if attr['bank_id'] is None:
            attr['bank_id'] = self.default_bank_id

        self.g.node[acct_id] = attr

        self.bank_to_accts[attr['bank_id']].add(acct_id)
        self.acct_to_bank[acct_id] = attr['bank_id']


    def remove_typology_candidate(self, acct):
        """Remove an account vertex from AML typology member candidates
        :param acct: Account ID
        """
        self.hubs.discard(acct)
        bank_id = self.acct_to_bank[acct]
        del self.acct_to_bank[acct]
        self.bank_to_accts[bank_id].discard(acct)

    def add_edge_info(self, orig, bene):
        """Adds info to edge. Based on add_transaction.
        Add transaction will go away eventually.
        :param orig: Originator account ID
        :param bene: Beneficiary account ID
        :return:
        """
        self.check_account_exist(orig)  # Ensure the originator and beneficiary accounts exist
        self.check_account_exist(bene)
        if orig == bene:
            raise ValueError("Self loop from/to %s is not allowed for transaction networks" % str(orig))
        self.g.edge[orig][bene]['edge_id'] = self.edge_id
        self.edge_id += 1

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
            self.g.add_edge(src, dst)
            self.add_edge_info(src, dst)

    def load_edgelist(self, members, csv_name):
        """Load edgelist and add edges with existing account vertices
        :param members: Account vertex list
        :param csv_name: Edgelist file name
        :return:
        """
        topology = nx.DiGraph()
        topology = nx.read_edgelist(csv_name, delimiter=",", create_using=topology)
        self.add_subgraph(members, topology)


    def mark_active_edges(self):
        nx.set_edge_attributes(self.g, 'active', False)
        for normal_model in self.normal_models:
            subgraph = self.g.subgraph(normal_model.node_ids)
            nx.set_edge_attributes(subgraph, 'active', True)


    def load_normal_models(self):
        """Load a Normal Model parameter file
        """
        normal_models_file = os.path.join(self.input_dir, self.normal_models_file)
        with open(normal_models_file, "r") as csvfile:
            reader = csv.reader(csvfile)
            self.read_normal_models(reader)


    def read_normal_models(self, reader):
        """Parse the Normal Model parameter file
        """
        header = next(reader)

        self.nominator = Nominator(self.g, self.degree_threshold)

        for row in reader:
            count = int(row[header.index('count')])
            type = row[header.index('type')]
            schedule_id = int(row[header.index('schedule_id')])
            min_accounts = int(row[header.index('min_accounts')])
            max_accounts = int(row[header.index('max_accounts')])
            min_period = int(row[header.index('min_period')])
            max_period = int(row[header.index('max_period')])
            bank_id = row[header.index('bank_id')]
            if bank_id is None:
                bank_id = self.default_bank_id

            self.nominator.initialize_count(type, count)


    def build_normal_models(self):
        while(self.nominator.has_more()):
            for type in self.nominator.types():
                count = self.nominator.count(type)
                if count > 0:
                    self.choose_normal_model(type)
                    self.normal_model_id += 1
        logger.info("Generated %d normal models." % len(self.normal_models))
        logger.info("Normal model counts %s", self.nominator.used_count_dict)
        

    def choose_normal_model(self, type):
        if type == 'fan_in':
            self.fan_in_model(type)
        elif type == 'fan_out':
            self.fan_out_model(type)
        elif type == 'forward':
            self.forward_model(type)
        elif type == 'single':
            self.single_model(type)
        elif type == 'mutual':
            self.mutual_model(type)
        elif type == 'periodical':
            self.periodical_model(type)

        
    def fan_in_model(self, type):     
        node_id = self.nominator.next(type)

        if node_id is None:
            return

        candidates = self.nominator.fan_in_breakdown(type, node_id)

        if not candidates:
            raise ValueError('should always be candidates')

        normal_models = self.nominator.normal_models_in_type_relationship(type, node_id, {node_id})
        for nm in normal_models:
            nm.remove_node_ids(candidates)
            
        result_ids = candidates | { node_id }
        normal_model = NormalModel(self.normal_model_id, type, result_ids, node_id)

        for result_id in result_ids:
            self.g.node[result_id]['normal_models'].append(normal_model)

        self.normal_models.append(normal_model)
        
        self.nominator.post_fan_in(node_id, type)


    def fan_out_model(self, type):
        node_id = self.nominator.next(type)

        if node_id is None:
            return

        candidates = self.nominator.fan_out_breakdown(type, node_id)

        if not candidates:
            raise ValueError('should always be candidates')

        normal_models = self.nominator.normal_models_in_type_relationship(type, node_id, {node_id})
        for nm in normal_models:
            nm.remove_node_ids(candidates)

        result_ids = candidates | { node_id }
        normal_model = NormalModel(self.normal_model_id, type, result_ids, node_id)
        for id in result_ids:
            self.g.node[id]['normal_models'].append(normal_model)

        self.normal_models.append(normal_model)

        self.nominator.post_fan_out(node_id, type)
    

    def forward_model(self, type):
        node_id = self.nominator.next(type)

        if node_id is None:
            return

        succ_ids = self.g.successors(node_id)
        pred_ids = self.g.predecessors(node_id)

        sets = [{node_id, pred_id, succ_id} for pred_id in pred_ids for succ_id in succ_ids]

        set = next(
            set for set in sets if not self.nominator.is_in_type_relationship(type, node_id, set)
        )
        normal_model = NormalModel(self.normal_model_id, type, list(set), node_id)
        for id in set:
            self.g.node[id]['normal_models'].append(normal_model)

        self.normal_models.append(normal_model)

        self.nominator.post_forward(node_id, type)
                

    def single_model(self, type):
        node_id = self.nominator.next(type)

        if node_id is None:
            return
        
        succ_ids = self.g.successors(node_id)
        succ_id = next(succ_id for succ_id in succ_ids if not self.nominator.is_in_type_relationship(type, node_id, {node_id, succ_id}))

        result_ids = { node_id, succ_id }
        normal_model = NormalModel(self.normal_model_id, type, result_ids, node_id)
        for id in result_ids:
            self.g.node[id]['normal_models'].append(normal_model)

        self.normal_models.append(normal_model)

        self.nominator.post_single(node_id, type)

    
    def periodical_model(self, type):
        node_id = self.nominator.next(type)

        if node_id is None:
            return
        
        succ_ids = self.g.successors(node_id)
        succ_id = next(succ_id for succ_id in succ_ids if not self.nominator.is_in_type_relationship(type, node_id, {node_id, succ_id}))

        result_ids = { node_id, succ_id }
        normal_model = NormalModel(self.normal_model_id, type, result_ids, node_id)
        for id in result_ids:
            self.g.node[id]['normal_models'].append(normal_model)

        self.normal_models.append(normal_model)

        self.nominator.post_periodical(node_id, type)

    
    def mutual_model(self, type):
        node_id = self.nominator.next(type)

        if node_id is None:
            return
        
        succ_ids = self.g.successors(node_id)
        succ_id = next(succ_id for succ_id in succ_ids if not self.nominator.is_in_type_relationship(type, node_id, {node_id, succ_id}))

        result_ids = { node_id, succ_id }
        normal_model = NormalModel(self.normal_model_id, type, result_ids, node_id)
        for id in result_ids:
            self.g.node[id]['normal_models'].append(normal_model)

        self.normal_models.append(normal_model)

        self.nominator.post_mutual(node_id, type)
        

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
                elif k == "type":  # AML typology type (e.g. fan-out and cycle)
                    idx_type = i
                elif k == "schedule_id":  # Transaction scheduling type
                    idx_schedule = i
                elif k == "min_accounts":  # Minimum number of involved accounts
                    idx_min_accts = i
                elif k == "max_accounts":  # Maximum number of involved accounts
                    idx_max_accts = i
                elif k == "min_amount":  # Minimum initial transaction amount
                    idx_min_amt = i
                elif k == "max_amount":  # Maximum initial transaction amount
                    idx_max_amt = i
                elif k == "min_period":  # Minimum overall transaction period (number of simulation steps)
                    idx_min_period = i
                elif k == "max_period":  # Maximum overall transaction period (number of simulation steps)
                    idx_max_period = i
                elif k == "bank_id":  # Bank ID for internal-bank transactions
                    idx_bank = i
                elif k == "is_sar":  # SAR flag
                    idx_sar = i
                else:
                    logger.warning("Unknown column name in %s: %s" % (alert_file, k))

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
                bank_id = row[idx_bank] if idx_bank is not None else ""  # If empty, it has inter-bank transactions
                is_sar = parse_flag(row[idx_sar])

                if typology_name not in self.alert_types:
                    logger.warning("Pattern type name (%s) must be one of %s"
                                   % (typology_name, str(self.alert_types.keys())))
                    continue

                for i in range(num_patterns):
                    num_accts = random.randrange(min_accts, max_accts + 1)
                    period = random.randrange(min_period, max_period + 1)
                    self.add_aml_typology(is_sar, typology_name, num_accts, min_amount, max_amount, period, bank_id, schedule)
                    count += 1
                    if count % 1000 == 0:
                        logger.info("Created %d alerts" % count)

    def add_aml_typology(self, is_sar, typology_name, num_accounts, min_amount, max_amount, period, bank_id="", schedule=1):
        """Add an AML typology transaction set
        :param is_sar: Whether the alerted transaction set is SAR (True) or false-alert (False)
        :param typology_name: Name of pattern type
            ("fan_in", "fan_out", "cycle", "random", "stack", "scatter_gather" or "gather_scatter")
        :param num_accounts: Number of transaction members (accounts)
        :param min_amount: Minimum amount of the transaction
        :param max_amount: Maximum amount of the transaction
        :param period: Period (number of days) for all transactions
        :param bank_id: Bank ID which it chooses members from. If empty, it chooses members from all banks.
        :param schedule: AML pattern transaction schedule model ID
        """

        def add_node(_acct, _bank_id):
            """Set an attribute of bank ID to a member account
            :param _acct: Account ID
            :param _bank_id: Bank ID
            """
            attr_dict = self.g.node[_acct]
            attr_dict[IS_SAR_KEY] = True

            sub_g.add_node(_acct, attr_dict)


        def add_main_acct():
            """Create a main account ID and a bank ID from hub accounts
            :return: main account ID and bank ID
            """
            self.check_hub_exists()
            _main_acct = random.sample(self.hubs, 1)[0]
            _main_bank_id = self.acct_to_bank[_main_acct]
            self.remove_typology_candidate(_main_acct)
            add_node(_main_acct, _main_bank_id)
            return _main_acct, _main_bank_id

        def add_edge(_orig, _bene, _amount, _date):
            """Add transaction edge to the AML typology subgraph as well as the whole transaction graph
            :param _orig: Originator account ID
            :param _bene: Beneficiary account ID
            :param _amount: Transaction amount
            :param _date: Transaction timestamp
            """
            sub_g.add_edge(_orig, _bene, amount=_amount, date=_date)
            self.g.add_edge(_orig, _bene)
            self.add_edge_info(_orig, _bene)


        if bank_id == "" and len(self.bank_to_accts) >= 2:
            is_external = True
        elif bank_id != "" and bank_id not in self.bank_to_accts:  # Invalid bank ID
            raise KeyError("No such bank ID: %s" % bank_id)
        else:
            is_external = False

        start_date = random.randrange(0, self.total_steps - period + 1)
        end_date = start_date + period - 1 # end_date is inclusive

        # Create subgraph structure with transaction attributes
        model_id = self.alert_types[typology_name]  # alert model ID
        sub_g = nx.DiGraph(model_id=model_id, reason=typology_name, scheduleID=schedule,
                           start=start_date, end=end_date)  # Transaction subgraph for a typology


        if typology_name == "fan_in":  # fan_in pattern (multiple accounts --> single (main) account)
            main_acct, main_bank_id = add_main_acct()
            num_neighbors = num_accounts - 1
            amount = RoundedAmount(min_amount, max_amount).getAmount()

            if is_external:
                sub_bank_candidates = [b for b, nbs in self.bank_to_accts.items()
                                       if b != main_bank_id and len(nbs) >= num_neighbors]
                if not sub_bank_candidates:
                    logger.warning("No banks with appropriate number of neighboring accounts found.")
                    return
                sub_bank_id = random.choice(sub_bank_candidates)
            else:
                sub_bank_id = main_bank_id
            sub_accts = random.sample(self.bank_to_accts[sub_bank_id], num_neighbors)
            for n in sub_accts:
                self.remove_typology_candidate(n)
                add_node(n, sub_bank_id)

            for orig in sub_accts:
                date = random.randrange(start_date, end_date + 1)
                add_edge(orig, main_acct, amount, date)

        elif typology_name == "fan_out":  # fan_out pattern (single (main) account --> multiple accounts)
            main_acct, main_bank_id = add_main_acct()
            num_neighbors = num_accounts - 1
            amount = RoundedAmount(min_amount, max_amount).getAmount()

            if is_external:
                sub_bank_candidates = [b for b, nbs in self.bank_to_accts.items()
                                       if b != main_bank_id and len(nbs) >= num_neighbors]
                if not sub_bank_candidates:
                    logger.warning("No banks with appropriate number of neighboring accounts found.")
                    return
                sub_bank_id = random.choice(sub_bank_candidates)
            else:
                sub_bank_id = main_bank_id
            sub_accts = random.sample(self.bank_to_accts[sub_bank_id], num_neighbors)
            for n in sub_accts:
                self.remove_typology_candidate(n)
                add_node(n, sub_bank_id)

            for bene in sub_accts:
                date = random.randrange(start_date, end_date + 1)
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
                amount = RandomAmount(min_amount, max_amount).getAmount()
                date = random.randrange(start_date, end_date + 1)
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
                amount = RandomAmount(min_amount, max_amount).getAmount()
                date = random.randrange(start_date, end_date + 1)
                add_edge(orig, bene, amount, date)

            for orig, bene in itertools.product(mid_accts, bene_accts):  # all-to-all transactions
                amount = RandomAmount(min_amount, max_amount).getAmount()
                date = random.randrange(start_date, end_date + 1)
                add_edge(orig, bene, amount, date)

        elif typology_name == "random":  # Random transactions among members
            amount = RandomAmount(min_amount, max_amount).getAmount()
            date = random.randrange(start_date, end_date + 1)

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
                main_acct, main_bank_id = add_main_acct()
                sub_accts = random.sample(self.bank_to_accts[main_bank_id], num_accounts - 1)
                for n in sub_accts:
                    self.remove_typology_candidate(n)
                    add_node(n, main_bank_id)
                prev_acct = main_acct
                for _ in range(num_accounts - 1):
                    next_acct = random.choice([n for n in sub_accts if n != prev_acct])
                    add_edge(prev_acct, next_acct, amount, date)
                    prev_acct = next_acct

        elif typology_name == "cycle":  # Cycle transactions
            amount = RandomAmount(min_amount, max_amount).getAmount()
            dates = sorted([random.randrange(start_date, end_date + 1) for _ in range(num_accounts)])

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
                main_acct, main_bank_id = add_main_acct()
                sub_accts = random.sample(self.bank_to_accts[main_bank_id], num_accounts - 1)
                for n in sub_accts:
                    self.remove_typology_candidate(n)
                    add_node(n, main_bank_id)
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
                scatter_amount = RandomAmount(min_amount, max_amount).getAmount()
                margin = scatter_amount * self.margin_ratio  # Margin of the intermediate account
                amount = scatter_amount - margin
                scatter_date = random.randrange(start_date, mid_date)
                gather_date = random.randrange(mid_date, end_date + 1)

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
            amount = RandomAmount(min_amount, max_amount).getAmount()

            for i in range(num_orig_accts):
                orig_acct = orig_accts[i]
                date = random.randrange(start_date, mid_date)
                add_edge(orig_acct, mid_acct, amount, date)
                accumulated_amount += amount
                # print(orig_acct, "->", date, "->", mid_acct)

            for i in range(num_bene_accts):
                bene_acct = bene_accts[i]
                date = random.randrange(mid_date, end_date + 1)
                add_edge(mid_acct, bene_acct, amount, date)
                # print(mid_acct, "->", date, "->", bene_acct)
            # print(orig_accts, mid_acct, bene_accts)

        # TODO: Please add user-defined typology implementations here

        else:
            logger.warning("Unknown AML typology name: %s" % typology_name)
            return

        # Add the generated transaction edges to whole transaction graph
        sub_g.graph[MAIN_ACCT_KEY] = main_acct  # Main account ID
        sub_g.graph[IS_SAR_KEY] = is_sar  # SAR flag
        self.alert_groups[self.alert_id] = sub_g
        self.alert_id += 1

    def write_account_list(self):
        os.makedirs(self.output_dir, exist_ok=True)
        acct_file = os.path.join(self.output_dir, self.out_account_file)
        with open(acct_file, "w") as wf:
            writer = csv.writer(wf)
            base_attrs = ["ACCOUNT_ID", "CUSTOMER_ID", "INIT_BALANCE", "COUNTRY",
                          "ACCOUNT_TYPE", "IS_SAR", "BANK_ID"]
            writer.writerow(base_attrs + self.attr_names)
            for n in self.g.nodes(data=True):
                aid = n[0]  # Account ID
                cid = "C_" + str(aid)  # Customer ID bounded to this account
                prop = n[1]  # Account attributes
                balance = "{0:.2f}".format(prop["init_balance"])  # Initial balance
                country = prop["country"]  # Country
                business = prop["business"]  # Business type
                is_sar = "true" if prop[IS_SAR_KEY] else "false"  # Whether this account is involved in SAR
                bank_id = prop["bank_id"]  # Bank ID
                values = [aid, cid, balance, country, business, is_sar, bank_id]
                for attr_name in self.attr_names:
                    values.append(prop[attr_name])
                writer.writerow(values)
        logger.info("Exported %d accounts to %s" % (self.g.number_of_nodes(), acct_file))

    def write_transaction_list(self):
        tx_file = os.path.join(self.output_dir, self.out_tx_file)
        with open(tx_file, "w") as wf:
            writer = csv.writer(wf)
            writer.writerow(["id", "src", "dst", "ttype"])
            for e in self.g.edges(data=True):
                src = e[0]
                dst = e[1]
                attr = e[2]
                tid = attr['edge_id']
                tx_type = random.choice(self.tx_types)
                if attr['active']:
                    writer.writerow([tid, src, dst, tx_type])
        logger.info("Exported %d transactions to %s" % (self.g.number_of_edges(), tx_file))

    def write_alert_account_list(self):
        def get_out_edge_attrs(g, vid, name):
            return [v for k, v in nx.get_edge_attributes(g, name).items() if (k[0] == vid or k[1] == vid)]

        acct_count = 0
        alert_member_file = os.path.join(self.output_dir, self.out_alert_member_file)
        logger.info("Output alert member list to: " + alert_member_file)
        with open(alert_member_file, "w") as wf:
            writer = csv.writer(wf)
            base_attrs = ["alertID", "reason", "accountID", "isMain", "isSAR", "modelID",
                          "minAmount", "maxAmount", "startStep", "endStep", "scheduleID", "bankID"]
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

        logger.info("Exported %d members for %d AML typologies to %s" %
                    (acct_count, len(self.alert_groups), alert_member_file))

    def write_normal_models(self):
        output_file = os.path.join(self.output_dir, self.out_normal_models_file)
        with open(output_file, "w") as wf:
            writer = csv.writer(wf)
            column_headers = ["modelID", "type", "accountID", "isMain", "isSAR", "scheduleID"]
            writer.writerow(column_headers)
            
            for normal_model in self.normal_models:
                for account_id in normal_model.node_ids:
                    values = [normal_model.id, normal_model.type, account_id, normal_model.is_main(account_id), False, 2]
                    writer.writerow(values)


    def count__patterns(self, threshold=2):
        """Count the number of fan-in and fan-out patterns in the generated transaction graph
        """
        in_deg = Counter(self.g.in_degree().values())  # in-degree, count
        out_deg = Counter(self.g.out_degree().values())  # out-degree, count
        for th in range(2, threshold + 1):
            num_fan_in = sum([c for d, c in in_deg.items() if d >= th])
            num_fan_out = sum([c for d, c in out_deg.items() if d >= th])
            logger.info("\tNumber of fan-in / fan-out patterns with %d neighbors: %d / %d"
                        % (th, num_fan_in, num_fan_out))

        main_in_deg = Counter()
        main_out_deg = Counter()
        for sub_g in self.alert_groups.values():
            main_acct = sub_g.graph[MAIN_ACCT_KEY]
            main_in_deg[self.g.in_degree(main_acct)] += 1
            main_out_deg[self.g.out_degree(main_acct)] += 1
        for th in range(2, threshold + 1):
            num_fan_in = sum([c for d, c in main_in_deg.items() if d >= threshold])
            num_fan_out = sum([c for d, c in main_out_deg.items() if d >= threshold])
            logger.info("\tNumber of alerted fan-in / fan-out patterns with %d neighbors: %d / %d"
                        % (th, num_fan_in, num_fan_out))


if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)
    if argc < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    _conf_file = argv[1]
    _sim_name = argv[2] if argc >= 3 else None



    # Validation option for graph contractions
    deg_param = os.getenv("DEGREE")
    degree_threshold = 0 if deg_param is None else int(deg_param)

    with open(_conf_file, "r") as rf:
        conf = json.load(rf)

    txg = TransactionGenerator(conf, _sim_name)
    txg.set_num_accounts()
    txg.generate_normal_transactions()  # Load a parameter CSV file for the base transaction types
    txg.load_account_list()  # Load account list CSV file
    if degree_threshold > 0:
        logger.info("Generated normal transaction network")
        txg.count_fan_in_out_patterns(degree_threshold)
    txg.load_normal_models() # Load a parameter CSV file for Normal Models
    #cProfile.run('txg.build_normal_models()')
    txg.build_normal_models()
    txg.set_main_acct_candidates()
    txg.load_alert_patterns()  # Load a parameter CSV file for AML typology subgraphs
    txg.mark_active_edges()

    if degree_threshold > 0:
        logger.info("Added alert transaction patterns")
        txg.count_fan_in_out_patterns(degree_threshold)
    txg.write_account_list()  # Export accounts to a CSV file
    txg.write_transaction_list()  # Export transactions to a CSV file
    txg.write_alert_account_list()  # Export alert accounts to a CSV file
    txg.write_normal_models()
