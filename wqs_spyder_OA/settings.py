# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 09:25:43 2015

@author: dapenghuang
"""

import sys
import os
import urllib
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


algorithmDir=getFileDir(1)

#print algorithmDir


logOpen = True
logPrint = True
proxyList = [] #['http://proxy.tencent.com:8080']
threadlen = 5

logFile = algorithmDir+os.sep+'log'+os.sep+'logMessage.log'
#print logFile

#mongoConfig
mghost = '127.0.0.1'
mguser = 'user'
mgpass = urllib.quote_plus('password')
mgport = 12345
mglinkConfig = ''
if mguser == '':
    mglinkConfig = 'mongodb://%s:%d/' % (mghost,mgport)
else:
    mglinkConfig = 'mongodb://%s:%s@%s:%d/' % (mguser,str(mgpass),mghost,mgport)

post_url = 'http://mrs.oa.com:18881/moa/microtrend/openservices_new/service/AddJsonData'
