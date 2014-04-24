#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler 0.1 Alpha
# by Jiaheng Zhang, all rights reserved.

import sys
import os
from datetime import datetime
import json
import re

import general_func
import crawler_myapp
import crawler_googleplay
import crawler_anzhi
import crawler_hiapk
import crawler_91
import crawler_douban_subject
import crawler_tieba_forum
import crawler_tieba_search
import crawler_weibo
import crawler_discuz
import crawler_douban_group

# configurations
app_version = "0.1 Alpha"
configurations_file = "configs.json"

if __name__ == '__main__':

	print '\n' + "TencentCrawler " + app_version + " by Jiaheng Zhang, all rights reserved."
	os.chdir(sys.path[0])

	# read args
	crawler_args = {}
	crawler_args['website_id'] = sys.argv[1]
	crawler_args['start_time'] = datetime.strptime(sys.argv[2], "%Y%m%d%H%M")
	crawler_args['end_time'] = datetime.strptime(sys.argv[3], "%Y%m%d%H%M")
	# if len(crawler_args) >= 4:
	# 	crawler_args['keyword'] = sys.argv[4]
	# 	print_keyword = 'keyword \"' + crawler_args['keyword'] + '"'
	# else:
	# 	crawler_args['keyword'] = None
	# 	print_keyword = "no keyword"

	print 'Now crawling messages from website "' + crawler_args['website_id'] + '" in the period from ' + \
		str(crawler_args['start_time']) + ' to ' + str(crawler_args['end_time']) + '.'
		# ' with ' + print_keyword + '.'

	# read configs
	file_configs = open(configurations_file)
	configs_raw = file_configs.read()
	configs = json.loads(configs_raw)
	# proxies
	if configs.has_key('proxies') and configs['proxies'].has_key(crawler_args['website_id']):
		general_func.proxy_address = configs['proxies'][crawler_args['website_id']]
		print "-- Using proxy: " + general_func.proxy_address
	else:
		general_func.proxy_address = None
	# push address
	if configs.has_key('push_address'):
		if re.match(r'^https?:/{2}\w.+$', configs['push_address']):
			general_func.push_address = configs['push_address']
			print "-- Push address: " + general_func.push_address
		else:
			print "-- Invalid push address: " + configs['push_address']
	else:
		general_func.push_address = None

	# call the crawler
	if crawler_args['website_id'] == 'myapp':
		crawler_myapp.crawl(crawler_args)
	elif crawler_args['website_id'] == 'googleplay':
		crawler_googleplay.crawl(crawler_args)
	elif crawler_args['website_id'] == 'anzhi':
		crawler_anzhi.crawl(crawler_args)
	elif crawler_args['website_id'] == 'hiapk':
		crawler_hiapk.crawl(crawler_args)
	elif crawler_args['website_id'] == '91':
		crawler_91.crawl(crawler_args)
	elif crawler_args['website_id'] == 'douban_subject':
		crawler_douban_subject.crawl(crawler_args)
	elif crawler_args['website_id'] == 'tieba_forum':
		crawler_tieba_forum.crawl(crawler_args)
	elif crawler_args['website_id'] == 'tieba_search':
		crawler_tieba_search.crawl(crawler_args)
	elif crawler_args['website_id'] == 'weibo':
		crawler_weibo.crawl(crawler_args)
	elif crawler_args['website_id'] == 'tencentbbs' or \
		crawler_args['website_id'] == 'duowan' or \
		crawler_args['website_id'] == '178':
		crawler_discuz.crawl(crawler_args)
	elif crawler_args['website_id'] == 'douban_group':
		crawler_douban_group.crawl(crawler_args)
	else:
		print "Invalid website_id!"
