import csv
import json
import sys
import os
import shutil
import datetime
from dateutil.parser import parse
from random import random
from collections import defaultdict, Counter

from amlsim.account_data_type_lookup import AccountDataTypeLookup
from faker import Faker
import numpy as np


def days_to_date(days):
    date = datetime.datetime(2017, 1, 1) + datetime.timedelta(days=days)
    return date.strftime("%Y%m%d")


def get_simulator_name(csv_file):
    """Convert log file name to the simulator name
    :param csv_file: Transaction log file name
    :return: Simulator name
    """
    elements = csv_file.split("_")
    return "_".join(elements[:4])


def get_name(acct_id):
    return "Account" + str(acct_id)


def get_bank(acct_id):
    return "Bank" + str(acct_id)


CASH_TYPES = {"CASH-IN", "CASH-OUT"}


class AMLTypology:
    """Suspicious transaction and account group
    """

    def __init__(self, reason):
        self.is_sar = False  # SAR flag
        self.main_acct = None  # Main account ID
        self.reason = reason  # Description of the SAR
        self.transactions = dict()  # Transaction ID, attributes
        self.members = set()  # Accounts involved in the alert transactions
        self.recorded_members = set() # Accounts that have already been recorded. Avoid duplicates
        self.total_amount = 0.0  # Total transaction amount
        self.count = 0  # Number of transactions

    def add_member(self, member, is_sar):
        self.members.add(member)
        if is_sar:
            self.is_sar = True
            self.main_acct = member

    def add_tx(self, tx_id, amount, days, orig_acct, dest_acct, orig_name, dest_name, attr):
        self.transactions[tx_id] = (amount, days, orig_acct, dest_acct, orig_name, dest_name, attr)
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


class Schema:
    def __init__(self, data, base_date):
        self._base_date = base_date

        self.data = data

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
        self.alert_tx_id_idx = None
        self.alert_tx_type_idx = None
        self.alert_tx_sar_idx = None
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
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.acct_names.append(name)
            self.acct_defaults.append(default)
            self.acct_types.append(v_type)

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
                self.alert_tx_id_idx = idx
            elif d_type == "alert_type":
                self.alert_tx_type_idx = idx
            elif d_type == "sar_flag":
                self.alert_tx_sar_idx = idx
            elif d_type == "transaction_id":
                self.alert_tx_idx = idx
            elif d_type == "orig_id":
                self.alert_tx_orig_idx = idx
            elif d_type == "dest_id":
                self.alert_tx_dest_idx = idx
            elif d_type == "transaction_type":
                self.alert_tx_tx_type_idx = idx
            elif d_type == "amount":
                self.alert_tx_amount_idx = idx
            elif d_type == "timestamp":
                self.alert_tx_time_idx = idx

        # Individual party list
        for idx, col in enumerate(party_ind_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.party_ind_names.append(name)
            self.party_ind_defaults.append(default)
            self.party_ind_types.append(v_type)
            self.party_ind_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "party_id":
                self.party_ind_id_idx = idx

        # Individual party list
        for idx, col in enumerate(party_org_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.party_org_names.append(name)
            self.party_org_defaults.append(default)
            self.party_org_types.append(v_type)
            self.party_org_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "party_id":
                self.party_org_id_idx = idx

        # Account-Party list
        for idx, col in enumerate(acct_party_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.acct_party_names.append(name)
            self.acct_party_defaults.append(default)
            self.acct_party_types.append(v_type)
            self.acct_party_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "mapping_id":
                self.acct_party_mapping_idx = idx
            elif d_type == "account_id":
                self.acct_party_acct_idx = idx
            elif d_type == "party_id":
                self.acct_party_party_idx = idx

        # Party-Party list
        for idx, col in enumerate(party_party_data):
            name = col["name"]
            v_type = col.get("valueType", "string")
            d_type = col.get("dataType")
            default = col.get("defaultValue", "")

            self.party_party_names.append(name)
            self.party_party_defaults.append(default)
            self.party_party_types.append(v_type)
            self.party_party_name2idx[name] = idx

            if d_type is None:
                continue
            if d_type == "ref_id":
                self.party_party_ref_idx = idx
            elif d_type == "first_id":
                self.party_party_first_idx = idx
            elif d_type == "second_id":
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

        for idx, v_type in enumerate(self.tx_types):
            if v_type == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
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

        for idx, v_type in enumerate(self.alert_acct_types):
            if v_type == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_alert_tx_row(self, _alert_id, _alert_type, _is_sar, _tx_id, _orig, _dest,
                         _tx_type, _amount, _timestamp, **attr):
        row = list(self.alert_tx_defaults)
        row[self.alert_tx_id_idx] = _alert_id
        row[self.alert_tx_type_idx] = _alert_type
        row[self.alert_tx_sar_idx] = _is_sar
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

        for idx, v_type in enumerate(self.alert_tx_types):
            if v_type == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_party_ind_row(self, _party_id, **attr):
        row = list(self.party_ind_defaults)
        row[self.party_ind_id_idx] = _party_id

        for name, value in attr.items():
            if name in self.party_ind_name2idx:
                idx = self.party_ind_name2idx[name]
                row[idx] = value

        for idx, v_type in enumerate(self.party_ind_types):
            if v_type == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row

    def get_party_org_row(self, _party_id, **attr):
        row = list(self.party_org_defaults)
        row[self.party_org_id_idx] = _party_id

        for name, value in attr.items():
            if name in self.party_org_name2idx:
                idx = self.party_org_name2idx[name]
                row[idx] = value

        for idx, v_type in enumerate(self.party_org_types):
            if v_type == "date":
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

        for idx, v_type in enumerate(self.acct_party_types):
            if v_type == "date":
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

        for idx, v_type in enumerate(self.party_party_types):
            if v_type == "date":
                row[idx] = self.days2date(row[idx])  # convert days to date
        return row


class LogConverter:

    def __init__(self, conf, sim_name=None, fake=None):
        self.reports = dict()  # SAR ID and transaction subgraph
        self.org_types = dict()  # ID, organization type

        self.fake = fake

        general_conf = conf.get('general', {})
        input_conf = conf.get('temporal', {})  # Input directory of this converter is temporal directory
        output_conf = conf.get('output', {})

        # self.sim_name = os.getenv("SIMULATION_NAME")
        # if self.sim_name is None:
        #     self.sim_name = general_conf["simulation_name"]
        self.sim_name = sim_name if sim_name is not None else general_conf.get("simulation_name", "sample")
        print("Simulation name:", self.sim_name)

        self.input_dir = os.path.join(input_conf.get('directory', ''), self.sim_name)
        self.work_dir = os.path.join(output_conf.get('directory', ''), self.sim_name)
        if not os.path.isdir(self.work_dir):
            os.makedirs(self.work_dir)

        param_dir = conf.get('input', {}).get('directory', '')
        schema_file = conf.get('input', {}).get('schema', '')
        base_date_str = general_conf.get('base_date', '2017-01-01')
        base_date = parse(base_date_str)

        json_file = os.path.join(param_dir, schema_file)
        with open(json_file, "r") as rf:
            data = json.load(rf)
        self.schema = Schema(data, base_date)

        # Input files
        self.log_file = os.path.join(self.work_dir, output_conf["transaction_log"])
        self.in_acct_file = input_conf["accounts"]  # Account list file from the transaction graph generator
        self.group_file = input_conf["alert_members"]  # Alert account list file from the transaction graph generator

        # Output files
        self.out_acct_file = output_conf["accounts"]  # All account list file
        self.tx_file = output_conf["transactions"]  # All transaction list file
        self.cash_tx_file = output_conf["cash_transactions"]  # Cash transaction list file
        self.sar_acct_file = output_conf["sar_accounts"]  # SAR account list file
        self.alert_tx_file = output_conf["alert_transactions"]  # Alert transaction list file
        self.alert_acct_file = output_conf["alert_members"]  # Alert account list file

        self.party_individual_file = output_conf["party_individuals"]
        self.party_organization_file = output_conf["party_organizations"]
        self.account_mapping_file = output_conf["account_mapping"]
        self.resolved_entities_file = output_conf["resolved_entities"]

        # Copy the diameter CSV file if it exists
        dia_log = output_conf["diameter_log"]
        src_dia_path = os.path.join(self.input_dir, dia_log)
        dst_dia_path = os.path.join(self.work_dir, dia_log)
        if os.path.exists(src_dia_path):
            shutil.copy(src_dia_path, dst_dia_path)

    def convert_acct_tx(self):
        print("Convert transaction list from %s to %s, %s and %s" % (
            self.log_file, self.tx_file, self.cash_tx_file, self.alert_tx_file))

        in_acct_f = open(os.path.join(self.input_dir, self.in_acct_file), "r")  # Input account file
        in_tx_f = open(self.log_file, "r")  # Transaction log file from the Java simulator

        out_acct_f = open(os.path.join(self.work_dir, self.out_acct_file), "w")  # Output account file
        out_tx_f = open(os.path.join(self.work_dir, self.tx_file), "w")  # Output transaction file
        out_cash_tx_f = open(os.path.join(self.work_dir, self.cash_tx_file), "w")  # Output cash transaction file
        out_alert_tx_f = open(os.path.join(self.work_dir, self.alert_tx_file), "w")  # Output alert transaction file

        out_ind_f = open(os.path.join(self.work_dir, self.party_individual_file), "w")  # Party individuals
        out_org_f = open(os.path.join(self.work_dir, self.party_organization_file), "w")  # Party organizations
        out_map_f = open(os.path.join(self.work_dir, self.account_mapping_file), "w")  # Account mappings
        out_ent_f = open(os.path.join(self.work_dir, self.resolved_entities_file), "w")  # Resolved entities

        # Load account list
        reader = csv.reader(in_acct_f)
        acct_writer = csv.writer(out_acct_f)
        acct_writer.writerow(self.schema.acct_names)  # write header

        ind_writer = csv.writer(out_ind_f)
        ind_writer.writerow(self.schema.party_ind_names)
        org_writer = csv.writer(out_org_f)
        org_writer.writerow(self.schema.party_org_names)
        map_writer = csv.writer(out_map_f)
        map_writer.writerow(self.schema.acct_party_names)
        ent_writer = csv.writer(out_ent_f)
        ent_writer.writerow(self.schema.party_party_names)

        header = next(reader)

        mapping_id = 1  # Mapping ID for account-alert list

        lookup = AccountDataTypeLookup()
        us_gen = self.fake['en_US']

        for row in reader:
            output_row = list(self.schema.acct_defaults)

            acct_type = ""
            acct_id = ""

            gender = np.random.choice(['Male', 'Female'], p=[0.5, 0.5])

            good_address = False
            while good_address == False:
                address = us_gen.address()
                split1 = address.split('\n')
                street_address = split1[0]
                split2 = split1[1].split(', ')
                if len(split2) == 2:
                    good_address = True
            
            city = split2[0] 
            split3 = split2[1].split(' ')
            state = split3[0]
            postcode = split3[1]
            

            for output_index, output_item in enumerate(self.schema.data['account']):
                if 'dataType' in output_item:
                    output_type = output_item['dataType']
                    input_type = lookup.inputType(output_type)

                    try:
                        input_index = header.index(input_type)
                    except ValueError:
                        continue

                    if output_type == "start_time":
                        try:
                            start = int(row[input_index])
                            if start >= 0:
                                output_row[output_index] = start
                        except ValueError:  # If failed, keep the default value
                            pass

                    elif output_type == "end_time":
                        try:
                            end = int(row[input_index])
                            if end > 0:
                                output_row[output_index] = end
                        except ValueError:  # If failed, keep the default value
                            pass

                    elif output_type == "account_id":
                        acct_id = row[input_index]
                        output_row[output_index] = acct_id

                    elif output_type == "account_type":
                        acct_type = row[input_index]
                        output_row[output_index] = acct_type
        
                    else:
                        output_row[output_index] = row[input_index]

                if 'valueType' in output_item:
                    if output_item['valueType'] == 'date':
                        output_row[output_index] = self.schema.days2date(output_row[output_index])

                
                if 'name' in output_item:
                    if output_item['name'] == 'first_name':
                        output_row[output_index] = us_gen.first_name_male() if gender == "Male" else us_gen.first_name_female()
                    
                    elif output_item['name'] == 'last_name':
                        output_row[output_index] = us_gen.last_name_male() if gender == "Male" else us_gen.last_name_female()

                    elif output_item['name'] == 'street_addr':
                        output_row[output_index] = street_address

                    elif output_item['name'] == 'city':
                        output_row[output_index] = city

                    elif output_item['name'] == 'state':
                        output_row[output_index] = state

                    elif output_item['name'] == 'country':
                        output_row[output_index] = "US"

                    elif output_item['name'] == 'zip':
                        output_row[output_index] = postcode

                    elif output_item['name'] == 'gender':
                        output_row[output_index] = gender

                    elif output_item['name'] == 'birth_date':
                        output_row[output_index] = us_gen.date_of_birth()

                    elif output_item['name'] == 'ssn':
                        output_row[output_index] = us_gen.ssn()

                    elif output_item['name'] == 'lat':
                        output_row[output_index] = us_gen.latitude()
                    
                    elif output_item['name'] == 'lon':
                        output_row[output_index] = us_gen.longitude()

           

            acct_writer.writerow(output_row)
            self.org_types[int(acct_id)] = acct_type

            # Write a party row per account
            is_individual = random() >= 0.5  # 50%: individual, 50%: organization
            party_id = str(acct_id)
            if is_individual:  # Individual
                output_row = self.schema.get_party_ind_row(party_id)
                ind_writer.writerow(output_row)
            else:
                output_row = self.schema.get_party_org_row(party_id)
                org_writer.writerow(output_row)

            # Write account-party mapping row
            output_row = self.schema.get_acct_party_row(mapping_id, acct_id, party_id)
            map_writer.writerow(output_row)
            mapping_id += 1

        in_acct_f.close()
        out_ind_f.close()
        out_org_f.close()
        out_map_f.close()
        out_ent_f.close()

        # Avoid duplicated transaction CSV rows in the log file
        tx_set = set()
        cash_tx_set = set()

        # Load transaction log from the Java simulator
        reader = csv.reader(in_tx_f)
        tx_writer = csv.writer(out_tx_f)
        cash_tx_writer = csv.writer(out_cash_tx_f)
        alert_tx_writer = csv.writer(out_alert_tx_f)

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
        sar_idx = indices["isSAR"]
        alert_idx = indices["alertID"]
        type_idx = indices["type"]

        tx_id = 1
        for row in reader:
            if len(row) < num_columns:
                continue
            try:
                days = int(row[step_idx])
                date_str = str(days)  # days_to_date(days)
                amount = row[amt_idx]  # transaction amount
                orig_id = row[orig_idx]  # originator ID
                dest_id = row[dest_idx]  # beneficiary ID
                sar_id = int(row[sar_idx])  # SAR transaction index
                alert_id = int(row[alert_idx])  # Alert ID

                is_sar = sar_id > 0
                is_alert = alert_id >= 0
                ttype = row[type_idx]
            except ValueError:
                continue

            attr = {name: row[index] for name, index in indices.items()}
            if ttype in CASH_TYPES:  # Cash transactions
                cash_tx = (orig_id, dest_id, ttype, amount, date_str)
                if cash_tx not in cash_tx_set:
                    cash_tx_set.add(cash_tx)
                    output_row = self.schema.get_tx_row(tx_id, date_str, amount, ttype, orig_id, dest_id,
                                                        is_sar, alert_id, **attr)
                    cash_tx_writer.writerow(output_row)
            else:  # Account-to-account transactions including alert transactions
                tx = (orig_id, dest_id, ttype, amount, date_str)
                if tx not in tx_set:
                    output_row = self.schema.get_tx_row(tx_id, date_str, amount, ttype, orig_id, dest_id,
                                                        is_sar, alert_id, **attr)
                    tx_writer.writerow(output_row)
                    tx_set.add(tx)
            if is_alert:  # Alert transactions
                alert_type = self.reports.get(alert_id).get_reason()
                alert_row = self.schema.get_alert_tx_row(alert_id, alert_type, is_sar, tx_id, orig_id, dest_id,
                                                         ttype, amount, date_str, **attr)
                alert_tx_writer.writerow(alert_row)

            if tx_id % 1000000 == 0:
                print("Converted %d transactions." % tx_id)
            tx_id += 1

        in_tx_f.close()
        out_tx_f.close()
        out_cash_tx_f.close()
        out_alert_tx_f.close()

        # Count degrees (fan-in/out patterns)
        deg_param = os.getenv("DEGREE")
        if deg_param:
            max_threshold = int(deg_param)
            pred = defaultdict(set)  # Account, Predecessors
            succ = defaultdict(set)  # Account, Successors
            for orig, dest, _, _, _ in tx_set:
                pred[dest].add(orig)
                succ[orig].add(dest)
            in_degrees = [len(nbs) for nbs in pred.values()]
            out_degrees = [len(nbs) for nbs in succ.values()]
            in_deg = Counter(in_degrees)
            out_deg = Counter(out_degrees)
            for th in range(2, max_threshold+1):
                num_fan_in = sum([c for d, c in in_deg.items() if d >= th])
                num_fan_out = sum([c for d, c in out_deg.items() if d >= th])
                print("Number of fan-in / fan-out patterns with", th, "neighbors", num_fan_in, "/", num_fan_out)

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
            alert_id = int(row[indices["alertID"]])
            account_id = int(row[indices["accountID"]])
            is_sar = row[indices["isSAR"]].lower() == "true"
            model_id = row[indices["modelID"]]
            schedule_id = row[indices["scheduleID"]]
            bank_id = row[indices["bankID"]]

            if alert_id not in self.reports:
                self.reports[alert_id] = AMLTypology(reason)
            self.reports[alert_id].add_member(account_id, is_sar)

            attr = {name: row[index] for name, index in indices.items()}
            output_row = self.schema.get_alert_acct_row(alert_id, reason, account_id, account_id, is_sar,
                                                        model_id, schedule_id, bank_id, **attr)
            writer.writerow(output_row)


    def output_sar_cases(self):
        """Extract SAR account list involved in alert transactions from transaction log file
        """
        input_file = self.log_file
        output_file = os.path.join(self.work_dir, self.sar_acct_file)

        print("Convert SAR typologies from %s to %s" % (input_file, output_file))
        with open(input_file, "r") as rf:
            reader = csv.reader(rf)
            alerts = self.sar_accounts(reader)
        
        with open(output_file, "w") as wf:
            writer = csv.writer(wf)
            self.write_sar_accounts(writer, alerts)

    
    def sar_accounts(self, reader):
        header = next(reader)
        indices = {name: index for index, name in enumerate(header)}
        columns = len(header)

        tx_id = 0
        for row in reader:
            if len(row) < columns:
                continue
            try:
                days = int(row[indices["step"]])
                amount = float(row[indices["amount"]])
                orig = int(row[indices["nameOrig"]])
                dest = int(row[indices["nameDest"]])
                alert_id = int(row[indices["alertID"]])
                orig_name = "C_%d" % orig
                dest_name = "C_%d" % dest
            except ValueError:
                continue

            if alert_id >= 0 and alert_id in self.reports:  # SAR transactions
                attr = {name: row[index] for name, index in indices.items()}
                self.reports[alert_id].add_tx(tx_id, amount, days, orig, dest, orig_name, dest_name, attr)
                tx_id += 1

        sar_accounts = list()
        count = 0
        num_reports = len(self.reports)
        for sar_id, typology in self.reports.items():
            if typology.count == 0:
                continue
            reason = typology.get_reason()
            is_sar = "YES" if typology.is_sar else "NO"  # SAR or false alert
            for key, transaction in typology.transactions.items():
                amount, step, orig_acct, dest_acct, orig_name, dest_name, attr = transaction
                
                if (self.account_recorded(orig_acct) 
                and self.account_recorded(dest_acct)):
                    continue
                if (not self.account_recorded(orig_acct)):
                    acct_id = orig_acct
                    cust_id = orig_name
                    typology.recorded_members.add(acct_id)
                    sar_accounts.append((sar_id, acct_id, cust_id, days_to_date(step), reason, self.org_type(acct_id), is_sar))
                if (not self.account_recorded(dest_acct)):
                    acct_id = dest_acct
                    cust_id = dest_name
                    typology.recorded_members.add(acct_id)
                    sar_accounts.append((sar_id, acct_id, cust_id, days_to_date(step), reason, self.org_type(acct_id), is_sar))
                
            count += 1
            if count % 100 == 0:
                print("SAR Typologies: %d/%d" % (count, num_reports))
        return sar_accounts

    def org_type(self, acct_id):
        return "INDIVIDUAL" if self.org_types[acct_id] == "I" else "COMPANY"


    def write_sar_accounts(self, writer, sar_accounts):
        writer.writerow(
            ["ALERT_ID", "ACCOUNT_ID", "CUSTOMER_ID", "EVENT_DATE",
             "ALERT_TYPE", "ACCOUNT_TYPE", "IS_SAR"])

        for alert in sar_accounts:
            writer.writerow(alert)

    def account_recorded(self, acct_id):
        for sar_id, typology in self.reports.items():
            if acct_id in typology.recorded_members:
                return True
        return False


if __name__ == "__main__":
    argv = sys.argv

    if len(argv) < 2:
        print("Usage: python3 %s [ConfJSON]" % argv[0])
        exit(1)

    _conf_json = argv[1]
    _sim_name = argv[2] if len(argv) >= 3 else None

    with open(_conf_json, "r") as rf:
        conf = json.load(rf)
    converter = LogConverter(conf, _sim_name)
    fake = Faker(['en_US'])
    Faker.seed(0)
    converter = LogConverter(conf, _sim_name, fake)
    converter.convert_alert_members()
    converter.convert_acct_tx()
    converter.output_sar_cases()
