import csv
import json
import sys
import os
import datetime
from dateutil.parser import parse
from random import random


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

    def add_transaction(self, txID, amount, days, origAcct, destAcct, origName, destName, attr):
        self.transactions[txID] = (amount, days, origAcct, destAcct, origName, destName, attr)
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
        for txid, tx in self.transactions.items():
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
        for tx_id, tx in self.transactions.items():
            origAcct = str(tx[2])
            origName = str(tx[4])
            date = days_to_date(tx[1])
            rows.append((origAcct, origName, date))
        return rows


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
            self.acct_fraud_idx = None
            self.acct_model_idx = None

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
            self.tx_fraud_idx = None
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
            self.alert_acct_subject_idx = None
            self.alert_acct_model_idx = None
            self.alert_acct_schedule_idx = None

            self.alert_tx_num_cols = None
            self.alert_tx_names = list()
            self.alert_tx_defaults = list()
            self.alert_tx_types = list()
            self.alert_tx_name2idx = dict()
            self.alert_tx_id_idx = None
            self.alert_tx_type_idx = None
            self.alert_tx_fraud_idx = None
            self.alert_tx_idx = None
            self.alert_tx_orig_idx = None
            self.alert_tx_dest_idx = None
            self.alert_tx_tx_type_idx = None
            self.alert_tx_amount_idx = None
            self.alert_tx_time_idx = None

            self.party_ind_num_cols = None
            self.party_ind_names = list()
            self.party_ind_defaults = list()
            self.party_ind_types = list()
            self.party_ind_name2idx = dict()
            self.party_ind_id_idx = None

            self.party_org_num_cols = None
            self.party_org_names = list()
            self.party_org_defaults = list()
            self.party_org_types = list()
            self.party_org_name2idx = dict()
            self.party_org_id_idx = None

            self.acct_party_num_cols = None
            self.acct_party_names = list()
            self.acct_party_defaults = list()
            self.acct_party_types = list()
            self.acct_party_name2idx = dict()
            self.acct_party_mapping_idx = None
            self.acct_party_acct_idx = None
            self.acct_party_party_idx = None

            self.party_party_num_cols = None
            self.party_party_names = list()
            self.party_party_defaults = list()
            self.party_party_types = list()
            self.party_party_name2idx = dict()
            self.party_party_ref_idx = None
            self.party_party_first_idx = None
            self.party_party_second_idx = None
        self._parse()

    def _parse(self):
        acct_data = self.data["account"]
        tx_data = self.data["transaction"]
        alert_tx_data = self.data["alert_tx"]
        alert_acct_data = self.data["alert_member"]
        party_ind_data = self.data["party_individual"]
        party_org_data = self.data["party_organization"]
        acct_party_data = self.data["account_mapping"]
        party_party_data = self.data["resolved_entities"]

        self.acct_num_cols = len(acct_data)
        self.tx_num_cols = len(tx_data)
        self.alert_tx_num_cols = len(alert_tx_data)
        self.alert_acct_num_cols = len(alert_acct_data)
        self.party_ind_num_cols = len(party_ind_data)
        self.party_org_num_cols = len(party_org_data)
        self.acct_party_num_cols = len(acct_party_data)
        self.party_party_num_cols = len(party_party_data)

        # Account list
        for idx, col in enumerate(acct_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.acct_names.append(name)
            self.acct_defaults.append(default)
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
            default = col.get("defaultValue", "")

            self.tx_names.append(name)
            self.tx_defaults.append(default)
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

        # Alert member list
        for idx, col in enumerate(alert_acct_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.alert_acct_names.append(name)
            self.alert_acct_defaults.append(default)
            self.alert_acct_types.append(vtype)
            self.alert_acct_name2idx[name] = idx

            if dtype is None:
                continue
            if dtype == "alert_id":
                self.alert_acct_alert_idx = idx
            elif dtype == "alert_type":
                self.alert_acct_reason_idx = idx
            elif dtype == "account_id":
                self.alert_acct_id_idx = idx
            elif dtype == "account_name":
                self.alert_acct_name_idx = idx
            elif dtype == "subject_flag":
                self.alert_acct_subject_idx = idx
            elif dtype == "model_id":
                self.alert_acct_model_idx = idx
            elif dtype == "schedule_id":
                self.alert_acct_schedule_idx = idx

        # Alert transaction list
        for idx, col in enumerate(alert_tx_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.alert_tx_names.append(name)
            self.alert_tx_defaults.append(default)
            self.alert_tx_types.append(vtype)
            self.alert_tx_name2idx[name] = idx

            if dtype is None:
                continue
            if dtype == "alert_id":
                self.alert_tx_id_idx = idx
            elif dtype == "alert_type":
                self.alert_tx_type_idx = idx
            elif dtype == "fraud_flag":
                self.alert_tx_fraud_idx = idx
            elif dtype == "transaction_id":
                self.alert_tx_idx = idx
            elif dtype == "orig_id":
                self.alert_tx_orig_idx = idx
            elif dtype == "dest_id":
                self.alert_tx_dest_idx = idx
            elif dtype == "transaction_type":
                self.alert_tx_tx_type_idx = idx
            elif dtype == "amount":
                self.alert_tx_amount_idx = idx
            elif dtype == "timestamp":
                self.alert_tx_time_idx = idx

        # Individual party list
        for idx, col in enumerate(party_ind_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.party_ind_names.append(name)
            self.party_ind_defaults.append(default)
            self.party_ind_types.append(vtype)
            self.party_ind_name2idx[name] = idx

            if dtype is None:
                continue
            if dtype == "party_id":
                self.party_ind_id_idx = idx

        # Individual party list
        for idx, col in enumerate(party_org_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.party_org_names.append(name)
            self.party_org_defaults.append(default)
            self.party_org_types.append(vtype)
            self.party_org_name2idx[name] = idx

            if dtype is None:
                continue
            if dtype == "party_id":
                self.party_org_id_idx = idx

        # Account-Party list
        for idx, col in enumerate(acct_party_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.acct_party_names.append(name)
            self.acct_party_defaults.append(default)
            self.acct_party_types.append(vtype)
            self.acct_party_name2idx[name] = idx

            if dtype is None:
                continue
            if dtype == "mapping_id":
                self.acct_party_mapping_idx = idx
            elif dtype == "account_id":
                self.acct_party_acct_idx = idx
            elif dtype == "party_id":
                self.acct_party_party_idx = idx

        # Party-Party list
        for idx, col in enumerate(party_party_data):
            name = col["name"]
            vtype = col.get("valueType", "string")
            dtype = col.get("dataType")
            default = col.get("defaultValue", "")

            self.party_party_names.append(name)
            self.party_party_defaults.append(default)
            self.party_party_types.append(vtype)
            self.party_party_name2idx[name] = idx

            if dtype is None:
                continue
            if dtype == "ref_id":
                self.party_party_ref_idx = idx
            elif dtype == "first_id":
                self.party_party_first_idx = idx
            elif dtype == "second_id":
                self.party_party_second_idx = idx

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

    def get_acct_row(self, acct_id, acct_name, init_balance, start_str, end_str, is_fraud, model_id, **attr):
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

        row[self.acct_fraud_idx] = is_fraud
        row[self.acct_model_idx] = model_id

        for name, value in attr.items():
            if name in self.acct_name2idx:
                idx = self.acct_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.acct_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_tx_row(self, _tx_id, _timestamp, _amount, _tx_type, _orig, _dest, _is_fraud, _alert_id, **attr):
        row = list(self.tx_defaults)
        row[self.tx_id_idx] = _tx_id
        row[self.tx_time_idx] = _timestamp
        row[self.tx_amount_idx] = _amount
        row[self.tx_type_idx] = _tx_type
        row[self.tx_orig_idx] = _orig
        row[self.tx_dest_idx] = _dest
        row[self.tx_fraud_idx] = _is_fraud
        row[self.tx_alert_idx] = _alert_id

        for name, value in attr.items():
            if name in self.tx_name2idx:
                idx = self.tx_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.tx_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_alert_acct_row(self, _alert_id, _reason, _acct_id, _acct_name, _is_subject, _model_id, _schedule_id,
                           **attr):
        row = list(self.alert_acct_defaults)
        row[self.alert_acct_alert_idx] = _alert_id
        row[self.alert_acct_reason_idx] = _reason
        row[self.alert_acct_id_idx] = _acct_id
        row[self.alert_acct_name_idx] = _acct_name
        row[self.alert_acct_subject_idx] = _is_subject
        row[self.alert_acct_model_idx] = _model_id
        row[self.alert_acct_schedule_idx] = _schedule_id

        for name, value in attr.items():
            if name in self.alert_acct_name2idx:
                idx = self.alert_acct_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.alert_acct_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_alert_tx_row(self, _alert_id, _alert_type, _is_fraud, _tx_id, _orig, _dest, _tx_type, _amount, _timestamp,
                         **attr):
        row = list(self.alert_tx_defaults)
        row[self.alert_tx_id_idx] = _alert_id
        row[self.alert_tx_type_idx] = _alert_type
        row[self.alert_tx_fraud_idx] = _is_fraud
        row[self.alert_tx_idx] = _tx_id
        row[self.alert_tx_orig_idx] = _orig
        row[self.alert_tx_dest_idx] = _dest
        row[self.alert_tx_tx_type_idx] = _tx_type
        row[self.alert_tx_amount_idx] = _amount
        row[self.alert_tx_time_idx] = _timestamp

        for name, value in attr.items():
            if name in self.alert_tx_name2idx:
                idx = self.alert_tx_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.alert_tx_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_party_ind_row(self, _party_id, **attr):
        row = list(self.party_ind_defaults)
        row[self.party_ind_id_idx] = _party_id

        for name, value in attr.items():
            if name in self.party_ind_name2idx:
                idx = self.party_ind_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.party_ind_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_party_org_row(self, _party_id, **attr):
        row = list(self.party_org_defaults)
        row[self.party_org_id_idx] = _party_id

        for name, value in attr.items():
            if name in self.party_org_name2idx:
                idx = self.party_org_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.party_org_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_acct_party_row(self, _mapping_id, _acct_id, _party_id, **attr):
        row = list(self.acct_party_defaults)
        row[self.acct_party_mapping_idx] = _mapping_id
        row[self.acct_party_acct_idx] = _acct_id
        row[self.acct_party_party_idx] = _party_id

        for name, value in attr.items():
            if name in self.acct_party_name2idx:
                idx = self.acct_party_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.acct_party_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_party_party_row(self, _ref_id, _first_id, _second_id, **attr):
        row = list(self.party_party_defaults)
        row[self.party_party_ref_idx] = _ref_id
        row[self.party_party_first_idx] = _first_id
        row[self.party_party_second_idx] = _second_id

        for name, value in attr.items():
            if name in self.party_party_name2idx:
                idx = self.party_party_name2idx[name]
                row[idx] = value

        for idx, vtype in enumerate(self.party_party_types):
            if vtype == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row


class LogConverter:

    def __init__(self, conf_file):
        self.frauds = dict()
        self.org_types = dict()  # ID, organization type

        with open(conf_file, "r") as rf:
            conf = json.load(rf)

        general_conf = conf["general"]
        input_conf = conf["temporal"]
        output_conf = conf["output"]

        self.sim_name = general_conf["simulation_name"]
        self.input_dir = input_conf["directory"]
        self.work_dir = output_conf["directory"]
        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)

        param_dir = conf["input"]["directory"]
        schema_file = output_conf["schema"]
        base_date_str = general_conf["base_date"]
        base_date = parse(base_date_str)
        self.schema = Schema(os.path.join(param_dir, schema_file), base_date)

        self.log_file = os.path.join(self.input_dir, self.sim_name, output_conf["transaction_log"])
        self.in_acct_file = input_conf["accounts"]
        self.group_file = input_conf["alert_members"]

        self.out_acct_file = output_conf["accounts"]
        self.tx_file = output_conf["transactions"]
        self.cash_tx_file = output_conf["cash_transactions"]
        self.fraud_file = output_conf["frauds"]
        self.alert_tx_file = output_conf["alert_transactions"]
        self.alert_acct_file = output_conf["alert_members"]

        self.party_individual_file = output_conf["party_individuals"]
        self.party_organization_file = output_conf["party_organizations"]
        self.account_mapping_file = output_conf["account_mapping"]
        self.resolved_entities_file = output_conf["resolved_entities"]

    def convert_acct_tx(self):
        print("Convert transaction list from %s to %s, %s and %s" % (
        self.log_file, self.tx_file, self.cash_tx_file, self.alert_tx_file))

        af = open(os.path.join(self.input_dir, self.in_acct_file), "r")
        rf = open(self.log_file, "r")

        of = open(os.path.join(self.work_dir, self.out_acct_file), "w")
        tf = open(os.path.join(self.work_dir, self.tx_file), "w")
        cf = open(os.path.join(self.work_dir, self.cash_tx_file), "w")
        lf = open(os.path.join(self.work_dir, self.alert_tx_file), "w")

        pif = open(os.path.join(self.work_dir, self.party_individual_file), "w")
        pof = open(os.path.join(self.work_dir, self.party_organization_file), "w")
        amf = open(os.path.join(self.work_dir, self.account_mapping_file), "w")
        ref = open(os.path.join(self.work_dir, self.resolved_entities_file), "w")

        reader = csv.reader(af)
        acct_writer = csv.writer(of)
        acct_writer.writerow(self.schema.acct_names)  # write header

        pi_writer = csv.writer(pif)
        pi_writer.writerow(self.schema.party_ind_names)
        po_writer = csv.writer(pof)
        po_writer.writerow(self.schema.party_org_names)
        am_writer = csv.writer(amf)
        am_writer.writerow(self.schema.acct_party_names)
        re_writer = csv.writer(ref)
        re_writer.writerow(self.schema.party_party_names)

        header = next(reader)
        indices = {name: index for index, name in enumerate(header)}
        id_idx = indices["ACCOUNT_ID"]
        name_idx = indices["CUSTOMER_ID"]
        balance_idx = indices["INIT_BALANCE"]
        start_idx = indices["START_DATE"]
        end_idx = indices["END_DATE"]
        type_idx = indices["ACCOUNT_TYPE"]
        fraud_idx = indices["IS_FRAUD"]
        model_idx = indices["TX_BEHAVIOR_ID"]

        mapping_id = 1  # Mapping ID for account-alert mapping list

        for row in reader:
            # Write an account row
            acct_id = row[id_idx]
            acct_name = row[name_idx]
            balance = row[balance_idx]
            start = row[start_idx]
            end = row[end_idx]
            acct_type = row[type_idx]
            acct_fraud = row[fraud_idx]
            acct_model = row[model_idx]
            attr = {name: row[index] for name, index in indices.items()}
            output_row = self.schema.get_acct_row(acct_id, acct_name, balance, start, end, acct_fraud, acct_model,
                                                  **attr)
            acct_writer.writerow(output_row)
            self.org_types[acct_id] = acct_type

            # Write a party row per account
            is_individual = random() >= 0.5  # 50%: individual, 50%: organization
            party_id = str(acct_id)
            if is_individual:  # Individual
                output_row = self.schema.get_party_ind_row(party_id)
                pi_writer.writerow(output_row)
            else:
                output_row = self.schema.get_party_org_row(party_id)
                po_writer.writerow(output_row)

            # Write account-party mapping row
            output_row = self.schema.get_acct_party_row(mapping_id, acct_id, party_id)
            am_writer.writerow(output_row)
            mapping_id += 1

        af.close()
        pif.close()
        pof.close()
        amf.close()
        ref.close()

        tx_set = set()
        cash_tx_set = set()

        reader = csv.reader(rf)
        tx_writer = csv.writer(tf)
        cash_tx_writer = csv.writer(cf)
        alert_tx_writer = csv.writer(lf)

        header = next(reader)
        indices = {name: index for index, name in enumerate(header)}
        num_columns = len(header)

        tx_header = self.schema.tx_names
        alert_header = self.schema.alert_tx_names
        tx_writer.writerow(tx_header)
        cash_tx_writer.writerow(tx_header)
        alert_tx_writer.writerow(alert_header)

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
                date_str = str(days)  # days_to_date(days)

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

            attr = {name: row[index] for name, index in indices.items()}
            if ttype in CASH_TYPES:
                cash_tx = (origID, destID, ttype, amount, date_str)
                if cash_tx not in cash_tx_set:
                    # cash_tx_writer.writerow([txID, origID, destID, ttype, amount, date_str, is_fraud, alertID])
                    cash_tx_set.add(cash_tx)
                    output_row = self.schema.get_tx_row(txID, date_str, amount, ttype, origID, destID, is_fraud,
                                                        alertID, **attr)
                    cash_tx_writer.writerow(output_row)
            else:
                tx = (origID, destID, ttype, amount, date_str)
                if tx not in tx_set:
                    # tx_writer.writerow([txID, origID, destID, ttype, amount, date_str, is_fraud, alertID])
                    output_row = self.schema.get_tx_row(txID, date_str, amount, ttype, origID, destID, is_fraud,
                                                        alertID, **attr)
                    tx_writer.writerow(output_row)
                    tx_set.add(tx)
            if is_alert:
                alert_type = self.frauds.get(alertID).get_reason()
                # alert_tx_writer.writerow([alertID, alert_type, is_fraud, txID, origID, destID, ttype, amount, date_str])
                alert_row = self.schema.get_alert_tx_row(alertID, alert_type, is_fraud, txID, origID, destID, ttype,
                                                         amount, date_str, **attr)
                alert_tx_writer.writerow(alert_row)

            txID += 1

        rf.close()
        tf.close()
        cf.close()
        lf.close()

    def convert_alert_members(self):
        input_file = self.group_file
        output_file = self.alert_acct_file

        print("Load alert groups: %s" % input_file)
        rf = open(os.path.join(self.input_dir, input_file), "r")
        wf = open(os.path.join(self.work_dir, output_file), "w")
        reader = csv.reader(rf)
        header = next(reader)
        indices = {name: index for index, name in enumerate(header)}

        writer = csv.writer(wf)
        header = self.schema.alert_acct_names
        writer.writerow(header)

        for row in reader:
            reason = row[indices["reason"]]
            alertID = int(row[indices["alertID"]])
            clientID = row[indices["clientID"]]
            isSubject = row[indices["isSubject"]].lower() == "true"
            modelID = row[indices["modelID"]]
            scheduleID = row[indices["scheduleID"]]

            if alertID not in self.frauds:
                self.frauds[alertID] = FraudGroup(reason)
            self.frauds[alertID].add_member(clientID, isSubject)

            attr = {name: row[index] for name, index in indices.items()}
            output_row = self.schema.get_alert_acct_row(alertID, reason, clientID, clientID, isSubject, modelID,
                                                        scheduleID, **attr)
            writer.writerow(output_row)

    def output_fraud_cases(self):
        input_file = self.log_file
        fpath = os.path.join(self.work_dir, self.fraud_file)

        print("Convert fraud cases from %s to %s" % (input_file, fpath))
        rf = open(input_file, "r")
        reader = csv.reader(rf)
        header = next(reader)
        indices = {name: index for index, name in enumerate(header)}
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
                attr = {name: row[index] for name, index in indices.items()}
                self.frauds[alertID].add_transaction(txID, amount, days, orig, dest, orig_name, dest_name, attr)
                txID += 1

        alerts = set()
        count = 0
        frauds = len(self.frauds)
        for fraud_id, fg in self.frauds.items():
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
            writer.writerow(
                ["ALERT_ID", "MAIN_ACCOUNT_ID", "MAIN_CUSTOMER_ID", "EVENT_DATE", "ALERT_TYPE", "ACCOUNT_TYPE",
                 "IS_FRAUD"])
            for alert in alerts:
                fraud_id, acct_id, cust_id, date, alert_type, acct_type, is_fraud = alert
                writer.writerow((count, acct_id, cust_id, date, alert_type, acct_type, is_fraud))
                count += 1


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: python %s [ConfJSON]" % argv[0])
        exit(1)

    converter = LogConverter(argv[1])
    converter.convert_alert_members()
    converter.convert_acct_tx()
    converter.output_fraud_cases()
    # converter.output_subject_accounts()
