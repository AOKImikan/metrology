#!/usr/bin/env bash

prog=./fitFmark.py
scanDir=/nfs/space3/itkpixel/Metrology/data/2023.05/PreProdAssembledFlexITkv4.1_327647_0104_Size_-1_1

file=${scanDir}/Img100872.jpg

${prog} -i $file -b


