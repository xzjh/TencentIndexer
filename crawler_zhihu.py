#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for Zhihu http://zhihu.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from datetime import datetime, timedelta
import time
import json
import random
import re
import requests
import multiprocessing
import functools

import general_func
import general_func_zhihu

# configurations
website_id = 'zhihu'
website_name = 'Zhihu http://zhihu.com'
page_list_file = general_func.page_list_dir_name + '/' + website_id + '.txt'
time_format = '%Y%m%d%H%M'
search_url_base = 'https://www.zhihu.com/api/v4/search_v3'
search_url_params = {
    't': 'general',
    'correction': '1',
    'offset': 0,
    'limit': 100,
    'time_zone': 'a_day',
}
sessions = []

def get_search_results(keyword, processes_num):
    search_url_params['q'] = keyword
    search_results = []
    search_url_params['offset'] = 0

    end_time = datetime.now()
    start_time = end_time - timedelta(days = 1)

    # use random session fetch search results
    session = random.SystemRandom().choice(sessions)
    mp_pool = multiprocessing.Pool(processes_num)

    result_items_json_all = []
    while True:
        print 'Fetching all search results...' + str(search_url_params['offset'])

        search_url = search_url_base + '?' + urllib.urlencode(search_url_params)
        data_raw = session.get(search_url, headers = general_func_zhihu.header).text
        data_json = json.loads(data_raw)
        result_items_json = filter(lambda item: item['type'] == 'search_result', data_json['data'])
        if len(result_items_json) == 0:
            break;
        result_items_json_all.extend(result_items_json)

        search_url_params['offset'] += search_url_params['limit']

    search_result_process_impl_func = functools.partial(search_result_process_impl, start_time = start_time, end_time = end_time)
    results = mp_pool.map(search_result_process_impl_func, result_items_json_all)
    results = filter(lambda result: result != None, results)
    search_results.extend(results)

    mp_pool.close()

    return search_results

def search_result_process_impl(result_item_json, start_time, end_time):
    result_type = result_item_json['object']['type']

    if result_type == 'answer':
        result_item = {}
        result_item['question_title'] = result_item_json['highlight']['title']
        result_item['question_created_time'] = datetime.fromtimestamp(result_item_json['object']['created_time']).strftime(time_format)
        result_item['question_updated_time'] = datetime.fromtimestamp(result_item_json['object']['updated_time']).strftime(time_format)
        result_item['answer_id'] = str(result_item_json['object']['id'])
        question_id = result_item_json['object']['question']['id']
        result_item['question_id'] = question_id
    elif result_type == 'question':
        result_item = {}
        result_item['question_title'] = result_item_json['highlight']['title']
        question_id = result_item_json['object']['id']
        result_item['question_id'] = question_id
    else:
        return None

    # use random session fetch question data
    session = random.SystemRandom().choice(sessions)
    question_data = general_func_zhihu.get_question_data(session, question_id, start_time, end_time)
    result_item.update(question_data)

    return result_item

def crawl(args):
    global sessions

    print "Now running TencentCrawler for " + website_name

    start_time = args['start_time']
    end_time = args['end_time']

    keyword_list = general_func.get_list_from_file(page_list_file)

    sessions.extend(general_func_zhihu.init_sessions())

    for keyword in keyword_list:

        keyword = keyword.strip('\n')

        print "********************************************************************************"
        print "Crawling keyword: " + keyword

        # try:
        data = get_search_results(keyword, args['processes_num'])
        # except:
        #     print "Failed to get the data for this keyword: {}!".format(keyword)
        #     continue

        # save to json file

        data_file_prefix = 'data_' + website_id + '_'
        dir_name = 'data_' + website_id
        file_name = data_file_prefix + keyword + '_' + datetime.now().strftime("%Y%m%d%H%M") + '.json'

        general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

    print "Please run the crawler from crawler.py!"
