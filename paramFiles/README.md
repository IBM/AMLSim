# Parameter CSV files

## Files and directories


### accounts.csv
Account configuration list
- `count` Number of accounts
- `min_balance` Minimum initial balance
- `max_balance` Maximum initial balance
- `country` Alpha-2 country code
- `business_type` business type
- `model` Account behavior model ID (See also `AbstractTransactionModel.java`)
  - 0: Single transactions
  - 1: Fan-out
  - 2: Fan-in
  - 3: Mutual
  - 4: Forward
  - 5: Periodical
- `bank_id` Bank ID which these accounts belong to (optional)


Raw account list
- `uuid` Account ID
- `seq`
- `first_name`
- `last_name`
- `street_addr`
- `city`
- `state`
- `zip`
- `gender`
- `phone_number`
- `birth_date`
- `ssn`



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
The transaction network generator constructs a directed graph from the degree distribution data with
[Configuration Model](https://networkx.github.io/documentation/networkx-1.11/reference/generated/networkx.generators.degree_seq.directed_configuration_model.html).

### alertPatterns.csv
AML typology transaction pattern parameters (CSV columns)

- `count` Number of typologies (transaction sets)
- `type` Name of transaction type (`fan_in`, `fan_out`, `cycle`...) as the AML typology
- `schedule_id` Transaction scheduling ID of the typology
  - 0: All member accounts send money in order with the same interval (number of days)
  - 1: All member accounts send money in order with random intervals
  - 2: All member accounts send money randomly
- `min_accounts`: Minimum number of involved accounts
- `max_accounts`: Maximum number of involved accounts
- `min_amount` Minimum initial transaction amount
- `max_amount` Maximum initial transaction amount
- `min_period` Minimum overall transaction period (number of days)
- `max_period` Maximum overall transaction period (number of days)
- `bank_id` Bank ID which member accounts belong to (optional: if empty, no limitation for the bank ID) 
- `is_sar` Whether the alert is SAR (True) or false alert (False)


### transactionType.csv
This CSV file has two columns with header names: `Type` (transaction type name) 
and `Frequency` (relative number of transaction frequency)

Here is an example of transactionType.csv.
```
Type,Frequency
WIRE,5
CREDIT,10
DEPOSIT,15
CHECK,20
```
In this case, "WIRE" transaction will appear with 10% probability (5 / (5+10+15+20) = 0.1)