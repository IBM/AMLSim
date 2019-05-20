# External jar files

# UPDATE the basepath to your local one

mvn install:install-file  \
 -Dfile={basepath}/jars/paysim.jar \
 -DgroupId=org.paysim \
 -DartifactId=paysim \
 -Dversion=2.0.0 \
 -Dpackaging=jar \
 -DgeneratePom=true




Please download external jar files from the following sites.

- [MASON](https://cs.gmu.edu/~eclab/projects/mason/)
  - Download "mason18.zip" from the homepage and extract it.
- [PaySim](https://github.com/EdgarLopezPhD/PaySim)
  - Compile Java source files and generate a jar file.
- [Commons-Math](http://commons.apache.org/proper/commons-math/download_math.cgi) 3.6.1
  - Download "commons-math3-3.6.1-bin.tar.gz" and extract the following jar files.
    - commons-math3-3.6.1.jar
    - commons-math3-3.6.1-tests.jar
    - commons-math3-3.6.1-tools.jar
- dsiutils-2.4.2.jar
- fastutil-8.1.0.jar
- jsap-2.1.jar
- mysql-connector-java-5.1.46-bin.jar
- slf4j-api-1.7.25.jar
- sux4j-4.2.0.jar
- webgraph-3.6.1.jar

