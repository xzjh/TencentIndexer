#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler module of general functions
# by Jiaheng Zhang, all rights reserved.

import os
import json
import urllib
import urllib2

#configurations
data_dir_name = "data"
page_list_dir_name = "page_list"
proxy_address = None
push_address = None

# read the list of page to get info from
def get_list_from_file(file_name):

	the_file = open(file_name, 'r')
	the_list = the_file.readlines()
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

def url_open(url, post_args = None):

	# set up the proxy
	if proxy_address != None:
		proxy_handler = urllib2.ProxyHandler({"http": proxy_address})
	else:
		proxy_handler = urllib2.ProxyHandler({})
	opener = urllib2.build_opener(proxy_handler)
	urllib2.install_opener(opener)

	if post_args != None:
		url_args_encoded = urllib.urlencode(post_args)
		req = urllib2.Request(url, url_args_encoded, headers = {'User-Agent': 'Mozilla/5.0'})
	else:		
		req = urllib2.Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
	data = urllib2.urlopen(req).read()

	return data