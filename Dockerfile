FROM maven:3.8.4-jdk-11 AS build

COPY . /usr/src/app

WORKDIR /usr/src/app

RUN mvn install:install-file \
-Dfile=jars/mason.20.jar \
-DgroupId=mason \
-DartifactId=mason \
-Dversion=20 \
-Dpackaging=jar \
-DgeneratePom=true

RUN ["scripts/build_AMLSim.sh"]

ENTRYPOINT ["scripts/run_AMLSim.sh", "conf.json"]



