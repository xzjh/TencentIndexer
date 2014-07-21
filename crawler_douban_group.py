#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 豆瓣小组 http://www.douban.com/group
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'douban_group'
website_name = '豆瓣小组 http://www.douban.com/group'
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
forum_url_base = 'http://www.douban.com/group/{forum_id}/discussion'
forum_url_args = {}
post_url_base = 'http://www.douban.com/group/topic/{post_id}/'
post_url_args = {}
time_format = '%Y%m%d%H%M'

# get the forum ID from the page url
def parse_forum_url(forum_url):

	try:
		rep = re.compile(r'(?<=douban\.com/group/).+?(?=/|$|\?|#|\s)')
		return True, rep.search(forum_url).group()
	except:
		return False, None

# get the post ID from the page url
def get_post_id(post_url):

	try:
		rep = re.compile(r'(?<=douban\.com/group/topic/)\d+?(?=/|$|\?|#|\s)')
		return True, rep.search(post_url).group()
	except:
		return False, None

# get post time from raw string
def get_post_time_from_str(time_str):

	rep_this_year = re.compile(r'\d{2}-\d{2} \d{2}:\d{2}')
	rep_full = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
	# rep_old = re.compile(r'\d{4}-\d{2}-\d{2}')

	if rep_full.search(time_str):
		return datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').replace(second = 0)
	elif rep_this_year.search(time_str):
		return datetime.strptime(time_str, '%m-%d %H:%M').replace(year = \
			general_func.get_beijing_time().year)
	else:
		# can not get time from post list, set to 12:00
		return datetime.strptime(time_str, '%Y-%m-%d').replace(hour = 12, minute = 0)

def get_posts_data(forum_id, start_time, end_time):

	global forum_url_base

	forum_url_args['start'] = 0
	posts_data = {}
	posts_data['forum_id'] = forum_id
	posts_data['forum_posts'] = []
	forum_url_base = forum_url_base.format(forum_id = forum_id)

	while True:
		# the url of forum page
		forum_url = forum_url_base + '?' + urllib.urlencode(forum_url_args)
		print 'Processing forum page: ' + forum_url
		forum_html = general_func.url_open(forum_url)
		soup = BeautifulSoup(forum_html)
		posts_data['forum_name'] = soup.find('div', attrs = {'class': 'title'}).text.strip()
		# get posts list
		soup_posts = soup.find_all('tr', attrs = {'class': ''})
		for i in range(len(soup_posts))[::-1]:
			if not (soup_posts[i].a and \
				soup_posts[i].a.attrs['href'].startswith('http://www.douban.com/group/topic/')):
				del soup_posts[i]
		# get page num
		soup_page_indicator = soup.find('div', attrs = {'class': 'paginator'})
		if soup_page_indicator:
			# more than 1 page
			last_page_num = int(soup_page_indicator.find_all('a')[-2].text.strip())
		else:
			# only 1 page
			last_page_num = 1

		post_time = None

		# process every post
		for soup_post in soup_posts:
			# get post time
			post_time = get_post_time_from_str(soup_post.find('td', attrs = {'class': 'time'}).text.strip())

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue

				# now it's the post needed
				post_url_raw = soup_post.a.attrs['href']
				is_success, post_id = get_post_id(post_url_raw)
				if not is_success:
					print '-- Failed to get post!'
					continue

				# get post data
				print "Getting post data: " + post_id + ', post time: ' + post_time.strftime('%Y-%m-%d %H:%M')
				is_success, this_post = get_post_data(post_id)
				if is_success:
					posts_data['forum_posts'].append(this_post)
				else:
					print '-- Failed to get post: ' + post_id
					continue
			else:
				break

		if post_time != None and post_time >= start_time and forum_url_args['start'] < last_page_num:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! Post time: " + post_time.strftime('%Y-%m-%d %H:%M')
			forum_url_args['start'] += 25
		else:
			break

	posts_data['forum_posts_count'] = len(posts_data['forum_posts'])
	posts_data['forum_posts_start_time'] = start_time.strftime(time_format)
	posts_data['forum_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

def get_post_data(post_id):

	this_post = {}
	this_post['forum_post_id'] = post_id
	post_url_author = post_url_base.format(post_id = post_id)

	# try:
	soup_post_author = BeautifulSoup(general_func.url_open(post_url_author))
	soup_page_indicator = soup_post_author.find('div', attrs = {'class': 'paginator'})
	if soup_page_indicator:
		# more than 1 page
		last_page_num = int(soup_page_indicator.find_all('a')[-2].text.strip())
		post_url_reply = soup_page_indicator.find_all('a')[-2].attrs['href']
		soup_post_reply = BeautifulSoup(general_func.url_open(post_url_reply))
	else:
		# only 1 page
		last_page_num = 1
		soup_post_reply = soup_post_author

	# get author data
	soup_author = soup_post_author.find('div', attrs = {'class': 'topic-content'})

	soup_author_info = soup_author.find('span', attrs = {'class': 'from'}).a
	this_post['forum_post_author_user_link'] = soup_author_info.attrs['href']
	this_post['forum_post_author_user_name'] = soup_author_info.text.strip()

	soup_author_user_photo = soup_author.find('div', attrs = {'class': 'user-face'})
	if soup_author_user_photo.img:
		this_post['forum_post_author_user_photo'] = soup_author_user_photo.img.attrs['src']

	this_post['forum_post_author_content'] = soup_author.find('div', \
		attrs = {'class': 'topic-content'}).text.strip()
	author_time = get_post_time_from_str(soup_author.find('span', \
		attrs = {'class': 'color-green'}).text.strip())
	this_post['forum_post_author_time'] = author_time.strftime(time_format)

	# get reply data
	soup_replies = soup_post_reply.find_all('li', attrs = {'class': 'comment-item'})
	if soup_replies:
		# have replies
		soup_reply = soup_replies[-1]

		soup_reply_user_info = soup_reply.find('div', attrs = {'class': 'bg-img-green'}).a
		this_post['forum_post_reply_user_link'] = soup_reply_user_info.attrs['href']
		this_post['forum_post_reply_user_name'] = soup_reply_user_info.text.strip()

		soup_reply_user_photo = soup_reply.find('div', attrs = {'class': 'user-face'})
		if soup_reply_user_photo.img:
			this_post['forum_post_reply_user_photo'] = soup_reply_user_photo.img.attrs['src']

		this_post['forum_post_reply_content'] = soup_reply.p.text.strip()
		reply_time = get_post_time_from_str(soup_reply.find('span', \
			attrs = {'class': 'pubtime'}).text.strip())
		this_post['forum_post_reply_time'] = reply_time.strftime(time_format)

	# except:
	# 	return False, None

	return True, this_post

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']

	forum_list = general_func.get_list_from_file(page_list_file)

	for forum_url in forum_list:

		# get forum id from forum url
		is_success, forum_id = parse_forum_url(forum_url.strip('\n'))
		if not is_success:
			print "Wrong page URL: " + forum_url
			continue

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