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
