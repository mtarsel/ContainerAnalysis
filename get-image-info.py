""" Written by Mick Tarsel"""
import sys
import requests
import json
import logging
import argparse
import yaml
import tarfile
import errno
import shutil
from urllib import urlretrieve
from objects.hub import Hub
from objects.image import Image
from objects.image import App
from utils.indexparser import *

#NEVER CALLED
def pp_json(json_thing, sort=True, indents=4):
	""" Nicely print out a JSON string with indents."""
	#pprint(vars(your_object)) #a way to print out all attr in obj
	if type(json_thing) is str:
		print(json.dumps(json.loads(json_thing), sort_keys=sort, indent=indents))
	else:
		print(json.dumps(json_thing, sort_keys=sort, indent=indents))
	return None

def setup_logging():
	"""Begin execution here.
	Before we call main(), setup the logging from command line args """
	parser = argparse.ArgumentParser(
					description='A script to get information about images from DockerHub')

	parser.add_argument('-d', '--debug',
						help="DEBUG output enabled. Logs a lot of stuff",
						action="store_const", dest="loglevel",
						const=logging.DEBUG, default=logging.WARNING)

	parser.add_argument('-v', '--verbose',help="INFO logging enabled",
					action="store_const", dest="loglevel", const=logging.INFO)

	parser.add_argument('file', help="yaml file containing username/password and Image info", metavar='FILE.yaml')
		
	args = parser.parse_args()
		
	logging.getLogger("requests").setLevel(logging.WARNING) #turn off requests

	# let argparse do the work for us
	logging.basicConfig(level=args.loglevel,filename='container-output.log',
						format='%(levelname)s:%(message)s')

def get_registries(yaml_doc):
	"""setup Hub objects and store in a list of objects"""

	hub_list = [ ]

	with open(yaml_doc, 'r') as input_file:
		yaml_doc = yaml.safe_load(input_file)
	
	for url in yaml_doc['registries'].iteritems():
		for repos in url[1].iteritems():
			hub = Hub(url[0],repos[0],repos[1])
			hub_list.append(hub)
	return hub_list

def output_CSV(main_image, f):
	"""from a list of images in the App, determine if all the images are supported/
	If all the images are supported then do not output anything.

	This will return to runit() and do it again for another main image
	"""

	f.write('%s\n' %(main_image.name)) #just output this once

	if len(main_image.images) != len(main_image.tags) or len(main_image.repos) != len(main_image.images):
		f.write(',Images not parsed correctly from index.yaml\n')
		return

	for image_obj in main_image.sub_images:
		  
		if image_obj.is_amd64 and image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,Y,Y,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',%s,%s,Y,Y,Y,N\n' % (image_obj.name, image_obj.container))

		if image_obj.is_amd64 and image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,Y,Y,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',%s,%s,Y,Y,N,N\n' % (image_obj.name, image_obj.container))
	
		if image_obj.is_amd64 and not image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,Y,N,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',%s,%s,Y,N,Y,N\n' % (image_obj.name, image_obj.container))
			
		if image_obj.is_amd64 and not image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,Y,N,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',%s,%s,Y,N,N,N\n' % (image_obj.name, image_obj.container))

		if not image_obj.is_amd64 and image_obj.is_ppc64le and image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,N,Y,Y,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',%s,%s,N,Y,Y,N\n' % (image_obj.name, image_obj.container))

			
		if not image_obj.is_amd64 and image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,N,Y,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				f.write(',%s,%s,N,Y,N,N\n' % (image_obj.name, image_obj.container))
			 
		if not image_obj.is_amd64 and not image_obj.is_ppc64le and not image_obj.is_s390x:
			if image_obj.is_container == True:
				f.write(',%s,%s,N,N,N,Y\n' % (image_obj.name, image_obj.container))
			else:
				if image_obj.exist_in_repo == False:
					f.write(',%s NOT FOUND IN REPO,%s,N,N,N,N\n' % (image_obj.name, image_obj.container))
				else:
					f.write(',%s,%s,N,N,N,N\n' % (image_obj.name, image_obj.container))

def runit(app_list, hub_list):
	"""This function will call output_CSV() for each App from the helm chart"""

	f = open("results.csv", "a+")
	f.write("App,Images,Container,amd64,ppc64le,s390x,Container Exists?\n")

	for app_obj in app_list:
		for i in range(len(app_obj.images)):

			if len(app_obj.images) != len(app_obj.tags) or len(app_obj.repos) != len(app_obj.images):
				logging.warning('%s contains a weird image from index.yaml', app_obj.name)
				break
			
			final_repo = 'hub.docker.com/' + app_obj.clean_repos[i] + '/' + str(app_obj.tags[i])
			logging.warning('%s: %s  %s ', app_obj.name, str(app_obj.images[i]), final_repo)
		
			image_obj = Image(app_obj.images[i], app_obj.clean_repos[i], str(app_obj.tags[i])) #init image object with name
			regis = 'hub.docker.com/' #TODO - add more repos

			for obj in hub_list: #only authorize the regis for the image we want
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
		#After creating a list of all the subimages in mainImage, output it
		output_CSV(app_obj, f)
	f.close() #close csv file

def mkdir_p(path):
	"""Allow us to make sub dirs, just like mkdir -p
	This is used to move the files from the Application tarball into the permanet 
	Applications dir in the root of the project's dir. Why you ask? For debuggin of course!"""
	try:
		os.makedirs(path)
	except OSError as exc:  # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise

def parse_index_yaml(yaml_doc):
	"""parse index.yaml (the helm chart) and initalize the App object"""

	app_list = [ ]
   
	#keys = MainImage.name, values=url where a tgz file contains values.yaml
	for k, v in yaml_doc["entries"].iteritems():
		app_name = k 
		url_for_app = ''.join(v[0]['urls']) #returns a list with only 1 element = url str
		
		main_image = App(app_name, str(url_for_app))
		
		#TODO using black list from utils/indexparser.py
		if main_image.name not in black_list:
			mkdir_p(str(os.getcwd() + "/Applications/" + main_image.name)) #Create the Applications/app_name dir
			get_tarfile(main_image) #Download tarballs and start parsing

		logging.info('app: %s has %s images', main_image.name, str(len(main_image.images)))
		app_list.append(main_image)

	return app_list

def add_header_to_yaml():
	"""add creds and proper formatting to yaml so we can runit"""

	#if we are not in debug mode, still need creds, so create the file
	if os.path.exists("generated_input.yaml") is False:
		open("generated_input.yaml", 'a').close()

	generated_input = os.getcwd() + "/generated_input.yaml"

	f = open(generated_input, "r")
	contents = f.readlines()
	f.close()

	contents.insert(0, "registries:\n")
	contents.insert(1, "  hub.docker.com:\n")
	contents.insert(2, "    ibmdev: MTAweWFyZC0=\n")
	contents.insert(3, "container-images:\n")

	f = open(generated_input, "w")
	contents = "".join(contents)
	f.write(contents)
	f.close()

	return generated_input

def main():

	#first setup registries for url access
	if ( len(sys.argv) <  2):
		print "***ERROR: Please provide a single yaml file to parse!\n"
		print "Usage:\n python get-image-info.py index.yaml"
		sys.exit()

	if (str(sys.argv[1]).endswith('.yaml')):
		with open(sys.argv[1], 'r') as input_file:
			index_yaml_doc = yaml.safe_load(input_file)
	else:
		print "***ERROR: Please provide a yaml file to parse!\n"
		print "Usage:\n python get-image-info.py index.yaml"
		sys.exit()

	shutil.rmtree(str(os.getcwd() + "/Applications"), ignore_errors=True)

	"""write a yaml file to easily see exactly what info about each 
	container in the App was parsed"""
	if logging.getLogger().level == logging.DEBUG:
		if os.path.exists("generated_input.yaml") is True:
			os.remove("generated_input.yaml")

		#TODO how to handle repo different user/passwords?
		yaml_doc = add_header_to_yaml() # add creds to top of yaml file

		with open(yaml_doc, 'r') as input_file:
			yaml_doc = yaml.safe_load(input_file)

		if len(yaml_doc) > 2:
			print "[registries] \n [container-images] \n format only!"
			sys.exit()

	app_list = parse_index_yaml(index_yaml_doc)
	#returns generated_input.yaml and all the info we need to crawl

	yaml_doc = add_header_to_yaml() # add creds to top of yaml file

	hub_list = get_registries(yaml_doc)
	"""create a Hub object containing url and creds. return a list of
	objects"""

	runit(app_list, hub_list) # does not read generated_input.yaml - uses App object
	"""needs list of hubs (registries) to create special header per each
	image. creates Image objects from images in App. writes to csv 
	file via output_CSV() """


if __name__ == "__main__":
	setup_logging()
	main()