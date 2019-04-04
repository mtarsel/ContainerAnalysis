# The Container Analysis
An application to gather information about images and containers on DockerHub.

## NOTE: currently only supports dockerhub repoistory
 
# How to Run it

```bash
wget https://raw.githubusercontent.com/IBM/charts/master/repo/stable/index.yaml
python get-image-info.py index.yaml
```
After execution is complete, you can view the Applications/

Please note this script may not print out every result... or correctly. values.yaml are specific to each Application and so they are all written differently.

## Specify Logging

By default, WARNING level logging is enabled. Otherwise run:

```bash
python get-image-info.py --help
```

Output is saved to a file called container-output.log in same directory as [get-image-info.py](./get-image-info.py). 

# Python Installation

Tested with Python 2.7

```bash
pip install -r requirements.txt
```

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
