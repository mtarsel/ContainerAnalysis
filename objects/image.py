import requests
import json
import logging
import urllib
import re
import yaml

from nested_lookup import nested_lookup
from utils.crawler import find_image
from utils.crawler import get_repo_pages


class App:
	"""This is the App Name but easier to use mainimage, subimage for 
	   documentation. These attributes will be from values.yaml 
	   (from a tgz) which is derived from the big index.yaml file. 
	   Keywords are taken from Chart.yaml which is not saved anywhere.
	"""
	def __init__(self, name, url):
		self.name = name
		self.url = url	#Base url to muddle with later
		#should be same length as keys[1] from yaml
		#all the images for Main image. for output_CSV()
		self.sub_images = [ ] 
		self.keywords = []
		self.repos = [ ] #not parsed
		self.tags = [ ]
		self.images = [ ]
		self.clean_repos = [ ] #sanitized
		# something did't parse correctly so its causing problems
		self.is_bad = False
		self.product_name = '' #taken from README file of app

	def add_keyword(self, keyword):
		self.keywords.append(keyword)

	def verify(self):
		"""iterate thru an App's sub images to make sure we have all 
		   the info we need.
		   if something doesn't seem right, let it be known
		"""
		if len(self.tags) == 0:
			self.is_bad = True
		if len(self.images) == 0:
			self.is_bad = True
		#if images != tags, just use first tag
		#if len(self.images) != len(self.tags) or 
		#len(self.repos) != len(self.images):
		if len(self.repos) != len(self.images):
			self.is_bad = True
		for image_obj in self.sub_images:
			if image_obj.name is None or image_obj.name == "":
				print("gotcha in verify()")
			#iterate thru images in app and 
			#set the app.is_bad var based on image info		
			if image_obj.exist_in_repo == False:
		 		self.is_bad = True

	def get_product_name(self, dest_dir):
		readme_url = self.url + "README.md"	#base url + readme
		dest_loc = dest_dir + "README.md"
		#download and return local file location
		readme_loc = urllib.request.urlretrieve(readme_url, dest_loc)[0]
		#open local file and find the product name
		with open(readme_loc, 'r') as readme:
			readme_lines = readme.readlines()#get list of lines
			regex = re.compile("^# ") 
			#make regex string looking for "# " at the 
			#beginning of a line
			for line in readme_lines: #search all of the lines
				if (regex.search(line) != None):
					#If the regex got a hit make the product
					# name a sanitize version of the line
					self.product_name = line.replace\
					('#','').strip()
					return		
		self.product_name = "NOT FOUND"
		logging.critical("No product_name found in README for {} \
from {}".format(self.name, readme_url))

	def get_chart_yaml(self, dest_dir):
		chart_yaml_url = self.url + "Chart.yaml"#base url + Chart
		dest_loc = dest_dir + "Chart.yaml"
		#download file into applications directory
		urllib.request.urlretrieve(chart_yaml_url, dest_loc)

	def get_values_yaml(self, dest_dir):
		values_yaml_url = self.url + "values.yaml"#base url + Chart
		dest_loc = dest_dir + "values.yaml"
		#download file into applications directory
		urllib.request.urlretrieve(values_yaml_url, dest_loc)

	def parse_values_yaml(self, dir_loc):
		file_loc = dir_loc + "values.yaml"
		with open(file_loc, 'r') as values:
			yaml_doc = yaml.safe_load(values)
		#results from this will contain repository results
		image_results = nested_lookup(key='image', 
					      document=yaml_doc, wild=True, 
					      with_keys=True)
		tag_from_image = nested_lookup(key='tag', 
					       document=image_results, 
					       wild=True)
		if self.name == "ibm-microclimate":
			tag_from_image = [item for sublist in tag_from_image \
			for item in sublist]
		if self.name == "ibm-reactive-platform-lagom-sample" or \
		self.name == "ibm-eventstreams-rhel-dev":
			#this app contains a large list comprised of 
			#another list and a dict
			#all the tags are the same so grab first value in dict
			for tag in tag_from_image:
				if type(tag) is dict:
					for k,v in tag.items():
						tag_from_image = v
		# add the tags to app obj
		if (len(tag_from_image) > 0):
			if self.name == "ibm-eventstreams-dev":
				#the first member of the list is a dict
				tag_dict = tag_from_image[0]
				for image,tag in tag_dict.items():
					self.tags = str(tag)
			else:
				self.tags = tag_from_image
		repo_from_image = nested_lookup(key='repository', 
						document=image_results, 
						wild=True)
		#ibm-ace-server-dev is getting a dict in a list 
		#as the repo_from_image
		if self.name == "ibm-ace-server-dev":
			#the format we get is {image: repo}
			ace_server_dict = next(item for item in repo_from_image)
			for image,repo in ace_server_dict.items():
				self.images.append(str(image))
				self.repos.append(str(repo))
				self.clean_repos.append(str(repo))
			if len(self.images) != len(self.tags):
				#there is a single tag for all the images. 
				#so add more tags
				missing_tags = len(self.images) - len(self.tags)
				for i in range(missing_tags):
					self.tags.append(str(self.tags[0]))
			return
		if (len(repo_from_image) == 0):
			repo_from_image = nested_lookup(key='name', 
							document=image_results, 
							wild=True)
			if (len(repo_from_image) == 0):
				repo_from_image = nested_lookup\
						(key='imageName',
						document=image_results, 
						wild=True)
				if (len(repo_from_image) == 0):
					repo_from_image = nested_lookup\
					(key='Image', document=image_results, 
					 wild=True)	
		#add repos to app obj
		logging.info('%s Num of repos: %s', 
			     self.name, 
			     str(len(repo_from_image)))
		# add repos to app object
		if len(repo_from_image) > 0:
			for repo in repo_from_image:
				#TODO for microclimate, this repo var is 
				#actually a list of 2 repos along with 
				#other lists
				if isinstance(repo, list):
				#could be a sub list 
				#(ibm-microservicebuilder-pipeline)
					for i in repo:
						#print "\n repo is a list, has 
						#member: " + str(i)
						if type(i) is dict: 
						#the image name may be a dict 
						#so iterate
						#print "\n repo is a DICT"
							for k,v in i.items(): 
								if "ibmcom" in \
								str(v) and "/" \
								in str(v):
								#typically this 
								#means all the 
								#repos use one 
								#tag_from_image
									if \
									type(v)\
									 is \
									dict:
										for j,l in v.items():
											if "ibmcom" in str(l) and "/" in str(l):
												self.repos.append(str(v))
											else:
												self.repos.append(str(v))
						if type(i) != dict:
						# it should be in format 
						#org/app_name MUST CONTAIN / 
						#(not a dict)
							if "ibmcom" in str(i) \
							and "/" in str(i):
								self.repos.\
								append(str(i))
				else:
					if '/' in str(repo):
						#SEEMS LIKE THE BEST (ONLY) 
						#WORKING EXAMPLES. repo aint a 
						#sublist and has a slash
						logging.info('repo: %s', repo)
						self.repos.append(repo)
					else:
						repo = "ibmcom/" + repo
						self.repos.append(str(repo))
						#TODO ibm-eventstreams-dev 
						#lands here with "ibmcom" as 
						#the repo!
						#repo is not a list and has no 
#						slash
		else: 
			print("\n Cannot locate any repos for images.\
 \n NADA! \n")

	def parse_chart_yaml(self, dir_loc):
		file_loc = dir_loc + "Chart.yaml"
		with open(file_loc, 'r') as values:
			chart_yaml_doc = yaml.safe_load(values)
			if (len(nested_lookup('keywords', 
					      document=chart_yaml_doc)) > 0):
				keywords = nested_lookup('keywords', 
							 document=\
							 chart_yaml_doc)
				for key in keywords[0]:
					self.add_keyword(key)

	def clean_image_repo(self):
		"""from list of repo strings, get image names and repos.
			will use ibmcom if no repo is there
		"""
		if (len(self.repos) != 0 and self.repos is not None):
			for repo in self.repos:
				if repo is None:#double check it
					continue
				if "ibmcom" in repo:
				#repos = ibmcom/image_name or image_name 
				#or ibmcom
					if "/" in repo:
						self.clean_repos.append\
						(repo.split("/",1)[0])
						self.images.append\
						(repo.split("/",1)[1])
						#this point, have all the info
				else:
					if "/" in repo:
						self.clean_repos.append\
						(repo.split("/",1)[0])
						self.images.append\
						(repo.split("/",1)[1])
					else:
						#its not a repo, 
						#its the image name
						#print "ibmcom NOT in repo. 
						#and NO SLASH!\n"
						self.images.append(repo)
						self.clean_repos.append\
						("ibmcom")
		"""write a yaml file to easily see exactly what info about each 
		container in the App was parsed
		"""
		
	def repo_crawl(self, hub_list):
		""" Initialize the Image object and add tags, repos, and archs 
		    to image obj. Once Image obj is setup, add it to a sublist 
		    of App obj. This function will call output_CSV() for each 
		    App from the helm chart.
		"""
		# this list contains apps which repo/org is ppc64le 
		#and not ibmcom
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
		# make sure app and images have all the info we need. 
		#if not, its print it out
		self.verify() 
		for i in range(len(self.images)):
			#TODO since we output CSV during crawling, 
			#this check does not happen in testit()
			if self.is_bad == True:
				logging.warning('%s contains a weird image \
from index.yaml', self.name)
				break
			name = str(self.images[i])
			org = str(self.clean_repos[i])
			if len(self.tags) == 0:
				container = "Not found!"
			else: 
				if len(self.tags) < len(self.images):
					container = str(self.tags[0])
				else:
					container = str(self.tags[i])
			if name in ppc64_list:
				org = "ppc64le"
			# initialize Image object
			image_obj = Image(name, org, container)
			final_repo = 'hub.docker.com/' + org + '/' + container
			logging.warning('%s: %s  %s ', 
					self.name, 
					name, 
					final_repo)
			
			regis = 'hub.docker.com/' 
			#TODO - add more repos. this is why hub obj is not 
			#really utilized

			for obj in hub_list:
			#only authorize the regis for the image we want
				if regis == obj.regis:
					obj.token_auth()
					image_obj.header = obj.header
					break

			#This is the url we'll query for all the dockerhub info
			image_url = ('https://' + regis + '/v2/repositories/'
			             + image_obj.org + '/' + image_obj.name
				     + '/tags/?page=1&page_size=100')

			# Continue to look at urls for tags until next == none
			while (image_url is not None):
				image_obj.request_data(image_url)
				if (image_obj.exist_in_repo):
					image_obj.get_image_tag_names()
					# If dealing w/ container and haven't 
					#gotten archs
					if (image_obj.container in \
					image_obj.tags
								and len\
								(image_obj.\
								archs) == 0):
						image_obj.is_container = True
						# Now the container is part of 
						#image_obj
						image_obj.get_archs()
					image_url = image_obj.requested_data\
						    ["next"]
				else:
					image_url = None

			# From here, all the vars are set for the output.
			self.sub_images.append(image_obj)

	def output_app_keywords(self, f):
		""" use keywords from App. no for loop so outputs only once"""
		if 'amd64' in self.keywords and 'ppc64le' in self.keywords \
		and 's390x' in self.keywords:
			f.write('%s,%s,Y,Y,Y\n' %(self.product_name,self.name)) 
			return
		if 'amd64' in self.keywords and 'ppc64le' in self.keywords:
			f.write('%s,%s,Y,Y,N\n' %(self.product_name,self.name)) 
			return
		if 'amd64' in self.keywords and 's390x' in self.keywords:
			f.write('%s,%s,Y,N,Y\n' %(self.product_name,self.name))
			return
		if 'ppc64le' in self.keywords and 's390x' in self.keywords:
			f.write('%s,%s,N,Y,Y\n' %(self.product_name,self.name))
			return
		if 'amd64' in self.keywords:
			f.write('%s,%s,Y,N,N\n' %(self.product_name,self.name))
			return
		if 'ppc64le' in self.keywords:
			f.write('%s,%s,N,Y,N\n' %(self.product_name,self.name))
			return
		if 's390x' in self.keywords:
			f.write('%s,%s,N,N,Y\n' %(self.product_name,self.name))
			return
		# if arch is not in keyword, print it out anyways
		f.write('%s,%s,N,N,N\n' %(self.product_name,self.name))

	def output_CSV(self, f):
		#TODO maybe verify here?
		if self.is_bad == True:
			f.write(',,,,,Image is bad!\n')
			return
		for image_obj in self.sub_images:
			if image_obj.is_amd64 and image_obj.is_ppc64le and \
			image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,Y,Y,Y,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,Y,Y,Y,N\n' % \
					(image_obj.name, image_obj.container))
			if image_obj.is_amd64 and image_obj.is_ppc64le \
			and not image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,Y,Y,N,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,Y,Y,N,N\n' % \
					(image_obj.name, image_obj.container))
			if image_obj.is_amd64 and not image_obj.is_ppc64le \
			and image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,Y,N,Y,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,Y,N,Y,N\n' % \
					(image_obj.name, image_obj.container))
			if image_obj.is_amd64 and not image_obj.is_ppc64le \
			and not image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,Y,N,N,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,Y,N,N,N\n' % \
					(image_obj.name, image_obj.container))
			if not image_obj.is_amd64 and image_obj.is_ppc64le \
			and image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,N,Y,Y,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,N,Y,Y,N\n' % \
					(image_obj.name, image_obj.container))
			if not image_obj.is_amd64 and image_obj.is_ppc64le \
			and not image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,N,Y,N,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					f.write(',,,,,%s,%s,N,Y,N,N\n' % \
					(image_obj.name, image_obj.container))
			if not image_obj.is_amd64 and not image_obj.is_ppc64le\
 			and not image_obj.is_s390x:
				if image_obj.is_container == True:
					f.write(',,,,,%s,%s,N,N,N,Y\n' % \
					(image_obj.name, image_obj.container))
				else:
					if image_obj.exist_in_repo == False: 
					#TODO could use app.is_bad??
						self.is_bad = True
						f.write(',,,,,%s NOT FOUND IN \
						REPO,%s,N,N,N,N\n' % \
						(image_obj.name, 
						image_obj.container))
					else:
						f.write(',,,,,%s,%s,N,N,N,N\n'\
						%(image_obj.name, 
						image_obj.container))

	def generate_output(self):
		"""writes to a 'yaml' file using some space and colons."""
		logging.info('%s: Num of images: %s Num of tags: %s \
			     Num of repos: %s', 
			     self.name, str(len(self.images)), 
			     str(len(self.tags)),
 			     str(len(self.images)))
		with open ('generated_input.yaml', 'a') as outputski:
			if len(self.images) != len(self.tags) or \
			len(self.repos) != len(self.images):
				#self.is_bad = True
				outputski.write('# ' + self.name + ':\n')
				outputski.write('# ***ERROR SOMETHING NOT \
				FORMATTED CORRECTLY\n')
				outputski.write('# *** go to ./Applications and\
				 view the values.yaml file\n')
			else:
				outputski.write('  ' + self.name + ':\n')
				for i in range(len(self.images)):
					final_repo = ('hub.docker.com/' 
						      + self.clean_repos[i] 
						      + '/' + str(self.tags[i]))
					image = str(self.images[i])
					if str(self.images[i]) == "" or \
					str(self.images[i]) is None:
						image = "imageNAme" 
						#TODO this is a quick fix for 
						#--debug mode and ibm-cem
					outputski.write('    '+ image + ': '  
							+ final_repo + '\n')


class Image:
	""" This is the object containing all the information we care about.
	    Eventually all the attributes will contain everything we need

            The info we will need to query dockerhub will be from values.yaml, 
	    the	rest of these attributes will be from hub.docker.com
	"""
	def __init__(self, name, org, container):
		self.name = name
		self.org = org # also called repository or repo
		#the important container for this image
		self.container = container 
		self.num_archs = ''
		self.num_tags = ''
		self.is_multiarch = False
		self.is_ppc64le = False
		self.is_amd64 = False
		self.is_s390x = False
		self.archs = [ ]
		self.tags = [ ] # now tag[1] and data[1] give all the info
		self.data = [ ]
		self.header = ''
		self.is_container = False#if container in tags -regex * works
		self.exist_in_repo = True #if it doesnt exist, big problem!
		self.requested_data = ''  # dict requested from dockerhub

	def add_tag(self, tag_name):
		self.tags.append(tag_name)

	def add_arch(self, arch_name):
		self.archs.append(arch_name)
	
	# Given a url, get all the data from it
	def request_data(self, url):
		r = requests.get(url, headers=self.header)  # header from hub
		logging.debug('%s %s %s', self.name, self.org, url)

		# Image is not in this org - big problem!!!
		if r.status_code == 404:
			logging.critical('image: %s does not exist in %s \
organization', self.name, self.org)
			logging.critical(url)
			#TODO find_image(self, regis)
			self.is_container = False
			self.is_multiarch = False
			self.is_ppc64le = False
			self.num_tags = 0
			self.exist_in_repo = False
			return

		r.raise_for_status()
		# Turns the reply into JSON containing dict of strings
		data = json.loads(r.text)
		self.requested_data = data

	# Uses dockerhub data to get names of tags
	def get_image_tag_names(self):
		if (self.num_tags == 0):  # double check to avoid failure
			logging.critical('There is no tags for %s', self.name)
		# results: field in data holds all tag info as list of dicts
		results = self.requested_data["results"]
		for tag in results:
			tag_name = tag["name"]
			self.add_tag(tag_name)
			logging.info('get_image_tag_names: image name: %s tag:\
 %s',
							self.name, \
							self.tags[-1])

	# Uses dockerhub data to get archs for specific image (container)
	def get_archs(self):
		""" determine if specific image tag is multiarch.
			iterate over all the archs and add them to the 
			objects list of archs
		"""
		# results: field in data holds all tag info as list of dicts
		results = self.requested_data["results"]
		# Search results for tag where name is same as container
		wanted_tag = next(tag for tag in results
			     if tag["name"] == self.container)
		self.num_archs = len(wanted_tag["images"])

		if self.num_archs == 1:  # I have one arch so ill take it
			self.is_multiarch = False
			self.add_arch(wanted_tag["images"][0]["architecture"])
		else:
			self.is_multiarch = True
			for arch_name in range(self.num_archs):
				self.add_arch(wanted_tag["images"][arch_name]\
					      ["architecture"])

				if 'ppc64le' in self.archs:
					self.is_ppc64le = True
				if 'amd64' in self.archs:
					self.is_amd64 = True
				if 's390x' in self.archs:
					self.is_s390x = True
