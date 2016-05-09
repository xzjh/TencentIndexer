# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 09:59:02 2015

@author: dapenghuang

用于提供通用爬虫，获得url返回爬取内容
"""

import urllib2
from log import Log
import settings
import random
import sys


proxyList = settings.proxyList
#logFile = settings.logFile


class GeneralSpyder:
    '''
    通用爬虫，获得链接，原样返回爬取文本，不予处理
    '''
    def __init__(self):
        '''
        初始化爬虫opener
        '''
        if isinstance(proxyList,list) and len(proxyList) > 0:
            random.shuffle(proxyList)
            proxy_handler = urllib2.ProxyHandler({'http': proxyList[0]})
            self.opener = urllib2.build_opener(proxy_handler)
        else:
            self.opener = urllib2.build_opener()
    def __del__(self):
        self.opener.close()
    def getStaticUrl(self,url):
        '''
        爬取静态url内容
        '''
        try:
            contant = self.opener.open(url)
        except Exception as e:
            Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'打开URL错误,url为%s,错误信息为%s'%(url,e))
            return False
        return contant.read()
        
    def getJSurl(self,url,headers):
        '''
        获取动态交互页面产生的数据
        @headers  : [('Host', 'intf.baike.360.cn'),('Proxy-Connection','keep-alive'),('Cookie','__guid=170536683.461179487652093800.1436251685646.9321')]
        '''
        try:
            req = urllib2.Request(url)
            for head in headers:
                req.add_header(head[0],head[1])
            content = self.opener.open(req)
        except Exception as e:
            Log().writeLog('ERROR',self.__class__.__name__,sys._getframe().f_code.co_name,u'打开URL错误,url为%s,错误信息为%s'%(url,e))
            return False
        return content.read()

"""
#debug
import cookielib
cj = cookielib.CookieJar()
print cj._cookies.values()
product = '360手机卫士'
num = []
for i in range(10):
    num.append(28185825+i)
numstring = ''
for i in num:
    numstring += str(i)+','
numstring = numstring[:-1]
k = urllib2.quote(product)
z = urllib2.quote(numstring)
url5 = 'http://intf.baike.360.cn/index.php?callback=jQuery17206441723585594445_1436424493131&name=%E8%81%9A%E7%BE%8E%E4%BC%98%E5%93%81+Android_com.jm.android.jumei&c=message&a=getmessage&start=20&count=10&type=&_=1436424502593'
headers = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.81 Safari/537.36'),('Host', 'intf.baike.360.cn'),('Referer', 'http://zhushou.360.cn/detail/index/soft_id/77208'),('Proxy-Connection','keep-alive'),('Cookie','__guid=170536683.461179487652093800.1436251685646.9321')]

SP = Spyder()
result = SP.getJSurl(url5,headers)
print result

import cookielib, urllib2  
cj = cookielib.CookieJar()  
proxy_handler = urllib2.ProxyHandler({'http': proxyList[0]})
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_handler)
opener.open(url5)
print cj._cookies.values()
#enddebug
"""
