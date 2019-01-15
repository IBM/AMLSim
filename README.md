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
- aletPatterns.csv
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
- [PaySim](https://github.com/EdgarLopezPhD/PaySim) Please generate the jar file from class files
- [Commons-Math](http://commons.apache.org/proper/commons-math/download_math.cgi) 3.6.1


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
mkdir bin
javac -cp "jars/*" -d bin src/amlsim/*.java src/amlsim/stat/*.java src/amlsim/model/*.java src/amlsim/model/normal/*.java src/amlsim/model/fraud/*.java src/amlsim/model/cash/*.java
java -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=2 -Xmx1g -cp "jars/*:bin" amlsim.AMLSim -file [PropFile] -for [Steps] -r [Simulations] -name [Name]
```
- PropFile: Property file path of the Java application (`amlsim.properties`)
- Steps: Number of steps per simulation
- Simulations: Number of simulation iterations
- Name: Simulation name (optional: if absent, the current timestamp will be used)

Example:
```bash
java -Xms2g -Xmx4g -cp "jars/*:bin" amlsim.AMLSim -file amlsim.properties -for 150 -r 1 -name sample
```


### Example: generate transaction CSV files from small sample parameter files
```bash
cd /path/to/AMLSim
python scripts/transaction_relationship_generator.py prop.ini paramFiles/1K/degree.csv paramFiles/transactionType.csv
java -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=2 -Xmx1g -cp "jars/*:bin" amlsim.AMLSim -file amlsim.properties -for 150 -r 1 -name sample
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
1. First, please copy transaction `tx.csv` and case account ID list `case_accts.csv` files from the sample data directory to the `output` directory.
    ```bash
    cp /path/to/sample/1K/*.csv outputs/
    ```
1. Launch JanusGraph server
    ```bash
    cd /path/to/janusgraph-0.1.1-hadoop2/
    ./bin/janusgraph.sh start
    ```
1. Launch Groovy script to load transaction graph edge list and case account file list.
    ```bash
    cd /path/to/AMLSim
    /path/to/janusgraph-0.1.1-hadoop2/bin/gremlin.sh scripts/janusgraph/load_transaction_janusgraph.groovy
    ```
1. Then, run graph analytics on the JanusGraph.
    ```bash
    cd /path/to/janusgraph/scripts
    /path/to/janusgraph-0.1.1-hadoop2/bin/gremlin.sh egonet/ego_test.groovy
    ```


## Remove all log and image files from outputs directory
```bash
sh scripts/clean_logs.sh
```


