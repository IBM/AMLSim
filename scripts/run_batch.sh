#!/usr/bin/env bash

if [[ $# -lt 1 ]]; then
    echo "Usage: sh $0 [ConfJSON] [LogFile(Optional)]"
    exit 1
fi

CONF_JSON=$1
OUTPUT_LOG=${2:-/dev/stdout}

echo "Configuration JSON file: ${CONF_JSON}"
echo "Output Log file: ${OUTPUT_LOG}"

python3 scripts/transaction_graph_generator.py "${CONF_JSON}" > "${OUTPUT_LOG}" 2>&1
sh scripts/run_AMLSim.sh "${CONF_JSON}" >> "${OUTPUT_LOG}" 2>&1
python3 scripts/convert_logs.py "${CONF_JSON}" >> "${OUTPUT_LOG}" 2>&1

