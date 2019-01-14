import csv
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
    for txid, tx in self.transactions.iteritems():
      origAcct = tx[2]
      origName = tx[4]
      date = days_to_date(tx[1])
      rows.append([origAcct, origName, date])
    return rows


class LogConverter:

  def __init__(self, confFile, tx_log):
    self.frauds = dict()
    self.org_types = dict()  # ID, organization type
    self.log_file = tx_log
    conf = ConfigParser()
    conf.read(confFile)
    self.acct_file = conf.get("Input", "acct_file")
    self.tx_file = conf.get("Output", "tx_file")
    self.cash_tx_file = conf.get("Output", "cash_tx_file")
    self.group_file = conf.get("Input", "group_file")
    self.alert_file = conf.get("Output", "alert_file")
    self.fraud_dir = conf.get("Output", "fraud_dir")
    self.subject_file = conf.get("Output", "subject_file")



  def convert_transaction_list(self):
    print("Convert transaction list from %s to %s, %s and %s" % (self.log_file, self.tx_file, self.cash_tx_file, self.alert_file))

    af = open(self.acct_file, "r")
    rf = open(self.log_file, "r")
    tf = open(self.tx_file, "w")
    cf = open(self.cash_tx_file, "w")
    lf = open(self.alert_file, "w")

    reader = csv.reader(af)
    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}
    columns = len(header)
    for row in reader:
      acct = row[indices["ACCOUNT_ID"]]
      atype = row[indices["business"]]
      self.org_types[acct] = atype
    af.close()

    tx_set = set()
    cash_tx_set = set()

    reader = csv.reader(rf)
    tx_writer = csv.writer(tf)
    cash_tx_writer = csv.writer(cf)
    alert_writer = csv.writer(lf)

    header = next(reader)
    indices = {name:index for index, name in enumerate(header)}
    columns = len(header)

    tx_writer.writerow(["TXN_ID", "ACCOUNT_ID", "COUNTER_PARTY_ACCOUNT_NUM", "TXN_SOURCE_TYPE_CODE",
                        "tx_count", "TXN_AMOUNT_ORIG", "start", "end"])
    cash_tx_writer.writerow(["TXN_ID", "ACCOUNT_ID", "BRANCH_ID", "TXN_SOURCE_TYPE_CODE",
                        "tx_count", "TXN_AMOUNT_ORIG", "RUN_DATE", "end"])
    alert_writer.writerow(["AlertId", "TranNo", "ByOrderAcct", "BeneAcct"])

    txID = 1
    for row in reader:
      if len(row) < columns:
        continue
      try:
        days = int(row[indices["step"]])
        datestr = str(days) # days_to_date(days)

        amount = row[indices["amount"]]
        origID = row[indices["nameOrig"]]
        destID = row[indices["nameDest"]]
        # origName = "Account" + origID
        # destName = "Account" + destID
        # origBank = "Bank" + origID
        # destBank = "Bank" + destID

        fraudID = int(row[indices["isFraud"]])
        alertID = int(row[indices["alertID"]])

        is_sar = fraudID > 0
        is_alert = alertID >= 0
        ttype = row[indices["type"]]
      except ValueError:
        continue

      if ttype in CASH_TYPES:
        cash_tx = (origID, destID, ttype, 1, amount, datestr, datestr)
        if cash_tx not in cash_tx_set:
          cash_tx_writer.writerow([txID, origID, destID, ttype, 1, amount, datestr, datestr])
          cash_tx_set.add(cash_tx)
      else:
        tx = (origID, destID, ttype, 1, amount, datestr, datestr)
        if tx not in tx_set:
          tx_writer.writerow([txID, origID, destID, ttype, 1, amount, datestr, datestr])
          tx_set.add(tx)
      if is_alert:
        alert_writer.writerow([alertID, txID, origID, destID])

      txID += 1

    rf.close()
    tf.close()
    cf.close()



  def load_fraud_groups(self):
    input_file = self.group_file

    print("Load alert groups: %s" % input_file)
    rf = open(input_file, "r")
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
    fraud_dir = self.fraud_dir

    # create fraud case directory
    if not os.path.isdir(fraud_dir):
      os.makedirs(fraud_dir)
    fname = "alerts.csv"
    fpath = os.path.join(fraud_dir, fname)

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
      except ValueError:
        continue

      if alertID >= 0 and alertID in self.frauds:
        self.frauds[alertID].add_transaction(txID, amount, days, orig, dest, orig, dest)
        txID += 1
    # print txID


    alerts = set()
    count = 0
    frauds = len(self.frauds)
    for fraudID, fg in self.frauds.iteritems():
      # print fraudID, fg.count, fg.subject
      if fg.count == 0:
        continue
      data = fg.get_alerts()
      reason = fg.get_reason()
      escalated = "YES" if (fg.subject is not None) else "NO"
      # if escalated == "YES":
      #   print fraudID
      for row in data:
        acct = str(row[0])
        org_type = "INDIVIDUAL" if self.org_types[acct] == "I" else "COMPANY"
        alerts.add((fraudID, row[0], row[1], row[2], reason, org_type, escalated))
      count += 1
      if count % 100 == 0:
        print count, "/", frauds

    count = 0
    with open(fpath, "w") as wf:
      writer = csv.writer(wf)
      writer.writerow(["ALERT_KEY", "ALERT_TEXT", "ACCOUNT_ID", "CUSTOMER_ID", "EVENT_DATE", "CHECK_NAME", "Organization_Type", "Escalated_To_Case_Investigation"])
      for alert in alerts:
        writer.writerow((count,) + alert)
        count += 1
      # for fraudID, fg in self.frauds.iteritems():
      #   if fg.count == 0:
      #     continue
      #   data = fg.get_alerts()
      #   reason = fg.get_reason()
      #   escalated = "YES" if (fg.subject is not None) else "NO"
      #   for row in data:
      #     acct = str(row[0])
      #     org_type = "INDIVIDUAL" if self.org_types[acct] == "I" else "COMPANY"
      #     writer.writerow([count, fraudID, row[0], row[1], row[2], reason, org_type, escalated])  # escalated or not



  def output_subject_accounts(self):
    subject_ids = set()
    for fg in self.frauds.values():
      subject = fg.subject
      if subject:
        subject_ids.add(subject)

    output_file = self.subject_file
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



