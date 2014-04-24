#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 91.com http://www.91.com/
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = '91'
website_name = "91.com http://www.91.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['ResourceType'] = '1'
comment_url_args['pagesize'] = '10'
comment_url_args['order'] = '2'
comment_url_args['format'] = 'json'
comment_url_base = "http://comment.sj.91.com/Service/GetComment.aspx"
app_url_base = "http://apk.91.com/Soft/Android/"
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + app_id + '.html'
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.find('div', attrs = {'class': 's_title'}).contents[1].contents[0].strip()
	soup_app_info = soup.find('ul', attrs = {'class': 's_info'})
	app_info['app_version'] = soup_app_info.contents[1].contents[0].split(u'：')[1].strip()
	app_info['app_downloads_count'] = soup_app_info.contents[3].contents[0].split(u'：')[1].strip()
	app_info['app_score'] = float(soup.find('span', attrs = {'class': 'star'}).contents[0].attrs['class'][0][1:])

	comment_url_args['ResourceID'] = soup.find('input', attrs = {'name': 'ResourceID'}).attrs['value']

	return app_info

# get the App ID from the page url
def get_app_id(app_url):
	
	rep = re.compile("(?<=Android\/).+?(?=\.html)")
	result = rep.findall(app_url)
	if len(result) > 0:
		return True, result[0]
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['pageindex'] = 1
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		data_raw = general_func.url_open(comment_url)
		data_json = json.loads(data_raw)

		if len(data_json['list']) == 0:
			break;

		# get useful information
		for comment_item in data_json['list']:

			item = {}
			comment_time = datetime.strptime(comment_item['p'], "%Y-%m-%d %H:%M:%S").replace(second = 0)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_item['un']
				item['app_comment_user_id'] = comment_item['ui']
				item['app_comment_content'] = comment_item['data']
				item['app_comment_time'] = comment_time.strftime(time_format)
				item['app_comment_user_score'] = int(comment_item['s']) / 2
				item['app_comment_agree_count'] = int(comment_item['up'])
				item['app_comment_disagree_count'] = int(comment_item['dn'])

				data['app_comments'].append(item)

			else:
				break

		if comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['pageindex'] += 1
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

		app_url = app_url.strip('\n')

		print "********************************************************************************"
		print "Crawling page: " + app_url

		# get app id from app url
		is_success, app_id = get_app_id(app_url)
		if is_success:
			comment_url_args['app_id'] = app_id
		else:
			print "Wrong page URL: " + app_url
			continue

		# get app info
		app_info = get_app_info(app_id)
		print "App name: " + app_info['app_name'] + ", App ID: " + app_id
		app_info['app_id'] = app_id

		print "Analyzing comment pages..."

		# get comments data
		data = get_comments_data(app_info, start_time, end_time)

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'

		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"