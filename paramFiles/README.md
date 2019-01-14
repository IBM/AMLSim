# Parameter files

## Files and directories


### accounts.csv
Account configuration list
- `num` Number of accounts
- `min_balance` Minimum initial balance
- `max_balance` Maximum initial balance
- `start_day` The day when the account is opened
- `end_day` The day when the account is closed
- `country` Alpha-2 country code
- `business_type` business type
- `suspicious` Suspicious account or not (true/false)
- `model` Account behavior model ID
  - 0: Single transactions
  - 1: Coarse-grained transactions
  - 2: Fine-grained transactions
  - 3: Distribution (fan-out)
  - 4: Gather (fan-in)
  - 5: Mutual
  - 6: Forward
  - 7: Periodical


### fraudPatterns.csv
Fraud transaction pattern list
- `num` Number of transaction sets
- `type` Fraud pattern name (`fan_in`, `fan_out` or `cycle`)
- `individual_amount` Minimum individual amount
- `aggregated_amount` Minimum aggregated amount
- `transaction_count` Minimum transaction count
- `amount_difference` Proportion of transaction difference
- `period` Lookback period (days)
- `amount_rounded` Proportion of transactions with rounded amounts
- `orig_country` Whether the originator country is suspicious
- `bene_country` Whether the beneficiary country is suspicious
- `orig_business` Whether the originator business type is suspicious
- `bene_business` Whether the beneficiary business type is suspicious
- `is_fraud` Whether the alert is fraud (True) or false alert (False)
