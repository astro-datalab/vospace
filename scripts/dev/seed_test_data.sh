#!/bin/bash
#
# Seeds a database with various initialization and test data for dev and
# test environments. 
#
# Usage:
# ./scripts/dev/seedTestData.sh [<env_file_path>]
set -e;

# load environment
ENV_FILE=${1:-.env}
source "$PWD/$ENV_FILE"

# for the dev env the host is vos-mysql
DB_HOST="vos-mysql"

# make sure the proper environment settings are present
if [[ -z "$MYSQL_DB_NAME" || -z "$MYSQL_USER" || -z "$MYSQL_PW" ]]; then
    echo "Missing one or more required env settings: MYSQL_DB_NAME, MYSQL_USER, MYSQL_PW"
    exit 1;
fi

# this is initializes the DB with some required records
$PWD/scripts/db/vospace_create.sh "$MYSQL_DB_NAME" "$MYSQL_USER" "$MYSQL_PW" "$DB_HOST"

# create various users to use for testing. This should match our file store fixtures
$PWD/scripts/db/vospace_init_user.sh "userone" "/net/dl2/vospace/users" "$MYSQL_DB_NAME" "$MYSQL_USER" "$MYSQL_PW" "$DB_HOST"
$PWD/scripts/db/vospace_init_user.sh "usertwo" "/net/dl2/vospace/users" "$MYSQL_DB_NAME" "$MYSQL_USER" "$MYSQL_PW" "$DB_HOST"
