import csv
import sys

output_acct = "nodes.csv"
output_tx = "transactions.csv"

argv = sys.argv
if len(argv) < 3:
  print("Usage: python %s [AcctCSV] [TxCSV]" % argv[0])
  exit(1)

input_acct = argv[1]
input_tx = argv[2]

first_fraud = dict()

wf = open(output_tx, "w")
writer = csv.writer(wf)
writer.writerow(["sourceNodeId", "targetNodeId" , "value", "time"])

with open(input_tx, "r") as rf:
  reader = csv.reader(rf)
  next(reader)
  for row in reader:
    step = row[0]
    ttype = row[1]
    amt = row[2]
    src = row[3]
    dst = row[6]
    isFraud = row[9] == "1"
    if "CASH" not in ttype:
      writer.writerow([src, dst, amt, step])
      if isFraud and src not in first_fraud:
        first_fraud[src] = step

wf.close()


wf = open(output_acct, "w")
writer = csv.writer(wf)
writer.writerow(["nodeid", "isFraud", "init_balance", "fraudStep"])

with open(input_acct, "r") as rf:
  reader = csv.reader(rf)
  next(reader)
  for row in reader:
    acct = row[0]
    init_balance = row[2]
    isFraud = row[8] == "true"
    fraud_frag = 1 if isFraud else 0
    fraud_step = first_fraud[acct] if isFraud and acct in first_fraud else -1
    writer.writerow([acct, fraud_frag, init_balance, fraud_step])

wf.close()

