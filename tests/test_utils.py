import pytest

from utils.crawler import get_repo_pages
from utils.setup_utils import progress_bar
from utils.setup_utils import parse_creds
from utils.setup_utils import parse_index_yaml
from utils.setup_utils import travis_trial

#Just a sanity check, if this fails, something is VERY wrong
def test_travis_1():
	assert(travis_trial() == True)


#test get_repo_pages from crawler
def test_get_repo_pages_10():
        assert(get_repo_pages(10) == 1)

def test_get_repo_pages_100():
        assert(get_repo_pages(100) == 1)

def test_get_repo_pages_101():
        assert(get_repo_pages(101) == 2)

def test_get_repo_pages_999():
        assert(get_repo_pages(999) == 10)

def test_get_repo_pages_1000():
        assert(get_repo_pages(1000) == 10)


#test progress_bar function from setup_utils
def test_progress_bar_1_100():
	assert(progress_bar(1, 100) == 1)

def test_progress_bar_1_50():
	assert(progress_bar(1, 50) == 2)

def test_progress_bar_466_693():
	assert(progress_bar(466, 693) == 67)

def test_progress_bar_385_745():
	assert(progress_bar(385, 745) == 51)


#test parse_creds function from setup_utils
def test_parse_creds():
	assert(parse_creds("user.yaml")[0].regis == "hub.docker.com")


#test parse_index_yaml from setup_utils
def test_parse_index_yaml():
	app_list, need_keywords_list = parse_index_yaml("test_index.yaml")
	assert(app_list[0].name == "ibm-ace-dashboard-dev")
	assert(need_keywords_list == [])
