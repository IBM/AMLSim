class AccountDataTypeLookup:
    def __init__(self):
        self.output_to_input = {
            'account_id': 'ACCOUNT_ID',
            'account_name': 'CUSTOMER_ID',
            'initial_balance': 'INIT_BALANCE',
            'start_time': 'START_DATE',
            'end_time': 'END_DATE',
            'country': 'COUNTRY',
            'account_type': 'ACCOUNT_TYPE',
            'sar_flag': 'IS_SAR',
            'model_id': 'TX_BEHAVIOR_ID',
            'bank_id': 'BANK_ID'
        }

    def inputType(self, input):
        return self.output_to_input[input]
