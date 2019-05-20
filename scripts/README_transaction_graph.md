# Readme on trasaction graph generator python file

This info can be found from their wiki page:

##Transaction Network Generator (Python)
###Package requirements
- NetworkX 1.10 (2.0 or later will not work)

### Launch the Python script

    python scripts/transaction_graph_generator.py [PropFile] [DegreeFile] [TransactionTypeFile]

- PropFile: Configuration file path (prop.ini) of the transaction graph generator
- DegreeFile: Degree distribution parameter file
- TransactionTypeFile: Transaction type parameter file

Example:

    python scripts/transaction_relationship_generator.py prop.ini paramFiles/degree.csv paramFiles/transactionType.csv

### Input files

See CSV files under paramFiles directory

- accounts.csv, account parameter file
- aletPatterns.csv, alert (fraud) transaction pattern parameter file
- degree.csv, degree distribution parameter file
- transactionType.csv, transaction distribution parameter file

Property file
- prop.ini
