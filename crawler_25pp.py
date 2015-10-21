#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for PP助手 http://www.25pp.com/
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = '25pp'
website_name = "PP助手 http://www.25pp.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['pagesize'] = 20
comment_url_args['modelid'] = 2
comment_url_args['group'] = 1
comment_url_base = "http://www.25pp.com/api/getComments"
time_format = '%Y%m%d%H%M'

def get_app_info(app_url):

	app_info = {}

	app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')
	soup = BeautifulSoup(app_page_html)

	rep = re.compile('var\s(\w*)\s=\s\"(.*)\";')
	infos_script = soup.find('div', attrs = {'class': 'wrap'}).find_all('script')[-3].text
	infos = dict(rep.findall(infos_script))
	app_info['app_version'] = infos['version']
	app_info['app_id'] = infos['bundleid']
	app_info['app_name'] = infos['shareText']
	update_time_str = soup.find('ul', attrs = {'class': 'edition'}).find_all('li')[3].span.text
	app_info['app_update_time'] = datetime.strptime(update_time_str, '%Y-%m-%d').strftime(time_format)

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['page'] = 1
	comment_url_args['buid'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base
		print 'Processing comment page: ' + str(comment_url_args['page'])
		# get the source code of comment page
		data_html = general_func.url_open(comment_url, post_args = comment_url_args)

		# get useful information
		comments_json = json.loads(data_html)['commentList']

		comment_time = None

		for comment_json in comments_json:

			item = {}
			comment_time = datetime.fromtimestamp(int(comment_json['creatTime']))

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_json['username']
				item['app_comment_content'] = comment_json['content'].strip()
				item['app_comment_time'] = comment_time.strftime(time_format)
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['page'] += 1
		else:
			break

	data['app_comments_count'] = len(data['app_comments'])
	data['app_comments_start_time'] = start_time.strftime(time_format)
	data['app_comments_end_time'] = end_time.strftime(time_format)

	return data

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']

	page_list = general_func.get_list_from_file(page_list_file)

	for app_url in page_list:

		print "********************************************************************************"
		print "Crawling page: " + app_url

		# try:
		# get app info
		app_info = get_app_info(app_url)
		print "App name: " + app_info['app_name'] + ", App ID: " + app_info['app_id']
		app_info['app_id'] = app_info['app_id']

		print "Analyzing comment pages..."

		# get comments data
		data = get_comments_data(app_info, start_time, end_time)
		# except:
		# 	print "-- Failed to get the comments of this App!"
		# 	continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_info['app_id'] + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'

		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
