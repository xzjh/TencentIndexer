#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 360手机助手 http://zhushou.360.cn
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'oppo'
website_name = "oppo软件商店 http://store.oppomobile.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_base = "http://store.oppomobile.com/comment/list.json"
app_url_base = "http://store.oppomobile.com/product"
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + '/' + app_id + '.html'
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.h3.text.strip()

	soup_app_infos_1 = soup.find('div', class_ = 'soft_info_nums')
	app_info['app_score'] = float(soup_app_infos_1.div.attrs['class'][0].split('_')[1]) / 10.0
	app_info['app_comments_count'] = int(soup_app_infos_1.a.span.text)

	soup_app_infos_2 = soup.find('ul', class_ = 'soft_info_more').find_all('li')
	app_info['app_size'] = soup_app_infos_2[1].text.strip(ur'大小：')
	app_info['app_version'] = soup_app_infos_2[2].text.strip(ur'版本：')

	app_info['app_id'] = soup.find('input', id = 'product_id').attrs['value']

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	rep_appid = re.compile(ur'(?<=product\/)(.*)(?=\.html)')
	res_appid = rep_appid.search(app_url)
	if res_appid:
		return True, res_appid.group()
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['id'] = app_info['app_id']
	comment_url_args['page'] = 1

	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		data_raw = general_func.url_open(comment_url)
		data_json = json.loads(data_raw)
		page_num = int(data_json['totalPage'])
		if comment_url_args['page'] > page_num:
			break
		comments_json = data_json['commentsList']

		comment_time = None

		# get useful information
		for comment_item in comments_json:

			item = {}
			comment_time = datetime.strptime(comment_item['createDate'], '%Y.%m.%d').replace(hour = 12)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_item['userNickName']
				item['app_comment_user_score'] = float(comment_item['userGrade'] / 10.0)
				item['app_comment_content'] = comment_item['word']
				item['app_comment_reply'] = comment_item['reply']
				item['app_comment_time'] = comment_time.strftime(time_format)
				item['app_comment_app_version'] = comment_item['version']
				item['app_comment_source'] = comment_item['source']

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
			comment_url_args['appid'] = app_id
		else:
			print "Wrong page URL: " + app_url
			continue

		try:
		# get app info
			app_info = get_app_info(app_id)
			print "App name: " + app_info['app_name'] + ", App ID: " + comment_url_args['appid']

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
