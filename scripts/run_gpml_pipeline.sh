#!/usr/bin/env bash

if [ $# -lt 2 ]; then
  echo "Usage sh $0 [ConfJSON] [SimName] [EdgeRatio]"
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

run_cmd(){
  cmd=$1
  echo "Started: $cmd"
  time $cmd || { echo "Failed: $cmd" ; exit 1 ; }
  echo "Finished: $cmd"
}

# scripts/run_batch.sh
run_cmd "python3 scripts/transaction_graph_generator.py ${CONF_JSON} ${SIMULATION_NAME} ${EDGE_RATIO}"

# scripts/run_AMLSim.sh
run_cmd "java -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=2 -Dsimulation_name=${SIMULATION_NAME} -Xms2g -Xmx4g -cp jars/*:bin amlsim.AMLSim ${CONF_JSON} ${MODEL_PROP}"

# scripts/convert_logs.py
run_cmd "python3 scripts/convert_logs.py ${CONF_JSON} ${SIMULATION_NAME}"

#run_cmd "python3 scripts/validation/validate_alerts.py ${CONF_JSON} ${SIMULATION_NAME}"

run_cmd "python3 scripts/visualize/plot_distributions.py ${CONF_JSON} ${SIMULATION_NAME}"


# Move to GPML
run_cmd "cd $GPML_HOME"

run_cmd "sh scripts/run_from_amlsim.sh $SIM_HOME $SIM_HOME/$CONF_JSON data/$SIMULATION_NAME $SIMULATION_NAME"

