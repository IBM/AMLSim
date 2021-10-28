#!/usr/bin/env bash

OUTPUT=./outputs
TMP=./tmp

rm -f ${OUTPUT}/*.txt
rm -f ${OUTPUT}/*.csv
rm -f ${OUTPUT}/*.png
rm -f ${OUTPUT}/*.gif

find ${OUTPUT} -mindepth 1 -maxdepth 1 -type d -exec rm -rf {} \;

if [ -d ${TMP} ]; then
rm -rf ${TMP:?}/*/
fi
