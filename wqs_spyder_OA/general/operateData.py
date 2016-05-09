# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 10:18:53 2015

@author: dapenghuang
用于处理爬虫获取的数据
爬虫返回的结果为两个
title 及 data 例如：
        其中title为['username','create_time','content','type']
        resultData 为数据两层嵌套列表，其中内层列表顺序与字段名对应
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


from pymongo import MongoClient
import pymongo
import settings
import time
from general.log import Log

linkConfig = settings.mglinkConfig
#logFile = settings.logFile

class OperateData:
    '''
    用于处理爬虫获取的数据
    爬虫返回的结果为两个
    title 及 data 例如：
            其中title为['username','create_time','content','type']
            resultData 为数据两层嵌套列表，其中内层列表顺序与字段名对应
    '''
    def __init__(self,mongodbName = 'MicroTrendSpyder' ,mongocollName = 'SpyderConfig' , dataCollName = 'SpyderData'):
        try:
            self._client = MongoClient(linkConfig)#连接mongDB数据库
            self._db = self._client[mongodbName]
            self._configColl = self._db[mongocollName]
            self._dataColl = self._db[dataCollName]
        except:
            time.sleep(10)
            try:
                self._client = MongoClient(linkConfig)
                self._db = self._client[mongodbName]
                self._configColl = self._db[mongocollName]
                self._dataColl = self._db[dataCollName]
            except Exception as e:
                Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'无法连接mongodb,错误信息为%s'%(e))

        try:
            self._configColl.create_index([('spyder', pymongo.ASCENDING)])
            self._configColl.create_index([('key',pymongo.ASCENDING)])
        except Exception as e:
            Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'无法创建爬虫配置数据库索引,错误信息为%s'%(e))

    def __del__(self):
        self._client.close()
    def saveResultsToDB(self, title, spyderData , config):
        '''
        存储到mongoDB数据库中
        其中title为['username','create_time','content','type']
        resultData 为数据两层嵌套列表，其中内层列表顺序与字段名对应
        其中config为爬虫配置，由GetSpyderConfig获取
        config案例见_tempWriteConfig说明
        取config中的productName，channel，key
        增加insertTime
        '''
        dataList = []
        j = 0
        for line in spyderData:
            data = {}
            for i in range(len(line)):
                data.setdefault(title[i],line[i])
            data['ProductUniqueName'] = config['productName']
            data['ProductUniqueId'] = config['productUniqueId']
            data['channel'] = config['channel']
            data['key'] = config['key']
            data['insertTime'] = time.ctime()
            data['fetched_by_microtrend'] = 0
            data['ExtractDate'] = time.strftime('%Y%m%d', time.strptime(data['create_time'], '%Y-%m-%d %H:%M:%S'))

            dataList.append(data)
            j += 1

        try:
            self._dataColl.insert(dataList, continue_on_error=True)
        except pymongo.errors.DuplicateKeyError:
            pass

        Log().writeLog('INFO',self.__class__.__name__,sys._getframe().f_code.co_name,u'向Mongodb数据库中存储爬取的%s产品，%s渠道的%d条数据成功  '%(config['productName'] , config['channel'], j))


    def getConfigsFromDB(self):
        '''
        从mongodb中获得所有有效爬虫设置
        '''
        results =  self._configColl.find({},{'_id':0})
        configList = []
        for r in results:
            if str(r['open']) == '1':
                configList.append(r)
        return configList
    def _tempWriteConfig(self):
        '''
        用于临时写入mongodb数据库配置
        {'productName':u'乐视影视', #产品名称，对于爬虫无限制
        'channel':u'360助手',      #渠道，对于爬虫无限制
        'spyder':'SpyderZhushou360',#爬虫，必须要与爬虫的类名保持一致
        'key':u'乐视影视',          #爬取的key，需要人工确认
        'beginTime':'0',           #爬取的开始时间，若为0 则采用爬虫默认配置，否则格式为20150201
        'endTime':'0'              #爬取的结束时间，若为0 则采用爬虫默认配置，否则格式为20150201 结束时间要小于开始时间。倒序。
        'open':'1'                 #爬虫是否开放，在运行时会判断1 为开放，0 为关闭
        }
        spyder一定要与类名保持一致
        '''
        zhushou360Config = [{'productName':u'乐视影视',
                             "productUniqueId" : "6b86d5e837eb4ed895074bc6f7b634df",
                            'channel':u'assistant_360',
                            'spyder':'SpyderZhushou360',
                            'key':'http://zhushou.360.cn/detail/index/soft_id/6276',
                            'beginTime':'0',
                            'endTime':'0',
                            'open':'1'},
                            {'productName':u'梦幻西游',
                             "productUniqueId" : "7b86d5e837eb4ed895074bc6f7b634df",
                            'channel':u'assistant_360',
                            'spyder':'SpyderZhushou360',
                            'key':u'http://zhushou.360.cn/detail/index/soft_id/2720322',
                            'beginTime':'0',
                            'endTime':'0',
                            'open':'1'
                            },
                            {'productName':u'唯品会',
                             "productUniqueId" : "8b86d5e837eb4ed895074bc6f7b634df",
                            'channel':u'assistant_360',
                            'spyder':'SpyderZhushou360',
                            'key':u'http://zhushou.360.cn/detail/index/soft_id/21972',
                            'beginTime':'0',
                            'endTime':'0',
                            'open':'1'},
                            {'productName':u'全民突击',
                             "productUniqueId" : "8b86d5e837eb4ed895074bc6f7b634df",
                            'channel':u'assistant_360',
                            'spyder':'SpyderZhushou360',
                            'key':'http://zhushou.360.cn/detail/index/soft_id/2408095',
                            'beginTime':'0',
                            'endTime':'0',
                            'open':'1'}
                            ]
        self._configColl.insert(zhushou360Config)
        Log().writeLog('INFO',self.__class__.__name__,sys._getframe().f_code.co_name,u'利用临时函数写入爬虫配置文件成功')



#debug
#OperateData()._tempWriteConfig()
#configList = OperateData().getConfigsFromDB()
#print configList
#enddebug

