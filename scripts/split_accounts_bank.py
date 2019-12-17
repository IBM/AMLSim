"""
Split account-based CSV list by bank ID
"""

import os
import sys
import csv
from collections import defaultdict


if __name__ == "__main__":
    argv = sys.argv
    if len(argv) < 3:
        print("Usage: python3 %s [InputCSV] [AccountCSV]" % argv[0])
        exit(1)

    input_csv = argv[1]
    acct_csv = argv[2]

    work_dir = os.path.dirname(input_csv)
    base_path, _ = os.path.splitext(input_csv)

    acct_bank = dict()
    bank_acct = defaultdict(set)

    with open(acct_csv, "r") as rf:
        reader = csv.reader(rf)
        header = next(reader)
        col_idx = {name: i for i, name in enumerate(header)}
        acct_idx = col_idx["acct_id"]
        bank_idx = col_idx["bank_id"]

        for row in reader:
            acct_id = row[acct_idx]
            bank_id = row[bank_idx]
            acct_bank[acct_id] = bank_id
            bank_acct[bank_id].add(acct_id)
    print("Loaded account list CSV file %s" % acct_csv)

    for bank_id, accts in bank_acct.items():
        output_csv = base_path + "." + bank_id + ".csv"
        wf = open(output_csv, "w")
        writer = csv.writer(wf)

        with open(input_csv, "r") as rf:
            reader = csv.reader(rf)
            header = next(reader)
            writer.writerow(header)

            for row in reader:
                acct_id = row[0]
                if acct_id in accts:
                    writer.writerow(row)
        wf.close()
        print("Extracted %d accounts in the bank %s from %s to %s" % (len(accts), bank_id, input_csv, output_csv))
