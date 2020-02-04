#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
    echo "Usage: sh $0 [ConfJSON] [LogFile(Optional)]"
    exit 1
fi

CONF_JSON=$1
OUTPUT_LOG=${2:-/dev/null}
EDGE_RATIO=${3:-0.0}

echo "Configuration JSON file: ${CONF_JSON}"
echo "Output Log file: ${OUTPUT_LOG}"

time python3 scripts/transaction_graph_generator.py "${CONF_JSON}" "${EDGE_RATIO}" 2>&1 | tee "${OUTPUT_LOG}"
time sh scripts/run_AMLSim.sh "${CONF_JSON}" 2>&1 | tee -a "${OUTPUT_LOG}"
time python3 scripts/convert_logs.py "${CONF_JSON}" 2>&1 | tee -a "${OUTPUT_LOG}"

#python3 scripts/validation/validate_alerts.py "${CONF_JSON}" 2>&1 | tee -a "${OUTPUT_LOG}"
#python3 scripts/visualize/plot_distributions.py "${CONF_JSON}" 2>&1 | tee -a "${OUTPUT_LOG}"

