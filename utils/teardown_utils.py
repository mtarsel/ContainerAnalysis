""" This is the mirror image of setup_utils.py.
	Whereas that sript has functions to get ready for main,
	this script has functions that finish up the program.
"""

from datetime import datetime, timedelta
import difflib
from json import load

def print_external_conflict_apps(app_list, dash_dict, sfile):
	"""Prints out all of the app names that conflict with dashboard."""
	conflict_list = []
	print("\n==== CONFLICT WITH DASHBOARD ====\n")
	for app in app_list:
		if not app.matches_dashboard(dash_dict):
			conflict_list.append(app.name)
			print(app.name)
	if conflict_list != []:
                sfile.write("\n==== CONFLICT WITH DASHBOARD ====\n")
                for i in conflict_list:
                        sfile.write(i + "\n")
	print("Total mismatched: {}".format(len(conflict_list)))
	return len(conflict_list)


def print_bad_apps(app_list):
	""" Prints out all of the apps that didn't parse correctly
		and those with images that weren't found in repo.
	"""
	i = 0
	print("\n==== BAD APPS ====\n")
	for app in app_list:
		if app.is_bad:
			print(app.name)
			i += 1
	print("Total bad apps: {}".format(i))
	return i


def print_internal_conflict_apps(app_list, sfile):
	""" Prints apps where the app's supported architectures are not
		the same as all of the sub-images' supported architectures.
	"""
	conflict_list = []
	print("\n==== APP ARCHS CONFLICT WITH IMAGE ARCHS ====\n")
	for app in app_list:
		if not app.archs_match:
			conflict_list.append(app.name)
			print(app.name)
	if conflict_list != []:
                sfile.write("\n==== APP ARCHS CONFLICT WITH IMAGE ARCHS ====\n")
                for i in conflict_list:
                        sfile.write(i + "\n")
	print("Total internally conflicting apps: {}".format(len(conflict_list)))
	return len(conflict_list)


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

