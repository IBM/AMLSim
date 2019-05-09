#!/usr/bin/env bash

SIM=$(pwd)

STEPS=124
EDGE_FACTORS="1 2 4 8 12"
AML_RULES="amlrule50_star5 amlrule100_star5 amlrule200_star5"

for EF in ${EDGE_FACTORS}
do

for AMLRULE in ${AML_RULES}
do

SIM_NAME=${AMLRULE}_${EF}

cd ${SIM}
mkdir ${SIM_NAME}
WORK=${SIM}/${SIM_NAME}
SIM_LOG=${WORK}/sim.log

echo "Start ${SIM_NAME}"
echo "Generating Transaction Graph"
python scripts/generate_scalefree.py 1000 ${EF} paramFiles/deg_aml.csv >> ${SIM_LOG} 2>&1
python scripts/transaction_graph_generator.py prop.ini paramFiles/deg_aml.csv paramFiles/tx_type.csv paramFiles/${AMLRULE}.csv  >> ${SIM_LOG} 2>&1
sh scripts/run_AMLSim.sh ${SIM_NAME} ${STEPS} >> ${SIM_LOG} 2>&1
python scripts/convert_logs.py convert.ini outputs/${SIM_NAME}/${SIM_NAME}_log.csv >> ${SIM_LOG} 2>&1

pythonw scripts/plot_distributions.py outputs/tx.csv prop.ini paramFiles/${AMLRULE}.csv >> ${SIM_LOG} 2>&1
mv *.png outputs/*.png ${WORK}

echo "Finished ${SIM_NAME}"

done

done

