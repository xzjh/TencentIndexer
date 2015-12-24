#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 安卓市场 http://apk.hiapk.com/
# by Jiaheng Zhang, all rights reserved. 2015.11.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'hiapk2'
website_name = "安卓市场 http://apk.hiapk.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['qt'] = 1701
comment_url_args['ps'] = 10
comment_url_base = "http://apk.hiapk.com/web/api.do"
time_format = '%Y%m%d%H%M'

def get_app_info(app_url):

	app_info = {}

	app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')
	soup = BeautifulSoup(app_page_html)

	app_name_and_version = soup.find('div', id = 'appSoftName').text.strip()
	rep = re.compile('(.*)\((.*)\)')
	res = rep.search(app_name_and_version)
	app_info['app_name'] = res.group(1)
	app_info['app_version'] = res.group(2)
	app_info['app_id'] = soup.find('input', id = 'hidAppId').attrs['value']
	star_str = filter(lambda s: 'star_m_' in s, soup.find('div', attrs = {'class': 'star_bg'}).attrs['class'])[0]
	star_str = star_str.split('_')[-1]
	app_info['app_score'] = float(star_str) / 10.0
	uptime_str = soup.find('span', text = '上架时间：').find_next('span').text.strip()
	app_info['app_update_time'] = datetime.strptime(uptime_str, '%Y-%m-%d').strftime(time_format)

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['pi'] = 1
	comment_url_args['id'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base
		print 'Processing comment page: ' + str(comment_url_args['pi'])
		# get the source code of comment page
		data_html = general_func.url_open(comment_url, post_args = comment_url_args)

		# get useful information
		comments_json = json.loads(data_html)['data']

		comment_time = None

		for comment_json in comments_json:

			item = {}
			comment_time = datetime.fromtimestamp(int(comment_json['time']))

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_json['nick']
				item['app_comment_user_rating'] = float(comment_json['rating'])
				item['app_comment_content'] = comment_json['content'].strip()
				item['app_comment_time'] = comment_time.strftime(time_format)
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['pi'] += 1
		else:
			break

	data['app_comments_count'] = len(data['app_comments'])
	data['app_comments_start_time'] = start_time.strftime(time_format)
	data['app_comments_end_time'] = end_time.strftime(time_format)
	data['app_platform'] = website_id

	return data

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']

	page_list = general_func.get_list_from_file(page_list_file)

	for app_url in page_list:

		print "********************************************************************************"
		print "Crawling page: " + app_url

		try:
			# get app info
			app_info = get_app_info(app_url)
			print "App name: " + app_info['app_name'] + ", App ID: " + app_info['app_id']
			app_info['app_id'] = app_info['app_id']

			print "Analyzing comment pages..."

			# get comments data
			data = get_comments_data(app_info, start_time, end_time)
		except:
			print "-- Failed to get the comments of this App!"
			continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_info['app_id'] + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'

		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
