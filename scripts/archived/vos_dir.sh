#!/bin/bash

# Arguments are <username>, <hostname>, <database>, <root_dir>
d=`date +%Y-%m-%dT%H:%M:%S%z`
hn=`hostname -s`
if [ $# -lt 1 ]; then u=$USER; else u=$1; fi
if [ $# -lt 2 ]; then h=$hn; else h=$2; fi
if [ $# -lt 3 ]; then
    if [ $h == "dldb1" -o $h == "dldb1.sdm.noao.edu" ]; then
        db="vospace_prd"
    elif [ $h == "dltest" -o $h == "dltest.datalab.noao.edu" ]; then
        db="vospace_test"
    else
        db="vospace_dev"
    fi
else db=$3; fi
if [ $# -lt 4 ]; then
    if [ $h == "dldb1" -o $h == "dldb1.sdm.noao.edu" ]; then
        v="/dl2/vospace/users"
    else
        v="/data/vospace/users"
    fi
else v=$4; fi

# Make sure the directories actually exist
if [ ! -e ${v}/${u} ]; then
    sudo /bin/mkdir -p ${v}/${u}
    sudo /bin/chmod 775 ${v}/${u}
    sudo /bin/chown datalab:datalab ${v}/${u}
fi
if [ ! -e ${v}/${u}/public ]; then
    sudo /bin/mkdir -p ${v}/${u}/public
    sudo /bin/chmod 775 ${v}/${u}/public
    sudo /bin/chown datalab:datalab ${v}/${u}/public
fi
if [ ! -e ${v}/${u}/tmp ]; then
    sudo /bin/mkdir -p ${v}/${u}/tmp
    sudo /bin/chmod 770 ${v}/${u}/tmp
    sudo /bin/chown datalab:datalab ${v}/${u}/tmp
fi

/bin/sed -e "s/USER/${u}/g" -e "s/DATE/${d}/g" -e "s|ROOT|${v}|g" <<VOBASE | /usr/bin/mysql -u dba -pdba -h ${h} ${db}
# users/<USER>
insert ignore into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('vos://datalab.noao!vospace/USER', 0, 3, 'USER',
    'ivo://ivoa.net/vospace/views/blob', 'file://ROOT/USER', now());
insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('vos://datalab.noao!vospace/USER', 'DATE', 'DATE', 'DATE', 'DATE', 'USER', 'USER', 'False', 'False');

# users/<USER>/public
insert ignore into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('vos://datalab.noao!vospace/USER/public', 1, 3, 'USER',
    'ivo://ivoa.net/vospace/views/blob', 'file://ROOT/USER/public', now());
insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('vos://datalab.noao!vospace/USER/public', 'DATE', 'DATE', 'DATE', 'DATE', 'USER', 'USER', 'True', 'True');

# users/<USER>/tmp
insert ignore into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('vos://datalab.noao!vospace/USER/tmp', 1, 3, 'USER',
    'ivo://ivoa.net/vospace/views/blob', 'file://ROOT/USER/tmp', now());
insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('vos://datalab.noao!vospace/USER/tmp', 'DATE', 'DATE', 'DATE', 'DATE', 'USER', 'USER', 'False', 'False');
VOBASE
echo "$u VOSpace created on $h"