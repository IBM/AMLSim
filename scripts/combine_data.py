"""
Combine AMLSim outputs into a single dataset
"""

import os
import sys
from collections import Counter
import csv
import json
import datetime
from dateutil.parser import parse


class Schema:
    def __init__(self, json_file, base_date):
        self._base_date = base_date

        with open(json_file, "r") as rf:
            self.data = json.load(rf)

            self.acct_num_cols = None
            self.acct_names = list()
            self.acct_defaults = list()
            self.acct_types = list()
            self.acct_name2idx = dict()
            self.acct_id_idx = None
            self.acct_name_idx = None
            self.acct_balance_idx = None
            self.acct_start_idx = None
            self.acct_end_idx = None
            self.acct_sar_idx = None
            self.acct_model_idx = None
            self.acct_bank_idx = None

            self.tx_num_cols = None
            self.tx_names = list()
            self.tx_defaults = list()
            self.tx_types = list()
            self.tx_name2idx = dict()
            self.tx_id_idx = None
            self.tx_time_idx = None
            self.tx_amount_idx = None
            self.tx_type_idx = None
            self.tx_orig_idx = None
            self.tx_dest_idx = None
            self.tx_sar_idx = None
            self.tx_alert_idx = None

            self.alert_acct_num_cols = None
            self.alert_acct_names = list()
            self.alert_acct_defaults = list()
            self.alert_acct_types = list()
            self.alert_acct_name2idx = dict()
            self.alert_acct_alert_idx = None
            self.alert_acct_reason_idx = None
            self.alert_acct_id_idx = None
            self.alert_acct_name_idx = None
            self.alert_acct_sar_idx = None
            self.alert_acct_model_idx = None
            self.alert_acct_schedule_idx = None
            self.alert_acct_bank_idx = None

            self.alert_tx_num_cols = None
            self.alert_tx_names = list()
            self.alert_tx_defaults = list()
            self.alert_tx_types = list()
            self.alert_tx_name2idx = dict()
            self.alert_tx_alert_idx = None
            self.alert_tx_alert_type_idx = None
            self.alert_tx_sar_idx = None
            self.alert_tx_tx_idx = None
            self.alert_tx_orig_idx = None
            self.alert_tx_dest_idx = None
            self.alert_tx_tx_type_idx = None
            self.alert_tx_amount_idx = None
            self.alert_tx_date_idx = None

        self._parse()

    def _parse(self):
        acct_data = self.data["account"]
        tx_data = self.data["transaction"]
        alert_tx_data = self.data["alert_tx"]
        alert_acct_data = self.data["alert_member"]

        self.acct_num_cols = len(acct_data)
        self.tx_num_cols = len(tx_data)
        self.alert_tx_num_cols = len(alert_tx_data)
        self.alert_acct_num_cols = len(alert_acct_data)

        # Account list
        for idx, col in enumerate(acct_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.acct_names.append(name)
            self.acct_defaults.append(default)
            self.acct_types.append(v_type)
            self.acct_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "account_id":
                self.acct_id_idx = idx
            elif d_type == "account_name":
                self.acct_name_idx = idx
            elif d_type == "initial_balance":
                self.acct_balance_idx = idx
            elif d_type == "start_time":
                self.acct_start_idx = idx
            elif d_type == "end_time":
                self.acct_end_idx = idx
            elif d_type == "sar_flag":
                self.acct_sar_idx = idx
            elif d_type == "model_id":
                self.acct_model_idx = idx
            elif d_type == "bank_id":
                self.acct_bank_idx = idx

        # Transaction list
        for idx, col in enumerate(tx_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.tx_names.append(name)
            self.tx_defaults.append(default)
            self.tx_types.append(v_type)
            self.tx_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "transaction_id":
                self.tx_id_idx = idx
            elif d_type == "timestamp":
                self.tx_time_idx = idx
            elif d_type == "amount":
                self.tx_amount_idx = idx
            elif d_type == "transaction_type":
                self.tx_type_idx = idx
            elif d_type == "orig_id":
                self.tx_orig_idx = idx
            elif d_type == "dest_id":
                self.tx_dest_idx = idx
            elif d_type == "sar_flag":
                self.tx_sar_idx = idx
            elif d_type == "alert_id":
                self.tx_alert_idx = idx

        # Alert member list
        for idx, col in enumerate(alert_acct_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.alert_acct_names.append(name)
            self.alert_acct_defaults.append(default)
            self.alert_acct_types.append(v_type)
            self.alert_acct_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "alert_id":
                self.alert_acct_alert_idx = idx
            elif d_type == "alert_type":
                self.alert_acct_reason_idx = idx
            elif d_type == "account_id":
                self.alert_acct_id_idx = idx
            elif d_type == "account_name":
                self.alert_acct_name_idx = idx
            elif d_type == "sar_flag":
                self.alert_acct_sar_idx = idx
            elif d_type == "model_id":
                self.alert_acct_model_idx = idx
            elif d_type == "schedule_id":
                self.alert_acct_schedule_idx = idx
            elif d_type == "bank_id":
                self.alert_acct_bank_idx = idx

        # Alert transaction list
        for idx, col in enumerate(alert_tx_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.alert_tx_names.append(name)
            self.alert_tx_defaults.append(default)
            self.alert_tx_types.append(v_type)
            self.alert_tx_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "alert_id":
                self.alert_tx_alert_idx = idx
            elif d_type == "alert_type":
                self.alert_tx_alert_type_idx = idx
            elif d_type == "sar_flag":
                self.alert_tx_sar_idx = idx
            elif d_type == "transaction_id":
                self.alert_tx_tx_idx = idx
            elif d_type == "orig_id":
                self.alert_tx_orig_idx = idx
            elif d_type == "dest_id":
                self.alert_tx_dest_idx = idx
            elif d_type == "transaction_type":
                self.alert_tx_tx_type_idx = idx
            elif d_type == "amount":
                self.alert_tx_amount_idx = idx
            elif d_type == "timestamp":
                self.alert_tx_date_idx = idx

    def days2date(self, _days):
        """Get date as ISO 8601 format from days from the "base_date". If failed, return an empty string.
        :param _days: Days from the "base_date"
        :return: Date as ISO 8601 format
        """
        try:
            num_days = int(_days)
        except ValueError:
            return ""
        dt = self._base_date + datetime.timedelta(num_days)
        return dt.isoformat() + "Z"  # UTC

    def get_acct_row(self, acct_id, acct_name, init_balance, start_str, end_str, is_sar, model_id, bank_id, **attr):
        row = list(self.acct_defaults)
        row[self.acct_id_idx] = acct_id
        row[self.acct_name_idx] = acct_name
        row[self.acct_balance_idx] = init_balance
        try:
            start = int(start_str)
            if start >= 0:
                row[self.acct_start_idx] = start
        except ValueError:  # If failed, keep the default value
            pass

        try:
            end = int(end_str)
            if end > 0:
                row[self.acct_end_idx] = end
        except ValueError:  # If failed, keep the default value
            pass

        row[self.acct_sar_idx] = is_sar
        row[self.acct_model_idx] = model_id
        row[self.acct_bank_idx] = bank_id

        for name, value in attr.items():
            if name in self.acct_name2idx:
                idx = self.acct_name2idx[name]
                row[idx] = value

        return row

    def get_tx_row(self, _tx_id, _timestamp, _amount, _tx_type, _orig, _dest, _is_sar, _alert_id, **attr):
        row = list(self.tx_defaults)
        row[self.tx_id_idx] = _tx_id
        row[self.tx_time_idx] = _timestamp
        row[self.tx_amount_idx] = _amount
        row[self.tx_type_idx] = _tx_type
        row[self.tx_orig_idx] = _orig
        row[self.tx_dest_idx] = _dest
        row[self.tx_sar_idx] = _is_sar
        row[self.tx_alert_idx] = _alert_id

        for name, value in attr.items():
            if name in self.tx_name2idx:
                idx = self.tx_name2idx[name]
                row[idx] = value

        return row

    def get_alert_acct_row(self, _alert_id, _reason, _acct_id, _acct_name, _is_sar,
                           _model_id, _schedule_id, _bank_id, **attr):
        row = list(self.alert_acct_defaults)
        row[self.alert_acct_alert_idx] = _alert_id
        row[self.alert_acct_reason_idx] = _reason
        row[self.alert_acct_id_idx] = _acct_id
        row[self.alert_acct_name_idx] = _acct_name
        row[self.alert_acct_sar_idx] = _is_sar
        row[self.alert_acct_model_idx] = _model_id
        row[self.alert_acct_schedule_idx] = _schedule_id
        row[self.alert_acct_bank_idx] = _bank_id

        for name, value in attr.items():
            if name in self.alert_acct_name2idx:
                idx = self.alert_acct_name2idx[name]
                row[idx] = value

        return row

    def get_alert_tx_row(self, _alert_id, _alert_type, _is_sar, _tx_id, _orig, _dest,
                         _tx_type, _amount, _timestamp, **attr):
        row = list(self.alert_tx_defaults)
        row[self.alert_tx_alert_idx] = _alert_id
        row[self.alert_tx_alert_type_idx] = _alert_type
        row[self.alert_tx_sar_idx] = _is_sar
        row[self.alert_tx_tx_idx] = _tx_id
        row[self.alert_tx_orig_idx] = _orig
        row[self.alert_tx_dest_idx] = _dest
        row[self.alert_tx_tx_type_idx] = _tx_type
        row[self.alert_tx_amount_idx] = _amount
        row[self.alert_tx_date_idx] = _timestamp

        for name, value in attr.items():
            if name in self.alert_tx_name2idx:
                idx = self.alert_tx_name2idx[name]
                row[idx] = value

        return row


def load_output_conf_json(conf_json):
    with open(conf_json, "r") as rf:
        conf = json.load(rf)

    out_dir = os.path.join(conf["output"]["directory"], conf["general"]["simulation_name"])
    acct_file = conf["output"]["accounts"]
    tx_file = conf["output"]["transactions"]
    cash_file = conf["output"]["cash_transactions"]
    alert_acct_file = conf["output"]["alert_members"]
    alert_tx_file = conf["output"]["alert_transactions"]

    acct_path = os.path.join(out_dir, acct_file)
    tx_path = os.path.join(out_dir, tx_file)
    cash_path = os.path.join(out_dir, cash_file)
    alert_acct_path = os.path.join(out_dir, alert_acct_file)
    alert_tx_path = os.path.join(out_dir, alert_tx_file)

    schema_path = os.path.join(conf["input"]["directory"], conf["input"]["schema"])
    base_date = parse(conf["general"]["base_date"])
    schema = Schema(schema_path, base_date)

    return acct_path, tx_path, cash_path, alert_acct_path, alert_tx_path, schema


def load_input_conf_json(conf_json):
    with open(conf_json, "r") as rf:
        conf = json.load(rf)

    in_dir = conf["input"]["directory"]
    acct_file = conf["input"]["accounts"]
    alert_file = conf["input"]["alert_patterns"]
    deg_file = conf["input"]["degree"]
    tx_file = conf["input"]["transaction_type"]

    acct_path = os.path.join(in_dir, acct_file)
    alert_path = os.path.join(in_dir, alert_file)
    deg_path = os.path.join(in_dir, deg_file)
    tx_path = os.path.join(in_dir, tx_file)

    return acct_path, alert_path, deg_path, tx_path


class Combiner:

    def __init__(self, out_conf_json, out_sim_name=None):
        self.last_acct_id = 0
        self.last_tx_id = 0
        self.last_alert_id = 0

        with open(out_conf_json, "r") as rf:
            out_conf = json.load(rf)

        in_dir = out_conf["input"]["directory"]
        os.makedirs(in_dir, exist_ok=True)

        self.in_acct_path, self.in_alert_path, self.in_deg_path, self.in_tx_path = load_input_conf_json(out_conf_json)
        with open(self.in_acct_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(["count", "min_balance", "max_balance", "start_day", "end_day", 
                             "country", "business_type", "model", "bank_id"])

        with open(self.in_alert_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(["count", "type", "schedule_id", "min_accounts", "max_accounts",
                             "min_amount", "max_amount", "min_period", "max_period", "bank_id", "is_sar"])

        with open(self.in_tx_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(["Type", "Frequency"])

        self.in_deg = Counter()
        self.out_deg = Counter()

        if out_sim_name is None:
            out_sim_name = out_conf["general"]["simulation_name"]

        out_dir = os.path.join(out_conf["output"]["directory"], out_sim_name)
        os.makedirs(out_dir, exist_ok=True)

        self.out_acct_path, self.out_tx_path, self.out_cash_path, \
        self.out_alert_acct_path, self.out_alert_tx_path, self.out_schema = load_output_conf_json(out_conf_json)

        # Add headers
        with open(self.out_acct_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(self.out_schema.acct_names)

        with open(self.out_tx_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(self.out_schema.tx_names)

        with open(self.out_cash_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(self.out_schema.tx_names)

        with open(self.out_alert_acct_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(self.out_schema.alert_acct_names)

        with open(self.out_alert_tx_path, "w") as wf:
            writer = csv.writer(wf, lineterminator='\n')
            writer.writerow(self.out_schema.alert_tx_names)

    def append_input_data(self, in_conf_json):
        in_acct_path, in_alert_path, in_deg_path, in_tx_path = load_input_conf_json(in_conf_json)

        wf = open(self.in_acct_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_acct_path, "r")
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            writer.writerow(row)
        rf.close()
        wf.close()

        wf = open(self.in_alert_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_alert_path, "r")
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            writer.writerow(row)
        rf.close()
        wf.close()

        with open(in_deg_path, "r") as rf:
            reader = csv.reader(rf)
            next(reader)
            for row in reader:
                deg = int(row[0])
                in_num = int(row[1])
                out_num = int(row[2])
                self.in_deg[deg] += in_num
                self.out_deg[deg] += out_num

        wf = open(self.in_tx_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_tx_path, "r")
        reader = csv.reader(rf)
        next(reader)
        for row in reader:
            writer.writerow(row)
        rf.close()
        wf.close()

    def write_degrees(self):
        degrees = sorted(set(self.in_deg.keys()) | set(self.out_deg.keys()))

        with open(self.in_deg_path, "w") as wf:
            writer = csv.writer(wf)
            writer.writerow(["Count", "In-degree", "Out-degree"])
            for d in degrees:
                writer.writerow([d, self.in_deg[d], self.out_deg[d]])

    def append_output_data(self, in_conf_json):
        in_acct_path, in_tx_path, in_cash_path, in_alert_acct_path, in_alert_tx_path, in_schema = \
            load_output_conf_json(in_conf_json)

        max_acct_id = 0
        max_tx_id = 0
        max_alert_id = 0

        # Convert account list
        wf = open(self.out_acct_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_acct_path, "r")
        reader = csv.reader(rf)

        id_idx = in_schema.acct_id_idx
        name_idx = in_schema.acct_name_idx
        balance_idx = in_schema.acct_balance_idx
        start_idx = in_schema.acct_start_idx
        end_idx = in_schema.acct_end_idx
        sar_idx = in_schema.acct_sar_idx
        model_idx = in_schema.acct_model_idx
        bank_idx = in_schema.acct_bank_idx

        next(reader)
        for row in reader:
            acct_id = int(row[id_idx]) + self.last_acct_id
            max_acct_id = max(max_acct_id, acct_id)

            acct_name = row[name_idx]
            balance = row[balance_idx]
            start = row[start_idx]
            end = row[end_idx]
            is_sar = row[sar_idx]
            model = row[model_idx]
            bank_id = row[bank_idx]

            output_row = self.out_schema.get_acct_row(acct_id, acct_name, balance, start, end, is_sar, model, bank_id)
            writer.writerow(output_row)

        rf.close()
        wf.close()

        # Convert transaction list
        id_idx = in_schema.tx_id_idx
        orig_idx = in_schema.tx_orig_idx
        bene_idx = in_schema.tx_dest_idx
        date_idx = in_schema.tx_time_idx
        amt_idx = in_schema.tx_amount_idx
        type_idx = in_schema.tx_type_idx
        sar_idx = in_schema.tx_sar_idx
        alert_idx = in_schema.tx_alert_idx

        wf = open(self.out_tx_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_tx_path, "r")
        reader = csv.reader(rf)

        next(reader)
        for row in reader:
            tx_id = int(row[id_idx]) + self.last_tx_id
            max_tx_id = max(max_tx_id, tx_id)

            orig_id = int(row[orig_idx]) + self.last_acct_id
            bene_id = int(row[bene_idx]) + self.last_acct_id
            date = row[date_idx]
            amount = row[amt_idx]
            tx_type = row[type_idx]
            is_sar = row[sar_idx]
            alert_id = int(row[alert_idx])
            if alert_id >= 0 and self.last_alert_id is not None:
                alert_id += self.last_alert_id
            max_alert_id = max(max_alert_id, alert_id)

            output_row = self.out_schema.get_tx_row(tx_id, date, amount, tx_type, orig_id, bene_id, is_sar, alert_id)
            writer.writerow(output_row)

        rf.close()
        wf.close()

        # Convert cash transaction list
        wf = open(self.out_cash_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_cash_path, "r")
        reader = csv.reader(rf)

        next(reader)
        for row in reader:
            tx_id = int(row[id_idx]) + self.last_tx_id
            max_tx_id = max(max_tx_id, tx_id)

            orig_id = int(row[orig_idx]) + self.last_acct_id
            bene_id = int(row[bene_idx]) + self.last_acct_id
            date = row[date_idx]
            amount = row[amt_idx]
            tx_type = row[type_idx]
            is_sar = row[sar_idx]
            alert_id = int(row[alert_idx])
            if alert_id >= 0 and self.last_alert_id is not None:
                alert_id += self.last_alert_id
            max_alert_id = max(max_alert_id, alert_id)

            output_row = self.out_schema.get_tx_row(tx_id, date, amount, tx_type, orig_id, bene_id, is_sar, alert_id)
            writer.writerow(output_row)

        rf.close()
        wf.close()

        # Convert alert member list
        alert_idx = in_schema.alert_acct_alert_idx
        acct_idx = in_schema.alert_acct_id_idx
        reason_idx = in_schema.alert_acct_reason_idx
        sar_idx = in_schema.alert_acct_sar_idx
        model_idx = in_schema.alert_acct_model_idx
        schedule_idx = in_schema.alert_acct_schedule_idx
        bank_idx = in_schema.alert_acct_bank_idx

        wf = open(self.out_alert_acct_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_alert_acct_path, "r")
        reader = csv.reader(rf)

        next(reader)
        for row in reader:
            if self.last_alert_id is None:
                writer.writerow(self.out_schema.alert_acct_names)
                self.last_alert_id = 0

            alert_id = int(row[alert_idx]) + self.last_alert_id
            reason = row[reason_idx]
            acct_id = int(row[acct_idx]) + self.last_acct_id
            is_sar = row[sar_idx]
            model = row[model_idx]
            schedule = row[schedule_idx]
            bank_id = row[bank_idx]
            output_row = self.out_schema.get_alert_acct_row(alert_id, reason, acct_id, acct_id, is_sar, model,
                                                            schedule, bank_id)
            writer.writerow(output_row)

        rf.close()
        wf.close()

        # Convert alert transaction list
        alert_idx = in_schema.alert_tx_alert_idx
        type_idx = in_schema.alert_tx_alert_type_idx
        sar_idx = in_schema.alert_tx_sar_idx
        tx_idx = in_schema.alert_tx_tx_idx
        orig_idx = in_schema.alert_tx_orig_idx
        bene_idx = in_schema.alert_tx_dest_idx
        tx_type_idx = in_schema.alert_tx_tx_type_idx
        amt_idx = in_schema.alert_tx_amount_idx
        date_idx = in_schema.alert_tx_date_idx

        wf = open(self.out_alert_tx_path, "a")
        writer = csv.writer(wf, lineterminator='\n')
        rf = open(in_alert_tx_path, "r")
        reader = csv.reader(rf)

        next(reader)
        for row in reader:
            alert_id = int(row[alert_idx]) + self.last_alert_id
            max_alert_id = max(max_alert_id, alert_id)

            alert_type = row[type_idx]
            is_sar = row[sar_idx]
            tx_id = int(row[tx_idx]) + self.last_tx_id
            orig_id = int(row[orig_idx]) + self.last_acct_id
            bene_id = int(row[bene_idx]) + self.last_acct_id
            tx_type = row[tx_type_idx]
            amount = row[amt_idx]
            date = row[date_idx]

            output_row = self.out_schema.get_alert_tx_row(alert_id, alert_type, is_sar, tx_id, orig_id, bene_id,
                                                          tx_type, amount, date)
            writer.writerow(output_row)

        rf.close()
        wf.close()

        self.last_acct_id = (max_acct_id + 1)
        self.last_tx_id = (max_tx_id + 1)
        self.last_alert_id = (max_alert_id + 1)


if __name__ == "__main__":
    argv = sys.argv
    argc = len(argv)
    if argc < 4 or argc % 2 == 0:
        print("Usage: python3 %s [OutputConfJSON] [OutputSimName] ([InputConfJSON] [Repetitions]...)" % argv[0])
        exit(1)

    _conf_json = argv[1]
    _sim_name = argv[2]
    com = Combiner(_conf_json, _sim_name)
    for i in range(3, argc, 2):
        _in_conf_json = argv[i]
        _rep = int(argv[i+1])
        for j in range(_rep):
            print("Loading %s: %d/%d" % (_in_conf_json, j, _rep))
            com.append_input_data(_in_conf_json)
            com.append_output_data(_in_conf_json)
    com.write_degrees()
