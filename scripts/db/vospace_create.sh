#!/bin/bash
set -e;

if [ $# -lt 1 ]; then db='vospace_new'; else db=$1; fi
if [ $# -lt 2 ]; then user='test'; else user=$2; fi
if [ $# -lt 3 ]; then pw=''; else pw=$3; fi
if [ $# -lt 4 ]; then serviceName='vos-mysql'; else serviceName=$4; fi

echo "Starting init of $db for $user@$serviceName with pw: $pw..."

P_MYSQL="docker compose exec $serviceName mariadb -h $serviceName -u $user -p$pw $db -e"
ivoa_props_file="$(pwd)/java/src/main/webapp/WEB-INF/classes/ivoa_props.properties"
exd=`dirname $0`
$P_MYSQL "$(< $(pwd)/scripts/db/vospace_create.sql)"

echo "Initial tables created successfully."
echo "Updating metaproperties table from $ivoa_props_file"
# Fill the new metaproperties table
for c in $(cat "$ivoa_props_file" | grep -v '^#' | cut -f1 -d'='); do
    # This does not handle the Accepts/Provides/Contains/Read-only settings. The VOSpace must do that job on startup.
    $P_MYSQL "INSERT INTO metaproperties (identifier,type,readonly) VALUES ('ivo://ivoa.net/vospace/core#${c}','4','0');"
    echo "added metaproperty: $c";
done
echo "metaproperties table updated successfully!"

# Create properties table with all the columns
echo "Creating properties table"
prop_create='CREATE TABLE `properties` (`identifier` varchar(4096) NOT NULL'
for c in $($P_MYSQL "select identifier from metaproperties;" -N | cut -f2 -d'#'); do
    prop_create=$prop_create', `'${c}'` varchar(256) DEFAULT NULL'
done
prop_create=$prop_create', INDEX prop_id_idx (`identifier`(767)) ) ENGINE=InnoDB DEFAULT CHARSET=latin1;'
$P_MYSQL "$prop_create"
echo "Done!"
