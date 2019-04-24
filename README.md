# AMLSim
This project aims at building a multi-agent simulator of anti-money laundering - namely AML, and sharing synthetically generated data so that researchers can design and implement their new algorithms over the unified data.

# Directory Structure
See [Wiki Page](https://github.com/IBM/AMLSim/wiki/Directory-Structure) for details.



# Running codes

## Transaction Network Generator (Python)

### Package requirements
- NetworkX 1.10 (2.0 or later will not work)

### Launch the Python script
```bash
python scripts/transaction_graph_generator.py [PropFile] [DegreeFile] [TransactionTypeFile]
```
- PropFile: Configuration file path (`prop.ini`) of the transaction graph generator
- DegreeFile: Degree distribution parameter file
- TransactionTypeFile: Transaction type parameter file

Example:
```bash
python scripts/transaction_relationship_generator.py prop.ini paramFiles/deg1K.csv paramFiles/tx_type.csv
```


### Input files
See CSV files under `paramFiles` directory
- accounts.csv
  - Account parameter file
- alertPatterns.csv
  - Alert (fraud) transaction pattern parameter file
- degree.csv
  - Degree distribution parameter file
- transactionType.csv
  - Transaction distribution parameter file

Property file
- prop.ini


## Transaction Simulator (Java)

### Dependencies
Put all jar files of the following libraries to `jars` directory.
- [MASON](https://cs.gmu.edu/~eclab/projects/mason/) version 18
- [Commons-Math](http://commons.apache.org/proper/commons-math/download_math.cgi) 3.6.1
- [PaySim](https://github.com/EdgarLopezPhD/PaySim) Please generate `paysim.jar` with the following commands
```
git clone https://github.com/EdgarLopezPhD/PaySim.git
cd PaySim
git checkout 62a29b77c28bd03e717a67c8ab975c671ba0080d
mkdir bin jars
cp /path/to/commons-math-3-3.6.1*.jar /path/to/mason.18.jar jars/
javac -d bin -cp "jars/*" src/paysim/*.java
cd bin
jar cf paysim.jar paysim
```


### Input data files
All output files of the Python script
- accounts.csv
- transactions.csv
- alertPatterns.csv

Java property file
- amlsim.properties


### Build and launch AMLSim

Commands
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
account_list = accounts.csv
alertPattern = alertPatterns.csv
```

Then, please run transaction graph generator and simulator scripts.
```bash
cd /path/to/AMLSim
python scripts/transaction_graph_generator.py prop.ini paramFiles/1K/degree.csv paramFiles/1K/transactionType.csv
sh scripts/run_AMLSim.sh sample 150
```


## Visualize a transaction subgraph of the specified alert
```bash
python scripts/visualize/plot_transaction_graph.py [TransactionLog] [AlertID]
```
- TransactionLog: Log CSV file path from AMLSim (e.g. `outputs/sample/sample_log.csv`)
- AlertID: An alert ID to be visualized


## Convert Transaction Log into GPML Input Files
```bash
python scripts/convert_logs.py [ConfFile] [TransactionLog]
```
- ConfFile: Configuration ini file for the data conversion (`convert.ini`)
- TransactionLog: Transaction log CSV file under `outputs/(name)/` (e.g. `outputs/sample/sample_log.csv`)

Example: 
```bash
python scripts/convert_logs.py convert.ini outputs/sample/sample_log.csv
```


## Load transaction graph edge list and case account file list to JanusGraph
1. First, please copy account list `accounts.csv` and transaction list `tx.csv` files from the sample data directory to the `output` directory.
    ```bash
    cp /path/to/sample/1K/*.csv outputs/
    ```
1. Launch JanusGraph server
    ```bash
    cd /path/to/janusgraph-0.2.2-hadoop2/
    ./bin/janusgraph.sh start
    ```
1. Launch Groovy script to load transaction graph edge list and case account file list.
    ```bash
    cd /path/to/AMLSim
    /path/to/janusgraph-0.2.2-hadoop2/bin/gremlin.sh scripts/janusgraph/load_transaction_janusgraph.groovy
    ```
1. Then, run graph analytics on the JanusGraph.
    ```bash
    cd /path/to/janusgraph/scripts
    /path/to/janusgraph-0.2.2-hadoop2/bin/gremlin.sh egonet/ego_test.groovy
    ```


## Remove all log and image files from `outputs` directory
```bash
sh scripts/clean_logs.sh
```


