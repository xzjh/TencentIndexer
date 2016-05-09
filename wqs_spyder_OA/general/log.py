# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 09:36:59 2015

@author: dapenghuang
"""

import settings
import time
import sys
import os

def getFileDir(layer=1):
    file_full = os.path.abspath(sys.argv[0])
    floor=file_full.split(os.sep)
    fileDir=''
    for i in range(len(floor)-layer):
        fileDir+=floor[i]+os.sep
    return fileDir[:-1]
    
algorithmDir=getFileDir(1)#获得父目录

logOpen = settings.logOpen#log是否打开
logPrint = settings.logPrint#log是否打印控制台

logFile = settings.logFile

class Log:
    '''
    为过程提供日志支持
    '''
    def __init__(self,filename= logFile):
        '''
        以追加模式打开
        '''
        self._f = open(filename,'a')
    def __del__(self):
        self._f.close()
    def writeLog(self,logType,className,funcName,logtxt):
        if logOpen == True:
            log = '%s【%s】【%s.%s】%s' % (time.ctime(),logType,className,funcName,logtxt)
            log += '\n'
            if logPrint == True:
                print log
            self._f.write(log)


""" 
#example
#debug
class A:
    def __init__(self):
        pass
    def rec(self):
        log =Log()
        className =  self.__class__.__name__
        funcName =  sys._getframe().f_code.co_name
        log.writeLog('Info',className,funcName,'test')
        
a=A()
a.rec()
#enddebug
"""
