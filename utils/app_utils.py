""" parse_values_yaml() started getting messy, so here we are.
	All of these functions are used to parse tags &&/|| repos.
"""

from nested_lookup import nested_lookup
from itertools import chain, combinations

def parse_both_1(yaml_doc):
	""" parses the tags and repos from a yaml_doc with the format:
		{
 			'appName': {
        		'repository': 'repo/name',
        		'tag': 'X.X.X',
        		'resources': {UNUSED_DICT}
    		}, REPEAT PATERN FOR MORE SUB-IMAGES
		}

		Current known apps with this format:
			ibm-app-navigator
	"""
	tags = nested_lookup(key='tag', document=yaml_doc, wild=True)
	repos = nested_lookup(key='repository', document=yaml_doc, wild=True)
	return tags, repos

def parse_both_2(image_results):
	""" parses the tags and repos from a image_results with the format:
{
 	'image': [{
   		'pluginImage': {
    		'ibmContainerRegistry': 'internalRepo/name' 
    	   	'publicRegistry': 'repo/name'
       	},
   	   	'driverImage': {
   	       	'ibmContainerRegistry': 'internalRepo/name'
   	        'publicRegistry': 'repo/name'
  		},
   		    'pluginBuild': 'X.X.X',
   		    'driverBuild': 'X.X.X',
    	    'pullPolicy': 'Always'
    	}],
   	'pluginImage': [{EXACT SAME CONTENTS AS ABOVE}],
	'driverImage': [{EXACT SAME CONTENTS AS ABOVE}]
}

		Current known apps with this format:
			ibm-object-storage-plugin
	"""
	tags = []
	repos = []
	image_info = image_results['image'][0]
	for k,v in image_info.items():
		if "Build" in k:
			tags.append(v)
		elif "Image" in k:
			repos.append(v['publicRegistry'])
	return tags, repos

def parse_both_3(image_results):
	""" parses the tags and repos from a image_results with the format:
{
    'commonimages': [{
        'imageName': {
            'image': {
                'name': 'imageName',
                'tag': 'long_tag_string'
            }
        }, REPEAT FROM 'imageName',
        'rba': {
            'rbs': {
                'image': {
                    'name': 'hdm-icp-rba-rbs',
                    'tag': '1.16.0-ubi7-minimal-20190607T094727Z-L-MOCR-BC2KPL'
                }
            },
            'as': {
                'image': {
                    'name': 'hdm-icp-rba-as',
                    'tag': '1.16.0-ubi7-minimal-20190607T094727Z-L-MOCR-BC2KPL'
                }
            }
        }
    }],
    'image': [{
        'name': 'imageName',
        'tag': 'long_tag_string'
    }, {
		REPEAT PREVIOUS DICT STRUCTURE
	}, {
        'name': 'hdm-redis-ha'
    }, {
        'repository': 'ibmcom',
        'pullSecret': ''
    }]
}

	Current known apps with this format:
		ibm-cem
"""
	tags = []
	repos = []
	for image in image_results["image"]:
		if list(image.keys()) == ['name', 'tag']:
			repos.append(image['name'])
			tags.append(image['tag'])
	return tags, repos

def parse_tags_1(tag_from_image):
	""" parses the tags from a tag_from_image with the format:
[{
        'activity': '1.0.0-c5bc76a',
        'chirp': '1.0.0-c5bc76a',
        'friend': '1.0.0-c5bc76a',
        'frontend': '1.0.0-c5bc76a'
    },
    [{
        'activity': '1.0.0-c5bc76a',
        'chirp': '1.0.0-c5bc76a',
        'friend': '1.0.0-c5bc76a',
        'frontend': '1.0.0-c5bc76a'
    }]
]

	Current known apps with this format:
		ibm-eventstreams-dev
		ibm-eventstreams-rhel-dev
		ibm-reactive-platform-lagom-sample
"""
	tags = []
	#the first member of the list is a dict so get it
	tag_dict = tag_from_image[0]
	for image,tag in tag_dict.items():
		tags.append(tag)
	return tags

def parse_repos_1(repo_from_image):
	""" parses the repos from a repo_from_image with the format:
[{
    'imageName': 'repo/name',
	'imageName': 'repo/name',
	...
}]

	Current known apps with this format:
		ibm-ace-server-dev
"""
	repos = []
	ace_server_dict = repo_from_image[0]
	for name,repo in ace_server_dict.items():
		repos.append(str(repo))
	return repos

def powerset(iterable):
	""" Returns the powerset of an iterable as a list of lists.
		Much nicer to do this than write out the powerset manually
	"""
	set_list = list(iterable)
	return list(chain.from_iterable(combinations(set_list, r)
								for r in range(len(set_list)+1)))
