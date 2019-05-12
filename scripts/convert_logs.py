import csv
import json
import sys
import os
import datetime
from ConfigParser import ConfigParser


def days_to_date(days):
  date = datetime.datetime(2017, 1, 1) + datetime.timedelta(days=days)
  return date.strftime("%Y%m%d")

def get_simulator_name(csvFile):
  # PS_yyyyMMdd_HHmmss_SSS_log.csv --> PS_yyyyMMdd_HHmmss_SSS
  elements = csvFile.split("_")
  return "_".join(elements[:4])


def get_name(acctID):
  return "Account" + str(acctID)

def get_bank(acctID):
  return "Bank" + str(acctID)


CASH_TYPES = {"CASH-IN", "CASH-OUT"}


class FraudGroup:

  def __init__(self, reason):
    self.subject = None
    self.reason = reason
    self.transactions = dict()  # ID, fields
    self.members = set()
    self.start = None
    self.end = None
    self.total_amount = 0.0
    self.count = 0

  def add_member(self, member, isSubject):
    self.members.add(member)
    if isSubject:
      self.subject = member

  def add_transaction(self, txID, amount, days, origAcct, destAcct, origName, destName):
    self.transactions[txID] = (amount, days, origAcct, destAcct, origName, destName)
    self.total_amount += amount
    self.count += 1

  def get_reason(self):
    return self.reason

  def get_start_date(self):
    min_days = min([tx[1] for tx in self.transactions.values()])
    return days_to_date(min_days)

  def get_end_date(self):
    max_days = max([tx[1] for tx in self.transactions.values()])
    return days_to_date(max_days)


  def output_csv(self, fname):
    wf = open(fname, "w")
    writer = csv.writer(wf)

    ## Write header
    writer.writerow(["account", "", "", "", "", "", ""])
    writer.writerow([self.subject, "", "", "start", "end", "", ""])
    writer.writerow(["", "", "", self.get_start_date(), self.get_end_date(), "", ""])
    writer.writerow(["", "transaction", "amount", "", "", "", ""])
    writer.writerow(["", self.count, '{:.2f}'.format(self.total_amount), "", "", "", ""])

    writer.writerow(["gps_ref", "order_patry_acct", "beneficiary_acct", "order_party_name", "beneficiary_name",
                     "amount", "value_date"])

    ## Write transactions
    for txid, tx in self.transactions.iteritems():
      amount = tx[0]
      date = days_to_date(tx[1])
      origAcct = tx[2]
      beneAcct = tx[3]
      origName = tx[4]
      beneName = tx[5]
      writer.writerow([txid, origAcct, beneAcct, origName, beneName, amount, date])
    wf.close()


  def get_alerts(self):
    rows = list()
    for tx_id, tx in self.transactions.iteritems():
      origAcct = str(tx[2])
      origName = str(tx[4])
      date = days_to_date(tx[1])
      rows.append((origAcct, origName, date))
    return rows


class Schema:
  def __init__(self, json_file):
    with open(json_file, "r") as rf:
      self.data = json.load(rf)

      self.acct_num_cols = None
      self.acct_names = list()
      self.acct_types = list()
      self.acct_name2idx = dict()
      self.acct_id_idx = None
      self.acct_name_idx = None
      self.acct_balance_idx = None
      self.acct_start_idx = None
      self.acct_end_idx = None
      self.acct_fraud_idx = None
      self.acct_model_idx = None

      self.tx_num_cols = None
      self.tx_names = list()
      self.tx_types = list()
      self.tx_name2idx = dict()
      self.tx_id_idx = None
      self.tx_time_idx = None
      self.tx_amount_idx = None
      self.tx_type_idx = None
      self.tx_orig_idx = None
      self.tx_dest_idx = None
      self.tx_fraud_idx = None
      self.tx_alert_idx = None

      self.alert_num_cols = None
      self.alert_names = list()
      self.alert_types = list()
      self.alert_name2idx = dict()
      self.alert_id_idx = None
      self.alert_type_idx = None
      self.alert_fraud_idx = None
      self.alert_tx_idx = None
      self.alert_orig_idx = None
      self.alert_dest_idx = None
      self.alert_tx_type_idx = None
      self.alert_amount_idx = None
      self.alert_time_idx = None
    self._parse()


  def _parse(self):
    acct_data = self.data["account"]
    tx_data = self.data["transaction"]
    alert_data = self.data["alert"]
    self.acct_num_cols = len(acct_data)
    self.tx_num_cols = len(tx_data)
    self.alert_num_cols = len(alert_data)

    # Account list
    for idx, col in enumerate(acct_data):
      name = col["name"]
      vtype = col.get("valueType", "string")
      dtype = col.get("dataType")

      self.acct_names.append(name)
      self.acct_types.append(vtype)
      self.acct_name2idx[name] = idx

      if dtype is None:
        continue
      if dtype == "account_id":
        self.acct_id_idx = idx
      elif dtype == "account_name":
        self.acct_name_idx = idx
      elif dtype == "initial_balance":
        self.acct_balance_idx = idx
      elif dtype == "start_time":
        self.acct_start_idx = idx
      elif dtype == "end_time":
        self.acct_end_idx = idx
      elif dtype == "fraud_flag":
        self.acct_fraud_idx = idx
      elif dtype == "model_id":
        self.acct_model_idx = idx

    # Transaction list
    for idx, col in enumerate(tx_data):
      name = col["name"]
      vtype = col.get("valueType", "string")
      dtype = col.get("dataType")

      self.tx_names.append(name)
      self.tx_types.append(vtype)
      self.tx_name2idx[name] = idx

      if dtype is None:
        continue
      if dtype == "transaction_id":
        self.tx_id_idx = idx
      elif dtype == "timestamp":
        self.tx_time_idx = idx
      elif dtype == "amount":
        self.tx_amount_idx = idx
      elif dtype == "transaction_type":
        self.tx_type_idx = idx
      elif dtype == "orig_id":
        self.tx_orig_idx = idx
      elif dtype == "dest_id":
        self.tx_dest_idx = idx
      elif dtype == "fraud_flag":
        self.tx_fraud_idx = idx
      elif dtype == "alert_id":
        self.tx_alert_idx = idx

    # Alert list
    for idx, col in enumerate(alert_data):
      name = col["name"]
      vtype = col.get("valueType", "string")
      dtype = col.get("dataType")

      self.alert_names.append(name)
      self.alert_types.append(vtype)
      self.alert_name2idx[name] = idx

      if dtype is None:
        continue
      if dtype == "alert_id":
        self.alert_id_idx = idx
      elif dtype == "alert_type":
        self.alert_type_idx = idx
      elif dtype == "fraud_flag":
        self.alert_fraud_idx = idx
      elif dtype == "transaction_id":
        self.alert_tx_idx = idx
      elif dtype == "orig_id":
        self.alert_orig_idx = idx
      elif dtype == "dest_id":
        self.alert_dest_idx = idx
      elif dtype == "transaction_type":
        self.alert_tx_type_idx = idx
      elif dtype == "amount":
        self.alert_amount_idx = idx
      elif dtype == "timestamp":
        self.alert_time_idx = idx




  def get_acct_row(self, acct_id, acct_name, init_balance, start, end, is_fraud, model_id, **attr):
    row = [""] * self.acct_num_cols
    row[self.acct_id_idx] = acct_id
    row[self.acct_name_idx] = acct_name
    row[self.acct_balance_idx] = init_balance
    row[self.acct_start_idx] = start
    row[self.acct_end_idx] = end
    row[self.acct_fraud_idx] = is_fraud
    row[self.acct_model_idx] = model_id
    for name, value in attr.iteritems():
      if name in self.acct_name2idx:
        idx = self.acct_name2idx[name]
        row[idx] = value
    return row

  def get_tx_row(self, _tx_id, _timestamp, _amount, _tx_type, _orig, _dest, _is_fraud, _alert_id, **attr):
    row = [""] * self.tx_num_cols
    row[self.tx_id_idx] = _tx_id
    row[self.tx_time_idx] = _timestamp
    row[self.tx_amount_idx] = _amount
    row[self.tx_type_idx] = _tx_type
    row[self.tx_orig_idx] = _orig
    row[self.tx_dest_idx] = _dest
    row[self.tx_fraud_idx] = _is_fraud
    row[self.tx_alert_idx] = _alert_id
    for name, value in attr.iteritems():
      if name in self.tx_name2idx:
        idx = self.tx_name2idx[name]
        row[idx] = value
    return row

  def get_alert_row(self, _alert_id, _alert_type, _is_fraud, _tx_id, _orig, _dest, _tx_type, _amount, _timestamp, **attr):
    row = [""] * self.alert_num_cols

    row[self.alert_id_idx] = _alert_id
    row[self.alert_type_idx] = _alert_type
    row[self.alert_fraud_idx] = _is_fraud
    row[self.alert_tx_idx] = _tx_id
    row[self.alert_orig_idx] = _orig
    row[self.alert_dest_idx] = _dest
    row[self.alert_tx_type_idx] = _tx_type
    row[self.alert_amount_idx] = _amount
    row[self.alert_time_idx] = _timestamp
    for name, value in attr.iteritems():
      if name in self.alert_name2idx:
        idx = self.alert_name2idx[name]
        row[idx] = value
    return row




class LogConverter:

  def __init__(self, confFile, tx_log):
    self.frauds = dict()
    self.org_types = dict()  # ID, organization type
    self.log_file = tx_log
    conf = ConfigParser()
    conf.read(confFile)

    self.work_dir = conf.get("General", "work_dir")
    if not os.path.isdir(self.work_dir):
      os.makedirs(self.work_dir)
    schema_file = conf.get("General", "schema_file")
    self.schema = Schema(schema_file)

    self.in_acct_file = conf.get("Input", "acct_file")
    self.out_acct_file = conf.get("Output", "acct_file")
    self.tx_file = conf.get("Output", "tx_file")
    self.cash_tx_file = conf.get("Output", "cash_tx_file")
    self.group_file = conf.get("Input", "alert_member_file")
    self.case_file = conf.get("Output", "case_file")
    self.alert_tx_file = conf.get("Output", "alert_tx_file")
    self.subject_file = conf.get("Output", "subject_file")



  def convert_transaction_list(self):
    print("Convert transaction list from %s to %s, %s and %s" % (self.log_file, self.tx_file, self.cash_tx_file, self.alert_tx_file))

    af = open(os.path.join(self.work_dir, self.in_acct_file), "r")
    rf = open(self.log_file, "r")
    of = open(os.path.join(self.work_dir, self.out_acct_file), "w")
    tf = open(os.path.join(self.work_dir, self.tx_file), "w")
    cf = open(os.path.join(self.work_dir, self.cash_tx_file), "w")
    lf = open(os.path.join(self.work_dir, self.alert_tx_file), "w")

    reader = csv.reader(af)
    acct_writer = csv.writer(of)
    acct_writer.writerow(self.schema.acct_names)  # write header

    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}
    id_idx = indices["ACCOUNT_ID"]
    name_idx = indices["CUSTOMER_ID"]
    balance_idx = indices["INIT_BALANCE"]
    start_idx = indices["START_DATE"]
    end_idx = indices["END_DATE"]
    type_idx = indices["ACCOUNT_TYPE"]
    fraud_idx = indices["IS_FRAUD"]
    model_idx = indices["TX_BEHAVIOR_ID"]

    for row in reader:
      acct_id = row[id_idx]
      acct_name = row[name_idx]
      balance = row[balance_idx]
      start = row[start_idx]
      end = row[end_idx]
      acct_type = row[type_idx]
      acct_fraud = row[fraud_idx]
      acct_model = row[model_idx]
      attr = {name: row[index] for name, index in indices.iteritems()}
      output_row = self.schema.get_acct_row(acct_id, acct_name, balance, start, end, acct_fraud, acct_model, **attr)
      acct_writer.writerow(output_row)
      self.org_types[acct_id] = acct_type
    af.close()

    tx_set = set()
    cash_tx_set = set()

    reader = csv.reader(rf)
    tx_writer = csv.writer(tf)
    cash_tx_writer = csv.writer(cf)
    alert_tx_writer = csv.writer(lf)

    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}
    num_columns = len(header)

    tx_header = self.schema.tx_names
    alert_header = self.schema.alert_names
    tx_writer.writerow(tx_header)
    cash_tx_writer.writerow(tx_header)
    alert_tx_writer.writerow(alert_header)

    # tx_writer.writerow(["TX_ID", "SENDER_ACCOUNT_ID", "RECEIVER_ACCOUNT_ID", "TX_TYPE", "TX_AMOUNT", "TIMESTAMP", "IS_FRAUD", "ALERT_ID"])
    # cash_tx_writer.writerow(["TX_ID", "SENDER_ACCOUNT_ID", "RECEIVER_ACCOUNT_ID", "TX_TYPE", "TX_AMOUNT", "TIMESTAMP", "IS_FRAUD", "ALERT_ID"])
    # alert_tx_writer.writerow(["ALERT_ID", "ALERT_TYPE", "IS_FRAUD", "TX_ID", "SENDER_ACCOUNT_ID", "RECEIVER_ACCOUNT_ID", "TX_TYPE", "TX_AMOUNT", "TIMESTAMP"])

    step_idx = indices["step"]
    amt_idx = indices["amount"]
    orig_idx = indices["nameOrig"]
    dest_idx = indices["nameDest"]
    fraud_idx = indices["isFraud"]
    alert_idx = indices["alertID"]
    type_idx = indices["type"]

    txID = 1
    for row in reader:
      if len(row) < num_columns:
        continue
      try:
        days = int(row[step_idx])
        date_str = str(days) # days_to_date(days)

        amount = row[amt_idx]
        origID = row[orig_idx]
        destID = row[dest_idx]

        fraudID = int(row[fraud_idx])
        alertID = int(row[alert_idx])

        is_fraud = fraudID > 0
        is_alert = alertID >= 0
        ttype = row[type_idx]
      except ValueError:
        continue

      attr = {name: row[index] for name, index in indices.iteritems()}
      if ttype in CASH_TYPES:
        cash_tx = (origID, destID, ttype, amount, date_str)
        if cash_tx not in cash_tx_set:
          # cash_tx_writer.writerow([txID, origID, destID, ttype, amount, date_str, is_fraud, alertID])
          cash_tx_set.add(cash_tx)
          output_row = self.schema.get_tx_row(txID, date_str, amount, ttype, origID, destID, is_fraud, alertID, **attr)
          cash_tx_writer.writerow(output_row)
      else:
        tx = (origID, destID, ttype, amount, date_str)
        if tx not in tx_set:
          # tx_writer.writerow([txID, origID, destID, ttype, amount, date_str, is_fraud, alertID])
          output_row = self.schema.get_tx_row(txID, date_str, amount, ttype, origID, destID, is_fraud, alertID, **attr)
          tx_writer.writerow(output_row)
          tx_set.add(tx)
      if is_alert:
        alert_type = self.frauds.get(alertID).get_reason()
        # alert_tx_writer.writerow([alertID, alert_type, is_fraud, txID, origID, destID, ttype, amount, date_str])
        alert_row = self.schema.get_alert_row(alertID, alert_type, is_fraud, txID, origID, destID, ttype, amount, date_str, **attr)
        alert_tx_writer.writerow(alert_row)

      txID += 1

    rf.close()
    tf.close()
    cf.close()
    lf.close()



  def load_fraud_groups(self):
    input_file = self.group_file

    print("Load alert groups: %s" % input_file)
    rf = open(os.path.join(self.work_dir, input_file), "r")
    reader = csv.reader(rf)
    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}

    for row in reader:
      reason = row[indices["reason"]]
      alertID = int(row[indices["alertID"]])
      clientID = row[indices["clientID"]]
      isSubject = row[indices["isSubject"]].lower() == "true"

      if alertID not in self.frauds:
        self.frauds[alertID] = FraudGroup(reason)
      self.frauds[alertID].add_member(clientID, isSubject)



  def output_fraud_cases(self):
    input_file = self.log_file
    fpath = os.path.join(self.work_dir, self.case_file)

    print("Convert fraud cases from %s to %s" % (input_file, fpath))
    rf = open(input_file, "r")
    reader = csv.reader(rf)
    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}
    columns = len(header)

    txID = 0
    for row in reader:
      if len(row) < columns:
        continue
      try:
        days = int(row[indices["step"]])
        amount = float(row[indices["amount"]])
        orig = int(row[indices["nameOrig"]])
        dest = int(row[indices["nameDest"]])
        alertID = int(row[indices["alertID"]])
        orig_name = "C_%d" % orig
        dest_name = "C_%d" % dest
      except ValueError:
        continue

      if alertID >= 0 and alertID in self.frauds:
        self.frauds[alertID].add_transaction(txID, amount, days, orig, dest, orig_name, dest_name)
        txID += 1

    alerts = set()
    count = 0
    frauds = len(self.frauds)
    for fraud_id, fg in self.frauds.iteritems():
      if fg.count == 0:
        continue
      data = fg.get_alerts()
      reason = fg.get_reason()
      escalated = "YES" if (fg.subject is not None) else "NO"
      for row in data:
        acct_id, cust_id, date = row
        org_type = "INDIVIDUAL" if self.org_types[acct_id] == "I" else "COMPANY"
        alerts.add((fraud_id, acct_id, cust_id, date, reason, org_type, escalated))
      count += 1
      if count % 100 == 0:
        print("Frauds: %d/%d" % (count, frauds))

    count = 0
    with open(fpath, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["ALERT_ID", "MAIN_ACCOUNT_ID", "MAIN_CUSTOMER_ID", "EVENT_DATE", "ALERT_TYPE", "ACCOUNT_TYPE", "IS_FRAUD"])
      for alert in alerts:
        fraud_id, acct_id, cust_id, date, alert_type, acct_type, is_fraud = alert
        writer.writerow((count, acct_id, cust_id, date, alert_type, acct_type, is_fraud))
        count += 1


  def output_subject_accounts(self):
    subject_ids = set()
    for fg in self.frauds.values():
      subject = fg.subject
      if subject:
        subject_ids.add(subject)

    output_file = os.path.join(self.work_dir, self.subject_file)
    print("Write subject accounts to %s" % output_file)
    with open(output_file, "w") as wf:
      writer = csv.writer(wf)
      for subject in subject_ids:
          writer.writerow([subject])



if __name__ == "__main__":
  argv = sys.argv

  if len(argv) < 3:
    print("Usage: python %s [ConfFile] [TxLog]" % argv[0])
    exit(1)

  converter = LogConverter(argv[1], argv[2])
  converter.load_fraud_groups()
  converter.convert_transaction_list()
  converter.output_fraud_cases()
  converter.output_subject_accounts()



