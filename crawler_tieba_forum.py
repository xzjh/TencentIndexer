#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 百度贴吧吧内 http://tieba.baidu.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

import bs4

# configurations
website_id = ''
website_name = "百度贴吧吧内 http://tieba.baidu.com"
page_list_file = ''
forum_url_base = "http://tieba.baidu.com/mo/m"
forum_url_args = {}
post_url_base = 'http://tieba.baidu.com/mo/m'
post_url_args = {}
post_url_args['global'] = '1'
post_url_args['expand'] = '1'
time_format = '%Y%m%d%H%M'
additional_headers = {'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6,en;q=0.4'}

def get_time_from_str(time_str):

	rep_time = re.compile(r'\d+:\d+')
	rep_old_date = re.compile(r'\d+-\d+-\d+')
	rep_post_time = re.compile(r'\d+-\d+ \d+:\d+')
	time_now = general_func.get_beijing_time()
	if rep_post_time.search(time_str):
		# post time like 05-24 21:23
		post_time = datetime.strptime(time_str, '%m-%d %H:%M')
		post_time = post_time.replace(year = time_now.year)
	elif rep_time.search(time_str):
		# today's post like 21:23
		post_time = datetime.strptime(time_str, '%H:%M')
		post_time = post_time.replace(year = time_now.year, month = time_now.month, day = time_now.day)
	elif rep_old_date.search(time_str):
		# old post not in this year like 2013-05-24
		# no detailed time, so set to 12:00
		post_time = datetime.strptime(time_str + ' 12:00', '%Y-%m-%d %H:%M')
	else:
		# old post in this year like 05-24
		# no detailed time, so set to 12:00
		post_time = datetime.strptime(time_str + ' 12:00', '%m-%d %H:%M')
		post_time = post_time.replace(year = time_now.year)

	return post_time

def get_posts_data(forum_id, start_time, end_time):

	forum_url_args['pn'] = 0
	forum_url_args['kw'] = forum_id.encode('utf-8')
	posts_data = {}
	posts_data['forum_id'] = forum_id
	posts_data['forum_name'] = forum_id
	posts_data['forum_posts'] = []

	rep_post_id = re.compile(r'(?<=m\?kz=)\d+(?=&)')

	while True:
		# the url of forum page
		forum_url = forum_url_base + '?' + urllib.urlencode(forum_url_args)
		print 'Processing forum page: ' + forum_url
		forum_html = general_func.url_open(forum_url, additional_headers = additional_headers)
		soup = BeautifulSoup(forum_html)
		soup_div = soup.find_all('div', attrs = {'class': 'i'})

		post_time = None

		# get the IDs and times of the posts
		for item_div in soup_div:
			if 'm?kz=' in item_div.a.attrs['href']:
				# get post time
				post_time = get_time_from_str(item_div.p.text.split(u'\xa0')[-1])
				if post_time >= start_time:
					if post_time > end_time:
						# the post is too new
						continue
					
					# now it's the post needed
					# get post id
					post_id = rep_post_id.search(item_div.a.attrs['href']).group()
					# get post data
					print "Getting post data: " + post_id + ', post time: ' + post_time.strftime(time_format)
					is_success, this_post = get_post_data(post_id)
					if is_success:
						posts_data['forum_posts'].append(this_post)
					else:
						print '-- Failed to get post: ' + post_id
						continue
				elif item_div.find('span', attrs = {'class': 'light'}, text = u'顶'):
					# ignore the old top post
					continue
				else:
					break

		if post_time != None and post_time >= start_time:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! " + post_time.strftime(time_format)
			forum_url_args['pn'] += 20
		else:
			break

	posts_data['forum_posts_count'] = len(posts_data['forum_posts'])
	posts_data['forum_posts_start_time'] = start_time.strftime(time_format)
	posts_data['forum_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

def get_post_data(post_id):

	this_post = {}
	this_post['forum_post_id'] = post_id
	post_url_args['kz'] = post_id
	post_url_args['pn'] = 0
	post_url = post_url_base + '?' + urllib.urlencode(post_url_args)
	rep_page = re.compile(ur'(?<=第1/)\d+(?=页)')
	rep_reply = re.compile(ur'\d+楼\.')

	try:
		post_html = general_func.url_open(post_url, additional_headers = additional_headers)
		soup = BeautifulSoup(post_html)
		this_post['forum_post_title'] = soup.strong.text.strip()

		# get author content
		soup_author = soup.find('div', attrs = {'class': 'i'})
		this_post['forum_post_author_content'] = soup_author.text.strip()
		this_post['forum_post_author_user_name'] = soup_author.find('span', attrs = {'class': 'g'}).a.text.strip()
		this_post['forum_post_author_time'] = get_time_from_str(soup_author.find('span', \
			attrs = {'class': 'b'}).text.strip()).strftime(time_format)

		# get last reply content
		page_result = rep_page.search(soup.find('div', attrs = {'class': 'h'}).text.strip())
		if page_result:
			# more than 1 pages
			post_url_args['pn'] = (int(page_result.group()) - 1) * 30
			# get last page
			post_url = post_url_base + '?' + urllib.urlencode(post_url_args)
			post_html = general_func.url_open(post_url, additional_headers = additional_headers)
			soup = BeautifulSoup(post_html)

		# get last reply
		soup_reply = soup.find_all('div', attrs = {'class': 'i'})[-1]
		this_post['forum_post_reply_content'] = soup_reply.text.strip()
		this_post['forum_post_reply_user_name'] = soup_reply.find('span', attrs = {'class': 'g'}).text.strip()
		this_post['forum_post_reply_time'] = get_time_from_str(soup_reply.find('span', \
			attrs = {'class': 'b'}).text.strip()).strftime(time_format)
		
	except:
		return False, None

	return True, this_post

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']

	page_list_file = general_func.page_list_dir_name + '/' + args['website_id'] + ".txt"

	forum_list = general_func.get_list_from_file(page_list_file)

	for forum_item in forum_list:

		forum_id = forum_item.strip('\n')

		print "********************************************************************************"
		print "Crawling forum: " + forum_id
		print "Analyzing forum pages..."

		try:
			# get post list
			data = get_posts_data(forum_id, start_time, end_time)
		except:
			print "-- Failed to get the posts of this topic!"
			continue

		# save to json file
		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + forum_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
