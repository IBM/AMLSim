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
  try:
    return int(value)
  except ValueError:
    return None


def parse_amount(value):
  try:
    return float(value)
  except ValueError:
    return None


def parse_flag(value):
  return value.lower() == "true"



class TransactionGenerator:

  def __init__(self, confFile):
    """Initialize transaction network.
    
    :param confFile: Configuration (ini) file name
    """
    self.g = nx.MultiDiGraph()
    self.num_accounts = 0
    self.degrees = dict()
    self.hubs = list()
    
    self.conf = ConfigParser()
    self.conf.read(confFile)
    self.seed = int(self.conf.get("General", "seed"))
    np.random.seed(self.seed)
    random.seed(self.seed)

    self.factor = int(self.conf.get("Base", "edge_factor"))
    self.prob = float(self.conf.get("Base", "triangle_prob"))
    
    self.default_max_amount = parse_amount(self.conf.get("General", "default_max_amount"))
    self.default_min_amount = parse_amount(self.conf.get("General", "default_min_amount"))
    self.total_period = parse_int(self.conf.get("General", "total_period"))
    self.alert_ratio = parse_int(self.conf.get("General", "alert_ratio"))
    
    self.input_dir = self.conf.get("InputFile", "directory")
    self.output_dir = self.conf.get("OutputFile", "directory")
    
    highrisk_countries_str = self.conf.get("HighRisk", "countries")
    highrisk_business_str = self.conf.get("HighRisk", "business")
    self.highrisk_countries = set(highrisk_countries_str.split(","))
    self.highrisk_business = set(highrisk_business_str.split(","))
    
    self.tx_id = 0  # Transaction ID
    self.fraud_id = 0  # Fraud ID from AML rules
    self.fraudgroups = dict()  # Fraud ID and fraud transaction graph
    self.types = {"fan_in":1, "fan_out":2, "bipartite":3, "mixed":4, "stack":5, "dense":6}  ## Pattern name and model ID

  def generate_degrees(self):
    self.degrees = self.g.degree(self.g.nodes())
    self.hubs = [n for n in self.g.nodes() if self.factor <= self.degrees[n] <= self.factor * 2]

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
  
  
  #### Pickup account vertices
  def get_account_vertex(self, suspicious=None):
    """Get an account vertex
    
    :param suspicious: If True, extract one only from suspicious accounts.
    If False, extract one only from non-suspicious accounts. If None (default), extract one from all accounts.
    :return: An account ID
    """
    if suspicious is None:
      candidates = self.g.nodes()
    else:
      candidates = [n for n in self.g.nodes() if self.g.node[n]["suspicious"] == suspicious]  # True/False
    return random.choice(candidates)


  def get_hub_vertices(self, num):
    """Get account vertices randomly (high-degree vertices are likely selected)

    :param num: Number of total account vertices
    :return: Account ID list
    """
    # if suspicious is None:
    #   candidates = self.g.nodes()
    # else:
    #   candidates = [n for n in self.g.nodes() if self.g.nodes[n]["suspicious"] == suspicious]  # True/False
    # candidates = [n for n in candidates if self.factor <= self.degrees[n]]
    # degrees = [self.degrees[n] for n in candidates]
    # probs = np.array(degrees) / float(sum(degrees))

    candidates = set()
    while len(candidates) < num:
      hub = random.choice(self.hubs)
      candidates.update([hub]+self.g.adj[hub].keys()) # candidates.update(nx.ego_graph(self.g, hub).nodes())
    return np.random.choice(list(candidates), num, False)



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
    

  #### Load account vertices from CSV file
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
        if k == "num":
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
          init_balance = random.uniform(min_balance, max_balance)
          self.add_account(aid, init_balance, start_day, end_day, country, business, suspicious, modelID)
          aid += 1

    self.num_accounts = aid
    print("Created %d accounts." % self.num_accounts)


  #### Generate base transactions without attributes
  # https://networkx.github.io/documentation/stable/reference/generated/networkx.generators.random_graphs.powerlaw_cluster_graph.html
  def add_base_transactions(self):
    factor = self.factor  # the number of random edges to add for each new node
    prob = self.prob  # probability of adding a triangle after adding a random edge
    seed = self.seed    # seed for random number generator
    g = nx.generators.random_graphs.powerlaw_cluster_graph(self.num_accounts, factor, prob, seed)
    for src, dst in g.edges():
      self.add_transaction(src, dst)
    print("Added %d base transactions." % g.number_of_edges())
  
  
  #### Add an account vertex and a transaction edge
  def add_account(self, aid, init_balance, start, end, country, business, suspicious, modelID):
    """Add an account
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
    if self.check_account_absent(aid):
      self.g.add_node(aid, init_balance=init_balance, start=start, end=end, country=country, business=business, suspicious=suspicious, isFraud=False, modelID=modelID)


  def add_transaction(self, src, dst, amount=None, date=None):
    """Add a transaction
    :param src:
    :param dst:
    :param amount:
    :param date:
    :return:
    """
    self.check_account_exist(src)
    self.check_account_exist(dst)
    self.g.add_edge(src, dst, key=self.tx_id, amount=amount, date=date)
    self.tx_id += 1



  #### Load Simple Transaction Patterns
  def load_simple_patterns(self):
    """Load simple transaction pattern file
    
    :return:
    """
    types = ["cycle", "fan_in", "fan_out", "path", "dense"]
    
    csv_name = os.path.join(self.input_dir, self.conf.get("InputFile", "patterns"))
    
    idx_num = None
    idx_type = None
    idx_accts = None
    idx_min = None
    idx_max = None
    idx_start = None
    idx_end = None
    
    with open(csv_name, "r") as rf:
      reader = csv.reader(rf)

      ## Parse header
      header = next(reader)
      for i, k in enumerate(header):
        if k == "num":
          idx_num = i
        elif k == "type":
          idx_type = i
        elif k == "accounts":
          idx_accts = i
        elif k == "min_amount":
          idx_min = i
        elif k == "max_amount":
          idx_max = i
        elif k == "start_day":
          idx_start = i
        elif k == "end_day":
          idx_end = i
        else:
          print("Warning: unknown key: %s" % k)
      
      for row in reader:
        if "#" in row[0]:  ## Comment
          continue

        num = int(row[idx_num])
        pattern_type = row[idx_type]
        accounts = int(row[idx_accts])
        min_amount = parse_amount(row[idx_min])
        max_amount = parse_amount(row[idx_max])
        start_day = parse_int(row[idx_start])
        end_day = parse_int(row[idx_end])
        
        if pattern_type not in types:
          print("Warning: pattern type (%s) must be one of %s" % (pattern_type, str(types)))
          continue
        
        if accounts < 3:
          print("Warning: number of members (%d) must be 3 or more" % accounts)
          continue
        
        for i in range(num):
          amount = random.uniform(min_amount, max_amount)
          day = random.randrange(start_day, end_day)
          members = self.get_account_vertices(accounts)
          
          if pattern_type == "cycle":
            self.add_cycle_pattern(members, amount, day)
          elif pattern_type == "fan_in":
            self.add_fan_in_pattern(members[1:], members[0], amount, day)
          elif pattern_type == "fan_out":
            self.add_fan_out_pattern(members[0], members[1:], amount, day)
          elif pattern_type == "path":
            self.add_path_pattern(members, amount, day)
          else:
            print("Warning: unknown pattern type: %s" % pattern_type)
            break
    
  

  #### Add Simple Transaction Patterns
  
  def add_cycle_pattern(self, members, amount, date):
    """Add cycle transactions
    :param members: Transaction members
    :param amount:
    :param date:
    :return:
    """
    num = len(members)
    for i in range(num):
      src = members[i]
      dst = members[(i+1) % num]
      self.add_transaction(src, dst, amount, date)

  def add_fan_in_pattern(self, src_list, dst, amount, date):
    for src in src_list:
      self.add_transaction(src, dst, amount, date)

  def add_fan_out_pattern(self, src, dst_list, amount, date):
    for dst in dst_list:
      self.add_transaction(src, dst, amount, date)
  
  def add_path_pattern(self, members, amount, date):
    for i in range(len(members)-1):
      self.add_transaction(members[i], members[i+1], amount, date)

  
  
  #### Add Dense (multiple fan-in/out) Transaction Patterns
  
  def add_dense_transactions(self, src_list, dst_list, limit=None):
    pairs = list(itertools.product(src_list, dst_list))
    if limit is not None:
      limit = min(len(pairs), limit)
      random.shuffle(pairs)
      pairs = pairs[:limit]
    
    for src, dst in pairs:
      self.add_transaction(src, dst)
  
  
  
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


  
  #### Add transaction set of fraud groups based on AML rule
  
  def load_aml_rule(self):
    """Load AML CSV file
    
    :return:
    """
    
    csv_name = os.path.join(self.input_dir, self.conf.get("InputFile", "amlrule"))
    
    idx_num = None
    idx_type = None
    idx_accts = None
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
    
    with open(csv_name, "r") as rf:
      reader = csv.reader(rf)
      
      ## Parse header
      header = next(reader)
      for i, k in enumerate(header):
        if k == "num":
          idx_num = i
        elif k == "type":
          idx_type = i
        elif k == "accounts":
          idx_accts = i
        elif k == "individual_amount":
          idx_individual = i
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
        else:
          print("Warning: unknown key: %s" % k)
      
      ## Generate transaction set
      for row in reader:
        if "#" in row[0]:  ## Comment
          continue

        num = int(row[idx_num])
        pattern_type = row[idx_type]
        accounts = int(row[idx_accts])
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
        
        if not pattern_type in self.types:
          print("Warning: pattern type (%s) must be one of %s" % (pattern_type, str(self.types.keys())))
          continue
        
        if transaction_count is not None and transaction_count < accounts:
          print("Warning: number of transactions (%d) must not be smaller than the number of accounts (%d)" % (transaction_count, accounts))
          continue
        
        # members = self.get_account_vertices(accounts)
        
        for i in range(num):
          ## Add fraud patterns
          self.add_aml_rule(True, pattern_type, accounts, individual_amount, aggregated_amount, transaction_count,
                            amount_difference, period, amount_rounded, orig_country, bene_country, orig_business, bene_business)
          for j in range(self.alert_ratio):
            ## Add alert patterns
            self.add_aml_rule(False, pattern_type, accounts, individual_amount, aggregated_amount, transaction_count,
                              amount_difference, period, amount_rounded, orig_country, bene_country, orig_business, bene_business)
      
  
  
  def add_aml_rule(self, isFraud, pattern_type, accounts, individual_amount=None, aggregated_amount=None,
                   transaction_freq=None, amount_difference=None, period=None, amount_rounded=None,
                   orig_country=False, bene_country=False, orig_business=False, bene_business=False):
    """Add an AML rule transaction set

    :param isFraud: Whether the trasnsaction set is fraud or alert
    :param pattern_type: Pattern type ("fan_in", "fan_out", "dense", "mixed" or "stack")
    :param accounts: Number of transaction members (accounts)
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
    # members = self.get_account_vertices(accounts)
    members = self.get_hub_vertices(accounts)

    ## Prepare parameters
    if individual_amount is None:
      min_amount = self.default_min_amount
      max_amount = self.default_max_amount
    else:
      min_amount = individual_amount
      max_amount = individual_amount * 2
    
    if aggregated_amount is None:
      aggregated_amount = 0

    start_day = random.randint(0, self.total_period)
    if period is None:
      end_day = start_day + self.total_period
    else:
      end_day = start_day + period


    ## Create subgraph structure with transaction attributes
    modelID = self.types[pattern_type]  ## Fraud model ID
    sub_g = nx.MultiDiGraph(modelID=modelID)
    num_members = len(members)
    total_amount = 0
    transaction_count = 0
    subject = None  # Subject account ID
    
    if pattern_type == "fan_in":  # fan_in
      src_list = members[1:]
      dst = members[0]
      subject = dst
      
      if transaction_freq is None:
        transaction_freq = num_members - 1
        
      for src in itertools.cycle(src_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        
        transaction_count += 1
        total_amount += amount
        if transaction_count >= transaction_freq and total_amount >= aggregated_amount:
          break
      
      
    elif pattern_type == "fan_out":  # fan_out
      src = members[0]
      dst_list = members[1:]
      subject = src
      
      if transaction_freq is None:
        transaction_freq = num_members - 1
      
      for dst in itertools.cycle(dst_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        
        transaction_count += 1
        total_amount += amount
        if transaction_count >= transaction_freq and total_amount >= aggregated_amount:
          break
      
      
    elif pattern_type == "bipartite":  # dense bipartite
      src_list = members[:(num_members/2)]
      dst_list = members[(num_members/2):]
      
      if transaction_freq is None:
        transaction_freq = len(src_list) * len(dst_list)
      
      for src, dst in itertools.product(src_list, dst_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        
        transaction_count += 1
        total_amount += amount
        if transaction_count > transaction_freq and total_amount >= aggregated_amount:
          break

      subject = max(sub_g.nodes(), key=lambda n:sub_g.degree(n))  # hub vertex
      
      
    elif pattern_type == "mixed":  # fan_out, dense bipartite, fan_in
      src = members[0]
      dst = members[num_members-1]
      src_list = members[1:(num_members/2)]
      dst_list = members[(num_members/2):num_members-1]
      
      if transaction_freq is None:
        transaction_freq = len(src_list) + len(dst_list) + len(src_list) * len(dst_list)
        
      for _dst in src_list:
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, _dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
      
      for _src, _dst in itertools.product(src_list, dst_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(_src, _dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
      
      for _src in itertools.cycle(dst_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(_src, dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
        if transaction_count >= transaction_freq and total_amount >= aggregated_amount:
          break

      subject = max(sub_g.nodes(), key=lambda n:sub_g.degree(n))  # hub vertex
      
      
      
    elif pattern_type == "stack":  # two dense bipartite layers
      src_list = members[:num_members/3]
      mid_list = members[num_members/3:num_members*2/3]
      dst_list = members[num_members*2/3:]
      
      if transaction_freq is None:
        transaction_freq = len(src_list) * len(mid_list) + len(mid_list) * len(dst_list)

      for src, dst in itertools.product(src_list, mid_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
        if transaction_count > transaction_freq and total_amount >= aggregated_amount:
          break
      
      for src, dst in itertools.product(mid_list, dst_list):
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(src, dst, amount=amount, date=date)
        transaction_count += 1
        total_amount += amount
        if transaction_count > transaction_freq and total_amount >= aggregated_amount:
          break

      subject = max(sub_g.nodes(), key=lambda n:sub_g.degree(n))  # hub vertex


    elif pattern_type == "dense":  # Dense fraud accounts
      subject = members[0]  # Hub account
      dsts = members[1:]

      for dst in dsts:
        amount = random.uniform(min_amount, max_amount)
        date = random.randrange(start_day, end_day)
        sub_g.add_edge(subject, dst, amount=amount, date=date)
      for dst in dsts:
        nb1 = random.choice(dsts)
        if dst != nb1:
          amount = random.uniform(min_amount, max_amount)
          date = random.randrange(start_day, end_day)
          sub_g.add_edge(dst, nb1, amount=amount, date=date)
        nb2 = random.choice(dsts)
        if dst != nb2:
          amount = random.uniform(min_amount, max_amount)
          date = random.randrange(start_day, end_day)
          sub_g.add_edge(nb2, dst, amount=amount, date=date)

      
    else:
      print("Warning: unknown pattern type: %s" % pattern_type)
      return


    ## Add the generated transaction edges to whole transaction graph
    sub_g.graph["subject"] = subject if isFraud else None
    self.fraudgroups[self.fraud_id] = sub_g

    ## Add fraud flags to account vertices
    for n in sub_g.nodes():
      self.g.node[n]["isFraud"] = True
    self.fraud_id += 1
    
  
  
  #### Account and Transaction CSV Output
  def write_account_list(self):
    fname = os.path.join(self.output_dir, self.conf.get("OutputFile", "accounts"))
    with open(fname, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["ACCOUNT_ID", "ACCOUNT_BALANCE", "DATE_OPENED", "DATE_CLOSED", "COUNTRY_CODE", "ACCOUNT_TYPE", "suspicious", "isFraud", "modelID"])
      for n in self.g.nodes(data=True):
        aid = n[0]
        prop = n[1]
        balance = "{0:.2f}".format(prop["init_balance"])
        start = prop["start"]
        end = prop["end"]
        country = prop["country"]
        business = prop["business"]
        suspicious = prop["suspicious"]
        isFraud = "true" if prop["isFraud"] else "false"
        modelID = prop["modelID"]
        writer.writerow([aid, balance, start, end, country, business, suspicious, isFraud, modelID])
    print("Exported %d accounts." % self.g.number_of_nodes())
    
  
  def write_transaction_list(self):
    fname = os.path.join(self.output_dir, self.conf.get("OutputFile", "transactions"))
    with open(fname, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["id", "src", "dst"])
      for e in self.g.edges(data=True, keys=True):
        src = e[0]
        dst = e[1]
        tid = e[2]
        writer.writerow([tid, src, dst])
    print("Exported %d transactions." % self.g.number_of_edges())



  def write_alert_members_list(self):

    def get_outEdge_attrs(g, vid, name):
      return [v for k, v in nx.get_edge_attributes(g, name).iteritems() if (k[0] == vid or k[1] == vid)]

    fname = os.path.join(self.output_dir, self.conf.get("OutputFile", "alert_members"))
    with open(fname, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["alertID", "clientID", "isSubject", "modelID", "minAmount", "maxAmount", "startStep", "endStep"])
      for gid, sub_g in self.fraudgroups.iteritems():
        modelID = sub_g.graph["modelID"]
        for n in sub_g.nodes():
          isSubject = "true" if (sub_g.graph["subject"] == n) else "false"
          minAmount = '{:.2f}'.format(min(get_outEdge_attrs(sub_g, n, "amount")))
          maxAmount = '{:.2f}'.format(max(get_outEdge_attrs(sub_g, n, "amount")))
          minStep = min(get_outEdge_attrs(sub_g, n, "date"))
          maxStep = max(get_outEdge_attrs(sub_g, n, "date"))
          writer.writerow([gid, n, isSubject, modelID, minAmount, maxAmount, minStep, maxStep])

    print("Exported %d alert groups." % len(self.fraudgroups))



if __name__ == "__main__":
  argv = sys.argv
  if len(argv) < 2:
    print("Usage: python %s [ConfFile]" % argv[0])
    exit(1)

  txg = TransactionGenerator(argv[1])
  txg.load_account_list()
  txg.add_base_transactions()
  txg.load_simple_patterns()
  txg.generate_degrees()
  txg.load_aml_rule()
  txg.write_account_list()
  txg.write_transaction_list()
  txg.write_alert_members_list()


