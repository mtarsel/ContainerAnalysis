# The Container Analysis Project
[![Build Status](https://travis-ci.com/mtarsel/ContainerAnalysis.svg?branch=master)](https://travis-ci.com/mtarsel/ContainerAnalysis)

An application to gather information about images and containers on DockerHub and output this helpful info into a CSV file.  

This script will gather information from public data sources. In order to gather information online, you will have to authenticate with the websites. This is why a user.yaml file is required but is not stored in this repo.

## NOTE: currently only supports dockerhub repository
 
# How to Run it

## Create a user.yaml

A yaml file containing creditentials for your repositories (i.e. dockerhub). For example:

```yaml
registries:
  hub.docker.com:
    ibmdev: MTAwecVyZC0=
 ```

_The user.yaml file is required to execute the script._

## Install libraries
```bash
pip3 install -r requirements.txt
```
## Execute script

```bash
python3 get-image-info.py user.yaml
```
After execution is complete, you can view the [results.csv](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/results.pdf) file

A new directory called Applications/ will exist with more info about the Applications and Images.

Please note this script may not print out every result... or correctly. values.yaml are specific to each Application and so they are all written differently.

# Commandline Options

```bash
python get-image-info.py --help
```

You can add your own index.yaml from a Helm Chart if you like.

By default, WARNING level logging is enabled. Otherwise run:
Output is saved to a file called _container-output.log_ in same directory as [get-image-info.py](./get-image-info.py). 


# How To Gather Info on dockerhub.com

Utilizing DockerHub v2 API this will send an HTTP request to a registry like hub.docker.com and
receive a JSON file in return. Read about it [here.](https://docs.docker.com/registry/spec/api/)

This example has no tags for an image
https://hub.docker.com/v2/repositories/ppc64le/couchdb/tags/?page_size=100

This example has 1 tag for an image
https://hub.docker.com/v2/repositories/ppc64le/elk/tags/?page_size=100

This example is the most detailed information we can get for a specific image
tag
https://hub.docker.com/v2/repositories/ppc64le/ibmjava/tags/sdk/

# Contributing

[Read the guide here.](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/CONTRIBUTING.md)

# License
The Container Analysis Project uses the [Apache License Version 2.0](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/LICENSE) software license.
