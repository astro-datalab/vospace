#!/bin/bash

# Outputs the SQL to import all VOSpace users in a VOSpace database.
# Arguments are <username>, <hostname>
sedf=''
for f in /bin/sed /usr/bin/sed; do if [ -e $f ]; then sedf=$f; break; fi; done
if [ -z $sedf ]; then echo "No sed found." 1>&2; exit 1; fi

d=$(date +%Y-%m-%dT%H:%M:%S%z)
if [ $# -lt 1 ]; then h=$(hostname -s); else h=$1; fi
conffile=''
wd=$(dirname $0)
for f in ./vospace.properties.${h} ${wd}/vospace.properties.${h} \
        ./vospace.properties.default ${wd}/vospace.properties.default; do
    if [ -e $f ]; then conffile=$f; break; fi
done
if [ -z $conffile ]; then echo "No vospace configuration found." 1>&2; exit 1; fi
rn=$(grep space.rootnode $conffile | cut -d'=' -f2)
rd=$(grep server.http.basedir $conffile | cut -d'=' -f2)
echo "# $h $conffile $rd"

rcnt=$(( $(echo $rd | tr '/' ' ' | wc -w) + 2 ))
lastu=""

do_clean=0
# Clean up the VOSpace; remove .deleted files and links that don't link back to the VOSpace
for f in $(find $rd/ -depth -name '.deleted'); do
    df=$(dirname $f)
    nf=$(find $df -mindepth 1 -maxdepth 1 | wc -l)
    if [ $do_clean -eq 0 ]; then echo "# rm $f" 1>&2; else echo "# $(rm -v $f)" 1>&2; fi
    if [ $nf -eq 1 ]; then
       if [ $do_clean -eq 0 ]; then echo "# rmdir $df" 1>&2; else echo "# $(rmdir -v $df)" 1>&2; fi
    fi
done
for f in $(find $rd/ -mindepth 1 -type l); do
    if [ $(readlink -f $f | cut -d'/' -f-5) != "$rd" ]; then
        if [ $do_clean -eq 0 ]; then echo "# rm $f" 1>&2; else echo "# $(rm -v $f)" 1>&2; fi
    fi
done

for f in $(find $rd/ -mindepth 1 -not -path "$rd/_*" -a -not -name '.deleted'); do
    fd="file://${f}"
    fn=$(echo $f | sed -e "s|${rd}|${rn}|g")
    u=$(echo $f | cut -d'/' -f$rcnt)
    if [ -z $lastu ]; then lastu=$u; elif [ "$u" != "$lastu" ]; then echo "COMMIT;"; lastu=$u; fi
    if [ "$(echo $f | cut -d'/' -f$(($rcnt + 1)))" == 'public' ]; then pub='True'; else pub='False'; fi
    mt=$(date -d "$(stat -c '%y' $f)" +%Y-%m-%dT%H:%M:%S%z) #modification
    bt=$(date -d "$(stat -c '%z' $f)" +%Y-%m-%dT%H:%M:%S%z) #meta change
    dp=$(( $(echo $f | tr '/' ' ' | wc -w) - $rcnt + 1 ))

    if [ -L $f ]; then typ=2; targ=$(readlink -f $f | sed -e "s|${rd}|${rn}|g")
    elif [ -d $f ]; then typ=3; targ=""
    else typ=1; targ=""; fi

    $sedf -e "s/USER/${u}/g" -e "s/BDATE/${bt}/g" -e "s/MDATE/${mt}/g" -e "s/DATE/${d}/g" -e "s/TYPE/${typ}/g" \
            -e "s/DEPTH/${dp}/g" -e "s|IDENT|${fn}|g" -e "s|FSPEC|${fd}|g" -e "s/PUBLIC/${pub}/g" <<VOBASE
insert ignore into nodes(identifier, depth, type, owner, view, location, creationDate)
    values('IDENT', DEPTH, TYPE, 'USER', 'ivo://ivoa.net/vospace/views/blob', 'FSPEC', now());
insert ignore into properties(identifier, date, ctime, btime, mtime, groupread, groupwrite, ispublic, publicread)
    values('IDENT', 'BDATE', 'DATE', 'BDATE', 'MDATE', 'USER', 'USER', 'PUBLIC', 'PUBLIC');
VOBASE
    if [ -n "$targ" ]; then
        echo "insert ignore into links(identifier, target) values ('$fn', '$targ');"
    fi
done
