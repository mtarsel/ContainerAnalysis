""" Written by Mick Tarsel
    Optimized by Ethan Hansen"""
import shutil
import csv

from objects.image import Image
from datetime import datetime

from utils.setup_utils import *
from utils.teardown_utils import *


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
	sfile = open("slackfile.txt", "w+")
	diff_last_files(sfile)
	dash_dict = get_dashboard_json()
	num_xtrnl = print_external_conflict_apps(app_list, dash_dict, sfile)
	num_bad = print_bad_apps(app_list)
	num_ntrnl = print_internal_conflict_apps(app_list, sfile)
	sfile.close()
	args_enabled = [key for key,value in vars(args).items() if value is True]
	if logging.getLogger().level == logging.DEBUG:
		args_enabled.append("debug")

	with open("metrics.csv", "a+") as metrics_csv_file:
		metrics_writer = csv.writer(metrics_csv_file)
		metrics_writer.writerow([datetime.now(),
								args_enabled,
								datetime.now()-start_time,
								len(app_list), num_bad,
								num_xtrnl, num_ntrnl])


if __name__ == "__main__":
	start_time = datetime.now()
	args = setup_logging()
	main(args, start_time)
	end_time = datetime.now()
	print("Time to run program: {}".format(end_time - start_time))

