#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 百度贴吧搜索 http://tieba.baidu.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'tieba_search'
website_name = "百度贴吧搜索 http://tieba.baidu.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
forum_url_base = "http://tieba.baidu.com/f/search/res"
forum_url_args = {}
forum_url_args['ie'] = 'utf-8'
post_url_base = 'http://tieba.baidu.com'
#post_url_args = {}
#post_url_args['global'] = '1'
#post_url_args['expand'] = '1'
time_format = '%Y%m%d%H%M'

def get_posts_data(forum_id, start_time, end_time):

	forum_url_args['pn'] = 1
	forum_url_args['qw'] = forum_id.encode('utf-8')
	posts_data = {}
	posts_data['search_keyword'] = forum_id
	posts_data['forum_posts'] = []

	while True:
		# the url of forum page
		forum_url = forum_url_base + '?' + urllib.urlencode(forum_url_args)
		print 'Processing forum page: ' + forum_url
		forum_html = general_func.url_open(forum_url)
		soup = BeautifulSoup(forum_html)
		soup_posts = soup.find_all('div', attrs = {'class': 's_post'})
		soup_last_page_link = soup.find('a', text = u"尾页")
		if soup_last_page_link:
			last_page_url = soup_last_page_link.attrs['href']
			url_parse = urlparse.urlparse(last_page_url)
			last_page_num = urlparse.parse_qs(url_parse.query)['pn'][0]
		else:
			last_page_num = 1

		# get the IDs and times of the posts
		for soup_post in soup_posts:

			if soup_post.find('p', attrs = {'class': 'p_hot'}):
				# not a post
				continue

			# get post time
			post_time_str = soup_post.find('font', attrs = {'class': 'p_date'}).contents[0]
			post_time = datetime.strptime(post_time_str, '%Y-%m-%d %H:%M')

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue
				
				# now it's the post needed
				# get post id
				post_address = post_url_base + soup_post.a.attrs['href']
				# get post data
				print "Getting post data: " + post_address + ', post time: ' + post_time.strftime(time_format)
				is_success, this_post = get_post_data(post_address)
				if is_success:
					posts_data['forum_posts'].append(this_post)
				else:
					print '-- Failed to get this post!'
					continue
			else:
				break

		if post_time >= start_time and forum_url_args['pn'] < last_page_num:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! " + post_time.strftime(time_format)
			forum_url_args['pn'] += 1
		else:
			break

	posts_data['forum_posts_count'] = len(posts_data['forum_posts'])
	posts_data['forum_posts_start_time'] = start_time.strftime(time_format)
	posts_data['forum_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

def get_post_data(post_address):

	this_post = {}
	#this_post['post_address'] = post_address

	try:
		post_html = general_func.url_open(post_address)
		soup = BeautifulSoup(post_html)
		this_post['forum_post_title'] = soup.find('h1', attrs = {'class': 'core_title_txt'}).attrs['title']

		post_url_parse = urlparse.urlparse(post_address)
		post_url_args = urlparse.parse_qs(post_url_parse.query)
		post_pid = post_url_args['pid'][0]
		post_cid = post_url_args['cid'][0]

		if post_cid != '0':
			# it is a reply's comment
			# get comment data
			soup_anchor = soup.find('a', attrs = {'class': 'l_post_anchor', 'name': post_cid})

			this_post['forum_post_reply_content'] = unicode( \
				soup_anchor.find_next('span', attrs = {'class': 'lzl_content_main'}).contents[1])
			this_post['forum_post_reply_user_name'] = \
				soup_anchor.find_next('a', attrs = {'class': 'j_user_card'}).attrs['username']
			this_post['forum_post_reply_user_link'] = post_url_base + \
				soup_anchor.find_next('a', attrs = {'class': 'j_user_card'}).attrs['href']
			this_post['forum_post_reply_user_photo'] = post_url_base + \
				soup_anchor.find_next('img').attrs['src']
			this_post['forum_post_reply_time'] = datetime.strptime( \
				soup_anchor.find_next('span', attrs = {'class': 'lzl_time'}).contents[0], 
				'%Y-%m-%d %H:%M').strftime(time_format)

		# get post data
		soup_anchor = soup.find('a', attrs = {'class': 'l_post_anchor', 'name': post_pid})
		soup_user_info = soup_anchor.find_next('a', attrs = {'class': 'p_author_face'})
		this_post['forum_post_author_user_link'] = post_url_base + soup_user_info.attrs['href']
		this_post['forum_post_author_user_name'] = soup_user_info.img.attrs['username']
		this_post['forum_post_author_user_photo'] = post_url_base + soup_user_info.img.attrs['src']
		this_post['forum_post_content'] = soup_anchor.find_next('div', attrs = {'class': 'd_post_content'}).text.strip()
		this_post['forum_post_time'] = datetime.strptime( \
			soup_anchor.find_next('ul', attrs = {'class': 'p_tail'}).contents[1].contents[0].contents[0], \
			'%Y-%m-%d %H:%M').strftime(time_format)

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
		print "Crawling keyword: " + forum_id
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