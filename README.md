# AMLSim
This project aims at building a multi-agent simulator of anti-money laundering - namely AML, and sharing synthetically generated data so that researchers can design and implement their new algorithms over the unified data.


# Dependencies
- Java 8
  - commons-math 3.6.1
  - dsiutils 2.4.2
  - fastutil-8.1.0
  - jsap 2.1
  - json
  - mason
  - mysql-connector 5.1.46
  - PaySim
  - slf4j
  - sux4j
  - WebGraph 3.6.1
- Python 2.7
  - networkx 1.10 (2.* will not work)
  - matplotlib
  - powerlaw


# Directory Structure
See Wiki page [Directory Structure](https://github.com/IBM/AMLSim/wiki/Directory-Structure) for details.



# Introduction for Running AMLSim
See Wiki page [Quick Introduction to AMLSim](https://github.com/IBM/AMLSim/wiki/Quick-Introduction-to-AMLSim) for details.

## Transaction Simulator (Java)

```bash
sh scripts/build_AMLSim.sh
sh scripts/run_AMLSim.sh [SimulationName] [Steps]
```
- SimulationName: Simulation name
- Steps: Number of steps per simulation

Example:
```bash
sh scripts/run_AMLSim.sh sample 150
```


### Example: generate transaction CSV files from small sample parameter files
Before running the Python script, please check and edit configuration file `prop.ini`.
```ini
[InputFile]
directory = paramFiles/1K
alertPattern = alertPatterns.csv
```

Then, please run transaction graph generator and simulator scripts.
```bash
cd /path/to/AMLSim
python scripts/transaction_graph_generator.py prop.ini paramFiles/1K/accounts.csv paramFiles/1K/degree.csv paramFiles/1K/transactionType.csv
sh scripts/run_AMLSim.sh sample 150
```


## Visualize a transaction subgraph of the specified alert
```bash
python scripts/visualize/plot_transaction_graph.py [TransactionLog] [AlertID]
```
- TransactionLog: Log CSV file path from AMLSim (e.g. `outputs/sample/sample_log.csv`)
- AlertID: An alert ID to be visualized


## Convert the raw transaction log file
```bash
python scripts/convert_logs.py [ConfFile] [TransactionLog]
```
- ConfFile: Configuration ini file for the data conversion (`convert.ini`)
- TransactionLog: Transaction log CSV file under `outputs/(name)/` (e.g. `outputs/sample/sample_log.csv`)

Example: 
```bash
python scripts/convert_logs.py convert.ini outputs/sample/sample_log.csv
```


## Remove all log and image files from `outputs` directory
```bash
sh scripts/clean_logs.sh
```


