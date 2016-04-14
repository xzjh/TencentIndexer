#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for 魅族应用商店 http://app.flyme.cn/
# by Jiaheng Zhang, all rights reserved. 2016.02.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime
import json
import re
import HTMLParser

import general_func

# configurations
website_id = 'flyme'
website_name = "魅族应用商店 http://app.flyme.cn/"
page_list_file = general_func.page_list_dir_name + '/' + website_id + ".txt"
comment_url_args = {}
comment_url_args['max'] = 10
comment_url_base = "http://app.flyme.cn/apps/public/evaluate/list"
time_format = '%Y%m%d%H%M'
package_name = ""
re_package_name = re.compile(ur'package_name=(.*)')

def get_app_info(app_url):

    app_info = {}

    app_page_html = general_func.url_open(app_url, from_encoding = 'utf8')
    soup = BeautifulSoup(app_page_html)

    app_info['app_name'] = soup.find('div', attrs = {'class': 'detail_top'}).h3.text
    soup_lis = soup.find('div', attrs = {'class': 'app_download'}).find_all('li')
    for soup_li in soup_lis:
        this_title = soup_li.span.text.replace(u'\xa0', '').strip(u'：')
        if this_title == u'版本':
            app_info['app_version'] = soup_li.div.text.strip()
        elif this_title == u'下载':
            app_info['app_downloads_count'] = int(soup_li.div.text.strip())
        elif this_title == u'大小':
            app_info['app_size'] = soup_li.div.text.strip()
        elif this_title == u'更新时间':
            app_info['app_update_time'] = datetime.strptime(soup_li.div.text.strip(), '%Y-%m-%d').strftime(time_format)
        elif this_title == u'魅友评分':
            app_info['app_score'] = float(soup_li.find('div', attrs = {'class': 'star_bg'}).attrs['data-num']) / 10.0

    app_info['app_id'] = soup.find('div', id = 'wrapper').input.attrs['data-appid']

    return app_info

def get_comments_data(app_info, start_time, end_time):

    data = app_info
    data['app_comments'] = []
    comment_url_args['start'] = 0
    comment_url_args['app_id'] = app_info['app_id']

    while True:
        # the url of comment page
        comment_url = comment_url_base + '?' + urllib.urlencode(comment_url_args)
        print 'Processing comment page: ' + str(comment_url_args['start'] / 10 + 1)
        # get the source code of comment page
        data_html = general_func.url_open(comment_url)
        html_parser = HTMLParser.HTMLParser()
        # data_html = html_parser.unescape(data_html)

        # get useful information
        comments_json = json.loads(data_html)['value']['list']
        if not comments_json:
            break

        comment_time = None

        for comment_json in comments_json:

            item = {}
            comment_time = datetime.strptime(comment_json['create_time'], '%Y-%m-%d').replace(hour = 12)

            if comment_time >= start_time:

                # the comment is too new
                if comment_time > end_time:
                    continue

                item['app_comment_user_name'] = html_parser.unescape(comment_json['user_name'])
                item['app_comment_user_rating'] = float(comment_json['star']) / 10.0
                item['app_comment_content'] = html_parser.unescape(comment_json['comment'].strip())
                item['app_comment_time'] = comment_time.strftime(time_format)
                data['app_comments'].append(item)

            else:
                break

        if comment_time != None and comment_time >= start_time:
            # the comment is too new
            if comment_time > end_time:
                print "-- The comments are too new! Pass this page!"
            comment_url_args['start'] += 10
        else:
            break

    data['app_comments_count'] = len(data['app_comments'])
    data['app_comments_start_time'] = start_time.strftime(time_format)
    data['app_comments_end_time'] = end_time.strftime(time_format)
    data['app_platform'] = website_id

    return data

def crawl(args):

    print "Now running TencentCrawler for " + website_name

    start_time = args['start_time']
    end_time = args['end_time']

    page_list = general_func.get_list_from_file(page_list_file)

    for app_url in page_list:

        print "********************************************************************************"
        print "Crawling page: " + app_url

        package_name = re_package_name.search(app_url).group(1).strip()

        try:
            # get app info
            app_info = get_app_info(app_url)
            print "App name: " + app_info['app_name'] + ", App ID: " + app_info['app_id'] + ", package_name: " + package_name
            app_info['app_id'] = app_info['app_id']

            print "Analyzing comment pages..."

            # get comments data
            data = get_comments_data(app_info, start_time, end_time)

            data['app_id_orig'] = data['app_id']
            # c# will need this to match the data
            data['app_id'] = package_name

        except:
            print "-- Failed to get the comments of this App!"
            continue

        # save to json file

        data_file_prefix = 'data_' + website_id + '_'
        dir_name = 'data_' + website_id
        file_name = data_file_prefix + package_name + '_' + start_time.strftime(time_format) + \
                '_' + end_time.strftime(time_format) + '.json'

        general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

    print "Please run the crawler from crawler.py!"
