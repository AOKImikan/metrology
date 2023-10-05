#!/usr/bin/env bash

resultsDir1=/nfs/space3/tkohno/atlas/ITkPixel/Metrology/results
resultsDir2=/nfs/space3/tkohno/atlas/ITkPixel/Metrology/pmmWork
resultsDir3=/nfs/space3/itkpixel/Metrology/results

function prepPcbMetrologyUpload() {
    sn=$1
    stage=$2
    number=$3
    resultsDir=${resultsDir1}
    if [[ ${#} -ge 4 ]]; then
	resultsDir=$4
    fi
    dataFile=${resultsDir}/PCB/${sn}/${stage}/${number}/db.json
    ./scripts/prepCsvUpload.py -d ${dataFile}\
			       -t csv_templates/PCB_Metrology_Test.csv\
			       -s $sn \
			       -o pcb_metrology_test.csv
}


prepPcbMetrologyUpload 20UPGPQ2110199 PCB_POPULATION 007 ${resultsDir3}
