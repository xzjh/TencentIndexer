#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for Zhihu Topic http://zhihu.com
# by Jiaheng Zhang, all rights reserved.

import urllib
import urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time
import json
import re
import cookielib
import requests
import hmac
from hashlib import sha1
import base64
import yundama
import multiprocessing
import random
import dill as pickle
import functools

import general_func

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
question_url_base = 'https://www.zhihu.com/api/v4/topics/{topic_id}/feeds/timeline_activity'
question_url_params = {
    'include': 'data[?(target.type=topic_sticky_module)].target.data[?(target.type=answer)].target.content,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[?(target.type=topic_sticky_module)].target.data[?(target.type=answer)].target.is_normal,comment_count,voteup_count,content,relevant_info,excerpt.author.badge[?(type=best_answerer)].topics;data[?(target.type=topic_sticky_module)].target.data[?(target.type=article)].target.content,voteup_count,comment_count,voting,author.badge[?(type=best_answerer)].topics;data[?(target.type=topic_sticky_module)].target.data[?(target.type=people)].target.answer_count,articles_count,gender,follower_count,is_followed,is_following,badge[?(type=best_answerer)].topics;data[?(target.type=answer)].target.content,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[?(target.type=answer)].target.author.badge[?(type=best_answerer)].topics;data[?(target.type=article)].target.content,author.badge[?(type=best_answerer)].topics;data[?(target.type=question)].target.comment_count',
    'offset': 0,
    'limit': 100,
}
answer_url_base = 'https://www.zhihu.com/api/v4/questions/{}/answers'
answer_url_params = {
    'include': 'data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[*].mark_infos[*].url;data[*].author.follower_count,badge[?(type=best_answerer)].topics',
    'offset': 0,
    'limit': 100,
    'sort_by': 'created',
}
comment_url_base = 'https://www.zhihu.com/api/v4/answers/{}/comments'
comment_url_params = {
    'include': 'data[*].author,collapsed,reply_to_author,disliked,content,voting,vote_count,is_parent_author,is_author',
    'order': 'reverse',
    'limit': 100,
    'offset': 0,
    'status': 'open',
}
sessions = []

agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
header = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": agent,
    'Connection': 'keep-alive'
}

question_ui_url_base = 'https://www.zhihu.com/question/{question_id}'
answer_ui_url_base = 'https://www.zhihu.com/question/{question_id}/answer/{answer_id}'

def init_sessions():
    global sessions

    file_configs = open('configs.json')
    configs_raw = file_configs.read()
    configs = json.loads(configs_raw)
    account_list = configs['zhihu_accounts']
    file_configs.close()

    mp_pool = multiprocessing.Pool(len(account_list))
    serialized_sessions = mp_pool.map(init_session, account_list)
    sessions.extend(map(pickle.loads, serialized_sessions))

    mp_pool.close()

def init_session(account):
    
    username = account['name']
    password = account['password']

    # TODO lock
    session = requests.session()
    session.cookies = cookielib.LWPCookieJar(filename='cookies/zhihu_{}.txt'.format(username))
    try:
        session.cookies.load(ignore_discard=True)
    except:
        print("Failed to load cookie file for account {}!").format(username)

    try:
        is_login(session, username, password)
    except:
        print("Failed to log in account {}!").format(username)

    return pickle.dumps(session)

def get_xsrf_dc0(session):
    response = session.get("https://www.zhihu.com/signup", headers=header)
    return response.cookies["_xsrf"], response.cookies["d_c0"]

def get_signature(time_str):
    h = hmac.new(key='d1b964811afb40118a12068ff74a12f4'.encode('utf-8'), digestmod=sha1)
    grant_type = 'password'
    client_id = 'c3cef7c66a1843f8b3a9e6a1e3160e20'
    source = 'com.zhihu.web'
    now = time_str
    h.update((grant_type + client_id + source + now).encode('utf-8'))
    return h.hexdigest()

def get_captcha(session, headers):
    response = session.get('https://www.zhihu.com/api/v3/oauth/captcha?lang=en', headers=headers)
    r = re.findall('"show_captcha":(\w+)', response.text)
    if r[0] == 'false':
        return ''
    else:
        response = session.put('https://www.zhihu.com/api/v3/oauth/captcha?lang=en', headers=header)
        show_captcha = json.loads(response.text)['img_base64']
        with open('captcha/zhihu.gif', 'wb') as f:
            f.write(base64.b64decode(show_captcha))
        # im = Image.open('captcha.gif')
        # im.show()
        # im.close()
        # captcha = input('Input captcha: ')
        # session.post('https://www.zhihu.com/api/v3/oauth/captcha?lang=en', headers=header,
        #              data={"input_text": captcha})
        return yundama.get_captcha_result('captcha/zhihu.gif')

def is_login(session, username, password):
    response = session.get("https://www.zhihu.com/inbox", headers=header, allow_redirects=False)
    if response.status_code != 200:
        print 'Now log in Zhihu for account {}...'.format(username)
        login(session, username, password)
    else:
        print '{} already logged in!'.format(username)

def login(session, username, password):
    post_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'
    XXsrftoken, XUDID = get_xsrf_dc0(session)
    header.update({
        'authorization': 'oauth c3cef7c66a1843f8b3a9e6a1e3160e20',
        'X-Xsrftoken': XXsrftoken,
    })
    time_str = str(int((time.time() * 1000)))
    post_data = {
        'client_id': 'c3cef7c66a1843f8b3a9e6a1e3160e20',
        'grant_type': 'password',
        'timestamp': time_str,
        'source': 'com.zhihu.web',
        'password': password,
        'username': username,
        'lang': 'en',
        'ref_source': 'homepage',
        'utm_source': '',
        'signature': get_signature(time_str),
        'captcha': get_captcha(session, header)
    }

    response = session.post(post_url, data=post_data, headers=header, cookies=session.cookies)
    if response.status_code == 201:
        session.cookies.save()
    else:
        print 'Failed to log in for {}!'.format(username)

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
    data_raw = session.get(search_url, headers = header).text
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
    question_url_params['offset'] = 0

    # use random session fetch question data
    mp_pool = multiprocessing.Pool(processes_num)

    while True:
        print 'Processing topic ID: ' + topic_id + ', question #: ' + str(question_url_params['offset']) + '-' + str(question_url_params['offset'] + question_url_params['limit'] - 1)

        question_url = question_url_base.format(topic_id = topic_id) + '?' + urllib.urlencode(question_url_params)
        data_raw = session.get(question_url, headers = header).text
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
            question_url_params['offset'] += question_url_params['limit']
        else:
            break

    question_process_impl_func = functools.partial(question_process_impl, start_time = start_time, end_time = end_time)
    data['questions'] = mp_pool.map(question_process_impl_func, data['questions'])
    mp_pool.close()

    data['question_start_time'] = start_time.strftime(time_format)
    data['question_end_time'] = end_time.strftime(time_format)

    return data

def question_process_impl(question_data, start_time, end_time):
    question_id = question_data['question_id']
    question_data.update(get_question_data(question_id, start_time, end_time))
    return question_data

def get_question_data(question_id, start_time, end_time):

    data = {}
    data['answers'] = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days = 1)
    answer_url_params['offset'] = 0

    # use random session fetch question data
    session = random.SystemRandom().choice(sessions)

    while True:
        print 'Processing question ID: ' + question_id + ', answer #: ' + str(answer_url_params['offset']) + '-' + str(answer_url_params['offset'] + answer_url_params['limit'] - 1)

        answer_url = answer_url_base.format(question_id) + '?' + urllib.urlencode(answer_url_params)
        data_raw = session.get(answer_url, headers = header).text
        data_json = json.loads(data_raw)
        answers_json = filter(lambda answer_json: answer_json['type'] == 'answer', data_json['data'])

        answer_time = None
        for answer_json in answers_json:

            answer_item = {}
            answer_time = datetime.fromtimestamp(answer_json['created_time'])

            if answer_time >= start_time:

                # the answer is too new
                if answer_time > end_time:
                    continue

                answer_item['answer_created_time'] = answer_time.strftime(time_format)
                answer_id = str(answer_json['id'])
                answer_item['answer_id'] = answer_id
                answer_item['answer_voteup_count'] = answer_json['voteup_count']
                answer_item['answer_author_avatar_url'] = answer_json['author']['avatar_url']
                answer_item['answer_author_name'] = answer_json['author']['name']
                answer_item['answer_author_follower_count'] = answer_json['author']['follower_count']
                answer_item['answer_updated_time'] = datetime.fromtimestamp(answer_json['updated_time']).strftime(time_format)
                answer_item['answer_content'] = answer_json['content']
                answer_item['answer_comment_count'] = answer_json['comment_count']
                answer_item['answer_comments'] = get_comments_data(session, answer_id, start_time, end_time)
                answer_item['answer_url'] = answer_ui_url_base.format(question_id = question_id, answer_id = answer_id)

                data['answers'].append(answer_item)

            else:
                break

        if answer_time != None and answer_time >= start_time:
            # the answer is too new
            if answer_time > end_time:
                print "-- The answers are too new! Pass this page!"
            answer_url_params['offset'] += answer_url_params['limit']
        else:
            break

    data['answer_start_time'] = start_time.strftime(time_format)
    data['answer_end_time'] = end_time.strftime(time_format)

    return data

def get_comments_data(session, answer_id, start_time, end_time):

    data = []
    comment_url_params['offset'] = 0

    while True:
        comment_url = comment_url_base.format(answer_id) + '?' + urllib.urlencode(comment_url_params)
        data_raw = session.get(comment_url, headers = header).text
        data_json = json.loads(data_raw)
        if 'data' not in data_json:
            continue
        comments_json = filter(lambda comment_json: comment_json['type'] == 'comment', data_json['data'])

        comment_time = None
        for comment_json in comments_json:

            comment_item = {}
            comment_time = datetime.fromtimestamp(comment_json['created_time'])

            if comment_time >= start_time:

                # the comment is too new
                if comment_time > end_time:
                    continue

                comment_item['comment_created_time'] = comment_time.strftime(time_format)
                comment_item['comment_id'] = str(comment_json['id'])
                comment_item['comment_content'] = comment_json['content']
                comment_item['comment_author_id'] = comment_json['author']['member']['id']
                comment_item['comment_author_name'] = comment_json['author']['member']['name']
                comment_item['comment_author_avator_url'] = comment_json['author']['member']['avatar_url']
                comment_item['comment_voteup_count'] = comment_json['vote_count']
                
                data.append(comment_item)

            else:
                break

        if comment_time != None and comment_time >= start_time:
            # the answer is too new
            if comment_time > end_time:
                print "-- The comments are too new! Pass this page!"
            comment_url_params['offset'] += comment_url_params['limit']
        else:
            break

    return data

def crawl(args):

    print "Now running TencentCrawler for " + website_name

    start_time = args['start_time']
    end_time = args['end_time']

    keyword_list = general_func.get_list_from_file(page_list_file)

    init_sessions()

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
