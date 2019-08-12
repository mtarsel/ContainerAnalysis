import logging
import subprocess
import argparse
import yaml
import urllib
import sys
import os
import errno
import difflib
from json import load

from datetime import datetime, timedelta
from objects.hub import Hub
from objects.image import App


#Just making sure travis CI works for now
def travis_trial():
	print("It works")
	return True


def mkdir_p(path):
	"""Allow us to make sub dirs, just like mkdir -p
	This is used to move the files from the Application tarball 
	into the permanet. Applications dir in the root of the project's 
	dir. Why you ask? For debuggin of course!"""
	try:
		os.makedirs(path)
	except OSError as exc:  # Python >2.5
		if exc.errno == errno.EEXIST and os.path.isdir(path):
			pass
		else:
			raise


#prints a progress bar as a process runs with
#how many items are complete, how many need to complete,
#and the length of the bar on the screen
def progress_bar(num, total, start_time, length=50):
	#get decimal and integer percent done
	proportion = num / total
	percent = int(proportion * 100)
	#get number of octothorpes to display
	size = int(proportion * length)
	# Get runtime to display
	runtime = str(datetime.now() - start_time)
	#display [###   ] NN% done
	display = '[' + ('#' * size) + (' ' * (length - size)) + '] ' + str(percent) + '% done ' + runtime
	#write with stdout to allow for in-place printing
	sys.stdout.write(display)
	sys.stdout.flush()
	sys.stdout.write("\b" * 300)
	#return the proportion for logging
	return percent


def setup_logging():
	"""Begin execution here.
	Before we call main(), setup the logging from command line args """
	parser = argparse.ArgumentParser(description="A script to get \
information about images from DockerHub")
	parser.add_argument("user", 
						type=argparse.FileType('r'), 
						help="user.yaml holds creds for Dockerhub, Github")
	parser.add_argument("-d", "--debug",
						help="DEBUG output enabled. Logs a lot of stuff",
						action="store_const", dest="loglevel",
						const=logging.DEBUG, default=logging.WARNING)
	parser.add_argument("-v", "--verbose", 
						help="INFO logging enabled",
						action="store_const", 
						dest="loglevel", 
						const=logging.INFO)
	parser.add_argument("-i", "--index", 
						help="A index.yaml file from a Helm Chart", 
						type=argparse.FileType('r'))
	parser.add_argument("-k", "--keep", 
						help="Keeps old values and chart files", 
						action="store_true", dest="keep_files")
	parser.add_argument("-l", "--local",
						help="Skip dockerhub requests, use local data",
						action="store_true", dest="skip_dockerhub")
	parser.add_argument("-t", "--test", help="tests a list of specific\
 app names (1 or more input(s))", nargs='+', dest="test_names")

	args = parser.parse_args()
	logging.getLogger("requests").setLevel(logging.WARNING) 
	# let argparse do the work for us
	logging.basicConfig(level=args.loglevel,filename='container-output.log',
						format='%(asctime)s ~ %(levelname)s:\n%(message)s\n')
	return args


def parse_creds(creds_file_loc):
	hub_list = []
	#Open up creds_file (typically user.yaml) 
	with open(creds_file_loc, 'r') as creds_file:
		#load the yaml from creds file 
		raw_yaml_input = yaml.safe_load(creds_file)	
		#for each site with creds
		for site_info in raw_yaml_input['registries'].items():
			#site_info[0] is url of site
			if "hub.docker.com" in site_info[0]:
				"""create a Hub object containing url and creds 
				   return a list of objects"""
				#site_info[1] is dict of (typically) user:pass
				for repos in site_info[1].items():
					#Hub(url, user, pass)
					hub = Hub(site_info[0],
						  repos[0],repos[1])
					hub_list.append(hub)
	return hub_list


def get_index_yaml(args):
	#optional arg in index.yaml from Helm chart or download from IBM/charts
	if args.index:
		if args.index.name == "index.yaml":
			return str(os.getcwd() + "/" + args.index.name)
		else:
			print("Please only supply a index.yaml from a Helm \
Chart. Exiting.")
			sys.exit()
	else:
		url = "https://raw.githubusercontent.com/IBM/charts/master/\
repo/stable/index.yaml"
		#gets index.yaml and returns localFileName
		return urllib.request.urlretrieve(url)[0]	


def parse_index_yaml(index_file_loc, wanted_apps=None):
	app_list = []
	need_keywords_list = []
	with open(index_file_loc, 'r') as index_file:		
		#and load the yaml to the program
		index_yaml_doc = yaml.safe_load(index_file)	
	#keys = MainImage.name, values=other info about the app
	for k, v in index_yaml_doc["entries"].items():	
		app_name = k.replace('/', '')
		#if we didn't specify --test or we specified this app, make it
		if (wanted_apps == None or app_name in wanted_apps):
			url_for_app = "https://raw.githubusercontent.com/IBM/\
charts/master/stable/{}/".format(app_name)
			keywords = []
			try:
				keywords = v[0]['keywords']
			except:
				need_keywords_list.append(app_name)
			main_image = App(app_name, url_for_app)
			for key in keywords:
				main_image.add_keyword(key)
			app_list.append(main_image)
	#currently just apps with names and base urls
	return app_list, need_keywords_list 


def setup_output_file():
	"""Creates and returns file object for writing results"""
	#set up file name, make directory if it doesn't exist
	date = datetime.today().strftime("%d-%b-%Y")	#16-Jul-2019
	results_file_loc = "archives/results-{}.csv".format(date)
	os.makedirs("archives", exist_ok=True)
	#re-writes files on the same day, leaves old files
	f = open(results_file_loc, "w+")
	f.write("Product,App,amd64,ppc64le,s390x,Images,Container,amd64,\
ppc64le,s390x,Tag Exists?\n")
	return f

def diff_last_files(sfile):
	"""Opens today's file and yesterday's, reads the lines, then
		returns the difference between (if there is a difference)
	"""
	# Set up file names for today and yesterday
	slack_list = []
	today = datetime.today().strftime("%d-%b-%Y")  # 26-Jul-2019
	print(today)
	today_file_loc = "archives/results-{}.csv".format(today)
	yesterday = (datetime.today() - timedelta(1)).strftime("%d-%b-%Y")
	yesterday_file_loc = "archives/results-{}.csv".format(yesterday)
	# Open both files (read mode) and remove commas from every line
	today_f_commas = open(today_file_loc, "r").readlines()
	try:
		yesterday_f_commas = open(yesterday_file_loc, "r").readlines()
	except:
		print("\nYesterday's file not found, could not diff files")
		return "Yesterday not found"
	today_lines = [l.replace(",", "") for l in today_f_commas]
	yesterday_lines = [l.replace(",", "") for l in yesterday_f_commas]
	# Print ovnly the diff-ing lines, below progress bar
	print("\n")
	for line in difflib.ndiff(yesterday_lines, today_lines):
		if(line[0] != " "):  # diff-ing lines start with non-space
			slack_list.append(line)
			print(line)
	if slack_list != []:
		sfile.write("==== DIFF IN RESULTS ====\n")
		for i in slack_list:
			sfile.write(i)
	return "Finished properly"


def send_results(slackfile):
	sfile = open(slackfile, "r+")
	slackinfo = sfile.read()
	if slackinfo == "\n":
		print("No diff, no apps in conflict with dashboard")
	else:
		subprocess.call('''curl -X POST -H 'Content-type: application/json' --data '{"text": " %s " }' https://hooks.slack.com/services/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'''%(slackinfo) + "\n", shell=True)
	sfile.close()


def get_dashboard_json():
	""" Tries to return a dict from dash-charts.json, if it exists.
	    If it doesn't exist, None is returned and caught later
	"""

	try:
		dash_json_f = open("dash-charts.json", "r")
		dash_dict = load(dash_json_f)
		return dash_dict
	except:
		print("No dash-charts.json found in directory")
		print("Disregard 'CONFLICTS' section at end of printout")
		return None

