#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 高德地图
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'amap'
website_name = '高德地图论坛 http://bbs.amap.com'
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
forum_url_base = 'http://bbs.amap.com/forum.php'
forum_url_args = {}
forum_url_args['mod'] = 'forumdisplay'
post_url_base = forum_url_base
post_url_author_args = {}
post_url_author_args['mod'] = 'viewthread'
post_url_reply_args = {}
post_url_reply_args['mod'] = 'redirect'
post_url_reply_args['goto'] = 'lastpost'
time_format = '%Y%m%d%H%M'

# get the forum ID from the page url
def parse_forum_url(forum_url):

	rep_dash = re.compile(ur'(?<=forum-)\d+(?=-\d+)')

	try:
		page_url_parse = urlparse.urlparse(forum_url)
		result_dash = rep_dash.search(page_url_parse.path)
		if result_dash:
			# url like forum_url_base/forum-46-1.html
			return True, result_dash.group()
	except:
		return False, None

# get the post ID from the page url
def get_post_id(post_url):

	rep_dash = re.compile(ur'(?<=thread-)\d+(?=-\d+-\d+)')

	try:
		result_dash = rep_dash.search(post_url)
		if result_dash:
			# url like thread-7487-1-1.html
			return True, result_dash.group()
	except:
		return False, None

def get_posts_data(forum_id, start_time, end_time):

	forum_url_args['page'] = 1
	forum_url_args['fid'] = forum_id
	posts_data = {}
	posts_data['forum_id'] = forum_id
	posts_data['forum_posts'] = []

	while True:
		# the url of forum page
		forum_url = forum_url_base + '?' + urllib.urlencode(forum_url_args)
		print 'Processing forum page: ' + forum_url
		forum_html = general_func.url_open(forum_url)
		soup = BeautifulSoup(forum_html)
		posts_data['forum_name'] = soup.h1.a.text
		soup_posts = soup.find_all('tbody')
		# remove stick threads
		for i in range(len(soup_posts))[::-1]:
			if not (soup_posts[i].has_attr('id') and \
				soup_posts[i].attrs['id'].startswith('normalthread_')):
				del soup_posts[i]

		post_time = None

		# process every post
		for soup_post in soup_posts:
			# get post time
			soup_reply = soup_post.find('div', attrs = {'class': 'deanforumreply'})
			if soup_reply.span.a.span:
				post_time = get_post_time(soup_reply.span.a.span.attrs['title'])
			else:
				post_time = get_post_time(soup_reply.span.a.text)

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue

				# now it's the post needed
				# get post id
				# print soup_post
				# soup_post_as = soup_post.find_all('a')
				# for soup_post_a in soup_post_as:
				# 	if soup_post_a.attrs['href'].startswith('forum.php'):
				# 		post_url_raw = soup_post_a.attrs['href']
				# 		break
				post_url_raw = soup_post.find('a', attrs = {'class': 'xst'}).attrs['href']
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

		if post_time != None and post_time >= start_time:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! Post time: " + post_time.strftime('%Y-%m-%d %H:%M')
			forum_url_args['page'] += 1
		else:
			break

	posts_data['forum_posts_count'] = len(posts_data['forum_posts'])
	posts_data['forum_posts_start_time'] = start_time.strftime(time_format)
	posts_data['forum_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

# get post time from str
def get_post_time(time_str_raw):
	time_str = ':'.join(time_str_raw.split(':')[:2])
	return datetime.strptime(time_str, '%Y-%m-%d %H:%M')

def get_post_data(post_id):

	this_post = {}
	this_post['forum_post_id'] = post_id
	post_url_author_args['tid'] = post_id
	post_url_reply_args['tid'] = post_id
	post_url_author = post_url_base + '?' + urllib.urlencode(post_url_author_args)
	post_url_reply = post_url_base + '?' + urllib.urlencode(post_url_reply_args)

	try:
		post_html_author = general_func.url_open(post_url_author)
		soup_author = BeautifulSoup(post_html_author)
		post_counter = soup_author.find('div', attrs = {'class': 'ptn'})
		this_post['forum_post_view_count'] = int(post_counter.find('span', attrs = {'class': 'views'}).text)
		this_post['forum_post_reply_count'] = int(post_counter.find('span', attrs = {'class': 'replies'}).text)
		this_post['forum_post_title'] = soup_author.h1.span.text.strip()
		this_post['forum_post_url'] = post_url_author

		# get author content
		this_post['forum_post_author_time'] = get_post_time(soup_author.find('div', attrs = {'class': 'deanzb'}).em.text.strip(u'发表于 ')). \
			strftime(time_format)
		this_post['forum_post_author_user_name'] = soup_author.find('div', attrs = {'class': 'deanzb'}).span.a.text.strip()
		this_post['forum_post_author_content'] = soup_author.find('td', attrs = {'class': 't_f'}).text.strip()

		# get last reply content
		if this_post['forum_post_reply_count'] > 0:

			post_html_reply = general_func.url_open(post_url_reply)
			soup_reply = BeautifulSoup(post_html_reply)

			soup_last_reply = soup_reply.find_all('table', attrs = {'class': 'plhin'})[-1]
			this_post['forum_post_reply_time'] = get_post_time(soup_last_reply.find_all('div', \
				attrs = {'class': 'authi'})[-1].em.text.strip(u'发表于 ')).strftime(time_format)
			this_post['forum_post_reply_user_name'] = soup_last_reply.find('div', attrs = {'class': 'deanauthor'}).a.text.strip()
			this_post['forum_post_reply_content'] = soup_last_reply.find('div', attrs = {'class': 't_fsz'}).table.text.strip()

	except:
		return False, None

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
