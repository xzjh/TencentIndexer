#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 应用宝 http://android.myapp.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'myapp'
website_name = "应用宝 http://android.myapp.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_base = "http://android.app.qq.com/myapp/app/comment.htm"
app_url_base = "http://android.app.qq.com/myapp/detail.htm"
#start_time = time.strptime("2014-03-12 0:0", "%Y-%m-%d %H:%M")
#end_time = time.strptime("2014-03-14 23:59", "%Y-%m-%d %H:%M")
time_format = '%Y%m%d%H%M'

def get_app_info(app_id):

	rep_apkName = re.compile(ur'(?<=apkName:\").+(?=\")')
	rep_apkCode = re.compile(ur'(?<=apkCode:\").+(?=\")')

	app_info = {}

	app_url = app_url_base + '?apkName=' + app_id
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.find('div', attrs = {'class': 'det-name-int'}).text.strip()
	app_info['app_downloads_count'] = soup.find('div', attrs = {'class': 'det-ins-num'}).text.strip(u'下载')
	app_info['app_score'] = soup.find('div', attrs = {'class': 'com-blue-star-num'}).text.strip(u'分')
	app_info['app_version'] = soup.find('div', attrs = {'class': 'det-othinfo-data'}).text.strip()
	app_info_more_raw = soup.find_all('script')[-1].text.strip().replace(' ', '')
	comment_url_args['apkName'] = rep_apkName.search(app_info_more_raw).group()
	comment_url_args['apkCode'] = rep_apkCode.search(app_info_more_raw).group()

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	page_url_parse = urlparse.urlparse(app_url)
	page_url_args = urlparse.parse_qs(page_url_parse.query)
	if page_url_args.has_key('apkName') and page_url_args['apkName'] != '':
		return True, page_url_args['apkName'][0]
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['p'] = 1
	comment_url_args['contextData'] = ''
	stick_tolerence = 5
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		data_raw = general_func.url_open(comment_url)
		data_json = json.loads(data_raw)
		comment_url_args['contextData'] = data_json['obj']['contextData']

		# get useful information
		for comment_item in data_json['obj']['commentDetails']:

			item = {}
			comment_time = datetime.fromtimestamp(int(comment_item['createdTime']))

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['app_comment_user_name'] = comment_item['nickName']
				item['app_comment_user_id'] = comment_item['uin']
				# item['app_comment_user_photo'] = comment_item['userphoto']
				item['app_comment_content'] = comment_item['content']
				item['app_comment_time'] = comment_time.strftime(time_format)
				item['app_comment_user_score'] = comment_item['score']
				# item['app_comment_channel'] = comment_item['channel']
				# item['app_comment_agree_count'] = int(comment_item['agree'])
				# item['app_comment_disagree_count'] = int(comment_item['disagree'])

				data['app_comments'].append(item)

			else:
				# comment is old, but may be the stick-to-top comments
				if stick_tolerence:
					stick_tolerence -= 1
					continue
				else:
					break

		if comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['p'] += 1
		else:
			break


	# data['app_score'] = data_json['info']['allscore']
	# data['app_score_count_all'] = int(data_json['info']['allcount'])
	# data['app_score_count_1'] = int(data_json['info']['all1vcount'])
	# data['app_score_count_2'] = int(data_json['info']['all2vcount'])
	# data['app_score_count_3'] = int(data_json['info']['all3vcount'])
	# data['app_score_count_4'] = int(data_json['info']['all4vcount'])
	# data['app_score_count_5'] = int(data_json['info']['all5vcount'])
	
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

		# get app info
		app_info = get_app_info(app_id)
		print "App name: " + app_info['app_name'] + ", App ID: " + comment_url_args['appid']
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