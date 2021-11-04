import unittest

from convert_logs import AMLTypology, LogConverter

class LogConverterTests(unittest.TestCase):

    def setUp(self):
        self.conf = {
            "general": {
                "random_seed": 0,
                "simulation_name": "sample",
                "total_steps": 720,
                "base_date": "2017-01-01"
            },
            "input": {
                "directory": "tests/json",
                "schema": "schema.json",
                "accounts": "accounts.csv",
                "alert_patterns": "alertPatterns.csv",
                "degree": "degree.csv",
                "transaction_type": "transactionType.csv",
                "is_aggregated_accounts": True
            },
            "output": {
                "directory": "outputs",
                "accounts": "accounts.csv",
                "transactions": "transactions.csv",
                "cash_transactions": "cash_tx.csv",
                "alert_members": "alert_accounts.csv",
                "alert_transactions": "alert_transactions.csv",
                "sar_accounts": "sar_accounts.csv",
                "party_individuals": "individuals-bulkload.csv",
                "party_organizations": "organizations-bulkload.csv",
                "account_mapping": "accountMapping.csv",
                "resolved_entities": "resolvedentities.csv",
                "transaction_log": "tx_log.csv",
                "counter_log": "tx_count.csv",
                "diameter_log": "diameter.csv"
            },
            "temporal": {
                "directory": "tmp",
                "transactions": "transactions.csv",
                "accounts": "accounts.csv",
                "alert_members": "alert_members.csv"
            },
        }
    
    def test_sar_accounts_not_involved_not_included(self):
        converter = LogConverter(self.conf)
        typology = AMLTypology('fan_out')
        typology.add_member(1302, True)
        typology.add_member(44, True)
        typology.add_member(52, True)
        converter.reports[0] = typology


        reader = [
            ['step','type','amount','nameOrig','oldbalanceOrig','newbalanceOrig','nameDest','oldbalanceDest','newbalanceDest','isSAR','alertID'],
            ['0','TRANSFER','397.08','47','71052.47','70655.39','41','74678.89','75075.97','0','-1'],
            ['0','TRANSFER','374.96','1302','79080.81','78705.84','44','66260.21','66635.18','1','0'],
            ['0','TRANSFER','248.71','1302','88203.42','87954.7','52','54022.28','54271.0','1','0']
        ]
        converter.org_types = {
            47: "I",
            1302: "I",
            41: "I",
            44: "I",
            52: "I"
        }
        reader = iter(reader)
        sar_accounts = converter.sar_accounts(reader)
        self.assertEqual(sar_accounts, [
            (0, 1302, 'C_1302', '20170101', 'fan_out', 'INDIVIDUAL', 'YES'),
            (0, 44, 'C_44', '20170101', 'fan_out', 'INDIVIDUAL', 'YES'),
            (0, 52, 'C_52', '20170101', 'fan_out', 'INDIVIDUAL', 'YES')
        ])

    def test_sar_accounts_no_duplicates(self):
        converter = LogConverter(self.conf)
        typology = AMLTypology('fan_out')
        typology.add_member(1302, True)
        typology.add_member(44, True)
        typology.add_member(52, True)

        typology2 = AMLTypology('fan_in')
        typology2.add_member(1302, True)
        typology2.add_member(47, True)
        typology2.add_member(182, True)
        typology2.add_member(183, True)
        converter.reports = {
            0: typology,
            1: typology2
        }

        reader = [
            ['step','type','amount','nameOrig','oldbalanceOrig','newbalanceOrig','nameDest','oldbalanceDest','newbalanceDest','isSAR','alertID'],
            ['0','TRANSFER','397.08','47','71052.47','70655.39','41','74678.89','75075.97','0','-1'],
            ['0','TRANSFER','374.96','1302','79080.81','78705.84','44','66260.21','66635.18','1','0'],
            ['0','TRANSFER','248.71','1302','88203.42','87954.7','52','54022.28','54271.0','1','0'],
            ['1','TRANSFER','248.71','47','88203.42','87954.7','1302','54022.28','54271.0','1','1'],
            ['1','TRANSFER','248.71','182','88203.42','87954.7','1302','54022.28','54271.0','1','1'],
            ['1','TRANSFER','248.71','183','88203.42','87954.7','1302','54022.28','54271.0','1','1'],
        ]
        converter.org_types = {
            47: "I",
            1302: "I",
            41: "I",
            44: "I",
            52: "I",
            182: "I",
            183: "I"
        }
        reader = iter(reader)
        sar_accounts = converter.sar_accounts(reader)
        self.assertEqual(sar_accounts, [
            (0, 1302, 'C_1302', '20170101', 'fan_out', 'INDIVIDUAL', 'YES'),
            (0, 44, 'C_44', '20170101', 'fan_out', 'INDIVIDUAL', 'YES'),
            (0, 52, 'C_52', '20170101', 'fan_out', 'INDIVIDUAL', 'YES'),
            (1, 47, 'C_47', '20170102', 'fan_in', 'INDIVIDUAL', 'YES'),
            (1, 182, 'C_182', '20170102', 'fan_in', 'INDIVIDUAL', 'YES'),
            (1, 183, 'C_183', '20170102', 'fan_in', 'INDIVIDUAL', 'YES'),
        ])


if __name__ == ' main ':
    unittest.main()