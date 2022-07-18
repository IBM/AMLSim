# Installation

Set up a virtual environment:
```shell
python -m venv venv
source venv/bin/activate
```
Install dependencies:
```shell
brew install graphviz
python -m pip install \
    --global-option=build_ext \
    --global-option="-I$(brew --prefix graphviz)/include/" \
    --global-option="-L$(brew --prefix graphviz)/lib/" \
    pygraphviz
pip install -r requirements.txt
```
Download Mason jar file:
```shell
 wget -N "https://cs.gmu.edu/~eclab/projects/mason/mason.20.jar" -P jars/
```

# Usage

Generate transaction graph:
```shell
cd /path/to/AMLSim
python3 scripts/transaction_graph_generator.py conf.json
```
Please compile Java files (if not yet) (will detect and use Maven) and launch the simulator:
```bash
sh scripts/build_AMLSim.sh
sh scripts/run_AMLSim.sh conf.json
```
Convert the raw transaction log file:
```bash
python3 scripts/convert_logs.py conf.json
```
Remove all log and generated image files from `outputs` directory and a temporal directory:
```bash
sh scripts/clean_logs.sh
```
