#!/bin/bash

if [ $# -lt 1 ]; then db='vospace_new'; else db=$1; fi
if [ $# -lt 2 ]; then host='localhost'; else host=$2; fi

P_MYSQL="/usr/bin/mysql -u dba -pdba -h $host"

exd=`dirname $0`
$P_MYSQL $db < ${exd}/vospace_copy.sql

count=$(echo "select count(identifier) from properties" | $P_MYSQL vospace -N)
echo -ne "${count}\r"
echo "select * from properties" | $P_MYSQL vospace -N | while read -r i; do
    id=$(echo $i | cut -d' ' -f1)
    col=$(echo $i | cut -d' ' -f2 | cut -f2 -d'#')
    val=$(echo $i | cut -d' ' -f3)
    echo "INSERT INTO properties (identifier,${col}) VALUES ('${id}','${val}') ON DUPLICATE KEY UPDATE ${col}='${val}';" \
            | $P_MYSQL $db
    count=$((count-1))
    echo -ne "${count} \r"
done
