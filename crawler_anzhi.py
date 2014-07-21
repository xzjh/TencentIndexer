#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 安智 http://www.anzhi.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'anzhi'
website_name = "安智 http://www.anzhi.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_base = "http://www.anzhi.com/comment.php"
app_url_base = "http://www.anzhi.com/soft_"
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + app_id + '.html'
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.find('div', attrs = {'class': 'detail_line'}).h3.contents[0]
	app_info['app_version'] = soup.find('div', attrs = {'class': 'detail_line'}).span.contents[0].strip('()')
	app_info['app_downloads_count'] = soup.find('ul', attrs = {'id': 'detail_line_ul'}).find('span').contents[0].split(u'：')[1]
	print soup.find('div', attrs = {'id': 'stars_detail'})
	app_info['app_score'] = float(soup.find('div', attrs = {'id': 'stars_detail'}).attrs['style'].split(' ')[1].strip('px;')) / -30

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	rep = re.compile('(?<=soft_).+(?=\.html)')
	result = rep.findall(app_url)
	if len(result) > 0:
		return True, result[0]
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['page'] = 1
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		# POST method
		data_html = general_func.url_open(comment_url)

		# get useful information
		soup = BeautifulSoup(data_html)
		commments_count_raw = soup.find('div', attrs = {'class': 'app_detail_title'}).contents[0]
		# like this: 软件评论(137868)
		rep = re.compile('(?<=\().+?(?=\))')
		comments_count_result = rep.findall(commments_count_raw)
		if len(comments_count_result) > 0:
			app_info['app_score_count_all'] = int(comments_count_result[0])

		comment_time = None

		soup_comments = soup.find_all('ul', attrs = {'id': 'comment_list'})[0].find_all('li')
		for soup_comment_item in soup_comments:

			item = {}
			comment_time_raw = soup_comment_item.find('div', attrs = {'class': 'comment_list_top'}).em.contents[0]
			comment_time = datetime.strptime(comment_time_raw, "%Y-%m-%d %H:%M:%S").replace(second = 0)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = soup_comment_item.find('div', attrs = {'class': 'comment_list_top'}).span.contents[0]
				item['app_comment_user_photo'] = soup_comment_item.img.attrs['src']
				item['app_comment_content'] = soup_comment_item.p.text.strip()
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