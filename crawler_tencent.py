#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 腾讯财经 http://finance.qq.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
from multiprocessing import Pool

import general_func

# configurations
website_id = 'tencent'
website_name = "腾讯财经 http://finance.qq.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
news_url_base = "http://stockhtm.finance.qq.com/sstock/quotpage/q/{stock_id}.htm#news"
news_list_url_base = "http://news2.gtimg.cn/lishinews.php?name=finance_news&symbol={stock_symbol}&page={page_num}"
#start_time = time.strptime("2014-03-12 0:0", "%Y-%m-%d %H:%M")
#end_time = time.strptime("2014-03-14 23:59", "%Y-%m-%d %H:%M")
time_format = '%Y%m%d%H%M'

rep_stock_symbol = re.compile(r'\((.+):(\d+)\)')

def get_time_from_str(time_str):
	return datetime.strptime(time_str, u'%Y-%m-%d %H:%M:%S').replace(second = 0)

def get_news_data(stock_id, start_time, end_time, processes_num):

	data = {}
	data['start_time'] = start_time.strftime(time_format)
	data['end_time'] = end_time.strftime(time_format)
	data['stock_id'] = stock_id
	# load main news page
	news_page_url = news_url_base.format(stock_id = stock_id)
	news_page_raw = general_func.url_open(news_page_url, from_encoding = 'gbk')
	soup_news_page = BeautifulSoup(news_page_raw)
	data['stock_name'] = soup_news_page.find('span', attrs = {'class': 'fntHei'}).text
	data_stock_symbol_raw = soup_news_page.find('span',attrs = {'class': 'fs14'}).text

	res_stock_symbol = rep_stock_symbol.search(data_stock_symbol_raw)
	if res_stock_symbol:
		if res_stock_symbol.group(1) == ur'上海':
			data['stock_symbol'] = 'sh' + res_stock_symbol.group(2)
		elif res_stock_symbol.group(1) == ur'深圳':
			data['stock_symbol'] = 'sz' + res_stock_symbol.group(2)
		else:
			raise Exception('Stock symbol parsing error!')
	else:
		raise Exception('Stock symbol parsing error!')

	page_num = 1
	total_page = 1
	news_data_rets = []
	while page_num <= total_page:

		print 'Processing news list page: ' + str(page_num)
		news_list_url = news_list_url_base.format( \
			stock_symbol = data['stock_symbol'], \
			page_num = page_num)
		news_list_html = general_func.url_open(news_list_url, from_encoding = 'gbk')
		news_list_json = json.loads(news_list_html.split('finance_news=')[1])
		total_page = news_list_json['data']['total_page']

		post_time = None

		# get each news
		for this_news_data in news_list_json['data']['data']:

			# get news time
			post_time = get_time_from_str(this_news_data['datetime'])
			this_news_data_ret = {}
			this_news_data_ret['news_title'] = this_news_data['title']
			this_news_data_ret['news_url'] = this_news_data['url']
			this_news_data_ret['news_time'] = post_time.strftime(time_format)

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue
				
				# now it's the post needed
				# get post data
				print "Fetching news: " + str(this_news_data['title']) + ', post time: ' + post_time.strftime(time_format)
				news_data_rets.append(this_news_data_ret)
				# try:
				# 	this_news_data_ret.update(get_news_content(this_news_data['url']))
				# except:
				# 	print '-- Failed to get this news!'
				# 	continue
				
				# data['news_list'].append(this_news_data_ret)

			else:
				break

		if post_time != None and post_time >= start_time:
			# the comment is too new
			if post_time > end_time:
				print "-- The news is too new! Pass this page! " + post_time.strftime(time_format)
			page_num += 1
		else:
			break

	# async parallel get data
	print 'Awaiting data...'
	pool = Pool(processes = processes_num)
	news_urls = [x['news_url'] for x in news_data_rets]
	news_contents = pool.map(get_news_content, news_urls)		
	for i in range(len(news_contents)):
		news_data_rets[i].update(news_contents[i])
	data['news_list'] = news_data_rets

	data['news_count'] = len(data['news_list'])

	return data

def get_news_content(news_url):

	this_news = {}
	try:
		content_html = general_func.url_open(news_url, from_encoding = 'gbk')
		soup_content = BeautifulSoup(content_html)
		contents = soup_content.find('div', attrs = {'bosszone':'content'}).find_all('p')
		this_news['news_content'] = ''
		for line in contents:
			line_content = line.text.strip()
			if line_content != '':
				this_news['news_content'] += line_content + '\n'
	except:
		this_news['news_content'] = 'FAILED TO GET THIS NEWS!'

	return this_news


def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']
	processes_num = args['processes_num']

	page_list = general_func.get_list_from_file(page_list_file)

	for stock_id in page_list:

		stock_id = stock_id.strip('\n')

		print "********************************************************************************"
		print "Crawling news for stock: " + stock_id

		try:
			# get news data
			data = get_news_data(stock_id, start_time, end_time, processes_num)
		except:
			print "-- Failed to get news data!"
			continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + stock_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"