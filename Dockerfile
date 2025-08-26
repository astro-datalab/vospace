# Sets a specific version of tomcat
ARG TOMCAT_VERSION=9.0.93-jre8

# Tomcat official: https://hub.docker.com/_/tomcat
FROM tomcat:${TOMCAT_VERSION}

# Sets the UID of the storage and vospace user
ARG STORAGE_UID=91

# Sets the GID of the storage and vospace user
ARG STORAGE_GID=91

# Sets the name of the vospace user (for legacy reasons the default is tomcat)
ARG STORAGE_USER=tomcat

# Sets the name of the vospace group (for legacy reasons the default is tomcat)
ARG STORAGE_GROUP=tomcat

# Sets the root location of the tree storage (for legacy reasons the default is /net/dl2/vospace/)
# Note: the container path, host path, and database all need to be in agreement.
ARG STORAGE_ROOT=/net/dl2/vospace/

# Sets the root location of the read only mass store. This can be used to attach various
# high level science products which aren't associated with the mutable user storage.
ARG MASS_STORE_ROOT=/net/mss1/archive/hlsp/

# add entrypoint script as executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Create a user with the provided UID and GID. This needs to match the host files when mounting
# a VOSpace directory.
RUN groupadd --force -g "${STORAGE_GID}" "${STORAGE_GROUP}" && \
    useradd --non-unique -m -u ${STORAGE_UID} -g ${STORAGE_GROUP} ${STORAGE_USER}

# first create the base directory and give our user permissions
RUN mkdir -p /net && chown -R ${STORAGE_USER}:${STORAGE_GROUP} /net

# permit access to tomcat directory
RUN chown -R ${STORAGE_USER}:${STORAGE_GROUP} /usr/local/tomcat/*

# Switch to the custom user
USER ${STORAGE_USER}

# setup main VOS store directory
RUN mkdir -p ${STORAGE_ROOT} ${STORAGE_ROOT}users ${STORAGE_ROOT}tmp ${MASS_STORE_ROOT}

# storage location
VOLUME ${STORAGE_ROOT}users

# staging data location
VOLUME ${STORAGE_ROOT}tmp

# mass store
VOLUME ${MASS_STORE_ROOT}

# set working directory to tomcat location (this is the default install location)
WORKDIR /usr/local/tomcat/

# copy the vospace distributable into the container
COPY ./java/vospace-2.0.war ./webapps/

# the service is considered healthy when the root VOSpace document is available
HEALTHCHECK \
    --interval=10m \
    --timeout=30s \
    --start-period=10s \
    --retries=3 \
    CMD \
    curl -f "http://localhost:8080/vospace-2.0/vospace" || exit 1

# set the main entrpoint
ENTRYPOINT [ "/entrypoint.sh" ]

# start the tomcat server
CMD ["catalina.sh", "run"]
