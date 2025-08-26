#!/bin/csh
setenv CLASSPATH .
if (`uname` == "Darwin") then
    setenv JAVA_HOME /System/Library/Frameworks/JavaVM.framework/Versions/1.6/Home
else
    setenv JAVA_HOME /usr/lib/jvm/java/
endif

setenv VOSPACE_LIB $PWD/src/main/lib
#setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/jaxb-api-2.2.jar:$VOSPACE_LIB/jaxb-impl-2.2.1.1.jar:$VOSPACE_LIB/jsr311-api-1.1.1.jar:$VOSPACE_LIB/slf4j-api-1.6.1.jar:$VOSPACE_LIB/slf4j-simple-1.6.1.jar:$VOSPACE_LIB/wink-1.1.2-incubating.jar
setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/jaxb-api.jar:$VOSPACE_LIB/jaxb-impl.jar:$VOSPACE_LIB/jsr311-api-1.1.1.jar:$VOSPACE_LIB/slf4j-api-1.7.7.jar:$VOSPACE_LIB/slf4j-simple-1.7.7.jar:$VOSPACE_LIB/wink-1.4.jar
setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/servlet-api-3.0.1.jar
setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/mysql-connector-java-5.0.8-bin.jar
setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/vtd-xml.jar
setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/woodstox-core-asl-4.2.0.jar
setenv CLASSPATH ${CLASSPATH}:$VOSPACE_LIB/uws4.1b.jar
