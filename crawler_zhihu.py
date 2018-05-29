#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler for Zhihu http://zhihu.com
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
import yundama
import multiprocessing

import general_func

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
    'limit': 10,
    'time_zone': 'a_day',
}
answer_url_base = 'https://www.zhihu.com/api/v4/questions/{}/answers'
answer_url_params = {
    'include': 'data[*].is_normal,admin_closed_comment,reward_info,is_collapsed,annotation_action,annotation_detail,collapse_reason,is_sticky,collapsed_by,suggest_edit,comment_count,can_comment,content,editable_content,voteup_count,reshipment_settings,comment_permission,created_time,updated_time,review_info,relevant_info,question,excerpt,relationship.is_authorized,is_author,voting,is_thanked,is_nothelp;data[*].mark_infos[*].url;data[*].author.follower_count,badge[?(type=best_answerer)].topics',
    'offset': 0,
    'limit': 20,
    'sort_by': 'created',
}
comment_url_base = 'https://www.zhihu.com/api/v4/answers/{}/comments'
comment_url_params = {
    'include': 'data[*].author,collapsed,reply_to_author,disliked,content,voting,vote_count,is_parent_author,is_author',
    'order': 'reverse',
    'limit': 20,
    'offset': 0,
    'status': 'open',
}

username = 'quxwe36bnci6@163.com'
password = 'pnoign8952'
login_url_base = 'https://www.zhihu.com/login/email'
login_url_params = {
    'phone_num': username,
    'password': password,
}

session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename="cookies/zhihu.txt")
try:
    session.cookies.load(ignore_discard=True)
except:
    print("Failed to load cookie file!")

agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
header = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": agent,
    'Connection': 'keep-alive'
}

def get_xsrf_dc0():
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

def get_captcha(headers):
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

def is_login():
    response = session.get("https://www.zhihu.com/inbox", headers=header, allow_redirects=False)
    if response.status_code != 200:
        print 'Now log in Zhihu...'
        login()
    else:
        print 'You already logged in!'

def login():
    post_url = 'https://www.zhihu.com/api/v3/oauth/sign_in'
    XXsrftoken, XUDID = get_xsrf_dc0()
    header.update({
        "authorization": "oauth c3cef7c66a1843f8b3a9e6a1e3160e20",
        "X-Xsrftoken": XXsrftoken,
    })
    time_str = str(int((time.time() * 1000)))
    post_data = {
        "client_id": "c3cef7c66a1843f8b3a9e6a1e3160e20",
        "grant_type": "password",
        "timestamp": time_str,
        "source": "com.zhihu.web",
        "password": password,
        "username": username,
        "captcha": "",
        "lang": "en",
        "ref_source": "homepage",
        "utm_source": "",
        "signature": get_signature(time_str),
        'captcha': get_captcha(header)
    }

    response = session.post(post_url, data=post_data, headers=header, cookies=session.cookies)
    if response.status_code == 201:
        session.cookies.save()
    else:
        print 'Failed to log in!'

def get_search_results(keyword):
    search_url_params['q'] = keyword
    search_results = []
    search_url_params['offset'] = 0

    mp_pool = multiprocessing.Pool(search_url_params['limit'])

    while True:
        search_url = search_url_base + '?' + urllib.urlencode(search_url_params)
        data_raw = session.get(search_url, headers = header).text
        data_json = json.loads(data_raw)
        result_items_json = filter(lambda item: item['type'] == 'search_result', data_json['data'])
        if len(result_items_json) == 0:
            break;

        results = mp_pool.map(search_result_process_impl, result_items_json)
        results = filter(lambda result: result != None)
        search_results.extend(results)

        search_url_params['offset'] += search_url_params['limit']

    return search_results

def search_result_process_impl(result_item_json):
    result_type = result_item_json['object']['type']
    if result_type != 'answer':
        return None

    result_item = {}
    result_item['question_title'] = result_item_json['highlight']['title']
    result_item['question_created_time'] = datetime.fromtimestamp(result_item_json['object']['created_time']).strftime(time_format)
    result_item['answer_id'] = str(result_item_json['object']['id'])
    question_id = result_item_json['object']['question']['id']
    result_item['question_id'] = question_id

    question_data = get_question_data(question_id)
    result_item.update(question_data)

    return result_item

def get_question_data(question_id):

    print 'Processing question ID: ' + question_id

    data = {}
    data['answers'] = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days = 1)
    answer_url_params['offset'] = 0

    while True:
        print '- Processing answer #: ' + str(answer_url_params['offset']) + '-' + str(answer_url_params['offset'] + answer_url_params['limit'] - 1)

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
                answer_item['answer_comments'] = get_comments_data(answer_id, start_time, end_time)

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

def get_comments_data(answer_id, start_time, end_time):

    data = []
    comment_url_params['offset'] = 0

    while True:
        comment_url = comment_url_base.format(answer_id) + '?' + urllib.urlencode(comment_url_params)
        data_raw = session.get(comment_url, headers = header).text
        data_json = json.loads(data_raw)
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

    is_login()

    for keyword in keyword_list:

        keyword = keyword.strip('\n')

        print "********************************************************************************"
        print "Crawling keyword: " + keyword

        # try:
        data = get_search_results(keyword)
        # except:
        #   print "Failed to get the data for this keyword: {}!".format(keyword)
        #   continue

        # save to json file

        data_file_prefix = 'data_' + website_id + '_'
        dir_name = 'data_' + website_id
        file_name = data_file_prefix + keyword + '_' + datetime.now().strftime("%Y%m%d%H%M") + '.json'

        general_func.process_results(dir_name, file_name, data)

if __name__ == '__main__':

    print "Please run the crawler from crawler.py!"
