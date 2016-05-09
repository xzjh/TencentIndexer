# -*- coding: utf-8 -*-
"""
Created on Mon Jul 13 15:17:43 2015

@author: dapenghuang
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


algorithmDir = getFileDir(1)


sys.path.append(algorithmDir)
sys.path.append(algorithmDir + os.sep + 'general')
sys.path.append(algorithmDir + os.sep + 'spyder')

from spyder.spyder_zhushou360 import SpyderZhushou360
import settings
from general.operateData import OperateData

OperateData()._tempWriteConfig()
