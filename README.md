# AMLSim
This project aims at building a multi-agent simulator of anti-money laundering - namely AML, and sharing synthetically generated data so that researchers can design and implement their new algorithms over the unified data.


# Dependencies
- Java 8 (Download and copy all jar files to `jars` directory: See also `jars/README.md`)
  - commons-math 3.6.1
  - dsiutils 2.5.4
  - fastutil-8.2.3
  - jsap 2.1
  - json
  - mason
  - mysql-connector 5.1.46
  - PaySim (jar file already exists)
  - slf4j
  - sux4j
  - WebGraph 3.6.1
- Python 3.7 (You can install the following packages with `pip3 install -r requirements.txt`)
  - NumPy
  - networkx 1.11 (2.* will not work)
  - matplotlib
  - powerlaw
  - python-dateutil



# Directory Structure
See Wiki page [Directory Structure](https://github.com/IBM/AMLSim/wiki/Directory-Structure) for details.



# Introduction for Running AMLSim
See Wiki page [Quick Introduction to AMLSim](https://github.com/IBM/AMLSim/wiki/Quick-Introduction-to-AMLSim) for details.

## 1. Generate transaction CSV files from parameter files (Python)
Before running the Python script, please check and edit configuration file `conf.json`.
```json5
{
//...
  "input": {
    "directory": "paramFiles/1K",  // Parameter directory
    "schema": "schema.json",  // Configuration file of output CSV schema
    "accounts": "accounts.csv",  // Account list parameter file
    "alert_patterns": "alertPatterns.csv",  // Alert list parameter file
    "degree": "degree.csv",  // Degree sequence parameter file
    "transaction_type": "transactionType.csv",  // Transaction type list file
    "is_aggregated_accounts": true  // Whether the account list represents aggregated (true) or raw (false) accounts
  },
//...
}
```

Then, please run transaction graph generator script.
```bash
cd /path/to/AMLSim
python3 scripts/transaction_graph_generator.py conf.json
```

## 2. Build and launch the transaction simulator (Java)
Parameters for the simulator are defined at "general" section of `conf.json`. 

```json5
{
  "general": {
      "random_seed": 0,  // Seed of random number
      "simulation_name": "sample",  // Simulation name (identifier)
      "total_steps": 720,  // Total simulation steps
      "base_date": "2017-01-01"  // The date corresponds to the step 0 (beginning of this simulation)
  },
//...
}
```

Please compile Java files (if not yet) and launch the simulator.
```bash
sh scripts/build_AMLSim.sh
sh scripts/run_AMLSim.sh conf.json
```


## 3. Convert the raw transaction log file
The file names of the output data are defined at "output" section of `conf.json`.
```json5
{
//...
"output": {
    "directory": "outputs",  // Output directory
    "accounts": "accounts.csv",  // Account list CSV
    "transactions": "transactions.csv",  // All transaction list CSV
    "cash_transactions": "cash_tx.csv",  // Cash transaction list CSV
    "alert_members": "alert_accounts.csv",  // Alerted account list CSV
    "alert_transactions": "alert_transactions.csv",  // Alerted transaction list CSV
    "frauds": "frauds.csv",  // Fraud account list CSV
    "party_individuals": "individuals-bulkload.csv",
    "party_organizations": "organizations-bulkload.csv",
    "account_mapping": "accountMapping.csv",
    "resolved_entities": "resolvedentities.csv",
    "transaction_log": "tx_log.csv",
    "counter_log": "tx_count.csv",
    "diameter_log": "diameter.csv"
  },
//...
}
```

```bash
python3 scripts/convert_logs.py conf.json
```



## Remove all log and generated image files from `outputs` directory
```bash
sh scripts/clean_logs.sh
```


