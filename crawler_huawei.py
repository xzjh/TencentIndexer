#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 华为应用市场 http://appstore.huawei.com/
# by Jiaheng Zhang, all rights reserved. 2016.02.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'huawei'
website_name = "华为应用市场 http://appstore.huawei.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_base = "http://appstore.huawei.com/comment/commentAction.action"
time_format = '%Y%m%d%H%M'

def get_app_info(app_url):

	app_info = {}

	app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')
	soup = BeautifulSoup(app_page_html)

	soup_name = soup.find('span', attrs = {'class': 'title'})
	app_info['app_name'] = soup_name.text
	soup_downloads_count = soup_name.next_sibling
	app_info['app_downloads_count'] = int(soup_downloads_count.text.strip(u'下载次：'))
	soup_app_infos = soup.find_all('li', attrs = {'class': 'ul-li-detail'})
	for soup_app_info in soup_app_infos:
		this_info_text = soup_app_info.text
		if this_info_text.startswith(u'大小'):
			app_info['app_size'] = this_info_text.strip(u'大小：')
		elif this_info_text.startswith(u'版本'):
			app_info['app_version'] = this_info_text.strip(u'版本：')
		elif this_info_text.startswith(u'日期'):
			app_info['app_update_time'] = datetime.strptime(this_info_text.strip(u'日期：'), '%Y-%m-%d').strftime(time_format)

	app_info['app_id'] = soup.find('input', id = 'appId').attrs['value']
	for this_class in soup.find('span', attrs = {'class': re.compile('score_*')}).attrs['class']:
		if this_class.startswith('score_'):
			app_info['app_score'] = float(this_class.split('_')[1]) / 2.0

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['_page'] = 1
	comment_url_args['appId'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + str(comment_url_args['_page'])
		# get the source code of comment page
		data_html = general_func.url_open(comment_url, post_args = comment_url_args)

		# get useful information
		soup_comments = BeautifulSoup(data_html).find_all('div', attrs = {'class': 'comment'})

		comment_time = None

		for soup_comment in soup_comments:

			item = {}
			time_str = soup_comment.find('span', attrs = {'class': 'frt'}).text
			comment_time = datetime.strptime(time_str, '%Y-%m-%d %H:%M')

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				soup_spans = soup_comment.find_all('span')
				item['app_comment_user_name'] = soup_spans[1].text
				for this_class in soup_spans[0].attrs['class']:
					if this_class.startswith('score_'):
						item['app_comment_user_rating'] = float(this_class.split('_')[1]) / 2.0
				item['app_comment_content'] = soup_comment.find('p', attrs = {'class': 'content'}).text.strip()
				item['app_comment_time'] = comment_time.strftime(time_format)
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['_page'] += 1
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
