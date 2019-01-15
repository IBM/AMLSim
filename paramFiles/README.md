# Parameter files

## Files and directories


### accounts.csv
Account configuration list
- `count` Number of accounts
- `min_balance` Minimum initial balance
- `max_balance` Maximum initial balance
- `start_day` The day when the account is opened
- `end_day` The day when the account is closed
- `country` Alpha-2 country code
- `business_type` business type
- `suspicious` Suspicious account or not (currently unused)
- `model` Account behavior model ID (See also `AbstractTransactionModel.java`)
  - 0: Single transactions
  - 1: Fan-out
  - 2: Fan-in
  - 3: Mutual
  - 4: Forward
  - 5: Periodical


### degree.csv
This CSV file has three columns with header names: `Count`, `In-degree` and `Out-degree`.
Each CSV row indicates how many account vertices with certain in(out)-degrees should be generated.

Here is an example of degree.csv.
```
Count,In-degree,Out-degree
0,2,2
1,1,1
2,2,2
```
From this parameter file, the transaction graph generator generates a directed graph with five vertices (accounts) and five edges.
Two of five vertices has no outgoing edges and two of five vertices has no incoming edges (these two vertices might be same).


### alertPatterns.csv
Fraud transaction pattern list
- `count` Number of transaction sets
- `type` Fraud pattern name (`fan_in`, `fan_out` or `cycle`)
- `schedule_id` Transaction scheduling ID
  - 0: All accounts send money in order with the same interval
  - 1: All accounts send money in order with random intervals
  - 2: All accounts send money randomly
- `accounts`: Number of involved accounts
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


### transactionType.csv
This CSV file has two columns with header names: `Type`(transaction type name) and `Frequency`(frequency)

Here is an example of transactionType.csv.
```
Type,Frequency
WIRE,5
CREDIT,10
DEPOSIT,15
CHECK,20
```
In this case, "WIRE" transaction will appear with 10% probability (5 / (5+10+15+20) = 0.1)