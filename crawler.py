#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler 0.1 Alpha
# by Jiaheng Zhang, all rights reserved.

import sys
import os
from datetime import datetime
import json

import general_func
import crawler_myapp
import crawler_googleplay
import crawler_anzhi
import crawler_hiapk

# configurations
app_version = "0.1 Alpha"
configurations_file = "configs.json"

if __name__ == '__main__':

	print '\n' + "TencentCrawler " + app_version + " by Jiaheng Zhang, all rights reserved."
	os.chdir(sys.path[0])

	crawler_args = {}
	crawler_args['website_id'] = sys.argv[1]
	crawler_args['start_time'] = datetime.strptime(sys.argv[2], "%Y%m%d%H%M")
	crawler_args['end_time'] = datetime.strptime(sys.argv[3], "%Y%m%d%H%M")
	if len(crawler_args) >= 4:
		crawler_args['keyword'] = sys.argv[4]
		print_keyword = 'keyword \"' + crawler_args['keyword'] + '"'
	else:
		crawler_args['keyword'] = None
		print_keyword = "no keyword"

	print 'Now crawling messages from website "' + crawler_args['website_id'] + '" in the period from ' + \
		str(crawler_args['start_time']) + ' to ' + str(crawler_args['end_time']) + \
		' with ' + print_keyword + '.'

	# set up proxy
	file_configs = open(configurations_file)
	configs_raw = file_configs.read()
	configs = json.loads(configs_raw)
	if configs.has_key('proxies') and configs['proxies'].has_key(crawler_args['website_id']):
		#crawler_args['proxy_address'] = proxy_address[crawler_args['website_id']]
		general_func.proxy_address = configs['proxies'][crawler_args['website_id']]
		print "-- Using proxy: " + general_func.proxy_address
	else:
		#crawler_args['proxy_address'] = None
		general_func.proxy_address = ''

	# call the crawler
	if crawler_args['website_id'] == 'myapp':
		crawler_myapp.crawl(crawler_args)
	elif crawler_args['website_id'] == 'googleplay':
		crawler_googleplay.crawl(crawler_args)
	elif crawler_args['website_id'] == 'anzhi':
		crawler_anzhi.crawl(crawler_args)
	elif crawler_args['website_id'] == 'hiapk':
		crawler_hiapk.crawl(crawler_args)
	else:
		print "Invalid website_id!"