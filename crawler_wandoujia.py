#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 豌豆夹 http://www.wandoujia.com/
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'wandoujia'
website_name = "豌豆夹 http://www.wandoujia.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['max'] = 20
comment_url_base = "http://apps.wandoujia.com/api/v1/comments"
app_url_base = "http://www.wandoujia.com/apps/"
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + app_id
	app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')

	soup = BeautifulSoup(app_page_html)

	app_info['app_name'] = soup.h1.text
	app_info['app_downloads_count'] = soup.find('i', itemprop = 'interactionCount').text
	soup_infos = soup.find('dl', attrs = {'class': 'infos-list'}).find_all('dt')
	for soup_info in soup_infos:
		if soup_info.text == ur'版本':
			app_info['app_version'] = soup_info.find_next_sibling('dd').text

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['start'] = 0
	comment_url_args['packageName'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		data_html = general_func.url_open(comment_url)

		# get useful information
		comments_json = json.loads(data_html)

		comment_time = None

		for comment_json in comments_json:

			item = {}
			comment_time = datetime.fromtimestamp(comment_json['updatedDate'] / 1000)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_json['author']['name']
				item['app_comment_user_photo'] = comment_json['author']['avatar']
				item['app_comment_content'] = comment_json['content'].strip()
				item['app_comment_time'] = comment_time.strftime(time_format)
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['start'] += 20
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

	for app_id in page_list:

		print "********************************************************************************"
		print "Crawling page: " + app_id

		try:
			# get app info
			app_info = get_app_info(app_id)
			print "App name: " + app_info['app_name'] + ", App ID: " + app_id
			app_info['app_id'] = app_id

			print "Analyzing comment pages..."

			# get comments data
			data = get_comments_data(app_info, start_time, end_time)
		except:
			print "-- Failed to get the comments of this App!"
			continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'

		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"