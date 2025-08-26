FROM amazoncorretto:8-alpine

# setup our working directory
RUN mkdir -p /app
WORKDIR /app

# ensure git is available since our apps sometimes use git commands
RUN apk add git

# set specific ANT versions
ENV ANT_VERSION=1.10.14
ENV ANT_HOME=/opt/ant

# Download and extract apache ant to opt folder
RUN wget --no-check-certificate http://archive.apache.org/dist/ant/binaries/apache-ant-${ANT_VERSION}-bin.tar.gz \
    && wget --no-check-certificate http://archive.apache.org/dist/ant/binaries/apache-ant-${ANT_VERSION}-bin.tar.gz.sha512 \
    && echo "$(cat apache-ant-${ANT_VERSION}-bin.tar.gz.sha512) apache-ant-${ANT_VERSION}-bin.tar.gz" | sha512sum -c \
    && tar -zvxf apache-ant-${ANT_VERSION}-bin.tar.gz -C /opt/ \
    && ln -s /opt/apache-ant-${ANT_VERSION} /opt/ant \
    && rm -f apache-ant-${ANT_VERSION}-bin.tar.gz \
    && rm -f apache-ant-${ANT_VERSION}-bin.tar.gz.sha512

# set entry to ant with a default command of "dist"
ENTRYPOINT [ "/opt/ant/bin/ant" ]
