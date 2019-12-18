"""
Count the number of transactions for each originator and beneficiary bank pair
"""

import os
import sys
import csv
import json
from collections import Counter


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    conf_json = argv[1]
    with open(conf_json, "r") as rf:
        conf_data = json.load(rf)
    sim_name = argv[2] if len(argv) >= 3 else conf_data["general"]["simulation_name"]

    output_dir = os.path.join(conf_data["output"]["directory"], sim_name)
    acct_csv = conf_data["output"]["accounts"]
    tx_csv = conf_data["output"]["transactions"]
    acct_path = os.path.join(output_dir, acct_csv)
    tx_path = os.path.join(output_dir, tx_csv)

    schema_json = os.path.join(conf_data["input"]["directory"], conf_data["input"]["schema"])
    with open(schema_json, "r") as rf:
        schema_data = json.load(rf)
    acct_idx = None
    bank_idx = None
    orig_idx = None
    bene_idx = None
    sar_idx = None
    for i, col in enumerate(schema_data["account"]):
        data_type = col.get("dataType")
        if data_type == "account_id":
            acct_idx = i
        elif data_type == "bank_id":
            bank_idx = i
    for i, col in enumerate(schema_data["transaction"]):
        data_type = col.get("dataType")
        if data_type == "orig_id":
            orig_idx = i
        elif data_type == "dest_id":
            bene_idx = i
        elif data_type == "sar_flag":
            sar_idx = i

    all_bank_set = set()
    acct_bank = dict()
    bank2bank_all = Counter()
    bank2bank_sar = Counter()

    with open(acct_path, "r") as rf:
        print("Loading account list with bank ID")
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            acct = row[acct_idx]
            bank = row[bank_idx]
            acct_bank[acct] = bank
            all_bank_set.add(bank)

    with open(tx_path, "r") as rf:
        print("Loading transaction list")
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            orig = row[orig_idx]
            bene = row[bene_idx]
            is_sar = row[sar_idx].lower() == "true"

            orig_bank = acct_bank[orig]
            bene_bank = acct_bank[bene]
            bank_pair = (orig_bank, bene_bank)
            bank2bank_all[bank_pair] += 1
            if is_sar:
                bank2bank_sar[bank_pair] += 1

    total_num = sum(bank2bank_all.values())
    internal_total_num = sum([num for pair, num in bank2bank_all.items() if pair[0] == pair[1]])
    external_total_num = total_num - internal_total_num
    internal_total_ratio = internal_total_num / total_num * 100
    external_total_ratio = external_total_num / total_num * 100
    internal_sar_num = sum([num for pair, num in bank2bank_sar.items() if pair[0] == pair[1]])
    external_sar_num = sum([num for pair, num in bank2bank_sar.items() if pair[0] != pair[1]])

    print("Internal bank transactions\tTotal: %d (%.2f%%), SAR: %d"
          % (internal_total_num, internal_total_ratio, internal_sar_num))
    print("External bank transactions\tTotal: %d (%.2f%%), SAR: %d"
          % (external_total_num, external_total_ratio, external_sar_num))

    bank_list = sorted(all_bank_set)
    print("Number of total bank-to-bank transactions")
    print("To:\t\t" + "\t".join(bank_list))
    for orig_bank in bank_list:
        bene_bank_count = [bank2bank_all[(orig_bank, bene_bank)] for bene_bank in bank_list]
        print("From %s:\t" % orig_bank + "\t".join([str(n) for n in bene_bank_count]))

    print("Number of SAR bank-to-bank transactions")
    print("To:\t\t" + "\t".join(bank_list))
    for orig_bank in bank_list:
        bene_bank_count = [bank2bank_sar[(orig_bank, bene_bank)] for bene_bank in bank_list]
        print("From %s:\t" % orig_bank + "\t".join([str(n) for n in bene_bank_count]))
