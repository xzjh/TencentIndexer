# -*- coding: utf-8 -*-
"""
Created on Thu Jul 09 09:56:43 2015

@author: dapenghuang
"""
import threading

class MultiThread(threading.Thread):
    def __init__(self,func,args,name = ''):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args
        self.res = None
    def getResult(self):
        if self.res == None:
            self.res = False
        return self.res
    def run(self):
        self.res = self.func(*self.args)
        
'''
#example
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
                t_title,t_result = threads[n].getResult()
#example
'''