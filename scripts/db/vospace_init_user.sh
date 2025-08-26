#!/bin/bash

# Initialize primary container nodes for the provided user
# Arguments are <username>, <storage_root>, <db_name>, <db_pw>, <db_host>
d=`date +%Y-%m-%dT%H:%M:%S%z`
if [ $# -lt 1 ]; then u=$USER; else u=$1; fi
if [ $# -lt 2 ]; then v="/dl2/vospace/users"; else v=$2; fi
if [ $# -lt 3 ]; then db='vospace_new'; else db=$3; fi
if [ $# -lt 4 ]; then db_user='test'; else db_user=$4; fi
if [ $# -lt 5 ]; then pw=''; else pw=$5; fi
if [ $# -lt 6 ]; then db_host='localhost'; else db_host=$6; fi

# verify main root directory, public and tmp directories exist
ERR=$(echo "if [ ! -e ${v}/${u} ]; then exit 1; fi" | docker compose exec -T vos-api bash -s - && echo "error")
ERR=$(echo "if [ ! -e ${v}/${u}/public ]; then exit 1; fi" | docker compose exec -T vos-api bash -s - && echo "error")
ERR=$(echo "if [ ! -e ${v}/${u}/tmp ]; then exit 1; fi" | docker compose exec -T vos-api bash -s - && echo "error")
if [ -z "$ERR" ]; then
    printf "
User directories not found. Ensure the following directories exist:
${v}/${u}
${v}/${u}/public
${v}/${u}/tmp\n"
    exit 1;
fi

# error if anything below exits with an error
set -e;

# subsitute SQL with provided arguments
statement=$(cat <<SQL | /bin/sed -e "s/USER/${u}/g" -e "s/DATE/${d}/g" -e "s|ROOT|${v}|g"
# users/<USER>
insert into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('vos://datalab.noirlab!vospace/USER', 0, 3, 'USER',
    'ivo://ivoa.net/vospace/views/blob', 'file://ROOT/USER', now());

insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('vos://datalab.noirlab!vospace/USER', 'DATE', 'DATE', 'DATE', 'DATE', 'USER', 'USER', 'False', 'False');

# users/<USER>/public
insert into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('vos://datalab.noirlab!vospace/USER/public', 1, 3, 'USER',
    'ivo://ivoa.net/vospace/views/blob', 'file://ROOT/USER/public', now());

insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('vos://datalab.noirlab!vospace/USER/public', 'DATE', 'DATE', 'DATE', 'DATE', 'USER', 'USER', 'True', 'True');

# users/<USER>/tmp
insert into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('vos://datalab.noirlab!vospace/USER/tmp', 1, 3, 'USER',
    'ivo://ivoa.net/vospace/views/blob', 'file://ROOT/USER/tmp', now());

insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('vos://datalab.noirlab!vospace/USER/tmp', 'DATE', 'DATE', 'DATE', 'DATE', 'USER', 'USER', 'False', 'False');
SQL
)

# execute the SQL
docker compose exec -T vos-mysql mariadb -h $db_host -u $db_user -p$pw $db -e "$statement" 

echo "VOSpace meta created for user \"$u\" in $db_user@$db_host/$db"
