#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 小米应用商店 http://app.mi.com/
# by Jiaheng Zhang, all rights reserved. 2016.04.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import HTMLParser

import general_func

# configurations
website_id = 'xiaomi'
website_name = "小米应用商店 http://app.mi.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['ps'] = 1
comment_url_base = "http://miassist.app.xiaomi.com/v3/getComments"
app_info_url_base = "http://miassist.app.xiaomi.com/v3/detail/"
time_format = '%Y%m%d%H%M'

def get_app_info(app_url):

	app_info = {}

	rep_app_id = re.compile(r"app\.mi\.com/detail/(\d+)")
	res_app_id = rep_app_id.search(app_url)
	if not res_app_id:
		raise Exception("Invalid URL: " + app_url)
	app_id = res_app_id.group(1)
	app_info['app_id'] = app_id

	app_info_url = app_info_url_base + app_id
	app_page_html = general_func.url_open(app_info_url, from_encoding = 'utf8')
	soup = BeautifulSoup(app_page_html)

	app_info['app_name'] = soup.h1.text.strip()

	soup_app_info = soup.find('div', attrs = {'class': 'app-info'})

	app_info['app_score'] = float(soup_app_info.find('span', attrs = {'class': 'star-rank'}) \
									.attrs['class'][1].strip('s')) / 2.0
	soup_app_other_infos = soup_app_info.find_all('span', attrs = {'class': 'app-st-desc'})
	app_info['app_size'] = soup_app_other_infos[0].text
	app_info['app_version'] = soup_app_other_infos[2].text.replace(u'版本', '')

	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['page'] = 1
	comment_url_args['appId'] = app_info['app_id']
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + str(comment_url_args['page'])
		# get the source code of comment page
		data_html = general_func.url_open(comment_url)
		html_parser = HTMLParser.HTMLParser()
		# data_html = html_parser.unescape(data_html)

		# get useful information
		comments_json = json.loads(data_html)['list']
		if not comments_json:
			break

		comment_time = None

		for comment_json in comments_json:

			item = {}
			comment_time = datetime.strptime(comment_json['dataString'], '%m-%d') \
									.replace(year = datetime.now().year, hour = 12)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = html_parser.unescape(comment_json['user'])
				item['app_comment_user_score'] = float(comment_json['appRater'])
				item['app_comment_content'] = html_parser.unescape(comment_json['comment'].strip())
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
