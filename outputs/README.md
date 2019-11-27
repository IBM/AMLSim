# Output Directory

All final output files will be generated under a subdirectory (the name is the same as the value of "simulation_name") of this directory.
The directory and file names are defined at the "output" section of `conf.json`.

For example, the account list CSV file will be output at `outputs/sample/accounts.csv`.

```json5
{
"general": {
    "random_seed": 0,
    "simulation_name": "sample",
    "total_steps": 720,
    "base_date": "2017-01-01"
  },
//...
"output": {
    "directory": "outputs",  // Output directory
    "accounts": "accounts.csv",  // Account list CSV
    "transactions": "transactions.csv",  // All transaction list CSV
    "cash_transactions": "cash_tx.csv",  // Cash transaction list CSV
    "alert_members": "alert_accounts.csv",  // Alerted member account list CSV
    "alert_transactions": "alert_transactions.csv",  // Alerted transaction list CSV
    "sar_accounts": "sar_accounts.csv",  // SAR-flagged member account list CSV
    //  ...
    "transaction_log": "tx_log.csv",
    "counter_log": "tx_count.csv",
    "diameter_log": "diameter.csv"
  },
//...
}
```

Note: If you want to remove all files and directories except `README.md` (this file), please run `scripts/clean_logs.sh`
