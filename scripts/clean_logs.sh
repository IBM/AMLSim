#!/usr/bin/env bash

OUTPUT=./outputs
TMP=./tmp

#rm -rf ${OUTPUT:?}/*/
rm -f ${OUTPUT}/*.txt
rm -f ${OUTPUT}/*.csv
rm -f ${OUTPUT}/*.png
rm -f ${OUTPUT}/*.gif

rm -f ${TMP}/*.csv

