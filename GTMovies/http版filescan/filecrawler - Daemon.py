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
import uuid

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

class CONF:
    pidfile="/tmp/filecrawler.pid"
    threadCount=1
    httpServerSite=""
    movieDir=""
    appDir=""
    movieOutputFile="movies.json"
    appOutputFile="apps.json"
    # 单位分钟
    checkInterval=1
    logLevel='D'
conf=CONF() 

def enumDir(rootDir):
    dirlist = []
    files = os.listdir(rootDir)
    for f in files:
        subpath = os.path.join(rootDir,f)
        if (os.path.isdir(subpath)):
            dirlist.append(subpath)
    return dirlist

def enumFile(rootDir):
    filelist = []
    files = os.listdir(rootDir)
    for f in files:
        subpath = os.path.join(rootDir,f)
        if (os.path.isfile(subpath)):
            filelist.append(subpath)
    return filelist

def addJsonInfo(jsonSourcefile,destJson):
    filedir = os.path.dirname(jsonSourcefile)
    parentDirName = os.path.split(filedir)[-1]
    primaryFilename = ""
    jsSourceFileInfo = None
    with open(jsonSourcefile,"r") as f:
        jsSourceFileInfo = json.load(f,'utf8')	
    if jsSourceFileInfo !=None and isinstance(jsSourceFileInfo,dict):
        if jsSourceFileInfo.has_key("file"):
            primaryFilename = jsSourceFileInfo["file"]  
            if primaryFilename != "" :	
                primaryFileSize = os.path.getsize(os.path.join(filedir,primaryFilename))
                filetimestamp = time.localtime( os.path.getmtime(os.path.join(filedir,primaryFilename)) )
                primaryFileTime = time.strftime('%Y-%m-%d %H:%M:%S',filetimestamp)
                jsSourceFileInfo["filesize"] = str(primaryFileSize)
                jsSourceFileInfo["filetime"] = primaryFileTime
                jsSourceFileInfo["id"] = str(uuid.uuid1())
                if jsSourceFileInfo.has_key("file") :
                    jsSourceFileInfo["file"] = parentDirName +'/' + jsSourceFileInfo["file"]
                if jsSourceFileInfo.has_key("poster") :
                    jsSourceFileInfo["poster"] = parentDirName +'/' + jsSourceFileInfo["poster"]
                if jsSourceFileInfo.has_key("thumbnail") :
                    jsSourceFileInfo["thumbnail"] = parentDirName +'/' + jsSourceFileInfo["thumbnail"]
                if jsSourceFileInfo.has_key("extend") :
                    jsextend = jsSourceFileInfo["extend"]
                    if jsextend.has_key("screenshot") :
                        jsscreenshottmp = []
                        for picture in jsextend["screenshot"] :
                            picture = parentDirName +'/' + picture
                            jsscreenshottmp.append(picture)
                        jsextend["screenshot"] =jsscreenshottmp
                destJson["list"].append(jsSourceFileInfo)
                PLOG.debug('generate file info of dir "%s" success'%(filedir))
            else:
                PLOG.debug("generate file info of dir %s failed,primary File name is empty"% (filedir)) 

        else :
            PLOG.debug('not find "file" node in info file %s , skip it' %(jsonSourcefile))
    else:
        PLOG.warn('js file %s is null,maybe path error! skip it' %(jsonSourcefile))

def scanFile(rootpath,filetype):
    PLOG.debug('Type["%s"] file start crawling...dir = %s ' %(filetype,rootpath))
    outputjsfilename = ""
    rootDirname = ""
    if rootpath[-1] == '\\' or rootpath[-1] == '/' :
        rootpath = rootpath[:-1]
    rootDirname = os.path.split(rootpath)[-1]	
    if filetype == "movie":
        outputjsfilename = conf.movieOutputFile
    elif filetype == "app":
        outputjsfilename = conf.appOutputFile
    outputjsfilename = outputjsfilename.decode('utf8')
    rootpath = rootpath.decode('utf8')
    dirlist = enumDir(rootpath)
    allJsonInfo = {}
    allJsonInfo["update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allJsonInfo["source"] = conf.httpServerSite + rootDirname + '/'
    allJsonInfo["list"] =[]		    
    for subdir in dirlist:
        fileitems = enumFile(os.path.join(rootpath,subdir))
        for fileitem in fileitems:
            if fileitem[-5:] == ".json" : 	    
                addJsonInfo(fileitem,allJsonInfo)
    with open(outputjsfilename,"w") as f:
        json.dump(allJsonInfo, f,indent=4,ensure_ascii=False)
    PLOG.debug('Type["%s"] file crawl dir %s finished' %(filetype,rootpath))	

class filecrawlerDaemon(daemon):
    def run(self):
        init()  
        if conf.httpServerSite[-1] != '/' : conf.httpServerSite += '/'
        nowTime = datetime.datetime.now()
        secondWaitTime=0
        while 1:
            time.sleep(secondWaitTime)        
            # 爬取文件,生成最终json文件 start	    
            scanFile(conf.movieDir,"movie")
            scanFile(conf.appDir,"app")
            # 爬取文件,生成最终json文件 end
            nowTime = datetime.datetime.now()
            #计算下次执行时间 需等待时间(单位:ms)  sleep参数单位为s,可以是小数
            waitTime = (conf.checkInterval-(nowTime.minute%conf.checkInterval))*60*1000-nowTime.second*1000-nowTime.microsecond/1000
            secondWaitTime = float(waitTime)/1000  

def init():    
    configfile=assistant.SF("%s/filecrawler.conf"%(os.path.dirname(__file__)))
    print os.path.dirname(__file__)
    config=pysmartac.configer.openconfiger(configfile)

    #configer
    conf.pidfile=config.getstr("system","pidfile",conf.pidfile)
    conf.threadCount=config.getint("system","threadCount",conf.threadCount)
    conf.logLevel=config.getstr("system","logLevel",conf.logLevel)
    conf.httpServerSite=config.getstr("system","httpserversite",conf.httpServerSite)
    conf.movieDir=config.getstr("system","movieDir",conf.movieDir)
    conf.appDir=config.getstr("system","appDir",conf.appDir)
    conf.movieOutputFile=config.getstr("system","movieOutputFile",conf.movieOutputFile)
    conf.appOutputFile=config.getstr("system","appOutputFile",conf.appOutputFile)    
    conf.checkInterval=config.getint("system","checkInterval",conf.checkInterval)
    config.save()
    #log settings
    PLOG.setlevel(conf.logLevel)
    PLOG.enableFilelog("%s/log/FLCRAWLER_$(Date8)_$(filenumber2).log"%(os.path.dirname(__file__)))

if __name__ == "__main__":
    daemon = filecrawlerDaemon('/tmp/filecrawler.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        elif 'run' == sys.argv[1]:
            daemon.run()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart|run" % sys.argv[0]
        sys.exit(2)

