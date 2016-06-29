#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for PP助手 http://www.25pp.com/ ver.2.0 updated on 06/29/2016
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
comment_url_base = "http://www.25pp.com/api/getComments"
comment_url_base = None
comment_url_base_dict = {}
comment_url_base_dict['android'] = "http://www.25pp.com/android/api/getCommentList/"
comment_url_base_dict['ios'] = "http://www.25pp.com/ios/api/getCommentList/"
time_format = '%Y%m%d%H%M'

def get_app_info(app_url):

	global comment_url_base

	app_info = {}

	rep_app_url = re.compile(r'25pp\.com/(.+?)/detail_(\d+?)/')
	res_app_url = rep_app_url.search(app_url)
	platform_type = res_app_url.group(1)
	comment_url_base = comment_url_base_dict[platform_type]
	app_info['app_id'] = res_app_url.group(2)
	app_info['app_platform'] = platform_type

	app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')
	soup = BeautifulSoup(app_page_html)

	app_info['app_name'] = soup.h1.text.strip()
	app_info['app_score'] = float(soup.find('div', class_ = 'app-score').attrs['title'].strip(ur'分'))

	soup_app_info = soup.find('div', class_ = 'app-detail-info').find_all('p')
	soup_app_info_1 = soup_app_info[0].find_all('span')
	update_time_str = soup_app_info_1[0].strong.text.strip()
	app_info['app_update_time'] = datetime.strptime(update_time_str, '%Y-%m-%d').strftime(time_format)
	app_info['app_size'] = soup_app_info_1[1].strong.text.strip()
	soup_app_info_2 = soup_app_info[1].find_all('span')
	app_info['app_version'] = soup_app_info_2[0].strong.text.strip()

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['page'] = 1
	comment_url_args['id'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base
		print 'Processing comment page: ' + str(comment_url_args['page'])
		# get the source code of comment page
		data_html = general_func.url_open(comment_url, post_args = comment_url_args)

		# get useful information
		comments_html = json.loads(data_html)['result']
		soup_comments = BeautifulSoup(comments_html).find_all('div', class_ = 'comment-item')

		comment_time = None

		for soup_comment in soup_comments:

			item = {}
			comment_time_str = soup_comment.find('span', class_ = 'pub-date').text \
				.replace(ur'年', '-') \
				.replace(ur'月', '-') \
				.replace(ur'日', '')
			comment_time = datetime.strptime(comment_time_str, '%Y-%m-%d %H:%M')

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_time'] = comment_time.strftime(time_format)
				item['app_comment_user_name'] = soup_comment.find('span', class_ = 'user-name').text.strip()
				item['app_comment_content'] = soup_comment.find('p', class_ = 'comment-cnt').text.strip()
				item['app_comment_score'] = float(soup_comment.find('i', class_ = 'icon').attrs['style'].split(':')[1].strip('%')) / 20.0
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
