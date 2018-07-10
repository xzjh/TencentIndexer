#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for Zhihu Topic http://zhihu.com
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
website_id = 'zhihu_topic'
website_name = 'Zhihu Topic http://zhihu.com'
page_list_file = general_func.page_list_dir_name + '/' + website_id + '.txt'
time_format = '%Y%m%d%H%M'
search_url_base = 'https://www.zhihu.com/api/v4/search_v3'
search_url_params = {
    't': 'topic',
    'correction': '1',
    'offset': 0,
    'limit': 10,
}
question_list_url_base = 'https://www.zhihu.com/api/v4/topics/{topic_id}/feeds/timeline_activity'
question_list_url_params = {
    'include': 'data[?(target.type=topic_sticky_module)].target.data[?(target.type=answer)].target.content,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[?(target.type=topic_sticky_module)].target.data[?(target.type=answer)].target.is_normal,comment_count,voteup_count,content,relevant_info,excerpt.author.badge[?(type=best_answerer)].topics;data[?(target.type=topic_sticky_module)].target.data[?(target.type=article)].target.content,voteup_count,comment_count,voting,author.badge[?(type=best_answerer)].topics;data[?(target.type=topic_sticky_module)].target.data[?(target.type=people)].target.answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics;data[?(target.type=answer)].target.content,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[?(target.type=answer)].target.author.badge[?(type=best_answerer)].topics;data[?(target.type=article)].target.content,author.badge[?(type=best_answerer)].topics;data[?(target.type=question)].target.comment_count',
    'offset': 0,
    'limit': 100,
}

question_ui_url_base = 'https://www.zhihu.com/question/{question_id}'
answer_ui_url_base = 'https://www.zhihu.com/question/{question_id}/answer/{answer_id}'

sessions = []

def get_search_results(keyword, processes_num):
    search_url_params['q'] = keyword
    search_results = []
    search_url_params['offset'] = 0

    # use random session fetch search results
    session = random.SystemRandom().choice(sessions)
    # mp_pool = multiprocessing.Pool(processes_num)

    result_items_json_all = []

    print 'Fetching all search results...'

    search_url = search_url_base + '?' + urllib.urlencode(search_url_params)
    data_raw = session.get(search_url, headers = general_func_zhihu.header).text
    data_json = json.loads(data_raw)
    result_items_json_all = filter(lambda item: item['type'] == 'search_result', data_json['data'])

    search_result_process_func = functools.partial(search_result_process_impl, processes_num = processes_num, session = session)
    results = map(search_result_process_func, result_items_json_all)
    results = filter(lambda result: result != None, results)
    search_results.extend(results)

    # mp_pool.close()

    return search_results

def search_result_process_impl(result_item_json, processes_num, session):

    result_item = {}
    result_item['topic_title'] = result_item_json['highlight']['title']
    result_item['topic_description'] = result_item_json['highlight']['description']
    result_item['topic_aliases'] = result_item_json['object']['aliases']
    result_item['topic_followers_count'] = result_item_json['object']['followers_count']
    result_item['topic_avatar_url'] = result_item_json['object']['avatar_url']
    result_item['topic_id'] = result_item_json['object']['id']
    result_item['topic_questions_count'] = result_item_json['object']['questions_count']

    topic_data = get_topic_data(result_item['topic_id'], processes_num, session)
    result_item.update(topic_data)

    return result_item

def get_topic_data(topic_id, processes_num, session):

    data = {}
    data['questions'] = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days = 1)
    question_list_url_params['offset'] = 0

    # use random session fetch question data
    mp_pool = multiprocessing.Pool(processes_num)

    while True:
        print 'Processing topic ID: ' + topic_id + ', question #: ' + str(question_list_url_params['offset']) + '-' + str(question_list_url_params['offset'] + question_list_url_params['limit'] - 1)

        question_url = question_list_url_base.format(topic_id = topic_id) + '?' + urllib.urlencode(question_list_url_params)
        data_raw = session.get(question_url, headers = general_func_zhihu.header).text
        data_json = json.loads(data_raw)
        questions_json = filter(lambda question_json: question_json['type'] == 'topic_feed', data_json['data'])
        questions_json = map(lambda question_json: question_json['target'], questions_json)

        question_answer_updated_time = None
        for question_json in questions_json:

            if 'created_time' not in question_json:
                continue

            question_item = {}
            question_answer_updated_time = datetime.fromtimestamp(question_json['updated_time'])

            if question_answer_updated_time >= start_time:

                # the answer is too new
                if question_answer_updated_time > end_time:
                    continue

                question_item['question_created_time'] = datetime.fromtimestamp(question_json['question']['created']).strftime(time_format)
                question_item['question_answer_updated_time'] = question_answer_updated_time.strftime(time_format)
                question_id = str(question_json['question']['id'])
                question_item['question_id'] = question_id
                question_item['question_title'] = question_json['question']['title']

                question_item['question_author_avatar_url'] = question_json['author']['avatar_url']
                question_item['question_author_name'] = question_json['author']['name']
                question_item['question_content'] = question_json['content']
                question_item['question_url'] = question_ui_url_base.format(question_id = question_id)

                data['questions'].append(question_item)
            else:
                break

        if question_answer_updated_time != None and question_answer_updated_time >= start_time:
            # the answer is too new
            if question_answer_updated_time > end_time:
                print "-- The questions are too new! Pass this page!"
            question_list_url_params['offset'] += question_list_url_params['limit']
        else:
            break

    question_process_impl_func = functools.partial(question_process_impl, start_time = start_time, end_time = end_time)
    data['questions'] = mp_pool.map(question_process_impl_func, data['questions'])
    mp_pool.close()

    data['question_start_time'] = start_time.strftime(time_format)
    data['question_end_time'] = end_time.strftime(time_format)

    return data

def question_process_impl(question_data, start_time, end_time):
    # use random session fetch question data
    session = random.SystemRandom().choice(sessions)

    question_id = question_data['question_id']
    question_data.update(general_func_zhihu.get_question_data(session, question_id, start_time, end_time))
    return question_data

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
