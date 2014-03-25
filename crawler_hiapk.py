#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 安卓市场 http://apk.hiapk.com/
# by Jiaheng Zhang, all rights reserved.

import urllib
import urllib2
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'hiapk'
website_name = "安卓市场 http://apk.hiapk.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['action'] = "FindApkSoftCommentListJson"
comment_url_args['callback'] = ''
comment_url_base = "http://apk.hiapk.com/Detail.aspx"
app_url_base = "http://apk.hiapk.com/html/2014/03/"

def get_app_info(app_id):

	app_url = app_url_base + app_id + '.html'

	app_info = {}

	response = urllib.urlopen(app_url)
	app_page_html = response.read()

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.find('label', attrs = {'id': 'ctl00_AndroidMaster_Content_Apk_SoftName'}).contents[0]
	app_info['app_version'] = soup.find('label', attrs = {'id': 'ctl00_AndroidMaster_Content_Apk_SoftVersionName'}).contents[0]
	app_info['app_downloads_count'] = soup.find('label', attrs = {'id': 'ctl00_AndroidMaster_Content_Apk_Download'}).contents[0]
	app_info['app_score'] = float(soup.find('div', attrs = {'class': 'star_num'}).contents[0])
	app_score_count_all_raw = soup.find('div', attrs = {'class': 'star_human'}).contents[0]
	rep = re.compile("\d+")
	app_score_count_all_result = rep.findall(app_score_count_all_raw)
	if len(app_score_count_all_raw) > 0:
		app_info['app_score_count_all'] = int(app_score_count_all_result[0])

	app_scores_count_raw = soup.find_all('div', attrs = {'class': 'star_per_font'})
	for i in range(5):
		star_num = 5 - i
		count_percent = int(app_scores_count_raw[i].contents[0][:-1])
		app_info['app_score_count_' + str(star_num)] = int(app_info['app_score_count_all'] * count_percent / 100)

	comment_url_args['softcode'] = soup.find('input', attrs = {'id': 'PublishSoft_SoftCode'}).attrs['value']

	return app_info

# get the App ID from the page url
def get_app_id(app_url):
	
	rep = re.compile("(?<=\/)\d+(?=\.html)")
	result = rep.findall(app_url)
	if len(result) > 0:
		return True, result[0]
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['curPageIndex'] = 1
	
	while True:
		# the url of comment page
		comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
		print 'Processing comment page: ' + comment_url
		# get the source code of comment page
		# POST method
		req = urllib2.Request(comment_url, headers = {'User-Agent': 'Mozilla/5.0'})
		data_html = urllib2.urlopen(req).read()

		# get useful information
		soup = BeautifulSoup(data_html)

		soup_comments = soup.find_all('div', attrs = {'class': 'comment_item'})
		for soup_comment_item in soup_comments:

			item = {}
			comment_time_raw = soup_comment_item.find('div', attrs = {'class', 'detail_version'}).span.contents[0].split()
			comment_time = datetime.strptime(comment_time_raw[0] + ' ' + comment_time_raw[1], \
				"%Y-%m-%d %H:%M:%S").replace(second = 0)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item['user_name'] = soup_comment_item.find('div', attrs = {'class', 'author_tip'}).contents[0].strip().split(' ')[0]
				item['user_photo'] = soup_comment_item.find('div', attrs = {'class', 'headimg'}).img.attrs['src']
				item['comment_content'] = soup_comment_item.find('div', attrs = {'class', 'comcontent'}).contents[0].strip()
				item['comment_time'] = comment_time_raw[0] + ' ' + comment_time_raw[1]
				item['comment_channel'] = soup_comment_item.find('div', attrs = {'class', 'detail_version'}) \
					.span.next_sibling.next_sibling.contents[0].strip().split(u'：')[1]
				data['app_comments'].append(item)

			else:
				break

		if comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['curPageIndex'] += 1
		else:
			break

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
			comment_url_args['apkId'] = app_id
		else:
			print "Wrong page URL: " + app_url
			continue

		# get app info
		app_info = get_app_info(app_id)
		print "App name: " + app_info['app_name'] + ", App ID: " + comment_url_args['apkId']
		app_info['app_id'] = app_id

		print "Analyzing comment pages..."

		# get comments data
		data = get_comments_data(app_info, start_time, end_time)

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_id + '_' + start_time.strftime('%Y%m%d%H%M') + \
			'_' + end_time.strftime('%Y%m%d%H%M') + '.json'

		general_func.save_to_file_by_json(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"