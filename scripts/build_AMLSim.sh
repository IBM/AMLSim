#!/usr/bin/env bash

DESTINATION=target/classes/
if [[ ! -d ${DESTINATION} ]]; then
    rm -rf bin/
    mkdir -p ${DESTINATION}
fi

if ! command -v mvn &> /dev/null
then 
    echo 'maven not installed. compiling using javac'
    javac -encoding UTF-8 -cp "jars/*" -d ${DESTINATION} src/main/java/amlsim/*.java src/main/java/amlsim/stat/*.java src/main/java/amlsim/model/*.java src/main/java/amlsim/model/normal/*.java src/main/java/amlsim/model/aml/*.java src/main/java/amlsim/model/cash/*.java
    exit
else
    mvn clean package -DskipTests
fi

