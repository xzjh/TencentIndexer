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
website_id = 'tieba_forum'
website_name = "百度贴吧吧内 http://tieba.baidu.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
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
	time_now = general_func.get_beijing_time()
	time_strs = time_str.strip().split(' ')
	if rep_time.search(time_strs[0]):
		# today's post
		post_time = datetime.strptime(time_strs[0], '%H:%M')
		post_time = post_time.replace(year = time_now.year, month = time_now.month, day = time_now.day)
	else:
		# old post not today
		# time_strs[0] is date, time_strs[1] is time
		if rep_old_date.search(time_strs[0]):
			# old post not in this year
			# no detailed time, so set to 12:00
			post_time = datetime.strptime(time_strs[0] + ' 12:00', '%Y-%m-%d %H:%M')
		else:
			# old post in this year
			post_time = datetime.strptime(time_strs[0] + ' ' + time_strs[1], '%m-%d %H:%M')
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
		soup_a = soup.find_all('a')

		# get the IDs and times of the posts
		for item_a in soup_a:
			if 'm?kz=' in item_a.attrs['href']:
				# get post time
				post_time = get_time_from_str(item_a.find_next('br').next_sibling.split(u'\xa0')[2])
				if post_time >= start_time:
					if post_time > end_time:
						# the post is too new
						continue
					
					# now it's the post needed
					# get post id
					post_id = rep_post_id.search(item_a.attrs['href']).group()
					# get post data
					print "Getting post data: " + post_id
					is_success, this_post = get_post_data(post_id)
					if is_success:
						posts_data['forum_posts'].append(this_post)
					else:
						print '-- Failed to get post: ' + post_id
						continue
				elif u'[顶]' in item_a.next_sibling:
					# ignore the old top post
					continue
				else:
					break

		if post_time >= start_time:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! " + post_time.strftime(time_format)
			forum_url_args['pn'] += 10
		else:
			break

	posts_data['forum_posts_count'] = len(posts_data['forum_posts'])
	posts_data['forum_posts_start_time'] = start_time.strftime(time_format)
	posts_data['forum_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

def get_post_data(post_id):

	this_post = {}
	this_post['post_id'] = post_id
	post_url_args['kz'] = post_id
	post_url_args['pn'] = 0
	post_url = post_url_base + '?' + urllib.urlencode(post_url_args)
	rep_page = re.compile(ur'(?<=第1/)\d+(?=页)')
	rep_reply = re.compile(ur'\d+楼\.')

	try:
		post_html = general_func.url_open(post_url, additional_headers = additional_headers)
		soup = BeautifulSoup(post_html)
		this_post['forum_post_title'] = soup.card.attrs['title']
		# post content match re:
		#(?<=\d楼\.&#160;).+?(?=(<br/>)*<a href="/mo/.+</a>)

		# get author content
		soup_content_pos = soup.find('a', text = u'刷新').next_sibling
		post_content = ''
		while not (soup_content_pos.name == 'a' and soup_content_pos.attrs['href'].startswith('/mo/q')):
			post_content += unicode(soup_content_pos)
			soup_content_pos = soup_content_pos.next_sibling

		this_post['forum_post_author_content'] = post_content
		this_post['forum_post_author_username'] = soup_content_pos.contents[0]
		this_post['forum_post_author_time'] = get_time_from_str(unicode(soup_content_pos.next_sibling)) \
			.strftime(time_format)

		# get last reply content
		soup_next_page = soup.find('a', text = u'下一页')
		if soup_next_page:
			# more than 1 pages
			while soup_next_page:
				result = rep_page.search(unicode(soup_next_page))
				if result:
					page_num = result.group()
					break
				else:
					soup_next_page = soup_next_page.next_sibling
					continue
			post_url_args['pn'] = (int(page_num) - 1) * 10
			# get last page
			post_url = post_url_base + '?' + urllib.urlencode(post_url_args)
			post_html = general_func.url_open(post_url, additional_headers = additional_headers)
			soup = BeautifulSoup(post_html)

		# get last reply
		for item in soup.p.contents:
			if type(item) == bs4.element.NavigableString and rep_reply.match(item):
				soup_last_reply_pos = item
		post_content = ''
		while not (soup_last_reply_pos.name == 'a' and soup_last_reply_pos.attrs['href'].startswith('/mo/q')):
			post_content += unicode(soup_last_reply_pos)
			soup_last_reply_pos = soup_last_reply_pos.next_sibling

		this_post['forum_post_reply_content'] = post_content
		this_post['forum_post_reply_username'] = soup_last_reply_pos.string
		this_post['forum_post_reply_time'] = get_time_from_str(unicode(soup_last_reply_pos.next_sibling)) \
			.strftime(time_format)

	except:
		return False, None

	return True, this_post

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']

	forum_list = general_func.get_list_from_file(page_list_file)

	for forum_item in forum_list:

		forum_id = forum_item.strip('\n')

		print "********************************************************************************"
		print "Crawling forum: " + forum_id
		print "Analyzing forum pages..."

		# get post list
		data = get_posts_data(forum_id, start_time, end_time)

		# save to json file
		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + forum_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"