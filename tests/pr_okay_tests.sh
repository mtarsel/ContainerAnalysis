#!/bin/bash

#set the whole script to exit if any command fails
set -e

#All the tests in this file can be run w/o user.yaml
#and without secure Travis environment variables

#Run python get-image-info with different arguments
python get-image-info.py --help

