#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 新浪微博 http://weibo.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

from datetime import timedelta

# configurations
website_id = 'weibo'
website_name = "新浪微博 http://weibo.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
weibo_url_base = "http://weibo.cn/search/mblog"
weibo_url_args = {}
weibo_url_args['sort'] = 'time'
weibo_url_args['advancedfilter'] = '1'
cookies = {}
cookies['_T_WM'] = '77661910efa5e3ddcf3884aadea42a83'
cookies['gsid_CTandWM'] = '4uDL88bf1ztffa1cBXfI9lr6tew'
# post_url_base = 'http://tieba.baidu.com/mo/m'
# post_url_args = {}
# post_url_args['global'] = '1'
# post_url_args['expand'] = '1'
time_format = '%Y%m%d%H%M'
date_format = '%Y%m%d'

def get_time_from_str(time_str):

	rep_just_now = re.compile(ur'\d+(?=分钟前)')
	rep_today = re.compile(ur'(?<=今天\s)(\d+):(\d+)')
	rep_this_year = re.compile(ur'(\d+)月(\d+)日\s(\d+):(\d+)')
	# rep_old_day = re.compile(ur'\d+-\d+-\d+\s\d+:\d+')

	result_just_now = rep_just_now.search(time_str)
	result_today = rep_today.search(time_str)
	result_this_year = rep_this_year.search(time_str)
	if result_just_now:
		minute_delta = -int(result_just_now.group())
		weibo_time = general_func.get_beijing_time() + timedelta(minutes = minute_delta)
	elif result_today:
		time_now = general_func.get_beijing_time()
		weibo_time = datetime(year = time_now.year, month = time_now.month, day = time_now.day, \
			hour = int(result_today.group(1)), minute = int(result_today.group(2)))
	elif result_this_year:
		time_now = general_func.get_beijing_time()
		weibo_time = datetime(year = time_now.year, month = int(result_this_year.group(1)), \
			day = int(result_this_year.group(2)), hour = int(result_this_year.group(3)), \
			minute = int(result_this_year.group(4)))
	else:
		weibo_time = datetime.strptime(timestr, u'%Y-%m-%d %H:%M:%S').replace(second = 0)

	return weibo_time

def get_posts_data(search_keyword, start_time, end_time):

	weibo_url_args['page'] = 1
	weibo_url_args['keyword'] = search_keyword.encode('utf-8')
	weibo_url_args['starttime'] = start_time.strftime(date_format)
	weibo_url_args['endtime'] = end_time.strftime(date_format)
	posts_data = {}
	posts_data['search_keyword'] = search_keyword
	posts_data['weibo_posts'] = []

	rep_remove_content_extra = re.compile(ur'赞\[\d+\]\xa0转发\[\d+\]')
	rep_last_page = re.compile(ur'(?<=\d/)\d+(?=页)')

	while True:
		# the url of weibo page
		weibo_url = weibo_url_base + '?' + urllib.urlencode(weibo_url_args)
		print 'Processing weibo search result: ' + weibo_url
		weibo_html = general_func.url_open(weibo_url, cookies = cookies)
		soup = BeautifulSoup(weibo_html)
		soup_weibos = soup.find_all('div', attrs = {'class': 'c'})
		for i in range(len(soup_weibos))[::-1]:
			if not soup_weibos[i].has_attr('id'):
				# not a weibo
				del soup_weibos[i]
		soup_jump_page = soup.find('input', value = u'跳页')
		if soup_jump_page:
			# more than 1 page
			last_page_num = rep_last_page.search(unicode(soup_jump_page.next_sibling)).group()
		else:
			last_page_num = 1

		# get the IDs and times of the posts
		for soup_weibo in soup_weibos:
			# get post time
			time_str = soup_weibo.find('span', attrs = {'class': 'ct'}).contents[0].split(u'\xa0')[0]
			post_time = get_time_from_str(time_str)

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue
				
				# now it's the post needed
				# get post data
				# try:
				this_post = {}
				this_post['weibo_post_user_name'] = soup_weibo.find('a', attrs = {'class': 'nk'}).text
				this_post['weibo_post_user_link'] = soup_weibo.find('a', attrs = {'class': 'nk'}).attrs['href']
				soup_content = soup_weibo.find('span', attrs = {'class': 'ctt'})
				this_post['weibo_post_content'] = soup_content.text
				if soup_content.previous_sibling.name == 'span' and \
					u'转发了' in soup_content.previous_sibling.contents[0]:
					# it is a forwarded weibo
					this_post['weibo_post_original_user_name'] = soup_content.previous_sibling.a.text
					this_post['weibo_post_original_user_link'] = soup_content.previous_sibling.a.attrs['href']
					forward_content_raw = soup_content.find_next('span', text = u'转发理由:').parent.text
					remove_pos = rep_remove_content_extra.search(forward_content_raw).start()
					this_post['weibo_post_forward_content'] = forward_content_raw[:remove_pos].strip()

				posts_data['weibo_posts'].append(this_post)
				# except:
				# 	print '-- Failed to get current weibo!'
				# 	continue
			else:
				break

		if post_time >= start_time and weibo_url_args['page'] < last_page_num:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! " + post_time.strftime(time_format)
			weibo_url_args['page'] += 1
		else:
			break

	posts_data['weibo_posts_count'] = len(posts_data['weibo_posts'])
	posts_data['weibo_posts_start_time'] = start_time.strftime(time_format)
	posts_data['weibo_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']

	weibo_keyword_list = general_func.get_list_from_file(page_list_file)

	for weibo_keyword in weibo_keyword_list:

		weibo_keyword = weibo_keyword.strip('\n')

		print "********************************************************************************"
		print "Crawling weibo with keyword: " + weibo_keyword
		print "Analyzing weibo pages..."

		# get post list
		data = get_posts_data(weibo_keyword, start_time, end_time)

		# save to json file
		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + weibo_keyword + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"