#!/usr/bin/env bash

filelist=($(cat filelist.txt))
for db in ${filelist[@]};do
    dn=$(dirname $db)
    echo $dn
    db0=$dn/db_v0.json
    ls $db
    if [[ -e $db ]];then
	cp $db $db0
    fi
    db2=$dn/db_v2.json
    db0=$dn/db_v2.0.json
    if [[ -e $db2 ]];then
	cp $db2 $db0
    fi
done
