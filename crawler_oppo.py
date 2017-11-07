#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for oppo软件商店 http://store.oppomobile.com
# by Jiaheng Zhang, all rights reserved. 2017.11

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json
import re
import hashlib
from collections import OrderedDict

import general_func

# configurations
website_id = 'oppo'
website_name = "oppo软件商店 http://store.oppomobile.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
time_format = '%Y%m%d%H%M'
base_url = 'http://istore.oppomobile.com'
imei = '000000000000000'
query_data = {
	'oak': '23a8ba872e430653',
	'id': imei,
	't': str(int(round(time.time() * 1000))),
	'ch': '2101',
	'locale': 'en-US',
	'User-Agent': 'Android%2FGoogle+Nexus+5X+-+7.0.0+-+API+24+-+1080x1920%2F24%2F7.0%2F0%2F2%2F2101%2F5203',
	'ocs': 'Android%2FGoogle+Nexus+5X+-+7.0.0+-+API+24+-+1080x1920%2F24%2F7.0%2F0%2F2%2Fvbox86p-userdebug+7.0+NRD90M+eng.genymo.20170929.075335+test-keys%2F5203',
}

def get_sign(path, query_params, query_data):
	ocs = query_data['ocs']
	t = query_data['t']
	imei = query_data['id']

	sp = 'STORENEWMIICeAIBADANBgkqhkiG9w0BAQEFAASCAmIwggJeAgEAAoGBANYFY/UJGSzhIhpx6YM5KJ9yRHc7YeURxzb9tDvJvMfENHlnP3DtVkOIjERbpsSd76fjtZnMWY60TpGLGyrNkvuV40L15JQhHAo9yURpPQoI0eg3SLFmTEI/MUiPRCwfwYf2deqKKlsmMSysYYHX9JiGzQuWiYZaawxprSuiqDGvAgMBAAECgYEAtQ0QV00gGABISljNMy5aeDBBTSBWG2OjxJhxLRbndZM81OsMFysgC7dq+bUS6ke1YrDWgsoFhRxxTtx/2gDYciGp/c/h0Td5pGw7T9W6zo2xWI5oh1WyTnn0Xj17O9CmOk4fFDpJ6bapL+fyDy7gkEUChJ9+p66WSAlsfUhJ2TECQQD5sFWMGE2IiEuz4fIPaDrNSTHeFQQr/ZpZ7VzB2tcG7GyZRx5YORbZmX1jR7l3H4F98MgqCGs88w6FKnCpxDK3AkEA225CphAcfyiH0ShlZxEXBgIYt3V8nQuc/g2KJtiV6eeFkxmOMHbVTPGkARvt5VoPYEjwPTg43oqTDJVtlWagyQJBAOvEeJLno9aHNExvznyD4/pR4hec6qqLNgMyIYMfHCl6d3UodVvC1HO1/nMPl+4GvuRnxuoBtxj/PTe7AlUbYPMCQQDOkf4sVv58tqslO+I6JNyHy3F5RCELtuMUR6rG5x46FLqqwGQbO8ORq+m5IZHTV/Uhr4h6GXNwDQRh1EpVW0gBAkAp/v3tPI1riz6UuG0I6uf5er26yl5evPyPrjrD299L4Qy/1EIunayC7JYcSGlR01+EDYYgwUkec+QgrRC/NstV'
	s1 = '23a8ba872e43065370f68c62df3ba8a45f1c1a57c91df63e'
	s2 = s1 + ocs + t + imei
	s3 = s2 + path + query_params
	s4 = s3 + str(len(s3)) + sp

	return hashlib.md5(s4).hexdigest()

def get_search_result(keyword):
	path = '/search/v1/completion/card'
	query_dict = OrderedDict([
		('keyword', keyword),
		('size', 1),
		('start', 0)
	])
	query_str = "&".join("%s=%s" % (k,v) for k,v in query_dict.items())
	url = base_url + path + '?' + query_str
	sign = get_sign(path, query_str, query_data)
	query_data['sign'] = sign
	result = json.loads(general_func.url_open(url, additional_headers = query_data))
	return result['cards'][0]['app']

def get_app_info(keyword):

	app_result = get_search_result(keyword)

	app_info = {
		'app_name': app_result['appName'],
		'app_id': str(app_result['appId']),
		'app_version': app_result['verName'],
		'app_size': app_result['sizeDesc'],
		'app_score': float(app_result['grade']),

	}
	return app_info

def get_comments_data(app_info, start_time, end_time):

	data = app_info

	path = '/common/v1/comment/list'
	page = 0
	page_size = 10
	data['app_comments'] = []

	while True:
		print 'Processing comment page: ' + str(page + 1)
		query_dict = OrderedDict([
			('appId', app_info['app_id']),
			('imei', imei),
			('size', page_size),
			('start', page * page_size),
			('type', 'all'),
		])
		query_str = urllib.urlencode(query_dict)
		url = base_url + path + '?' + query_str
		sign = get_sign(path, query_str, query_data)
		query_data['sign'] = sign
		data_json = json.loads(general_func.url_open(url, additional_headers = query_data))

		page_num = int(data_json['total'])
		if page > page_num:
			break
		comments_json = data_json['comments']

		comment_time = None

		# get useful information
		for comment_item in comments_json:

			item = {}
			comment_time = datetime.fromtimestamp(comment_item['commentTime'] / 1000)

			if comment_time >= start_time:

				# the comment is too new
				if comment_time > end_time:
					continue

				item = {
					'app_comment_user_name': comment_item['userNickName'],
					'app_comment_user_score': float(comment_item['grade']),
					'app_comment_time': comment_time.strftime(time_format),
					'app_comment_source': comment_item['mobileName'],
					'app_comment_content': comment_item['content'],
					'app_comment_id': comment_item['id'],
				}

				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			page += 1
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

	keyword_list = general_func.get_list_from_file(page_list_file)

	for keyword in keyword_list:

		keyword = keyword.strip('\n')

		print "********************************************************************************"
		print "Crawling app: " + keyword

		try:
			# get app info
			app_info = get_app_info(keyword)
			print "App name: " + app_info['app_name'] + ", App ID: " + app_info['app_id']

			print "Analyzing comment pages..."

			# get comments data
			data = get_comments_data(app_info, start_time, end_time)
		except:
			print "-- Failed to get the comments of this App!"
			continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + keyword + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
