# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 09:27:53 2015

@author: dapenghuang

crawler函数为爬虫入口函数
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

import urllib2
from general.log import Log
from general.spyder import GeneralSpyder
from general.operateData import OperateData
from general.thread import MultiThread
import settings
import time
import random
import sys
import re

threadlen = settings.threadlen
#logFile = settings.logFile


class SpyderZhushou360:
    '''
    爬取360手机助手市场的产品评论
    逻辑：
    360手机助手产品评论依靠如下js动态产生
    http://intf.baike.360.cn/index.php?callback=jQuery17206441723585594445_1436424493131&name=%E8%81%9A%E7%BE%8E%E4%BC%98%E5%93%81+Android_com.jm.android.jumei&c=message&a=getmessage&start=20&count=10&type=&_=1436424502593

    结构为
    jQuery17206441723585594445_1436424493131  第一串数字代表固定的id 第二个为时间
    name=%E8%81%9A%E7%BE%8E%E4%BC%98%E5%93%81+Android_com.jm.android.jumei 产品名称，需要在上线时手工进行配置，配置文件为productInfo 方式为点击更多评论，看运行的js链接
    type=&_=1436424502593 时间，需要大于jQuery时间
    start=20&count=10 从20条评论开始，返回10条评论

    支持按时间爬取，
    '''
    def __init__(self):
        '''
        生成一个随机ID
        '''
        self.randomNum = int(random.random()*1000)

    def crawler(self,key, startTime , endTime , config):
        '''
        爬取产品名称为productName，从当前开始到前两天结束的评论 startTime 要大于 endTime 时间设置格式为文本 20150201
        如果endtime == 0 的话则默认爬取startTime（20150707）前一天的数据 20150707---20150706
        如果 startTime和endTime都为0 ，则爬昨天全天数据
        返回的格式为：title,resultData
        其中title为['username','create_time','content','type']
        resultData 为数据两层嵌套列表，其中内层列表顺序与字段名对应
        '''

        productName = _SpyderZhushou360_h()._getProductName(key)
        if int(startTime) == 0 or int(endTime) == 0:
            startTime = time.strftime('%Y%m%d',time.localtime(time.time()))
            endTime = 0
        try:
            startTimeU = time.mktime(time.strptime(startTime,'%Y%m%d'))#转时间戳
        except Exception as e:
            Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'爬虫时间设置错误，设置的时间为%s，错误信息为%s'%(startTime,e))
            return False,False

        if endTime == 0:
            endTimeU = startTimeU - 86400*1
        else:
            try:
                endTimeU = time.mktime(time.strptime(endTime,'%Y%m%d'))#转时间戳
            except Exception as e:
                Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'爬虫时间设置错误，设置的时间为%s，错误信息为%s'%(endTime,e))
                return False,False

        if endTimeU >= startTimeU:
            Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'爬虫时间设置错误，要求结束时间小于开始时间，实际设置开始时间：结束时间：'%(endTime,e))
            return False,False

        IDnum = str(17206441723585594000 + self.randomNum)
        productNameSplited = productName.split('+')
        if len(productNameSplited) == 1:
            urlProductName = urllib2.quote( productNameSplited[0].encode('utf-8') )
        else:
            urlProductName = urllib2.quote( productNameSplited[0].encode('utf-8') )+'+'+productNameSplited[1]

        Log().writeLog('INFO',self.__class__.__name__,sys._getframe().f_code.co_name,u'开始爬取%s的评论，爬取的区间是%s--%s'%(productName, startTime, time.strftime('%Y%m%d',time.localtime(endTimeU))))


        flag = True#用于标识是否超出时间范围
        resultsData = []
        title = []
        beginNum = 0#第几个评论开始
        urlNum = 0 #记录爬了多少个URL
        commentNum = 0#记录爬了多少个评论
        while flag:
            threads = []
            m = 0#记录有多少线程
            while m < threadlen:
                t = MultiThread(_SpyderZhushou360_h().getOneUrl, (IDnum, urlProductName, beginNum))
                threads.append(t)
                m += 1
                beginNum += 10
                urlNum += 1
            for n in range(len(threads)):
                threads[n].start()
            for n in range(len(threads)):
                threads[n].join()
            for n in range(len(threads)):
                try:
                    t_title,t_result = threads[n].getResult()
                    if t_title == False:
                        flag = False
                        continue
                    title = t_title


                    #urlBeginTime = time.mktime(time.strptime(t_result[0][1],'%Y-%m-%d %H:%M:%S'))
                    #urlEndTime = time.mktime(time.strptime(t_result[-1][1],'%Y-%m-%d %H:%M:%S'))

                    for i in range(len(t_result)):
                        urlTime = time.mktime(time.strptime(t_result[i][1],'%Y-%m-%d %H:%M:%S'))
                        #if urlBeginTime <= startTimeU and urlEndTime >= endTimeU:
                        if urlTime <= startTimeU and urlTime >= endTimeU:
                            resultsData.append(t_result[i])
                            commentNum += 1

                        if urlTime < endTimeU:
                            flag = False

                        if random.random() > 0.6:
                            Log().writeLog('INFO',self.__class__.__name__,sys._getframe().f_code.co_name,u'已爬取%d个URL,存储%d条评论' % (urlNum, commentNum))
                except Exception as e:
                    Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'错误信息为%s'%(e))


        Log().writeLog('INFO', self.__class__.__name__, sys._getframe().f_code.co_name,u'结束爬取%s的评论，爬取的区间是%s--%s，评论的条数为%d' % (productName, startTime, time.strftime('%Y%m%d',time.localtime(endTimeU)), commentNum))
        if len(resultsData) > 0:
            OperateData().saveResultsToDB(title, resultsData, config)
        return title,resultsData

class _SpyderZhushou360_h():
    '''
    为支持多线程，从主类SpyderZhushou360中分离
    '''
    def __init__(self):
        pass
    def getOneUrl(self, IDnum, urlProductName, startNum=0):
        '''
        为了支持多线程
        返回值为
        title：列表类型，对应的字段名
        data：数据两层嵌套列表，其中内层列表顺序与字段名对应
        '''
        jQtime = str(int(time.time()*1000))
        secendTime = str(int(time.time()*1000) + int(random.random()*1000))
        url = 'http://intf.baike.360.cn/index.php?callback=jQuery%s_%s&name=%s&c=message&a=getmessage&start=%s&count=10&type=&_=%s' % (IDnum, jQtime, urlProductName, str(startNum), secendTime)
        headers = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'),('Host', 'intf.baike.360.cn'),('Referer', 'http://zhushou.360.cn/detail/index/soft_id/77208'),('Proxy-Connection','keep-alive')]
        try:
            result = GeneralSpyder().getJSurl(url,headers)
        except Exception as e:
            Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'打开URL错误,url为%s,错误信息为%s'%(url,e))
            return False,False
        return self._resolveContent(result)


    def _resolveContent(self, content):
        '''
        需要解析的结构样例为
        try
            {jQuery17206441723585594081_1436430004632(
                {"errno":0,"error":"","data":
                    {"total":71971,"messages":
                        [
                            {"likes":"0","replies":"0","weight":"0","create_time":"2015-07-09 15:50:12","content":"\u8bf4\u662f\u5185\u5b58\u53d8\u5c0f\uff0c\u53ea\u662f\u628a\u6709\u7684\u529f\u80fd\u5206\u79bb\u51fa\u6765\u4e86\uff0c\u6709\u533a\u522b\u5417\uff1f\u5c31\u662f\u60f3\u4e00\u4e2aAPP\u91cc\u9762\u529f\u80fd\u90fd\u6709\uff0c\u7701\u7684\u4e0b\u592a\u591aAPP\uff0c\u771f\u662f\u65e0\u8bed","username":"faychou","image_url":"http:\/\/quc.qhimg.com\/dm\/50_50_100\/t010b2e26d79fbaf013.jpg","msgid":"28220745","type":"best","qid":"28744674","isadmin":""},
                            {"likes":"0","replies":"0","weight":"0","create_time":"2015-07-09 15:30:06","content":"\u5feb\u53bb360\u5b98\u7f51\u4e0b\u6700\u65b0\u6d4b\u8bd5\u7248\uff0c\u8001\u529f\u80fd\u90fd\u56de\u6765\u4e86\uff0c(\u8f6f\u4ef6\u642c\u5bb6\u7b49)\u3002","username":"360U1447896858","image_url":"http:\/\/quc.qhimg.com\/dm\/50_50_100\/t00df551a583a87f4e9.jpg","msgid":"28220184","type":"best","qid":"1447896858","isadmin":""}
                        ]}
                }
                );
            }
        catch(e){}

        messages 字典结构为 likes":,"replies":,"weight":,"create_time":"2015-07-0915:30:06","content":"","username":"3","image_url":"","msgid":"","type":"best","qid":"","isadmin":""
        有用的结构为  create_time content username type
        解析逻辑，首先去掉字符串前45位 后12位
        返回结构为
        title：列表类型，对应的字段名
        data：数据两层嵌套列表，其中内层列表顺序与字段名对应
        '''
        title = ['username','create_time','content','type']
        dic_data = eval(content[45:-13])
        commentData_dic = dic_data['data']['messages']
        returnData = []
        for oneUser in commentData_dic:
            oneData = []
            for col in title:
                oneData.append(oneUser[col].decode("unicode-escape"))
            returnData.append(oneData)

        if returnData == []:
            Log().writeLog('ERROR', self.__class__.__name__, sys._getframe().f_code.co_name,u'URL无结果返回，请检查设置的产品名称及爬取时间是否正确')
            return False,False

        return title,returnData

    def _getProductName(self,key):
        '''
        key 为360助手市场的一个产品顶层url，
        从返回的静态页面的scripe中获取产品名称
        获取的名称需要把空格替换为加号，以便和js调用的链接保持一致
        '''
        html = GeneralSpyder().getStaticUrl(key)
        string = re.findall('\'baike_name\': \'(.+)\'',html)
        return string[0].decode('utf-8').replace(' ','+')
#debug
#SpyderZhushou360().crawler()
#enddebug
