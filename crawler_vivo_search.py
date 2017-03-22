#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for vivo搜索
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'vivo_search'
website_name = "vivo搜索"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_base = "http://search.appstore.vivo.com.cn/port/packages/"
comment_url_args = {}
comment_url_args['app_version'] = '1021'
comment_url_args['page_index'] = '1'
comment_url_args['av'] = '19'
time_format = '%Y%m%d%H%M'

def get_app_info(search_keyword):

	app_info = {}
	app_info['search_keyword'] = search_keyword

	return app_info

def get_comments_data(app_info):

	data = app_info
	comment_url_args['key'] = app_info['search_keyword']

	# the url of comment page
	comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
	print 'Processing comment page: ' + comment_url
	# get the source code of comment page
	data_raw = general_func.url_open(comment_url)
	data_json = json.loads(data_raw)['value']
	data['results'] = []
	for this_item_data_json in data_json:
		this_item_data = {}
		this_item_data['app_name'] = this_item_data_json['title_zh']
		this_item_data['is_official'] = True if this_item_data_json['official'] == '1' else False
		this_item_data['app_id'] = str(this_item_data_json['id'])
		this_item_data['app_description'] = this_item_data_json.get('remark', '')
		data['results'].append(this_item_data)
	data['results_count'] = len(data['results'])

	return data

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	page_list = general_func.get_list_from_file(page_list_file)

	for app_keyword in page_list:

		app_keyword = app_keyword.strip('\n')

		print "********************************************************************************"
		print "Crawling search result: " + app_keyword

		app_info = get_app_info(app_keyword)
		data = get_comments_data(app_info)

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_keyword + '.json'
		
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
