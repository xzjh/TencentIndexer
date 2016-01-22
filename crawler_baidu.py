#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 百度手机助手 http://shouji.baidu.com/
# by Jiaheng Zhang, all rights reserved. 2016.01.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'baidu'
website_name = "百度手机助手 http://shouji.baidu.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['action_type'] = 'getCommentList'
comment_url_base = "http://shouji.baidu.com/comment"
time_format = '%Y%m%d%H%M'

def get_app_info(app_url):

	app_info = {}

	app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')
	soup = BeautifulSoup(app_page_html)

	app_info['app_name'] = soup.find('h1', attrs = {'class': 'app-name'}).span.text.strip()
	app_info['app_version'] = soup.find('span', attrs = {'class': 'version'}).text.split(':')[1].strip()
	app_info['app_id'] = soup.find('input', attrs = {'name': 'groupid'}).attrs['value']
	app_info['app_score'] = float(soup.find('span', attrs = {'class': 'star-percent'}).attrs['style'].split(':')[1].strip('%')) / 20.0

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['pn'] = 1
	comment_url_args['groupid'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + str(comment_url_args['pn'])
		# get the source code of comment page
		data_html = general_func.url_open(comment_url)
		soup = BeautifulSoup(data_html)
		soup_comments = soup.find('ol', attrs = {'class': 'comment-list'}).find_all('li')

		comment_time = None

		for soup_comment in soup_comments:

			item = {}
			comment_time = datetime.strptime(soup_comment.find('div', attrs = {'class': 'comment-time'}).text, \
				"%Y-%m-%d %H:%M").replace(second = 0)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = soup_comment.find('div', attrs = {'class': 'comment-info'}).find_all('div')[0].em.text.strip()
				item['app_comment_content'] = soup_comment.find('div', attrs = {'class': 'comment-info'}).find_all('div')[1].text.strip()
				item['app_comment_time'] = comment_time.strftime(time_format)
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['pn'] += 1
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
