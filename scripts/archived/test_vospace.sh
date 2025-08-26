#!/bin/bash

# This only tests the endpoints in NodeResource.java; GET, PUT, and DELETE.
# It doesn't test transfers; that is left to testing in the StorageManager.

# Arguments are <hostname> <username>
if [ $# -lt 1 ]; then h="dldev.datalab.noao.edu"; else h=$1; fi
if [ $# -lt 2 ]; then u=$USER; else u=$2; fi

wd=$(dirname $0)
if [ $h == "localhost" ]; then pf="docker"; else pf=${h%%.*}; fi
for f in ./vospace.properties.${pf} ${wd}/vospace.properties.${pf} \
        ./vospace.properties.default ${wd}/vospace.properties.default; do
    if [ -e $f ]; then conffile=$f; break; fi
done
if [ -z $conffile ]; then echo "No vospace configuration found." 1>&2; exit 1; fi

ROOT=$(grep -E "^space.rootnode" $conffile | cut -d'=' -f2)
BASE="http://${h}:8080/vospace-2.0/vospace"
AUTH=$(grep -E "^server.auth.url" $conffile | cut -d'=' -f2)

if [ ${AUTH:0:7} = "http://" ]; then
    if [ ! -e $HOME/.datalab/id_token.${u} ]; then
        echo "No token file $HOME/.datalab/id_token.${u}." 1>&2; exit
    fi
    token="X-Dl-Authtoken: $(cat $HOME/.datalab/id_token.${u})"
else
    token="X-Dl-Authtoken: $u.1.1.\$1\$salt\$checksum"
fi
echo "Config: $u $h $conffile $token"

read -r -d '' LINKNODE <<'EOF'
<ns0:node xmlns:ns0="http://www.ivoa.net/xml/VOSpace/v2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" uri="URI" xsi:type="vos:LinkNode">
  <ns0:properties />
  <ns0:accepts />
  <ns0:provides />
  <ns0:capabilities />
<ns0:target>TARGET</ns0:target></ns0:node>
EOF

read -r -d '' DATANODE <<'EOF'
<ns0:node xmlns:ns0="http://www.ivoa.net/xml/VOSpace/v2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" busy="false" uri="URI" xsi:type="vos:DataNode">
  <ns0:properties>
    <ns0:property uri="ivo://datalab.noao.edu/vospace/core#testprop">testval</ns0:property>
  </ns0:properties>
  <ns0:accepts />
  <ns0:provides />
  <ns0:capabilities />
</ns0:node>
EOF

read -r -d '' CONTAINER <<'EOF'
<ns0:node xmlns:ns0="http://www.ivoa.net/xml/VOSpace/v2.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" uri="URI" xsi:type="vos:ContainerNode">
  <ns0:properties>
    <ns0:property uri="ivo://datalab.noao.edu/vospace/core#testprop">testval</ns0:property>
  </ns0:properties>
  <ns0:accepts />
  <ns0:provides />
  <ns0:capabilities />
<ns0:nodes /></ns0:node>
EOF

# URL, protocol
function vo_curl {
    local curl_args=()
    if [ $# -gt 1 ]; then
        curl_args+=("-X" "${2}")
        if [ "${2}" == "PUT" ]; then curl_args+=("-H" "Content-type: text/xml" "-d" "@-"); fi
    fi
    curl -siH "${token}" -w'\n' "${curl_args[@]}" "${BASE}/${1}" \
            | sed -Ee '1s/^.*([[:digit:]]{3}).*$/\1/' -e '2,/^[[:space:]]*$/d' | tr '\n' ' '
}

function vo_get {
    local exstat=201
    local echoit=0
    if [ $# -gt 1 ]; then exstat=$2; fi
    if [ $# -gt 2 ]; then echoit=$3; fi
    local vout=$(vo_curl "nodes/$1")
    local vstat="${vout%%[[:space:]]*}"
    if [ $vstat -eq 200 ]; then
        local vtype=$(echo "$vout" | tr ' ' '\n' | grep ":type" | head -1 | cut -d'"' -f2)
        local node=$(echo "$vout" | tr ' ' '\n' | grep "\"${ROOT}/${1}\"" | cut -d'"' -f2 | sed -e "s|${ROOT}/||g")
        local resp=""
        if [ "$node" != "$1" ]; then node="$1 $node"; fi
        if [ "$vtype" == "vos:ContainerNode" ]; then
            local children=$(echo "$vout" | tr ' ' '\n' | grep "\"${ROOT}/${1}/" | cut -d'"' -f2 | sed -e "s|${ROOT}/||g")
            local nchild=$(echo "$children" | wc -l | tr -d '[:space:]')
            resp="$nchild children"
            if [ $echoit -ne 0 ]; then echo "$children"; fi
        elif [ "$vtype" == "vos:LinkNode" ]; then
            local tgt=$(echo "$vout" | tr ' ' '\n' | grep "<target>" | cut -d'<' -f2 | sed -e "s|${ROOT}/||g" -e "s|>| |g")
            resp="$tgt $resp"
        fi
        echo "OK GET $node $vtype $resp"
    elif [ "$vstat" -eq "$exstat" ]; then
        echo "OK ERROR $vstat GET $1 $vout"
    else
        echo "FAIL $vstat GET $1 $vout"
    fi
}

# Multiple gets with implied success
function vo_gets {
    while [ $# -ne 0 ]; do vo_get $1; shift; done
}

function vo_delete {
    local exstat=204
    if [ $# -gt 1 ]; then exstat=$2; fi
    local vout=$(vo_curl "nodes/$1" "DELETE")
    local vstat=${vout%%[[:space:]]*}
    if [ $vstat -eq 204 ]; then
        echo "OK DELETE $1"
    elif [ $vstat -eq $exstat ]; then
        echo "OK ERROR $vstat DELETE $1 $vout"
    else
        echo "FAIL $vstat DELETE $1 $vout"
    fi
}

# Multiple deletes with implied success
function vo_deletes {
    while [ $# -ne 0 ]; do vo_delete $1; shift; done
}

function vo_container {
    local exstat=201
    if [ $# -gt 1 ]; then exstat=$2; fi
    local vout=$(echo "$CONTAINER" | sed -e "s|URI|${ROOT}/${1}|g" | vo_curl "nodes/$1" "PUT")
    local vstat=${vout%%[[:space:]]*}
    if [ "$vstat" -eq 201 ]; then
        local created=$(echo "$vout" | tr ' ' '\n' | grep "${ROOT}/${1}" | cut -d'"' -f2 | sed -e "s|${ROOT}/||g")
        if [ "$1" != "$created" ]; then echo "OK CREATE CONTAINER $1 $created"
        else echo "OK CREATE CONTAINER $created"; fi
    elif [ "$vstat" -eq "$exstat" ]; then
        echo "OK ERROR $vstat CREATE CONTAINER $1 $vout"
    else
        echo "FAIL $vstat CREATE CONTAINER $1 $vout"
    fi
}

# Multiple creates with implied success
function vo_containers {
    while [ $# -ne 0 ]; do vo_container $1; shift; done
}

function vo_data {
    local exstat=201
    if [ $# -gt 1 ]; then exstat=$2; fi
    local vout=$(echo "$DATANODE" | sed -e "s|URI|${ROOT}/${1}|g" | vo_curl "nodes/$1" "PUT")
    local vstat=${vout%%[[:space:]]*}
    if [ $vstat -eq 201 ]; then
        local created=$(echo "$vout" | tr ' ' '\n' | grep "${ROOT}/${1}" | cut -d'"' -f2 | sed -e "s|${ROOT}/||g")
        if [ "$1" != "$created" ]; then echo "OK CREATE DATA $1 $created"
        else echo "OK CREATE DATA $created"; fi
    elif [ "$vstat" -eq "$exstat" ]; then
        echo "OK ERROR $vstat CREATE DATA $1 $vout"
    else
        echo "FAIL $vstat CREATE DATA $1 $vout"
    fi
}

# Multiple creates with implied success
function vo_datas {
    while [ $# -ne 0 ]; do vo_data $1; shift; done
}

function vo_link {
    local exstat=201
    if [ $# -gt 2 ]; then exstat=$3; fi
    local vout=$(echo "$LINKNODE" | sed -e "s|URI|${ROOT}/${2}|g" -e "s|TARGET|${ROOT}/${1}|g" | vo_curl "nodes/$2" "PUT")
    local vstat=${vout%%[[:space:]]*}
    if [ $vstat -eq 201 ]; then
        local created=$(echo "$vout" | tr ' ' '\n' | grep "${ROOT}/${2}" | cut -d'"' -f2 | sed -e "s|${ROOT}/||g")
        if [ "$2" != "$created" ]; then echo "OK LINK $2 $created -> $1"
        else echo "OK LINK $created -> $1"; fi
    elif [ "$vstat" -eq "$exstat" ]; then
        echo "OK ERROR $vstat LINK $2 $vout"
    else
        echo "FAIL $vstat LINK $2 $vout"
    fi
}

# Multiple creates with implied success
function vo_links {
    while [ $# -gt 1 ]; do vo_link $1 $2; shift; shift; done
}

datenode=$(date +"Z%Y%m%d%H%M")

vo_get "${u}" 200 1
vo_get "NOEXIST/NOEXIST" 404
vo_containers "${u}/${datenode}" "${u}/${datenode}/Z" "${u}/${datenode}/Z/Y"
vo_datas "${u}/${datenode}/DATAX" "${u}/${datenode}/Z/DATAZ" "${u}/${datenode}/Z/Y/DATAY"
vo_links "${u}/${datenode}/Z" "${u}/${datenode}/ZLINK" \
        "${u}/${datenode}/Z/DATAZ" "${u}/${datenode}/Z/DATAZLINK" \
        "${u}/${datenode}/Z/Y/DATAY" "${u}/${datenode}/Z/DATAYLINK" \
        "${u}/${datenode}/Z/DATAYLINK" "${u}/${datenode}/Z/LINKLINK" \
        "${u}/${datenode}/Z/LINKLINK" "${u}/${datenode}/Z/LINKLINKLINK"
vo_container "${u}/${datenode}" 409
vo_container "${u}/${datenode}/DATAX" 409
vo_data "${u}/${datenode}" 409
vo_data "${u}/${datenode}/DATAX" 409
vo_link "${u}/${datenode}/Z/DATAZ" "${u}/${datenode}/ZLINK" 409
vo_link "${u}/${datenode}/DATAX" "${u}/${datenode}/Z" 409
vo_link "${u}/${datenode}/Z/Y/NOEXIST" "${u}/${datenode}/Z/Y/DATAYLINK" 404
vo_data "${u}/${datenode}/Z/Y/X/DATAX" 404
vo_data "${u}/${datenode}/ZLINK/Y/DATAW" 400
vo_data "demo00/NOEXIST" 403
read -rsp $'Press any key to continue...\n' -n1 key
vo_gets "${u}" "${u}/${datenode}" "${u}/${datenode}/Z" "${u}/${datenode}/Z/Y" \
        "${u}/${datenode}/Z/Y/DATAY" "${u}/${datenode}/Z/LINKLINKLINK"
vo_get "${u}/${datenode}/NOEXIST" 404
vo_get "demo00/${datenode}" 403
read -rsp $'Press any key to continue...\n' -n1 key
vo_delete "${u}/${datenode}/ZLINK/Y/DATAY" 400
vo_deletes "${u}/${datenode}/Z/DATAZ"  "${u}/${datenode}/Z/Y/DATAY"
vo_delete "${u}/${datenode}/NOEXIST" 404
vo_get "${u}/${datenode}/Z"
vo_delete "${u}/${datenode}"
vo_get "${u}"
vo_delete "${u}/${datenode}/NOEXIST" 404
vo_delete "demo00/NOEXIST" 403
