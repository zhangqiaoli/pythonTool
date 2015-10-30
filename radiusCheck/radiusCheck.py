#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys,os
import io
import threading
import ConfigParser
import pysmartac
import pysmartac.configer
import pysmartac.assistant as assistant
from pysmartac.daemon import daemon
from pysmartac.log import PLOG
import httplib
import datetime
import time
import json
import re

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

class CONF:
    clientPath=""
    logDir="\\172.16.2.124\public\workspace\radius_sa\output\var\log\radius"
    radiusIP = "127.0.0.1"
    secret = "testing123"
    reponseTimeout = 10
    logLevel='D'
conf=CONF() 

def enumTodayLogFile():
    nowtime = datetime.datetime.now()
    logday = nowtime.strftime("%Y%m%d")
    filelist = []
    logdir = conf.logDir
    files = os.listdir(logdir)
    for f in files:
        subpath = os.path.join(logdir,f)
        if (os.path.isfile(subpath)):
            if (subpath.find(logday) != -1):
                filelist.append(subpath)      
    return filelist    

def getCurrentLogfile():
    logfilelist = enumTodayLogFile()
    currentlogfile = ""
    filetimestamp = 0
    for logfile in logfilelist:
        filetime = time.localtime( os.path.getmtime(logfile) )
        filetimestamptmp = time.mktime(filetime)
        if filetimestamptmp > filetimestamp :
            filetimestamp = filetimestamptmp
            currentlogfile = logfile
    return currentlogfile
    
# 调用radius auth 进行自检
def InvokeProc():
    #echo "User-Name = radiusSelfCheck, User-Password = radiusSelfCheck" | ./radclient -xxxx 127.0.0.1:1812 auth testing123
    strCMD="echo \"User-Name = radiusSelfCheck,User-Password = radiusSelfCheck\" | %s -xxxx %s:1812 auth %s" % \
    (conf.clientPath,conf.radiusIP,conf.secret)
    try:   
        PLOG.info("call:%s\n"%(strCMD))
        beforeInvokeAuth = int(time.time())
        retstr = os.popen(strCMD).read()
        afterInvokeAuth = int(time.time())
        PLOG.debug("output:%s\n"%(retstr))      
        if ( afterInvokeAuth - beforeInvokeAuth > conf.reponseTimeout ):   
            PLOG.info("radius auth reponse timeout,stop radius")
            InvokeStopRadius()
            return 0    
        if(retstr.find("rad_recv:") != -1 and retstr.find("Reply-Message") != -1) :
            # 收到回应
            if( retstr.find("radius status is ok") != -1 ) :
                # radius运行正常
                PLOG.info("radius run status is ok")
                return 1
            else:
                # radius状态不正确,关掉radius
                repmsg = ""
                repMsgpattern=re.compile('Reply-Message\s*=\s*(?P<repmsg>.*)\s*')
                m=repMsgpattern.search(retstr)
                if ( m != None and m.group('repmsg') != None):
                    repmsg = m.group('repmsg')
                PLOG.info("radius run status error,errmsg = %s ,stop radius" % repmsg)
                InvokeStopRadius()
                return 0
        else:
            # radius状态不正确,关掉radius
            PLOG.info("radius run status error,no response,stop radius")
            InvokeStopRadius()  
            return 0
    except Exception, e:
        PLOG.info("执行命令失败,CMD=%s\nError=%s\n"%(strCMD,e.args[1]))
        exit(1)
    return 1

def InvokeStopRadius():
    strStopradiusCMD = "service radiusd stop"
    try: 
        PLOG.info("call:%s\n"%(strStopradiusCMD))
        stopret = os.popen(strStopradiusCMD).read()
        PLOG.debug("output:%s\n"%(stopret) )
    except Exception, e:
        PLOG.info("执行命令失败,CMD=%s\nError=%s\n"%(strStopradiusCMD,e.args[1]))
        exit(1)
        
def run():
    init() 
    # radius 日志检查
    beforeInvoketime = datetime.datetime.now()
    currentLogFile = getCurrentLogfile()
    beforeInvokeLogFileSize = os.path.getsize(currentLogFile)
    # radius auth请求检查
    ret = InvokeProc()
    # radius auth请求检查 end
    if (ret == 1) :
        # radius 运行状态正常,检查log
        afterInvoketime = datetime.datetime.now()
        if beforeInvoketime.day == afterInvoketime.day:
            if os.path.getsize(currentLogFile) > beforeInvokeLogFileSize :
                PLOG.info("radius log status is ok")
            else:
                PLOG.info("radius log status error,no growth,stop radius")
                InvokeStopRadius()
        else:
            # 调用前后不是同一天(可能写入新日志,也可能写入旧日志,or判断)
            logfile = getCurrentLogfile()
            if ( logfile != None and len(logfile) >0 and os.path.getsize(logfile) > 0 ) or os.path.getsize(currentLogFile) > beforeInvokeLogFileSize:
                PLOG.info("radius log status is ok")
            else:
                PLOG.info("radius log status error,no growth or no new log,stop radius")
                InvokeStopRadius()
      


def init():    
    configfile=assistant.SF("%s/radiusCheck.conf"%(os.path.dirname(__file__)))
    print os.path.dirname(__file__)
    config=pysmartac.configer.openconfiger(configfile)

    #configer
    conf.logLevel=config.getstr("system","logLevel",conf.logLevel)
    conf.clientPath=config.getstr("system","clientPath",conf.clientPath)
    conf.logDir=config.getstr("system","logDir",conf.logDir)
    conf.radiusIP=config.getstr("system","radiusIP",conf.radiusIP)
    conf.reponseTimeout=config.getint("system","reponseTimeout",conf.reponseTimeout)
    conf.secret=config.getstr("system","secret",conf.secret)
    config.save()
    #log settings
    PLOG.setlevel(conf.logLevel)
    PLOG.enableFilelog("%s/log/RADCK_$(Date8).log"%(os.path.dirname(__file__)))

if __name__ == "__main__":
    run()

