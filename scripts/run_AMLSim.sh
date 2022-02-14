#!/usr/bin/env bash

if [[ $# -ne 1 ]]; then
    echo "Usage: sh $0 [ConfJSON]"
    exit 1
fi

MIN_HEAP=2g
MAX_HEAP=4g

CONF_JSON=$1

if ! command -v mvn &> /dev/null
then
    echo 'maven not installed. proceeding.'
    java -XX:+UseConcMarkSweepGC -XX:ParallelGCThreads=2 -Xms${MIN_HEAP} -Xmx${MAX_HEAP} -cp "jars/*:target/classes/" amlsim.AMLSim "${CONF_JSON}"
    exit
else
    echo 'maven is installed. proceeding'
    mvn exec:java -Dexec.mainClass=amlsim.AMLSim -Dexec.args="${CONF_JSON}"
fi

# Cleanup temporal outputs of AMLSim
rm -f outputs/_*.csv outputs/_*.txt outputs/summary.csv

