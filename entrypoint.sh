#!/usr/bin/env sh
set -e;

# startup the tomcat server in the background, we do this first since this causes
# all of the app files to be created so that they can be modified
echo "Starting server..."
/usr/local/tomcat/bin/catalina.sh start

# wait for vospace to come online, this way we know the files will be ready
echo "Waiting for VOSpace..."
curl \
    --fail \
    --connect-timeout 10 \
    --retry 3 \
    --retry-delay 5 \
    --retry-max-time 40 \
    --retry-all-errors \
    -o /dev/null \
    "http://127.0.0.1:8080/vospace-2.0/vospace"
echo "VOSpace is running!"

# Replace values in the vospace.properties file with various environment settings
APP_PATH="/usr/local/tomcat/webapps/vospace-2.0"
VOS_PROP_FILE="$APP_PATH/WEB-INF/classes/vospace.properties"
echo "Replacing environment variables in $VOS_PROP_FILE"
# Any environment setting that we want to use in the properties file needs to be
# set here
sed -i "s|\${DATA_URL}|$DATA_URL|g" "$VOS_PROP_FILE"
sed -i "s|\${TRANSFER_URL}|$TRANSFER_URL|g" "$VOS_PROP_FILE"
sed -i "s|\${AUTH_BASE_URL}|$AUTH_BASE_URL|g" "$VOS_PROP_FILE"
sed -i "s|\${MYSQL_DB_URL}|$MYSQL_DB_URL|g" "$VOS_PROP_FILE"
sed -i "s|\${MYSQL_USER}|$MYSQL_USER|g" "$VOS_PROP_FILE"
sed -i "s|\${MYSQL_PW}|$MYSQL_PW|g" "$VOS_PROP_FILE"
sed -i "s|\${PORT}|$PORT|g" "$VOS_PROP_FILE"
sed -i "s|\${STORAGE_ROOT}|$STORAGE_ROOT|g" "$VOS_PROP_FILE"
sed -i "s|\${STAGING_ROOT}|$STAGING_ROOT|g" "$VOS_PROP_FILE"
sed -i "s|\${VOS_IDENTIFIER}|$VOS_IDENTIFIER|g" "$VOS_PROP_FILE"
sed -i "s|\${ROOT_NODE_IDENTIFIER}|$ROOT_NODE_IDENTIFIER|g" "$VOS_PROP_FILE"
sed -i "s|\${CAPS_IDENTIFIER}|$CAPS_IDENTIFIER|g" "$VOS_PROP_FILE"
sed -i "s|\${DEBUG}|$DEBUG|g" "$VOS_PROP_FILE"

# stop the existing server and let the CMD take over
/usr/local/tomcat/bin/catalina.sh stop

exec "$@"