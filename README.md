# The Container Analysis Project
[![Build Status](https://travis-ci.com/mtarsel/ContainerAnalysis.svg?branch=master)](https://travis-ci.com/mtarsel/ContainerAnalysis)

An application to gather information about images and containers on DockerHub and output this helpful info into a CSV file.  

This script will gather information from public data sources. In order to gather information online, you will have to authenticate with the websites. This is why a user.yaml file is required but is not stored in this repo.

**NOTE: currently only supports dockerhub repositories**
 
## How to Run it

There are two ways to run CAP, either running get-image-info.py after cloning this repo, or running a docker image of this repo. If you just want to get basic, critical data about the apps in the [IBM charts repo](https://github.com/IBM/charts), skip down to [Running with Docker Image](https://github.com/1ethanhansen/ContainerAnalysis/blob/dockerize/README.md#running-with-docker-images). If you want to get the full information and/or hack on this project, keep reading below.

### Running with Python Code

#### Repo setup
This project is really meant to be run in a virutal environment, so here are the basics of setting that up.

1. clone this repo
2. go the directory that it cloned into
3. create a python 3.7 virtual environment
4. activate the python 3.7 virual environment
5. run `pip3 install -r requirements.txt`

#### Create a user.yaml
A yaml file containing creditentials for your repositories (i.e. dockerhub) with the format:
```yaml
registries:
  REGISTRY:
    USER: PASS
```
Where `REGISTRY`, `USER`, and `PASS` are replaced with your specific information. For example:
```yaml
registries:
  hub.docker.com:
    ibmdev: MTAwecVyZC0=
 ```
_The user.yaml file is required to execute the script._

#### Execute script
```bash
python3 get-image-info.py user.yaml
```
In the terminal there will be information about the run including differences from yesterday's results, apps that conflict with the dashboard, apps where something didn't parse correctly, apps that have internal inconsistencies in the supported architectures, and the time to run the program.

Metrics.csv in the same directory as get-image-info.py will hold a summary of all of that information for each run of the program, with a timestamp.

After execution is complete, you can view the results-DATE.csv file in the archvies directory. An example results file can be found in the [docs](./docs) directory.

A new directory called Applications/ will exist with more info about the Applications and Images. This holds values.yaml files and potentially Chart.yaml files for the application, as well as the .json data from dockerhub about each sub-image contained within that application.

Please note this script may not print out every result... or correctly. values.yaml are specific to each Application and so they are all written differently.

#### Commandline Options
```bash
python get-image-info.py --help
```
This will print all of the different options which should be pretty self-explanatory.

You can add your own index.yaml from a Helm Chart if you like.

By default, WARNING level logging is enabled. Otherwise run with the flag --debug or -d.

Log output is saved to a file called _container-output.log_ in same directory as [get-image-info.py](./get-image-info.py). 

### Running with Docker Images
**NOTE: the docker image can currently only run the base program without any CLI options**

That means you can't access any of the outputs mentioned in the [Running with Python Code](https://github.com/1ethanhansen/ContainerAnalysis/blob/dockerize/README.md#running-with-python-code) section besides the terminal outputs.
If you want more flexibility or want to track outputs over time, please set this project up to allow you to run Python code as described [here](https://github.com/1ethanhansen/ContainerAnalysis/blob/dockerize/README.md#running-with-python-code).
If you just want to run it to get the most up-to-date data about issues internally in the [IBM charts repo](https://github.com/IBM/charts), using the Docker images is the way to go.

#### Setup
1. make sure you have docker ce installed.
2. go to [the docker repo](https://hub.docker.com/r/1ethanhansen/container_analysis_project)
3. find the latest tag (version) substitute it for TAG below
4. run `docker pull 1ethanhansen/container_analysis_project:TAG`

#### Run Docker Image
1. run `docker run 1ethanhansen/container_analysis_project:TAG`

## How To Gather Info on dockerhub.com

Utilizing DockerHub v2 API this will send an HTTP request to a registry like hub.docker.com and
receive a JSON file in return. Read about it [here.](https://docs.docker.com/registry/spec/api/)

This example has no tags for an image
https://hub.docker.com/v2/repositories/ppc64le/couchdb/tags/?page_size=100

This example has 1 tag for an image
https://hub.docker.com/v2/repositories/ppc64le/elk/tags/?page_size=100

This example is the most detailed information we can get for a specific image
tag
https://hub.docker.com/v2/repositories/ppc64le/ibmjava/tags/sdk/

## Contributing
[Read the guide here.](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/CONTRIBUTING.md)

## License
The Container Analysis Project uses the [Apache License Version 2.0](https://github.com/mtarsel/ContainerAnalysis/blob/master/docs/LICENSE) software license.
