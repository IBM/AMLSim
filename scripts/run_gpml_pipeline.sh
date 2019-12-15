#!/usr/bin/env bash

if [ $# -lt 2 ]; then
  echo "Usage sh $0 [ConfJSON] [SimName] [EdgeRatio] [TxProb]"
  exit 1
fi

SIM_HOME=$(pwd)
MODEL_PROP=$SIM_HOME/paramFiles/model.properties
GPML_HOME=$SIM_HOME/../gpml

if [ ! -e "${GPML_HOME}" ]; then
  echo "GPML directory $GPML_HOME not found"
  exit 1
fi

export CONF_JSON=$1
export SIMULATION_NAME=$2
EDGE_RATIO=${3:-0.0}
TX_PROB=${4:-1.0}

# scripts/run_batch.sh
cmd="python3 scripts/transaction_graph_generator.py ${CONF_JSON} ${EDGE_RATIO}"
echo "$cmd"
time $cmd

# scripts/run_AMLSim.sh
cmd="java -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=2 -Dnormal2sar.tx.prob=${TX_PROB} -Xms2g -Xmx4g -cp jars/*:bin amlsim.AMLSim ${CONF_JSON} ${MODEL_PROP}"
echo "$cmd"
time $cmd

cmd="python3 scripts/convert_logs.py ${CONF_JSON}"
echo "$cmd"
time $cmd

# Move to GPML
cd "$GPML_HOME" || exit 1

cmd="sh scripts/run_from_amlsim.sh $SIM_HOME $SIM_HOME/$CONF_JSON data/$SIMULATION_NAME"
echo "$cmd"
time $cmd

