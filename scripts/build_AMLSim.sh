#!/usr/bin/env bash

BIN=bin
if [[ ! -d ${BIN} ]]; then
    mkdir ${BIN}
fi

javac -cp "jars/*" -d ${BIN} src/amlsim/*.java src/amlsim/stat/*.java src/amlsim/model/*.java src/amlsim/model/normal/*.java src/amlsim/model/fraud/*.java src/amlsim/model/cash/*.java

