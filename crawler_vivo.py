#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for vivo手机助手 http://zs.vivo.com.cn
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'vivo'
website_name = "vivo手机助手 http://zs.vivo.com.cn"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_base = "http://pl.appstore.vivo.com.cn/port/comments/"
comment_url_args = {
	'app_version': '1021',
	'cs': '0',
}
app_url_base = "http://info.appstore.vivo.com.cn/port/package/"
app_url_args = {
	'app_version': '1021',
	'content_complete': '1',
}
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url_args['id'] = app_id
	app_url = app_url_base + '?' + urllib.urlencode(app_url_args)
	app_page_raw = general_func.url_open(app_url)

	data_json = json.loads(app_page_raw)['value']
	app_info['app_name'] = data_json['title_zh']
	app_info['app_package_name'] = data_json['package_name']
	app_info['app_score'] = data_json['score']
	app_info['app_comments_total_count'] = data_json['raters_count']
	app_info['app_version'] = data_json['version_name']
	app_info['app_size'] = data_json['size']
	app_info['app_download_url'] = data_json['download_url']
	app_info['app_download_count'] = data_json['download_count']

	app_info['app_id'] = app_id

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['id'] = app_info['app_id']
	comment_url_args['page_index'] = 1

	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		data_raw = general_func.url_open(comment_url)
		data_json = json.loads(data_raw)
		page_num = int(data_json['maxPage'])
		if comment_url_args['page_index'] > page_num:
			break
		comments_json = data_json['value']

		comment_time = None

		# get useful information
		for comment_item in comments_json:

			item = {}
			comment_time = datetime.strptime(comment_item['comment_date'], '%Y-%m-%d %H:%M:%S')

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_item['user_name']
				item['app_comment_user_score'] = float(comment_item['score'])
				item['app_comment_content'] = comment_item['comment']
				item['app_comment_time'] = comment_time.strftime(time_format)
				item['app_comment_app_version'] = comment_item['appversion']
				item['app_comment_device_model'] = comment_item['model']

				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['page_index'] += 1
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

		app_id = app_id.strip('\n')

		print "********************************************************************************"
		print "Crawling page: " + app_id

		# try:
		# get app info
		app_info = get_app_info(app_id)
		print "App name: " + app_info['app_name'] + ", App ID: " + app_id

		print "Analyzing comment pages..."

		# get comments data
		data = get_comments_data(app_info, start_time, end_time)
		# except:
		# 	print "-- Failed to get the comments of this App!"
		# 	continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
