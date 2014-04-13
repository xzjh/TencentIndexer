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
		if the_list[i][0] == '#':
			del the_list[i]

	return the_list

# initialize the data dir, if exists, do nothing, else create a new
def init_dir(dir_name):

	is_exists = os.path.exists(dir_name)
	if not is_exists:
		os.makedirs(dir_name)

def process_results(dir_name, file_name, data):

	# encode to json
	data_encoded = json.dumps(data, ensure_ascii = False, indent = 4)

	# save to file
	init_dir(data_dir_name)
	init_dir(data_dir_name + '/' + dir_name)
	full_file_name = data_dir_name + '/' + dir_name + '/' + file_name
	file_json = open(full_file_name, 'w')
	file_json.write(data_encoded.encode('utf-8'))
	file_json.close()
	print "-- Saved to file: " + full_file_name

	# push to server
	if push_address != None:
		try:
			push_data = {}
			push_data['json'] = data_encoded
			push_data['file_name'] = os.getcwd() + '/' + full_file_name
			urllib2.urlopen(push_address, data = push_data)
			print "-- Pushed to address: " + push_address
		except:
			print "-- Failed to push to " + push_address

def url_open(url, post_args = None, additional_headers = None):

	# set up the proxy
	if proxy_address != None:
		proxy = {"http": proxy_address}
	else:
		proxy = {}

	headers = {'User-Agent': 'Mozilla/5.0'}
	if additional_headers != None:
		headers.update(additional_headers)

	if post_args != None:
		req = requests.post(url, data = post_args, headers = headers)
	else:
		req = requests.get(url, headers = headers)

	return req.text

def get_beijing_time():

	return datetime.datetime.utcnow() + datetime.timedelta(hours = 8)
