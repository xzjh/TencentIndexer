#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 豆瓣条目 http://www.douban.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'douban_subject'
website_name = "豆瓣条目 http://www.douban.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['sort'] = 'time'
comment_url_args['count'] = 10
comment_url_base = "http://www.douban.com/j/ilmen/thing/"
app_url_base = "http://www.douban.com/subject/"
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + app_id
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.h1.contents[0].strip()

	if soup.find('div', attrs = {'id': 'interest_sectl'}) != None:
		app_info['app_score'] = float(soup.strong.contents[0].strip())
		app_info['app_score_count_all'] = int(soup.find('span', property = 'v:votes').contents[0])
		# score counts
		for i in range(5):
			app_info['app_score_count_' + str(5 - i)] = int(int(app_info['app_score_count_all']) * \
				float(soup.find_all('div', attrs = {'class': 'power'})[i].next_sibling.strip()[:-1]) / 100)

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	rep = re.compile('(?<=subject\/)\d+(?=\/?)')
	result = rep.findall(app_url)
	if len(result) > 0:
		return True, result[0]
	else:
		return False, None

def get_comment_time(comment_url):

	print "** Getting comment time: " + comment_url
	try:
		data_html = general_func.url_open(comment_url)
		soup = BeautifulSoup(data_html)
		comment_time_raw = soup.find('span', attrs = {'class': 'pubtime'}).contents[0]
		comment_time = datetime.strptime(comment_time_raw, "%Y-%m-%d %H:%M:%S").replace(second = 0)
		return True, comment_time
	except:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['start'] = 0
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + app_info['app_id'] + '/notes?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		# POST method
		data_json = general_func.url_open(comment_url)
		data_html = json.loads(data_json)['list']

		# get useful information
		soup = BeautifulSoup(data_html)
		soup_comments = soup.find_all('li')

		if len(soup_comments) == 0:
			break

		comment_time = None

		for soup_comment_item in soup_comments:

			item = {}

			this_comment_url = soup_comment_item.find('span', attrs = {'class': 'pubtime'}).contents[0].attrs['href']
			is_success, comment_time = get_comment_time(this_comment_url)
			if not is_success:
				print '-- Failed to get comment time! Pass this comment!'
				continue

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = soup_comment_item.find('div', attrs = {'class': 'user-info'}).a.contents[0]
				item['app_comment_user_photo'] = soup_comment_item.img.attrs['src']
				item['app_comment_content'] = soup_comment_item.p.contents[0].strip()
				item['app_comment_time'] = comment_time.strftime(time_format)
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['start'] += comment_url_args['count']
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
			comment_url_args['softid'] = app_id
		else:
			print "Wrong page URL: " + app_url
			continue

		# get app info
		app_info = get_app_info(app_id)
		print "App name: " + app_info['app_name'] + ", App ID: " + comment_url_args['softid']
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