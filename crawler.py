#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler 0.1 Alpha
# by Jiaheng Zhang, all rights reserved.

import sys
import time

import general_func
import crawler_myapp

# configurations
app_version = "0.1 Alpha"

if __name__ == '__main__':

	print '\n' + "TencentCrawler " + app_version + " by Jiaheng Zhang, all rights reserved."

	crawler_args = {}
	crawler_args['website_id'] = sys.argv[1]
	crawler_args['start_time'] = time.strptime(sys.argv[2], "%Y%m%d%H%M")
	crawler_args['end_time'] = time.strptime(sys.argv[3], "%Y%m%d%H%M")
	if len(crawler_args) >= 4:
		crawler_args['keyword'] = sys.argv[4]
	else:
		crawler_args['keyword'] = None

	if crawler_args['website_id'] == 'myapp':
		crawler_myapp.crawl(crawler_args)
	else:
		print "Invalid website_id!"