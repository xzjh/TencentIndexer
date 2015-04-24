#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler module of general functions
# by Jiaheng Zhang, all rights reserved.

import os
import json
import urllib
import requests
import datetime
import codecs

# import traceback
import urllib2
import urllib
import httplib

#configurations
data_dir_name = "data"
page_list_dir_name = "page_list"
proxy_address = None
push_address = None

# read the list of page to get info from
def get_list_from_file(file_name):

	the_file = codecs.open(file_name, encoding = 'utf-8')
	the_list = the_file.readlines()

	for i in range(len(the_list))[::-1]:
		the_list[i] = the_list[i].strip()
		if the_list[i] == '' or the_list[i][0] == '#':
			del the_list[i]

	return the_list

# initialize the data dir, if exists, do nothing, else create a new
def init_dir(dir_name):

	is_exists = os.path.exists(dir_name)
	if not is_exists:
		os.makedirs(dir_name)

def process_results(dir_name, file_name, data):

	# encode to json
	try:
		data_encoded = json.dumps(data, ensure_ascii = False, indent = 4)
	except:
		print "-- Failed to save to json.dumps"


	# save to file
	try:
		init_dir(data_dir_name)
		init_dir(data_dir_name + '/' + dir_name)
		full_file_name = data_dir_name + '/' + dir_name + '/' + file_name
		full_file_name = full_file_name.encode('utf-8')           # 转换为utf-8编码
		full_file_name = full_file_name.strip().replace(' ', '_') # 把空格转为_
		file_json = open(full_file_name, 'w')
		file_json.write(data_encoded.encode('utf-8'))
		file_json.close()
		print "-- Saved to file: " + full_file_name
	except:
		print "-- Failed to save to file: " + full_file_name

	# push to server
	if push_address != None:
		try:
			push_data = {}
			push_data['json'] = data_encoded
			push_data['file_name'] = os.getcwd() + '/' + full_file_name

			# 必须要有这个头
			headers = {"Content-Type": "application/json", "Accept": "application/json"}
			# 加了个timeout防止有什么其它问题
			conn = httplib.HTTPConnection("mrs.oa.com", 18881, timeout = 5)
			values = json.dumps({'json': data_encoded})
			conn.request("POST", push_address, values, headers)
			# url_open(push_address, post_args = push_data, use_proxy = False, \
			# 	dditional_headers = headers)
			print "-- Pushed to address: " + push_address
		except:
			print "-- Failed to push to " + push_address

def url_open(url, post_args = None, additional_headers = None, cookies = None, use_proxy = True, from_encoding = None, use_spider = False):

	# set up the proxy
	if proxy_address and use_proxy:
		proxy = {"http": proxy_address}
	else:
		proxy = None

	# use spider.oa.com
	if use_spider:
		url = 'http://spider.oa.com/cgi-bin/bin/getCrawlResult.cgi?urls=' + urllib.quote(url.encode('utf-8', 'replace'))
		proxy = None

	headers = {'User-Agent': 'Mozilla/5.0'}
	if additional_headers != None:
		headers.update(additional_headers)

	if post_args != None:
		req = requests.post(url, data = post_args, headers = headers, cookies = cookies, \
			proxies = proxy, timeout = 10)
	else:
		req = requests.get(url, headers = headers, cookies = cookies, proxies = proxy, \
			timeout = 10)

	if from_encoding:
		req.encoding = from_encoding
	
	return req.text

def get_beijing_time():

	return datetime.datetime.utcnow() + datetime.timedelta(hours = 8)
