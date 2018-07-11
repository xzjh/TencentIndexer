#!/usr/bin/env python
# -*- coding: utf-8 -*-
# TencentCrawler module of general functions for Zhihu
# by Jiaheng Zhang, all rights reserved.

from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from hashlib import sha1
import hmac
import random
import dill as pickle
import json
import multiprocessing
import base64
import yundama
import requests
import cookielib
import urllib
import urlparse

request_data_from_webpage = False

time_format = '%Y%m%d%H%M'

question_ui_url_base = 'https://www.zhihu.com/question/{}'
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
question_comment_url_base = 'https://www.zhihu.com/api/v4/questions/{}/comments'
question_comment_url_params = {
	'include': 'data[*].author,collapsed,reply_to_author,disliked,content,voting,vote_count,is_parent_author,is_author',
	'order': 'reverse',
	'limit': 100,
	'offset': 0,
	'status': 'open',
}

agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36"
header = {
    "HOST": "www.zhihu.com",
    "Referer": "https://www.zhihu.com",
    "User-Agent": agent,
    'Connection': 'keep-alive'
}

answer_ui_url_base = 'https://www.zhihu.com/question/{question_id}/answer/{answer_id}'

def init_sessions():
    file_configs = open('configs.json')
    configs_raw = file_configs.read()
    configs = json.loads(configs_raw)
    account_list = configs['zhihu_accounts']
    file_configs.close()

    mp_pool = multiprocessing.Pool(len(account_list))
    serialized_sessions = mp_pool.map(init_session, account_list)
    sessions = map(pickle.loads, serialized_sessions)

    mp_pool.close()

    return sessions

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

def get_question_data(session, question_id, start_time, end_time):

    data = {}
    data['answers'] = []
    answer_count = 0
    answer_url_params['offset'] = 0
    
    if request_data_from_webpage:
	    question_url = question_ui_url_base.format(question_id)
	    question_html = session.get(question_url, headers = header).text
	    question_soup = BeautifulSoup(question_html, 'html.parser')
	    data['question_detail'] = question_soup.find('div', class_ = 'QuestionHeader-detail').text
	    question_numbers_soup = question_soup.find('div', class_ = 'QuestionFollowStatus').find_all('strong')
	    data['question_follower_count'] = question_numbers_soup[0].attrs['title']
	    data['question_view_count'] = question_numbers_soup[1].attrs['title']

    (data['question_comments'], data['question_comment_count']) = get_comments_data(session, question_id, start_time, end_time, question_comment_url_base, question_comment_url_params)

    while True:
        print 'Processing question ID: ' + question_id + ', answer #: ' + str(answer_url_params['offset']) + '-' + str(answer_url_params['offset'] + answer_url_params['limit'] - 1)

        answer_url = answer_url_base.format(question_id) + '?' + urllib.urlencode(answer_url_params)
        data_raw = session.get(answer_url, headers = header).text
        data_json = json.loads(data_raw)
        answer_count = data_json['paging']['totals']
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
                answer_item['answer_url'] = answer_ui_url_base.format(question_id = question_id, answer_id = answer_id)
                (answer_item['answer_comments'], _) = get_comments_data(session, answer_id, start_time, end_time, comment_url_base, comment_url_params)

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

    data['answer_count'] = answer_count
    data['answer_start_time'] = start_time.strftime(time_format)
    data['answer_end_time'] = end_time.strftime(time_format)

    return data

def get_comments_data(session, qa_id, start_time, end_time, url_base, url_params):
    data = []
    url_params['offset'] = 0
    comments_count = 0

    while True:
        comment_url = url_base.format(qa_id) + '?' + urllib.urlencode(url_params)
        data_raw = session.get(comment_url, headers = header).text
        data_json = json.loads(data_raw)
        if 'data' not in data_json:
            continue
        comments_count = data_json['common_counts']
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
            if comment_time > end_time:
                print "-- The comments are too new! Pass this page!"
            url_params['offset'] += url_params['limit']
        else:
            break

    return (data, comments_count)
