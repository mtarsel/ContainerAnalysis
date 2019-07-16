""" Written by Mick Tarsel
	Optimized by Ethan Hansen"""
import sys
import requests
import logging
import argparse
import yaml
import errno
import shutil
import json
from urllib.request import urlretrieve
from objects.hub import Hub
from objects.image import Image
from objects.image import App
#TODO what is actually neded from indexparser
from utils.indexparser import *
from utils.tests import testit
from datetime import datetime

#NEVER CALLED - can be helpful in the future to see what the JSON object looks like
def pp_json(json_thing, sort=True, indents=4):
	""" Nicely print out a JSON string with indents."""
	#pprint(vars(your_object)) #a way to print out all attr in obj
	#import json
	if type(json_thing) is str:
		print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
	else:
		print(json.dumps(json_thing, sort_keys=sort, indent=indents))
	return None

#prints a progress bar as a process runs with
#how many items are complete, how many need to complete,
#and the length of the bar on the screen
def progress_bar(num, total, length):
	#get decimal and integer percent done
	proportion = num / total
	percent = int(proportion * 100)
	#get number of octothorpes to display
	size = int(proportion * length)
	#display [###   ] NN% done
	display = '[' + ('#' * size) + (' ' * (length - size)) + '] ' + str(percent) + '% done'
	#write with stdout to allow for in-place printing
	sys.stdout.write(display)
	sys.stdout.flush()
	sys.stdout.write("\b" * 300)
	#return the proportion for logging
	return percent
	

def setup_logging():
	"""Begin execution here.
	Before we call main(), setup the logging from command line args """
	parser = argparse.ArgumentParser(
					description="A script to get information about images from DockerHub")

	parser.add_argument("user", type=argparse.FileType('r'), help="user.yaml contains creds for Dockerhub and Github")
	parser.add_argument("-d", "--debug",
						help="DEBUG output enabled. Logs a lot of stuff",
						action="store_const", dest="loglevel",
						const=logging.DEBUG, default=logging.WARNING)

	parser.add_argument("-v", "--verbose", help="INFO logging enabled",
					action="store_const", dest="loglevel", const=logging.INFO)

	parser.add_argument("-i", "--index", help="A index.yaml file from a Helm Chart", type=argparse.FileType('r'))

	parser.add_argument("-k", "--keep", help="Keeps old values and chart files", action="store_true", dest="keep_files")
		
	args = parser.parse_args()
		
	logging.getLogger("requests").setLevel(logging.WARNING) #turn off requests

	# let argparse do the work for us
	logging.basicConfig(level=args.loglevel,filename='container-output.log',
						format='%(levelname)s:%(message)s')

	return args

def output_app_keywords(main_image, f):
	""" use keywords from App. no for loop so outputs only once"""

	if 'amd64' in main_image.keywords and 'ppc64le' in main_image.keywords and 's390x' in main_image.keywords:
		f.write('%s,%s,Y,Y,Y\n' %(main_image.product_name,main_image.name)) 
		return

	if 'amd64' in main_image.keywords and 'ppc64le' in main_image.keywords:
		f.write('%s,%s,Y,Y,N\n' %(main_image.product_name,main_image.name)) 
		return
	
	if 'amd64' in main_image.keywords and 's390x' in main_image.keywords:
		f.write('%s,%s,Y,N,Y\n' %(main_image.product_name,main_image.name))
		return

	if 'ppc64le' in main_image.keywords and 's390x' in main_image.keywords:
		f.write('%s,%s,N,Y,Y\n' %(main_image.product_name,main_image.name))
		return

	if 'amd64' in main_image.keywords:
		f.write('%s,%s,Y,N,N\n' %(main_image.product_name,main_image.name))
		return

	if 'ppc64le' in main_image.keywords:
		f.write('%s,%s,N,Y,N\n' %(main_image.product_name,main_image.name))
		return

	if 's390x' in main_image.keywords:
		f.write('%s,%s,N,N,Y\n' %(main_image.product_name,main_image.name))
		return
	# if arch is not in keyword, print it out anyways
	f.write('%s,%s,N,N,N\n' %(main_image.product_name,main_image.name))

def output_CSV(main_image, f):
	"""from a list of images in the App, determine if all the images are supported/
	If all the images are supported then do not output anything.

	This will return to runit() and do it again for another main image
	"""

	output_app_keywords(main_image, f)

	#TODO maybe verify here?

	if main_image.is_bad == True:
		f.write(',,,,,Image is bad!\n')
		return

	for image_obj in main_image.sub_images:

		if image_obj.is_amd64 and image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,Y,Y,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,,%s,%s,Y,Y,Y,N\n' % (image_obj.name, image_obj.container))

		if image_obj.is_amd64 and image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,Y,Y,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,,%s,%s,Y,Y,N,N\n' % (image_obj.name, image_obj.container))
	
		if image_obj.is_amd64 and not image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,Y,N,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,,%s,%s,Y,N,Y,N\n' % (image_obj.name, image_obj.container))
			
		if image_obj.is_amd64 and not image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,Y,N,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,,%s,%s,Y,N,N,N\n' % (image_obj.name, image_obj.container))

		if not image_obj.is_amd64 and image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,N,Y,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,,%s,%s,N,Y,Y,N\n' % (image_obj.name, image_obj.container))

			
		if not image_obj.is_amd64 and image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,N,Y,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',,,,,%s,%s,N,Y,N,N\n' % (image_obj.name, image_obj.container))
			 
		if not image_obj.is_amd64 and not image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',,,,,%s,%s,N,N,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				if image_obj.exist_in_repo == False: #TODO could use app.is_bad??
					main_image.is_bad = True
					f.write(',,,,,%s NOT FOUND IN REPO,%s,N,N,N,N\n' % (image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,N,N,N,N\n' % (image_obj.name, image_obj.container))

def runit(app_list, hub_list):
	""" Initialize the Image object and add tags, repos, and archs to image obj.
	Once Image obj is setup, add it to a sublist of App obj. This function will 
	call output_CSV() for each App from the helm chart."""

	# this list contains apps which repo/org is ppc64le and not ibmcom
	ppc64_list = [ 
		"rabbitmq",
		"open-liberty",
		"couchdb",
		"cassandra",
		"websphere-liberty",
		"nginx"
	] #TODO could utilize find_image()

	#TODO not used yet but may be helpful later
	ibmcorp_list = [
		"ibmcorp/isam",
		"ibmcorp/db2_developer_c",
		"ibmcorp/db2_developer_c"
	]

	f = open("results.csv", "a+")
	f.write("Product,App,amd64,ppc64le,s390x,Images,Container,amd64,ppc64le,s390x,Tag Exists?\n")
	
	#used for the progress bar
	num_tracker = 0
	
	for app_obj in app_list:

		# make sure app and images have all the info we need. if not, its print it out
		app_obj.verify() 
		
		#make a progress bar out of the length of app_list and number already processed
		num_tracker += 1
		percent = progress_bar(num_tracker, len(app_list), 50)
		logging.info("Percent through runit: {}".format(percent))

		for i in range(len(app_obj.images)):

			#TODO since we output CSV during crawling, this check does not happen in testit()
			if app_obj.is_bad == True:
				logging.warning('%s contains a weird image from index.yaml', app_obj.name)
				break
		
			name = str(app_obj.images[i])
			org = str(app_obj.clean_repos[i])

			if len(app_obj.tags) == 0:
				container = "Not found!"
			else: 
				if len(app_obj.tags) < len(app_obj.images):
					container = str(app_obj.tags[0])
				else:
					container = str(app_obj.tags[i])

			if name in ppc64_list:
				org = "ppc64le"

			# initialize Image object
			image_obj = Image(name, org, container)

			final_repo = 'hub.docker.com/' + org + '/' + container
			logging.warning('%s: %s  %s ', app_obj.name, name, final_repo)
			
			regis = 'hub.docker.com/' #TODO - add more repos. this is why hub obj is not really utilized

			for obj in hub_list: 
			#only authorize the regis for the image we want
				if regis == obj.regis:
					obj.token_auth()
					image_obj.header = obj.header
					break

			image_obj.get_image_tag_count(regis)

			if (image_obj.num_tags > 100):
				"""since we use a iterator to store tag name along with data,
					if there is more than 100 tags than no data is stored. we
					only need 1 container to get arch, we still get all the
					data we want"""

				logging.warning('more than 100 tags. Querying several pages')
				image_obj.get_alot_image_tag_names(regis)
					#this function also gets arch for the image.
				logging.warning('no data stored in image_obj')
				# we can only get 100 tag names per page

			if(image_obj.num_tags < 99 and image_obj.num_tags > 0):
				# also gets arch for the image.
				image_obj.get_image_tag_names(regis)

			if image_obj.container in image_obj.tags:
				image_obj.is_container = True
				#now the container is part of image_obj
				image_obj.get_archs(regis, image_obj.container)

			app_obj.sub_images.append(image_obj)
			#From here, all the vars are set for the output.

		# end for loop for sub images of main_image
		output_CSV(app_obj, f) # After creating a list of all the subimages in mainImage, output it
	f.close() #close csv file

def parse_index_yaml(yaml_doc, download_tarfile):
	"""parse index.yaml (the helm chart) and initalize the App object"""

	app_list = [ ]

	if (download_tarfile is True):
		#cleanup from last run
		shutil.rmtree(str(os.getcwd() + "/Applications"), ignore_errors=True)
   
	#keys = MainImage.name, values=url where a tgz file contains values.yaml
	for k, v in yaml_doc["entries"].items():
		app_name = k 
		url_for_app = ''.join(v[0]['urls']) #returns a list with only 1 element = url str
		
		main_image = App(app_name, str(url_for_app))
		
		mkdir_p(str(os.getcwd() + "/Applications/" + main_image.name)) #Create the Applications/app_name dir
		if (download_tarfile is True):
			yaml_location = get_tarfile(main_image) #Download tarballs and start parsing. Inside indexparser.py
			get_app_info(main_image, yaml_location)
		else:
			yaml_location = os.getcwd() + "/Applications/{}/{}/values.yaml".format(main_image.name, main_image.name)
			get_app_info(main_image, yaml_location)

		logging.info('app: %s has %s images', main_image.name, str(len(main_image.images)))
		app_list.append(main_image)

	return app_list

def get_product_name(app_list, github_token):

	charts_repo_url = "https://api.github.com/repos/IBM/charts/contents/stable?ref=master"
	header = {'Authorization': 'token %s' %github_token}
	
	r = requests.get(charts_repo_url, headers=header)
	
	if r.status_code == 403:
		print("hit rate limit. Exiting...")
		sys.exit()

	data = json.loads(r.text)

	if len(app_list) != len(data):
		print("App list in index.yaml does match repo!")
		sys.exit()
 
 	#get the app obj instance
	for app_obj in app_list:
		#iterate thru the request's response to get the link to apps dir where readme is
		for i in range(len(data)):
			if data[i]["name"] == app_obj.name:

				#split the string at the ?ref=, so only use the first half[0] of the url, add the app name and README
				readme_url = str(charts_repo_url.split('?ref=')[0] + "/" + data[i]["name"]+"/README.md")
				#readme_url= str(charts_repo_url.split('?ref=')[0] + "/" + data[0]["name"]+"/README.md")

				#get the readme location
				r_app = requests.get(readme_url, headers=header)
				readme_link = json.loads(r_app.text)

				#get the link for raw readme from api
				raw_readme_link = readme_link['download_url']

				#obtaining the raw readme from API
				r_readme = requests.get(raw_readme_link, headers=header)
				
				readme = r_readme.text

				#get the first line of the long string, remove the # from h1, and strip white space
				product_name = readme.partition('\n')[0].replace('#','').strip()

				#print(product_name)
				app_obj.product_name = product_name

				break #terminate inner for loop - go to next app_obj

def main(args):

	creds_file_loc = str(os.getcwd() + "/" + args.user.name)
	#these vars have to be in the creds_file!
	hub_list = [ ]
	github_token = ""

	if logging.getLogger().level == logging.DEBUG:
		#write a yaml file to easily see exactly what info about each container in the App was parsed
		if os.path.exists("generated_input.yaml") is True:
			os.remove("generated_input.yaml")

	with open(creds_file_loc, 'r') as creds_file:	#Open up creds_file (typically user.yaml) 
		raw_yaml_input = yaml.safe_load(creds_file)	#load the yaml from creds file
		for site_info in raw_yaml_input['registries'].items():	#for each site with creds
			if "hub.docker.com" in site_info[0]:		#site_info[0] is url of site
				"""create a Hub object containing url and creds. return a list of objects"""
				for repos in site_info[1].items():	#site_info[1] is dict of (typically) user:pass
					hub = Hub(site_info[0],repos[0],repos[1]) #Hub(url, user, pass)
					hub_list.append(hub)
			if "github.com" in site_info[0]:
				for tokens in site_info[1].items():
					github_token = tokens[1]

	#optional arg for index.yaml from Helm chart, or just download latest from IBM/charts
	if args.index:
		if args.index.name == "index.yaml":
			index_file = args.index
			index_file = str(os.getcwd() + "/" + args.index.name)
		else:
			print("Please only supply a index.yaml from a Helm Chart. \n Exiting.")
			sys.exit()
	else:
		url = "https://raw.githubusercontent.com/IBM/charts/master/repo/stable/index.yaml"
		index_file_loc = urllib.request.urlretrieve(url)[0]	#returns (localFileName, Headers)

	with open(index_file_loc, 'r') as index_file:		#open the index file
		index_yaml_doc = yaml.safe_load(index_file)	#and load the yaml to the program

	#TODO this will not work with the latest input changes
	#A single run thru for 1 app will exit once complete. 
	# preserves Applications/ with just our single App we are testing
	#testit("ibm-glusterfs", index_yaml_doc) #working example

	app_list = parse_index_yaml(index_yaml_doc, not args.keep_files) #a list of Application objects

	get_product_name(app_list, github_token)

	runit(app_list, hub_list) # does not read generated_input.yaml - uses App object
	"""needs list of hubs (registries) to create special header per each
	image. creates Image objects from images in App. writes to csv 
	file via output_CSV() """

	#TODO - output names of bad apps at end of log
	print("\n========\n")
	i = 0
	for app in app_list:
		if app.is_bad == True:
			i = i + 1
			print(app.name)
	print(i)

if __name__ == "__main__":
	start_time = datetime.now()

	args = setup_logging()
	main(args)

	end_time = datetime.now()
	print("Time to run program: {}".format(end_time - start_time))
