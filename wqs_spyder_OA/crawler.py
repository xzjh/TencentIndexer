# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 09:26:44 2015

@author: dapenghuang

配置驱动
读配置
调爬虫
多进程
"""

import os
import sys
reload(sys)
sys.setdefaultencoding('utf-8')

def getFileDir(layer = 1):
    import sys
    file_full = os.path.abspath(sys.argv[0])
    floor = file_full.split(os.sep)
    fileDir = ''
    for i in range(len(floor)-layer):
        fileDir += floor[i] + os.sep
    return fileDir[:-1]


algorithmDir=getFileDir(2)

sys.path.append(algorithmDir)
sys.path.append(algorithmDir + os.sep + 'general')
sys.path.append(algorithmDir + os.sep + 'spyder')


logFile = algorithmDir+os.sep+'wqs_spyder'+os.sep+'log'+os.sep+'logMessage.log'

import multiprocessing
from spyder.spyder_zhushou360 import SpyderZhushou360
import settings
from general.operateData import OperateData
import requests
import json
import httplib

linkConfig = settings.mglinkConfig



class Spyder:
    '''
    处理GetSpyderConfig的结果，返回一个嵌套List
    [[spyderclass,key,starttime,endtime],[],[]]
    '''
    def __init__(self):
        '''
        获取配置
        配置
        {'productName':u'乐视影视', #产品名称，对于爬虫无限制
        'channel':u'360助手',      #渠道，对于爬虫无限制
        'spyder':'SpyderZhushou360',#爬虫，必须要与爬虫的类名保持一致
        'key':u'乐视影视',          #爬取的key，需要人工确认
        'beginTime':'0',           #爬取的开始时间，若为0 则采用爬虫默认配置，否则格式为20150201
        'endTime':'0'              #爬取的结束时间，若为0 则采用爬虫默认配置，否则格式为20150201 结束时间要小于开始时间。倒序。
        'open':'1'                 #爬虫是否开放，在运行时会判断1 为开放，0 为关闭
        }
        '''
        self._configList = OperateData().getConfigsFromDB()
    def getSpyders(self):
        '''
        根据配置list构造爬虫
        返回一个嵌套List
        [[spyderclass,key,starttime,endtime],[],[]]
        '''
        returnList = []
        for config in self._configList:
            func = eval(config['spyder']+'()').crawler
            key = config['key']
            startTime = config['beginTime']
            endTime = config['endTime']
            returnList.append([func, key, startTime, endTime , config])
        return returnList




spyderList = Spyder().getSpyders()

if __name__ == '__main__':
    jobs = []
    for spyder in spyderList:
        p = multiprocessing.Process(target=spyder[0], args=(spyder[1], spyder[2], spyder[3], spyder[4]))
        jobs.append(p)

    for j in jobs:
        j.start()
    for j in jobs:
        j.join()

    headers = {'Content-Type': 'application/json', 'Accept': 'application/json'}
    values = json.dumps({'json':"{\n    \"status\": \"0\", \n    \"operation\": \"\"\n}"})
    print "post " ,settings.post_url, " ", values
    print requests.post(settings.post_url, data=values, headers=headers)
