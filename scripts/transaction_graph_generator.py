from configparser import ConfigParser
import networkx as nx
import numpy as np
import itertools
import random
import csv
import os
import sys


#### Utility functions parsing values
def parse_int(value):
  """ Convert string to int
  :param value: string value
  :return: int value if the parameter can be converted to str, otherwise None
  """
  try:
    return int(value)
  except ValueError:
    return None


def parse_amount(value):
  """ Convert string to amount (float)
  :param value: string value
  :return: float value if the parameter can be converted to float, otherwise None
  """
  try:
    return float(value)
  except ValueError:
    return None


def parse_flag(value):
  """ Convert string to boolean (True or false)
  :param value: string value
  :return: True if the value is equal to "true" (case insensitive), otherwise False
  """
  return value.lower() == "true"



class TransactionGenerator:

  def __init__(self, confFile, ttypeCSV):
    """Initialize transaction network.
    
    :param confFile: Configuration (ini) file name
    :param ttypeCSV: Transaction type distribution CSV file
    """
    self.g = nx.MultiDiGraph()  # Transaction graph object
    self.num_accounts = 0  # Number of total accounts
    self.degrees = dict()  # Degree distribution
    self.hubs = list()  # Hub vertices
    self.subject_candidates = set()

    self.conf = ConfigParser()
    self.conf.read(confFile)
    self.seed = int(self.conf.get("General", "seed"))
    np.random.seed(self.seed)
    random.seed(self.seed)

    self.degree_threshold = int(self.conf.get("Base", "degree_threshold"))
    # self.prob = float(self.conf.get("Base", "triangle_prob"))

    self.default_max_amount = parse_amount(self.conf.get("General", "default_max_amount"))
    self.default_min_amount = parse_amount(self.conf.get("General", "default_min_amount"))
    self.total_step = parse_int(self.conf.get("General", "total_step"))

    self.input_dir = self.conf.get("InputFile", "directory")
    self.output_dir = self.conf.get("OutputFile", "directory")

    highrisk_countries_str = self.conf.get("HighRisk", "countries")
    highrisk_business_str = self.conf.get("HighRisk", "business")
    self.highrisk_countries = set(highrisk_countries_str.split(","))
    self.highrisk_business = set(highrisk_business_str.split(","))

    self.tx_id = 0  # Transaction ID
    self.alert_id = 0  # Alert ID from the alert parameter file
    self.alert_groups = dict()  # Alert ID and alert transaction subgraph
    self.alert_types = {"fan_out":1, "fan_in":2, "cycle":3, "bipartite":4, "stack":5, "dense":6}  # Pattern name and model ID


    def get_types(type_csv):
      ttypes = list()
      with open(type_csv, "r") as rf:
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
          ttype = row[0]
          ttypes.extend([ttype] * int(row[1]))
      return ttypes

    self.tx_types = get_types(ttypeCSV)




  def set_subject_candidates(self):
    """Choose fraud subject candidates
    Currently, it chooses hub accounts with large degree
    TODO: More options how to choose fraud accounts
    """
    self.degrees = self.g.degree(self.g.nodes())
    self.hubs = [n for n in self.g.nodes() if self.degree_threshold <= self.degrees[n]]
    self.subject_candidates = set(self.g.nodes())

  #### Highrisk country and business
  def is_highrisk_country(self, country):
    return country in self.highrisk_countries

  def is_highrisk_business(self, business):
    return business in self.highrisk_business


  #### Account existence check
  def check_account_exist(self, aid):
    if not self.g.has_node(aid):
      raise KeyError("Account %s does not exist" % str(aid))

  def check_account_absent(self, aid):
    if self.g.has_node(aid):
      print("Warning: account %s already exists" % str(aid))
      return False
    else:
      return True

  def get_alert_members(self, num, hasSubject):
    """Get account vertices randomly (high-degree vertices are likely selected)

    :param num: Number of total account vertices
    :param hasSubject: Whether it has a subject account
    :return: Account ID list
    """
    found = False
    subject = None
    members = list()

    while not found:
      candidates = set()
      while len(candidates) < num:  # Get sufficient alert members
        hub = random.choice(self.hubs)
        candidates.update([hub]+self.g.adj[hub].keys())
      members = np.random.choice(list(candidates), num, False)
      candidates_set = set(members) & self.subject_candidates
      if not candidates_set:
        continue
      subject = random.choice(list(candidates_set))  # Choose the subject accounts from members randomly
      found = True
      if hasSubject:
        self.subject_candidates.remove(subject)
    return subject, members



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


  #### Load and add account vertices from CSV file
  def load_account_list(self):
    fname = os.path.join(self.input_dir, self.conf.get("InputFile", "account_list"))

    idx_num = None
    idx_min = None
    idx_max = None
    idx_start = None
    idx_end = None
    idx_country = None
    idx_business = None
    idx_suspicious = None
    idx_model = None

    with open(fname, "r") as rf:
      reader = csv.reader(rf)

      ## Parse header
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
        elif k == "suspicious":
          idx_suspicious = i
        elif k == "model":
          idx_model = i
        else:
          print("Warning: unknown key: %s" % k)

      aid = 0
      for row in reader:
        num = int(row[idx_num])
        min_balance = parse_amount(row[idx_min])
        max_balance = parse_amount(row[idx_max])
        start_day = parse_int(row[idx_start])
        end_day = parse_int(row[idx_end])
        country = row[idx_country]
        business = row[idx_business]
        suspicious = parse_flag(row[idx_suspicious])
        modelID = parse_int(row[idx_model])

        for i in range(num):
          init_balance = random.uniform(min_balance, max_balance)  # Generate amount
          self.add_account(aid, init_balance, start_day, end_day, country, business, suspicious, modelID)
          aid += 1

    self.num_accounts = aid
    print("Created %d accounts." % self.num_accounts)


  #### Generate base transactions from same degree sequences of transaction CSV
  def generate_normal_transactions(self, degcsv):

    def get_degrees(deg_csv, num_v):
      """

      :param deg_csv: Degree distribution parameter CSV file
      :param num_v: Number of total account vertices
      :return: In-degree and out-degree sequence list
      """
      # print num_v
      in_deg = list()  # In-degree sequence
      out_deg = list()  # Out-degree sequence
      with open(deg_csv, "r") as rf:  # Load in/out-degree sequences from parameter CSV file for each account
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
          nv = int(row[0])
          in_deg.extend(int(row[1]) * [nv])
          out_deg.extend(int(row[2]) * [nv])

      print len(in_deg), len(out_deg)
      assert len(in_deg) == len(out_deg), "In/Out-degree Sequences must have equal length."
      total_v = len(in_deg)
      # print total_v
      # print total_v, num_v
      if total_v > num_v:  # If the number of total accounts from degree sequences is larger than specified, shrink degree sequence
        diff = total_v - num_v  # The number of extra accounts to be removed
        in_tmp = list()
        out_tmp = list()
        for i in range(total_v):
          num_in = in_deg[i]
          num_out = out_deg[i]
          if num_in == num_out and diff > 0:  # Remove element from in/out-degree sequences with the same number
            diff -= 1
          else:
            in_tmp.append(num_in)
            out_tmp.append(num_out)
        in_deg = in_tmp
        out_deg = out_tmp
      else:  # If the number of total accounts from degree sequences is smaller than specified, extend degree sequence
        repeats = num_v / total_v  # Number of repetitions of degree sequences
        print len(in_deg), len(out_deg), repeats
        in_deg = in_deg * repeats
        out_deg = out_deg * repeats
        print len(in_deg)
        remain = num_v - total_v * repeats  # Number of extra accounts
        in_deg.extend([1] * remain)  # Add 1-degree account vertices
        out_deg.extend([1] * remain)

      assert sum(in_deg) == sum(out_deg), "Sequences must have equal sums."
      return in_deg, out_deg


    in_deg, out_deg = get_degrees(degcsv, self.num_accounts)
    print sum(in_deg), sum(out_deg)
    g = nx.generators.degree_seq.directed_configuration_model(in_deg, out_deg, seed=0)  # Generate a directed graph from degree sequences (not transaction graph)

    print("Add %d base transactions" % g.number_of_edges())
    for src, dst in g.edges():
      self.add_transaction(src, dst)  # Add edges to transaction graph



  def add_account(self, aid, init_balance, start, end, country, business, suspicious, modelID):
    """Add an account vertex
    :param aid: Account ID
    :param init_balance: Initial amount
    :param start: The day when the account opened
    :param end: The day when the account closed
    :param country: Country
    :param business: business type
    :param suspicious: Whether the account is suspicious
    :param modelID: Remittance model ID
    :return:
    """
    if self.check_account_absent(aid):  # Add an account vertex with an ID and attributes if an account with the same ID is not yet added
      self.g.add_node(aid, init_balance=init_balance, start=start, end=end, country=country, business=business, suspicious=suspicious, isFraud=False, modelID=modelID)


  def add_transaction(self, src, dst, amount=None, date=None, ttype=None):
    """Add a transaction edge
    :param src: Source account ID
    :param dst: Destination account ID
    :param amount: Transaction amount
    :param date: Transaction date
    :param ttype: Transaction type description
    :return:
    """
    self.check_account_exist(src)  # Ensure the source and destination account exist
    self.check_account_exist(dst)
    self.g.add_edge(src, dst, key=self.tx_id, amount=amount, date=date, ttype=ttype)
    self.tx_id += 1
    if self.tx_id % 1000000 == 0:
      print("Added %d transactions" % self.tx_id)


  #### Load Custom Topology Files

  def add_subgraph(self, members, topology):
    """Add subgraph from exisiting account vertices and given graph topology

    :param members: Account vertex list
    :param topology: Topology graph
    :return:
    """
    if len(members) != topology.number_of_nodes():
      raise nx.NetworkXError("The number of account vertices does not match")

    nodemap = dict(zip(members, topology.nodes()))
    for e in topology.edges():
      src = nodemap[e[0]]
      dst = nodemap[e[1]]
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



  def load_alert_patterns(self, alert_file=None):
    """Load an alert (fraud) parameter CSV file
    :return:
    """
    if alert_file:
      csv_name = alert_file
    else:
      csv_name = os.path.join(self.input_dir, self.conf.get("InputFile", "alertPattern"))

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
    idx_fraud = None

    with open(csv_name, "r") as rf:
      reader = csv.reader(rf)

      ## Parse header
      header = next(reader)
      for i, k in enumerate(header):
        if k == "count":
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
        elif k == "is_fraud":
          idx_fraud = i
        else:
          print("Warning: unknown key: %s" % k)

      ## Generate transaction set
      count = 0
      for row in reader:
        if "#" in row[0]:  ## Comment
          continue

        num = int(row[idx_num])
        pattern_type = row[idx_type]
        accounts = int(row[idx_accts])
        scheduleID = int(row[idx_schedule])
        individual_amount = parse_amount(row[idx_individual])
        aggregated_amount = parse_amount(row[idx_aggregated])
        transaction_count = parse_int(row[idx_count])
        amount_difference = parse_amount(row[idx_difference])
        period = parse_int(row[idx_period])
        amount_rounded = parse_amount(row[idx_rounded])
        orig_country = parse_flag(row[idx_orig_country])
        bene_country = parse_flag(row[idx_bene_country])
        orig_business = parse_flag(row[idx_orig_business])
        bene_business = parse_flag(row[idx_bene_business])
        is_fraud = parse_flag(row[idx_fraud])

        if not pattern_type in self.alert_types:
          print("Warning: pattern type (%s) must be one of %s" % (pattern_type, str(self.alert_types.keys())))
          continue

        if transaction_count is not None and transaction_count < accounts:
          print("Warning: number of transactions (%d) must not be smaller than the number of accounts (%d)" % (transaction_count, accounts))
          continue

        # members = self.get_account_vertices(accounts)
        for i in range(num):
          ## Add alert patterns
          self.add_alert_pattern(is_fraud, pattern_type, accounts, scheduleID, individual_amount, aggregated_amount, transaction_count,
                                 amount_difference, period, amount_rounded, orig_country, bene_country, orig_business, bene_business)
          count += 1
          if count % 1000 == 0:
            print "Write %d alerts" % count


  def add_alert_pattern(self, isFraud, pattern_type, accounts, scheduleID=1, individual_amount=None, aggregated_amount=None,
                        transaction_freq=None, amount_difference=None, period=None, amount_rounded=None,
                        orig_country=False, bene_country=False, orig_business=False, bene_business=False):
    """Add an AML rule transaction set

    :param isFraud: Whether the trasnsaction set is fraud or alert
    :param pattern_type: Pattern type ("fan_in", "fan_out", "dense", "mixed" or "stack")
    :param accounts: Number of transaction members (accounts)
    :param scheduleID: AML pattern transaction schedule model ID
    :param individual_amount: Minimum individual amount
    :param aggregated_amount: Minimum aggregated amount
    :param transaction_freq: Minimum transaction frequency
    :param amount_difference: Proportion of maximum transaction difference
    :param period: Lookback period (days)
    :param amount_rounded: Proportion of rounded amounts
    :param orig_country: Whether the originator country is suspicious
    :param bene_country: Whether the beneficiary country is suspicious
    :param orig_business: Whether the originator business type is suspicious
    :param bene_business: Whether the beneficiary business type is suspicious
    :return:
    """
    subject, members = self.get_alert_members(accounts, isFraud)

    ## Prepare parameters
    if individual_amount is None:
      min_amount = self.default_min_amount
      max_amount = self.default_max_amount
    else:
      min_amount = individual_amount
      max_amount = individual_amount * 2

    if aggregated_amount is None:
      aggregated_amount = 0

    start_day = random.randint(0, self.total_step)
    if period is None:
      end_day = start_day + self.total_step
    else:
      end_day = start_day + period


    ## Create subgraph structure with transaction attributes
    modelID = self.alert_types[pattern_type]  ## alert model ID
    sub_g = nx.MultiDiGraph(modelID=modelID, reason=pattern_type, scheduleID=scheduleID, start=start_day, end=end_day)  # Transaction subgraph for an alert
    num_members = len(members)  # Number of accounts
    total_amount = 0
    transaction_count = 0

    if pattern_type == "fan_in":  # fan_in pattern (multiple accounts --> single (subject) account)
      src_list = [n for n in members if n != subject]
      dst = subject

      if transaction_freq is None:
        transaction_freq = num_members - 1

      for src in itertools.cycle(src_list):  # Generate transactions for the specified number
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        self.g.add_edge(src, dst, amount=amount, date=date)

        transaction_count += 1
        total_amount += amount
        if transaction_count >= transaction_freq and total_amount >= aggregated_amount:
          break


    elif pattern_type == "fan_out":  # fan_out pattern (single (subject) account --> multiple accounts)
      src = subject
      dst_list = [n for n in members if n != subject]

      if transaction_freq is None:
        transaction_freq = num_members - 1

      for dst in itertools.cycle(dst_list):  # Generate transactions for the specified number
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        self.g.add_edge(src, dst, amount=amount, date=date)

        transaction_count += 1
        total_amount += amount
        if transaction_count >= transaction_freq and total_amount >= aggregated_amount:
          break


    elif pattern_type == "bipartite":  # bipartite (some accounts --> other accounts)
      src_list = members[:(num_members/2)]  # The first half members are source accounts
      dst_list = members[(num_members/2):]  # The last half members are destination accounts

      if transaction_freq is None:  # Number of transactions
        transaction_freq = len(src_list) * len(dst_list)

      for src, dst in itertools.product(src_list, dst_list):  # Each source account makes transactions to destination accounts
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        self.g.add_edge(src, dst, amount=amount, date=date)

        transaction_count += 1
        total_amount += amount
        if transaction_count > transaction_freq and total_amount >= aggregated_amount:
          break


    elif pattern_type == "mixed":  # fan_out -> bipartite -> fan_in
      src = members[0]  # Source account
      dst = members[num_members-1]  # Destination account
      src_list = members[1:(num_members/2)]  # First intermediate accounts
      dst_list = members[(num_members/2):num_members-1]  # Second intermediate accounts

      if transaction_freq is None:
        transaction_freq = len(src_list) + len(dst_list) + len(src_list) * len(dst_list)

      for _dst in src_list:  # Fan-out
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, _dst, amount=amount, date=date)
        self.g.add_edge(src, _dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount

      for _src, _dst in itertools.product(src_list, dst_list):  # Bipartite
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(_src, _dst, amount=amount, date=date)
        self.g.add_edge(_src, _dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount

      for _src in itertools.cycle(dst_list):  # Fan-in
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(_src, dst, amount=amount, date=date)
        self.g.add_edge(_src, dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
        if transaction_count >= transaction_freq and total_amount >= aggregated_amount:
          break



    elif pattern_type == "stack":  # two dense bipartite layers
      src_list = members[:num_members/3]  # First 1/3 of members are source accounts
      mid_list = members[num_members/3:num_members*2/3]  # Second 1/3 of members are intermediate accounts
      dst_list = members[num_members*2/3:]  # Last 1/3 of members are destination accounts

      if transaction_freq is None:  # Total number of transactions
        transaction_freq = len(src_list) * len(mid_list) + len(mid_list) * len(dst_list)

      for src, dst in itertools.product(src_list, mid_list):  # Each source account makes transactions to all intermediate accounts
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        self.g.add_edge(src, dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
        if transaction_count > transaction_freq and total_amount >= aggregated_amount:
          break

      for src, dst in itertools.product(mid_list, dst_list):  # Each intermediate account makes transactions to all destination accounts
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        self.g.add_edge(src, dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
        if transaction_count > transaction_freq and total_amount >= aggregated_amount:
          break


    elif pattern_type == "dense":  # Dense alert accounts (all-to-all)
      dsts = [n for n in members if n != subject]

      for dst in dsts:
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(subject, dst, amount=amount, date=date)
        self.g.add_edge(subject, dst, amount=amount, date=date)
      for dst in dsts:
        nb1 = random.choice(dsts)
        if dst != nb1:
          amount = random.uniform(min_amount, max_amount)
          date = random.randrange(start_day, end_day)
          sub_g.add_edge(dst, nb1, amount=amount, date=date)
          self.g.add_edge(dst, nb1, amount=amount, date=date)
        nb2 = random.choice(dsts)
        if dst != nb2:
          amount = random.uniform(min_amount, max_amount)
          date = random.randrange(start_day, end_day)
          sub_g.add_edge(nb2, dst, amount=amount, date=date)
          self.g.add_edge(nb2, dst, amount=amount, date=date)


    elif pattern_type == "cycle":  # Cycle transactions
      subject_index = list(members).index(subject)  # Index of member list indicates the subject account
      num = len(members)  # Number of involved accounts
      amount = random.uniform(min_amount, max_amount)  # Transaction amount
      dates = sorted([random.randrange(start_day, end_day) for _ in range(num)])  # Transaction date (in order)

      for i in range(num):
        src_i = (subject_index + i) % num
        dst_i = (src_i + 1) % num
        src = members[src_i]  # Source account ID
        dst = members[dst_i]  # Destination account ID
        date = dates[i]  # Transaction date (timestamp)

        sub_g.add_edge(src, dst, amount=amount, date=date)
        self.g.add_edge(src, dst, amount=amount, date=date)

    else:
      print("Warning: unknown pattern type: %s" % pattern_type)
      return


    ## Add the generated transaction edges to whole transaction graph
    sub_g.graph["subject"] = subject if isFraud else None
    self.alert_groups[self.alert_id] = sub_g

    ## Add fraud flags to account vertices
    for n in sub_g.nodes():
      self.g.node[n]["isFraud"] = True
    self.alert_id += 1


  def write_account_list(self):
    """Write all account list

    """

    fname = os.path.join(self.output_dir, self.conf.get("OutputFile", "accounts"))
    with open(fname, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["ACCOUNT_ID", "PRIMARY_CUSTOMER_ID", "init_balance", "start", "end", "country", "business", "suspicious", "isFraud", "modelID"])
      for n in self.g.nodes(data=True):
        aid = n[0]  # Account ID
        cid = "C_%d" % aid  # Customer ID bounded to this account
        prop = n[1]  # Account attributes
        balance = "{0:.2f}".format(prop["init_balance"])  # Initial balance
        start = prop["start"]  # Start time (when the account is opened)
        end = prop["end"]  # End time (when the account is closed)
        country = prop["country"]  # Country
        business = prop["business"]  # Business type
        suspicious = prop["suspicious"]  # Whether this account is suspicious (unused)
        isFraud = "true" if prop["isFraud"] else "false"  # Whether this account is involved in fraud transactions
        modelID = prop["modelID"]  # Transaction behavior model ID
        writer.writerow([aid, cid, balance, start, end, country, business, suspicious, isFraud, modelID])
    print("Exported %d accounts." % self.g.number_of_nodes())


  def write_transaction_list(self):
    fname = os.path.join(self.output_dir, self.conf.get("OutputFile", "transactions"))
    with open(fname, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["id", "src", "dst", "ttype"])
      for e in self.g.edges(data=True, keys=True):
        src = e[0]
        dst = e[1]
        tid = e[2]
        ttype = random.choice(self.tx_types)
        writer.writerow([tid, src, dst, ttype])
    print("Exported %d transactions." % self.g.number_of_edges())



  def write_alert_members(self):
    """Write alert account list

    """

    def get_outEdge_attrs(g, vid, name):
      return [v for k, v in nx.get_edge_attributes(g, name).iteritems() if (k[0] == vid or k[1] == vid)]

    fname = os.path.join(self.output_dir, self.conf.get("OutputFile", "alertgroup"))
    with open(fname, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["alertID", "reason", "clientID", "isSubject", "modelID", "minAmount", "maxAmount", "startStep", "endStep", "scheduleID"])
      for gid, sub_g in self.alert_groups.iteritems():
        modelID = sub_g.graph["modelID"]
        scheduleID = sub_g.graph["scheduleID"]
        reason = sub_g.graph["reason"]
        start = sub_g.graph["start"]
        end = sub_g.graph["end"]
        for n in sub_g.nodes():
          isSubject = "true" if (sub_g.graph["subject"] == n) else "false"
          minAmount = '{:.2f}'.format(min(get_outEdge_attrs(sub_g, n, "amount")))
          maxAmount = '{:.2f}'.format(max(get_outEdge_attrs(sub_g, n, "amount")))
          minStep = start
          maxStep = end
          writer.writerow([gid, reason, n, isSubject, modelID, minAmount, maxAmount, minStep, maxStep, scheduleID])

    print("Exported members of %d alerted groups." % len(self.alert_groups))



if __name__ == "__main__":
  argv = sys.argv
  if len(argv) < 4:
    print("Usage: python %s [ConfFile] [DegreeFile] [TypeFile] [AlertFile]" % argv[0])
    exit(1)

  txg = TransactionGenerator(argv[1], argv[3])
  txg.load_account_list()  # Load account list CSV file
  txg.generate_normal_transactions(argv[2])  # Load a parameter CSV file for the base transaction types
  txg.set_subject_candidates()  # Load a parameter CSV file for degrees of the base transaction graph
  if len(argv) == 4:
    txg.load_alert_patterns()  # Add alert patterns
  else:
    txg.load_alert_patterns(argv[4])
  txg.write_account_list()  # Export accounts to a CSV file
  txg.write_transaction_list()  # Export transactions to a CSV file
  txg.write_alert_members()  # Export alert accounts to a CSV file

