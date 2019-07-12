import pytest

from utils.crawler import get_repo_pages

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

