#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for Financial News
# by Jiaheng Zhang, all rights reserved.

import sys
import os
from datetime import datetime
import json
import re

import general_func

# configurations
app_version = "0.2 Alpha"
configurations_file = "configs.json"
rep_crawler_module = re.compile('(?<=crawler_).+(?=\.py)')

if __name__ == '__main__':

	print '\n' + "TencentCrawler for Financial News " + app_version + " by Jiaheng Zhang, all rights reserved."
	os.chdir(sys.path[0])
	reload(sys)
	sys.setdefaultencoding("utf-8")

	# read args
	crawler_args = {}
	crawler_args['website_id'] = sys.argv[1]
	crawler_args['start_time'] = datetime.strptime(sys.argv[2], "%Y%m%d%H%M")
	crawler_args['end_time'] = datetime.strptime(sys.argv[3], "%Y%m%d%H%M")

	print 'Now crawling news from website "' + crawler_args['website_id'] + '" in the period from ' + \
		str(crawler_args['start_time']) + ' to ' + str(crawler_args['end_time']) + '.'
		# ' with ' + print_keyword + '.'

	# read configs
	file_configs = open(configurations_file)
	configs_raw = file_configs.read()
	configs = json.loads(configs_raw)
	file_configs.close()
	# proxies
	if 'proxies' in configs and configs['proxies'].has_key(crawler_args['website_id']):
		general_func.proxy_address = configs['proxies'][crawler_args['website_id']]
		print '-- Using proxy: ' + general_func.proxy_address
	# push_address
	if 'push_address' in configs:
		general_func.push_address = configs['push_address']
		print '-- Push address: ' + general_func.push_address
	if 'processes_num' in configs and configs['processes_num'] >= 1:
		crawler_args['processes_num'] = configs['processes_num']
	else:
		# default processes num is 10
		crawler_args['processes_num'] = 10
	print '-- Working processes: ' + str(crawler_args['processes_num'])
	if 'request_timeout' in configs and configs['request_timeout'] >= 1:
		general_func.request_timeout = configs['request_timeout']
	else:
		general_func.request_timeout = 10
	print '-- Request timeout: ' + str(general_func.request_timeout)

	# import crawler module dynamically

	files_list = os.listdir('.')
	module_name = None
	for file_name in files_list:
		res_crawler_module = rep_crawler_module.search(file_name)
		if not os.path.isdir(file_name) and res_crawler_module and \
			res_crawler_module.group() == crawler_args['website_id']:
			module_name = os.path.splitext(file_name)[0]
			break

	# import and call the crawler
	if module_name:
		crawler_module = __import__(module_name)
		crawler_module.crawl(crawler_args)
	else:
		print "\nInvalid website_id! Crawler program now exits."
