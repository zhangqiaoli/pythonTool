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
    httpServerSite=""
    movieDir=""
    iosDir=""
    androidDir=""
    movieOutputFile="movies.json"
    iosOutputFile="ios.json"
    androidOutputFile="android.json"
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
            if primaryFilename != "":	
                jsSourceFileInfo["id"] = str(uuid.uuid1())   
                if primaryFilename.startswith("https:") :
                    # ios info file
                    filetimestamp = time.localtime( os.path.getmtime(jsonSourcefile)) 
                    primaryFileTime = time.strftime('%Y-%m-%d %H:%M:%S',filetimestamp)
                    jsSourceFileInfo["filetime"] = primaryFileTime
                    if not jsSourceFileInfo.has_key("filesize") :
                        jsSourceFileInfo["filesize"] = "0"
                    #destJson["list"].append(jsSourceFileInfo)
                else:
                    try:
                        primaryFileSize = os.path.getsize(os.path.join(filedir,primaryFilename))
                        filetimestamp = time.localtime( os.path.getmtime(os.path.join(filedir,primaryFilename)) )
                        primaryFileTime = time.strftime('%Y-%m-%d %H:%M:%S',filetimestamp)
                        jsSourceFileInfo["filesize"] = str(primaryFileSize)
                        jsSourceFileInfo["filetime"] = primaryFileTime
                        if jsSourceFileInfo.has_key("file") :
                            jsSourceFileInfo["file"] = parentDirName +'/' + jsSourceFileInfo["file"]                        
                    except:          
                        PLOG.info("generate file info of dir %s failed,primary File %s not find,skip it"% (filedir,primaryFilename))      
                        return 
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
    allJsonInfo = {}
    allJsonInfo["update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allJsonInfo["source"] = conf.httpServerSite + rootDirname + '/'
    allJsonInfo["list"] =[]	
    
    if filetype == "movie":
        outputjsfilename = conf.movieOutputFile
    elif filetype == "android":
        outputjsfilename = conf.androidOutputFile
    elif filetype == "ios":
        outputjsfilename = conf.iosOutputFile
        
    outputjsfilename = outputjsfilename.decode('utf8')
    rootpath = rootpath.decode('utf8')
    dirlist = enumDir(rootpath)
	    
    for subdir in dirlist:
        fileitems = enumFile(os.path.join(rootpath,subdir))
        for fileitem in fileitems:
            if fileitem[-5:] == ".json" : 	    
                addJsonInfo(fileitem,allJsonInfo)
    with open(outputjsfilename,"w") as f:
        json.dump(allJsonInfo, f,indent=4,ensure_ascii=False)
    PLOG.debug('Type["%s"] file crawl dir %s finished' %(filetype,rootpath))	

def run():
    init()  
    if conf.httpServerSite[-1] != '/' : conf.httpServerSite += '/'
      
    # 爬取文件,生成最终json文件 start	
    if len(conf.movieDir) != 0 :
        scanFile(conf.movieDir,"movie")
    else:
        PLOG.warn("moviedir is empty,please check config file")
    if len(conf.androidDir) != 0 :
        scanFile(conf.androidDir,"android")
    else:
        PLOG.warn("androiddir is empty,please check config file")   
    if len(conf.iosDir) != 0 :
        scanFile(conf.iosDir,"ios")
    else:
        PLOG.warn("iosdir is empty,please check config file")        
    
    # 爬取文件,生成最终json文件 end

def init():    
    configfile=assistant.SF("%s/filecrawler.conf"%(os.path.dirname(__file__)))
    print os.path.dirname(__file__)
    config=pysmartac.configer.openconfiger(configfile)

    #configer
    conf.logLevel=config.getstr("system","logLevel",conf.logLevel)
    conf.httpServerSite=config.getstr("system","httpserversite",conf.httpServerSite)
    conf.movieDir=config.getstr("system","movieDir",conf.movieDir)
    conf.iosDir=config.getstr("system","iosDir",conf.iosDir)
    conf.androidDir=config.getstr("system","androidDir",conf.androidDir)
    conf.movieOutputFile=config.getstr("system","movieOutputFile",conf.movieOutputFile)
    conf.iosOutputFile=config.getstr("system","iosOutputFile",conf.iosOutputFile) 
    conf.androidOutputFile=config.getstr("system","androidOutputFile",conf.androidOutputFile) 
    config.save()
    #log settings
    PLOG.setlevel(conf.logLevel)
    PLOG.enableFilelog("%s/log/FLCRAWLER_$(Date8)_$(filenumber2).log"%(os.path.dirname(__file__)))

if __name__ == "__main__":
    run()

