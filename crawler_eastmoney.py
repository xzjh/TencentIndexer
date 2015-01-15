#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 东方财富网 http://quote.eastmoney.com/
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
website_id = 'eastmoney'
website_name = "东方财富网 http://quote.eastmoney.com/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
news_url_base = "http://guba.eastmoney.com/list,{stock_id},1,f_{page_num}.html"
news_list_url_base = "http://guba.eastmoney.com/list,{stock_id},1,f_{page_num}.html"
news_content_url_base = "http://guba.eastmoney.com/{r}"
#start_time = time.strptime("2014-03-12 0:0", "%Y-%m-%d %H:%M")
#end_time = time.strptime("2014-03-14 23:59", "%Y-%m-%d %H:%M")
time_format = '%Y%m%d%H%M'

rep_total_page_num = re.compile(r"gubapage\('.+',(\d+),(\d+),\d+\)")

def get_time_from_str(time_str):
	time_now = general_func.get_beijing_time().replace(minute = 0, second = 0)
	time_monthday = datetime.strptime(time_str, u'%m-%d').replace(year = time_now.year)
	if time_monthday > time_now:
		time_monthday = time_monthday.replace(year = time_monthday.year	- 1)
	return time_monthday

def get_news_data(stock_id, start_time, end_time, processes_num):

	data = {}
	start_time = start_time.replace(hour = 0, minute = 0)
	end_time = end_time.replace(hour = 23, minute = 59)
	data['start_time'] = start_time.strftime(time_format)
	data['end_time'] = end_time.strftime(time_format)
	data['stock_id'] = stock_id
	# load main news page
	news_page_url = news_url_base.format(stock_id = stock_id, page_num = 1)
	news_page_raw = general_func.url_open(news_page_url)
	soup_news_page = BeautifulSoup(news_page_raw)
	data['stock_name'] = soup_news_page.find('span', id = 'stockname').text.strip(u'吧')
	total_page_num = 1
	res_total_page_num = rep_total_page_num.search(soup_news_page.find('span', attrs = {'class': 'pagernums'}).script.text)
	if res_total_page_num:
		total_page_num = int(res_total_page_num.group(1)) // int(res_total_page_num.group(2)) + 1
	else:
		raise Exception('Total page number parsing error!')

	page_num = 1
	news_data_rets = []
	while page_num <= total_page_num:

		print 'Processing news list page: ' + str(page_num)
		news_list_url = news_list_url_base.format( \
			stock_id = data['stock_id'], \
			page_num = page_num)
		news_list_html = general_func.url_open(news_list_url)
		soup = BeautifulSoup(news_list_html)
		soup_news_list = soup.find('div', id = 'articlelistnew').find_all('div', attrs = {'class': 'articleh'})

		post_time = None

		# get each news
		for soup_news_title in soup_news_list:

			post_time = get_time_from_str(soup_news_title.find('span', attrs = {'class': 'l6'}).text)

			this_news_data_ret = {}
			soup_news_link = soup_news_title.find('span', attrs = {'class': 'l3'}).a
			this_news_data_ret['news_title'] = soup_news_link.text
			this_news_data_ret['news_url'] = news_content_url_base.format(r = soup_news_link.attrs['href'])
			this_news_data_ret['news_time'] = post_time.strftime(time_format)

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue
				
				# now it's the post needed
				# get post data
				print "Fetching news: " + str(this_news_data_ret['news_title']) + ', post time: ' + post_time.strftime(time_format)
				news_data_rets.append(this_news_data_ret)
				# try:
					# this_news_data_ret.update(get_news_content(this_news_data_ret['news_url']))
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

def get_news_content(news_content_url):

	this_news = {}
	try:
		content_html = general_func.url_open(news_content_url)
		soup_content = BeautifulSoup(content_html)
		soup_content_lines = soup_content.find('div', {'class': 'stockcodec'}).find_all('p')
		news_content = ''
		for soup_content_line in soup_content_lines:
			news_content += soup_content_line.text.strip() + '\n'
	except:
		this_news['news_content'] = 'FAILED TO GET THIS NEWS!'
	else:
		this_news['news_content'] = news_content.strip()

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