#!/bin/bash

python get-image-info.py --help

python get-image-info.py user.yaml

python get-image-info.py user.yaml --debug

if [ $(head -1 results.csv | sed 's/[^,]//g' | wc -c) != 11 ]; then
echo "Wrong number of columns in results";
exit 1;
fi
