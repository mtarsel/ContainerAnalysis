""" Written by Mick Tarsel
    Optimized by Ethan Hansen"""
import shutil

from objects.image import Image
from datetime import datetime
from utils.setup_utils import *


def main(args, start_time):
	#storage variables
	creds_file_loc = str(os.getcwd() + "/" + args.user.name)
	if logging.getLogger().level == logging.DEBUG:
		# write a yaml file to easily see exactly what info 
		# about each container in the App was parsed
		if os.path.exists("generated_input.yaml") is True:
			os.remove("generated_input.yaml")
	# get the hub creds (user.yaml)
	hub_list = parse_creds(creds_file_loc)
	# either local or remote
	index_yaml_loc = get_index_yaml(args)
	# a list of Application objects
	app_list, need_keywords_list = parse_index_yaml(index_yaml_loc,
                                                        args.test_names) 
	output_f = setup_output_file()

	#if we don't want to keep and use the old values.yaml
	if ((args.keep_files or args.skip_dockerhub) is not True):
		#cleanup from last run
		shutil.rmtree(str(os.getcwd() + "/Applications"),
			      ignore_errors=True)
	dash_dict = get_dashboard_json()
	num_tracker = 0
	# for each app, get a lot of info on them
	for app in app_list:
		num_tracker += 1
		progress_bar(num_tracker, len(app_list), start_time, 50)
		dest_dir = "{}/Applications/{}/".format(os.getcwd(), app.name)
		mkdir_p(dest_dir)  	# Create the Applications/app/ dir
		app.get_product_name(dest_dir)
		if not args.keep_files:
			# download the values.yaml file into dest_dir
			app.get_values_yaml(dest_dir)
		if logging.getLogger().level == logging.DEBUG or app.name\
        	in need_keywords_list:
		   	app.get_chart_yaml(dest_dir)
		if app.name in need_keywords_list:
			app.parse_chart_yaml(dest_dir)
		app.parse_values_yaml(dest_dir)
		app.clean_image_repo()
		app.repo_crawl(hub_list, args.skip_dockerhub)
		app.output_app_keywords(output_f)
		app.output_CSV(output_f)
		if logging.getLogger().level == logging.DEBUG:
			app.generate_output()
	output_f.close()
	diff_last_files()
	print("\n==== CONFLICT WITH DASHBOARD ====\n")
	for app in app_list:
		if not app.matches_dashboard(dash_dict):
			print(app.name)
	print("\n==== BAD APPS ====\n")
	i = 0
	for app in app_list:
		if app.is_bad:
			i += 1
			print(app.name)
	print("Total: {}".format(i))


if __name__ == "__main__":
	start_time = datetime.now()
	args = setup_logging()
	main(args, start_time)
	end_time = datetime.now()
	print("Time to run program: {}".format(end_time - start_time))

