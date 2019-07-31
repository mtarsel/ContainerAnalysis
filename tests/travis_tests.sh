#!/bin/bash

#set the whole script to exit if any command fails
set -e

#gets number of columns in results.csv
#head -l outputs the first row of the file
#sed removes everything expect commas
#wc -c gives the character count (includes \n)
check_num_columns () {
	if [ $(head -1 archives/results-$(date +"%d-%b-%Y").csv | sed 's/[^,]//g' | wc -c) != 11 ]; then
	echo "Wrong number of columns in results";
	exit 1;	#travis build should fail if it get the wrong number of columns
	fi
}

#gets number of lines in results.csv
check_num_rows () {
	if [ $(cat archives/results-$(date +"%d-%b-%Y").csv | xargs -l echo | wc -l) == 1 ]; then
	echo "Only 1 row in results!";
	exit 1;
	fi
}

#test different args to get-image-info
python get-image-info.py docs/test_user.yaml
check_num_columns
check_num_rows

python get-image-info.py docs/test_user.yaml --debug
check_num_columns
check_num_rows

python get-image-info.py docs/test_user.yaml --keep
check_num_columns
check_num_rows

python get-image-info.py docs/test_user.yaml --local
check_num_columns
check_num_rows

python get-image-info.py docs/test_user.yaml -kl
check_num_columns
check_num_rows

python get-image-info.py docs/test_user.yaml --test ibm-cam
check_num_columns
check_num_rows

python get-image-info.py --help

#tests if container-output.log exists
if [ ! -f container-output.log ]; then exit 1; fi

