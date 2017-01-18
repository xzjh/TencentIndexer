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
website_id = '360'
website_name = "360手机助手 http://zhushou.360.cn"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_base = "http://comment.mobilem.360.cn/comment/getComments"
app_url_base = "http://zhushou.360.cn/detail/index/soft_id"
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + '/' + app_id
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	soup_scripts = soup.find_all('script')
	soup_script_info = filter(lambda x: ur'详情页的命名空间' in x.text, soup_scripts)[0]
	rep_script_info = re.compile(ur'\'(.*?)\': [\'"](.*?)[\'"]')
	res_script_infos = rep_script_info.findall(soup_script_info.text)
	for res_script_info in res_script_infos:
		if res_script_info[0] == 'sname':
			app_info['app_name'] = res_script_info[1]
		elif res_script_info[0] == 'baike_name':
			app_info['app_name_internal'] = res_script_info[1]

	app_info['app_score'] = soup.find('span', class_ = 'js-votepanel').text.strip(ur'分')
	app_info['app_downloads_count'] = re.search('\d+', soup.find('span', class_ = 's-3').text).group()

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	rep_appid = re.compile(ur'(?<=soft_id\/)(\d+)')
	res_appid = rep_appid.search(app_url)
	if res_appid:
		return True, res_appid.group()
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['c'] = 'message'
	comment_url_args['start'] = 0
	comment_url_args['count'] = 10
	comment_url_args['baike'] = app_info['app_name_internal']

	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		data_raw = general_func.url_open(comment_url)
		data_json = json.loads(data_raw)
		comments_json = data_json['data']['messages']

		comment_time = None

		# get useful information
		for comment_item in comments_json:

			item = {}
			comment_time = datetime.strptime(comment_item['create_time'], '%Y-%m-%d %H:%M:%S').replace(second = 0)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_item['username']
				item['app_comment_user_photo'] = comment_item['image_url']
				item['app_comment_user_score'] = float(comment_item['score'])
				item['app_comment_content'] = comment_item['content']
				item['app_comment_time'] = comment_time.strftime(time_format)
				item['app_comment_app_version'] = comment_item['version_name']
				item['app_comment_likes_count'] = int(comment_item['likes'])
				item['app_comment_replies_count'] = int(comment_item['replies'])

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
			comment_url_args['appid'] = app_id
		else:
			print "Wrong page URL: " + app_url
			continue

		try:
			# get app info
			app_info = get_app_info(app_id)
			print "App name: " + app_info['app_name'] + ", App ID: " + comment_url_args['appid']
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
