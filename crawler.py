#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler test version 0.1 Alpha for 应用宝 http://android.myapp.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urllib2
import urlparse
import json
from bs4 import BeautifulSoup
import time
import os

# configurations
page_list_file = "page_list.txt"
comment_url_args = {}
comment_url_args['pageSize'] = 10
#comment_url_args['appid'] = '48157'
comment_url_base = "http://android.myapp.com/android/commentlist_web"
app_url_base = "http://android.app.qq.com/android/appdetail.jsp"
data_dir_name = 'data_myapp'
data_file_prefix = 'data_myapp_'
start_time = time.strptime("2014-03-11 0:0", "%Y-%m-%d %H:%M")
end_time = time.strptime("2014-03-13 23:59", "%Y-%m-%d %H:%M")


def get_app_info(app_id):

	app_url = app_url_base + '?appid=' + app_id

	app_info = {}

	response = urllib2.urlopen(app_url)
	app_page_html = response.read()

	soup = BeautifulSoup(app_page_html)
	soup_app_info = soup.find('div', attrs = {"class": "app-msg"})
	app_info['app_name'] = soup_app_info.h1.contents[0].string
	
	soup_dts = soup_app_info.dl.find_all('dt')
	for item in soup_dts:
		if item.string.replace(u'\xa0', '').find(u'版本') >= 0:
			app_info['app_version'] = item.next_sibling.contents[0].string
			break

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	page_url_parse = urlparse.urlparse(app_url)
	page_url_args = urlparse.parse_qs(page_url_parse.query)
	if page_url_args.has_key('appid') and page_url_args['appid'] != '':
		return True, page_url_args['appid'][0]
	else:
		return False, None

# initialize the data dir, if exists, do nothing, else create a new
def init_dir(dir_name):

	is_exists = os.path.exists(dir_name)
	if not is_exists:
		os.makedirs(dir_name)

def get_comments_data():

	data = app_info
	data['app_comments'] = []
	comment_url_args['pageNo'] = 1
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Comment page URL: ' + comment_url
		# get the source code of comment page
		response = urllib2.urlopen(comment_url)
		data_raw = response.read().decode('utf-8')
		data_json = json.loads(data_raw)

		# get useful information
		for comment_item in data_json['info']['value']:

			item = {}
			comment_time = time.strptime(comment_item['createtime'], "%Y-%m-%d %H:%M")

			if comment_time >= start_time and comment_time <= end_time:

				item['user_name'] = comment_item['username']
				item['user_id'] = comment_item['userid']
				item['user_photo'] = comment_item['userphoto']
				item['comment_content'] = comment_item['content']
				item['comment_time'] = comment_item['createtime']
				item['comment_star_rating'] = int(comment_item['userpoststarno']) / 20
				item['comment_channel'] = comment_item['channel']
				item['comment_agree_count'] = int(comment_item['agree'])
				item['comment_disagree_count'] = int(comment_item['disagree'])

				data['app_comments'].append(item)

			else:
				break

		if comment_time >= start_time and comment_time <= end_time:
			comment_url_args['pageNo'] += 1
		else:
			break

	data['app_comments_count'] = len(data['app_comments'])

	return data


if __name__ == '__main__':

	print '\n' + "TencentCrawler test version 0.1 Alpha for 应用宝 http://android.myapp.com"
	print "by Jiaheng Zhang, all rights reserved." + '\n'

	# read the list of page to get info from
	file_page_list = open(page_list_file, 'r')
	page_list = file_page_list.readlines()

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

		# get comments data
		data = get_comments_data()

		# encode to json
		data_encoded = json.dumps(data, ensure_ascii = False, indent = 4)

		# save to file
		init_dir(data_dir_name)
		file_name = data_dir_name + '/' + data_file_prefix + app_id + '.json'
		file_json = open(file_name, 'w')
		file_json.write(data_encoded.encode('utf-8'))
		file_json.close()
		print "Saved to file: " + file_name
