#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for bbs.g.qq.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func
import traceback

# configurations
post_url_base = 'http://bbs.g.qq.com/' # TBD
time_format = '%Y%m%d%H%M'

posts_list_api = (
'http://andfcg.qq.com/fcg-bin/mobile/android/base_common_interface_v2?'
'param={{%22QueryTopic_2%22:{{%22module%22:%22MiniGame.ForumAccessLogicSvr.ForumAccessLogicSvrObj%22,%22'
'method%22:%22QueryTopic%22,%22param%22:{{%22forum_type%22:3,%22'
'forum_id%22:{0},%22page_no%22:{1},%22page_size%22:10,%22rank_way%22:2}}}}}}')

post_api = (
'http://andfcg.qq.com/fcg-bin/mobile/android/base_common_interface_v2?'
'param={{%22QueryReply_1%22:{{%22module%22:%22MiniGame.ForumAccessLogicSvr.ForumAccessLogicSvrObj%22,%22'
'method%22:%22QueryReply%22,%22param%22:{{%22forum_type%22:3,%22forum_id%22:{0},%22page_no%22:1,%22'
'page_size%22:10,%22topic_id%22:{1},%22author_id%22:0,%22rank_way%22:6}}}}}}')

# get the forum ID from the page url
def parse_forum_url(forum_url):

	global post_url_base

	rep_dash = re.compile(ur'(?<=forum-)\d+(?=-\d+)')

	try:
		page_url_parse = urlparse.urlparse(forum_url)
		# parse fid
		result_dash = rep_dash.search(page_url_parse.path)
		if result_dash:
			# url like post_url_base/forum-46-1.html
			page_url_args = urlparse.parse_qs(page_url_parse.query)
			page_url_args['fid'] = result_dash.group()
			return True, page_url_args
		else:
			return False, None
	except:
		return False, None

def get_forum_url(forum_url_args):
	global post_url_base
	forum_url = post_url_base + 'forum-' + forum_url_args['fid'] + '-1-1.html'
	return forum_url

# get the post ID from the page url
def get_post_data(forum_id, post_id):

	post_url = post_api.format(forum_id, post_id)

	post_data = {}
	json_posts = json.loads(general_func.url_open(post_url))['rsp_obj']['QueryReply_1']['data']['pageContent']
	if not json_posts:
		return {}
	json_post = json_posts[-1]
	post_data['forum_post_reply_content'] = json_post['content_info']['content']
	post_data['forum_post_reply_user_name'] = json_post['content_info']['author_name']
	post_data['forum_post_reply_time'] = datetime.fromtimestamp(json_post['content_info']['publish_time']).strftime(time_format)

	return post_data

def get_posts_data(forum_url_args, start_time, end_time):

	forum_id = forum_url_args['fid']

	posts_data = {}
	posts_data['forum_id'] = forum_id
	posts_data['forum_posts'] = []
	page_num = 1

	while True:
		# the url of forum page
		forum_url = posts_list_api.format(forum_id, page_num)

		print 'Processing forum page: ' + str(page_num)
		json_posts = json.loads(general_func.url_open(forum_url))['rsp_obj']['QueryTopic_2']['data']['pageContent']
		html_posts_raw = general_func.url_open(get_forum_url(forum_url_args), from_encoding = 'utf-8')
		soup = BeautifulSoup(html_posts_raw)
		posts_data['forum_name'] = soup.find('div', attrs = {'class': 'gb-bbs-if-inner'}).h2.text

		post_time = None

		# process every post
		for json_post in json_posts:
			post_time = datetime.fromtimestamp(int(json_post['content_info']['last_modify_time']))

			if post_time >= start_time:
				if post_time > end_time:
					# the post is too new
					continue

				# now it's the post needed
				# get post id
				post_id = json_post['content_info']['topic_id']
				posts_data['forum_posts'].append(get_post_data(forum_id, post_id))

			else:
				break

		if post_time != None and post_time >= start_time:
			# the comment is too new
			if post_time > end_time:
				print "-- The posts are too new! Pass this page! Post time: " + post_time.strftime('%Y-%m-%d %H:%M')
			page_num += 1
		else:
			break

	posts_data['forum_posts_count'] = len(posts_data['forum_posts'])
	posts_data['forum_posts_start_time'] = start_time.strftime(time_format)
	posts_data['forum_posts_end_time'] = end_time.strftime(time_format)

	return posts_data

def crawl(args):

	website_id = args['website_id']
	page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"

	print "Now running TencentCrawler for Discuz!"

	start_time = args['start_time']
	end_time = args['end_time']

	forum_list = general_func.get_list_from_file(page_list_file)

	for forum_url in forum_list:

		# get forum id from forum url
		is_success, page_url_args = parse_forum_url(forum_url.strip('\n'))
		if not is_success:
			print "Wrong page URL: " + forum_url
			continue
		print "********************************************************************************"
		print "Crawling forum: " + page_url_args['fid']
		print "Analyzing forum pages..."

		# try:
		# get post list
		data = get_posts_data(page_url_args, start_time, end_time)
		# except:
		# 	print "-- Failed to get the posts of this topic!"
		# 	print traceback.format_exc()
		# 	continue

		# save to json file
		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + page_url_args['fid'] + \
			'_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'
		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"
