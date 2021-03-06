#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for Google Play https://play.google.com
# by Jiaheng Zhang, all rights reserved.

import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re

import general_func

# configurations
website_id = 'googleplay'
website_name = "Google Play https://play.google.com"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['reviewType'] = '0'
comment_url_args['reviewSortOrder'] = '0'
comment_url_args['xhr'] = '1'
comment_url_args['hl'] = 'zh-cn'
comment_url_base = "https://play.google.com/store/getreviews"
app_url_base = "https://play.google.com/store/apps/details"
time_format = '%Y%m%d'

def get_app_info(app_id):

	app_info = {}

	app_url = app_url_base + '?hl=zh-cn&id=' + app_id
	app_page_html = general_func.url_open(app_url)

	soup = BeautifulSoup(app_page_html)
	app_info['app_name'] = soup.find('div', attrs = {"class": "id-app-title"}).text.strip()
	app_info['app_version'] = soup.find('div', attrs = {'itemprop': 'softwareVersion'}).contents[0].strip()
	app_info['app_downloads_count'] = soup.find('div', attrs = {'itemprop': 'numDownloads'}).contents[0].strip()
	app_info['app_score'] = soup.find('div', attrs = {'class': 'score'}).contents[0]
	app_info['app_score_count_all'] = int(soup.find('span', attrs = {'class': 'reviews-num'}).contents[0].replace(',', ''))

	soup_app_scores = soup.find_all('span', attrs = {'class': 'bar-number'})
	app_info['app_score_count_5'] = int(soup_app_scores[0].contents[0].replace(',', ''))
	app_info['app_score_count_4'] = int(soup_app_scores[1].contents[0].replace(',', ''))
	app_info['app_score_count_3'] = int(soup_app_scores[2].contents[0].replace(',', ''))
	app_info['app_score_count_2'] = int(soup_app_scores[3].contents[0].replace(',', ''))
	app_info['app_score_count_1'] = int(soup_app_scores[4].contents[0].replace(',', ''))

	return app_info

# get the App ID from the page url
def get_app_id(app_url):

	page_url_parse = urlparse.urlparse(app_url)
	page_url_args = urlparse.parse_qs(page_url_parse.query)
	if page_url_args.has_key('id') and page_url_args['id'] != '':
		return True, page_url_args['id'][0]
	else:
		return False, None

def get_comments_data(app_info, start_time, end_time):

	data = app_info
	data['app_comments'] = []
	comment_url_args['pageNum'] = 0
	
	while True:
		# the url of comment page
		print 'Processing comment page: ' + str(comment_url_args['pageNum'])
		# get the source code of comment page
		# POST method
		data_raw = general_func.url_open(comment_url_base, comment_url_args)
		data_raw = data_raw[5:]
		data_json = json.loads(data_raw)
		data_html = data_json[0][2]
		# f = open('test/google.html','w')
		# f.write(data_html.encode('utf8'))
		# f.close()
		# get useful information
		soup = BeautifulSoup(data_html)
		soup_comments = soup.find_all('div', attrs = {'class': 'single-review'})

		rep_photo = re.compile(ur'url\((.*)\)')
		rep_rating = re.compile(ur'width: (\d+)%')

		comment_time = None

		for soup_comment_item in soup_comments:
			item = {}
			comment_time_raw = soup_comment_item.find('span', attrs = {'class': 'review-date'}).contents[0].strip().replace(u'???', '-').replace(u'???', '-').replace(u'???', '')
			comment_time = datetime.strptime(comment_time_raw, "%Y-%m-%d").replace(hour = 12)

			if comment_time >= start_time:
				# the comment is too new
				if comment_time > end_time:
					continue

				soup_user_info = soup_comment_item.find('span', attrs = {'class': 'author-name'})
				if soup_user_info == None:
					continue
				item['app_comment_user_name'] = soup_user_info.text.strip()
				photo_attr = soup_comment_item.find('span', class_ = 'author-image').attrs['style']
				item['app_comment_user_photo'] = rep_photo.search(photo_attr).group(1)

				comment_title = soup_comment_item.find('div', class_ = 'review-body').text.strip().strip(ur'??????').strip()
				item['app_comment_content'] = comment_title
				item['app_comment_time'] = comment_time.strftime(time_format)
				user_score_str = soup_comment_item.find('div', class_ = 'current-rating').attrs['style']
				item['app_comment_user_score'] = int(rep_rating.search(user_score_str).group(1)) / 20.0
				data['app_comments'].append(item)

			else:
				break

		if comment_time != None and comment_time >= start_time:
			# the comment is too new
			if comment_time > end_time:
				print "-- The comments are too new! Pass this page!"
			comment_url_args['pageNum'] += 1
		else:
			break

	data['app_comments_count'] = len(data['app_comments'])
	data['app_comments_start_time'] = start_time.strftime(time_format)
	data['app_comments_end_time'] = end_time.strftime(time_format)

	return data

def crawl(args):

	print "Now running TencentCrawler for " + website_name

	start_time = args['start_time']
	end_time = args['end_time']
	# ignore the time
	start_time = start_time.replace(hour = 0, minute = 0)
	end_time = end_time.replace(hour = 23, minute = 59)

	page_list = general_func.get_list_from_file(page_list_file)

	for app_url in page_list:

		app_url = app_url.strip('\n')

		print "********************************************************************************"
		print "Crawling page: " + app_url

		# get app id from app url
		is_success, app_id = get_app_id(app_url)
		if is_success:
			comment_url_args['id'] = app_id
		else:
			print "Wrong page URL: " + app_url
			continue

		try:
			# get app info
			app_info = get_app_info(app_id)
			print "App name: " + app_info['app_name'] + ", App ID: " + comment_url_args['id']
			app_info['app_id'] = app_id

			print "Analyzing comment pages..."

			# get comments data
			data = get_comments_data(app_info, start_time, end_time)
		except:
			print "-- Failed to get the comments of this App!"
			continue

		# save to json file

		data_file_prefix = 'data_' + website_id + '_'
		dir_name = 'data_' + website_id
		file_name = data_file_prefix + app_id + '_' + start_time.strftime(time_format) + \
			'_' + end_time.strftime(time_format) + '.json'

		general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

	print "Please run the crawler from crawler.py!"