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
from ftplib import FTP
import re
import uuid

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

class CONF:
    pidfile="/tmp/filecrawler.py.pid"
    threadCount=1
    ftpServerMovieSource="ftp://172.16.3.130/YCommon/"
    ftpServerAppSource="ftp://172.16.3.130/YCommon/"
    ftpJsonOutputPath="ftp://172.16.3.130/YCommon/"
    ftpServerUser="zhangqiaoli"
    ftpServerPwd="churencai"
    movieOutputFile="movies.json"
    appOutputFile="apps.json"
    # 单位分钟
    checkInterval=1
    logLevel='D'
conf=CONF() 

class FtpHandler(FTP):  
    def __init__(self,host,user,pwd):
        self.host = host
        self.user = user
        self.pwd = pwd
        #self.worddir = worddir
        # 文件目录map
        #self.fileDir = []
        self.filePattern=re.compile('Type=(?P<type>\w+);Size=(?P<size>\d+);Modify=(?P<modify>\d+.?\d+);\s(?P<filename>.*)')
    def scanFtpServerFiles(self,root,filetype):
        PLOG.debug('Type["%s"] file start crawling...ftpserver = %s ,dir = %s ' %(filetype,self.host,root))
        outputjsfilename = ""
        filesource = ""
        if filetype == "movie":
            outputjsfilename = conf.movieOutputFile
            filesource = conf.ftpServerMovieSource
        elif filetype == "app":
            outputjsfilename = conf.appOutputFile
            filesource = conf.ftpServerAppSource
        # 枚举工作目录下的所有目录
        fileDir = self.listdir(root)
        # 所有电影 or APP信息json串
        allJsonInfo = {}
        allJsonInfo["update"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        allJsonInfo["source"] = filesource
        allJsonInfo["list"] =[]
        for filedir in fileDir :
            PLOG.debug('start generate file info of dir "%s"...'%(root+filedir))
            fileItems = self.listFile(root+filedir)
            primaryFilename = ""
            primaryFileSize = ""
            primaryFileTime = ""
            jsFileInfo = None
            for fileitem in  fileItems:
                if fileitem[-5:] == ".json" :                     
                    fileinfo = []
                    if fileitem.find("/") == -1 : fileitem = root+filedir+'/'+fileitem
                    try:  
                        self.retrlines("RETR %s"%fileitem,fileinfo.append)  
                    except:    
                        PLOG.warn('retr %s except! skip it !' %fileitem)
                    filedetailinfo = ""
                    for linestr in fileinfo:
                        filedetailinfo += linestr
                    if filedetailinfo != "":
                        try:
                            filedetailinfo = filedetailinfo.decode("gbk")
                        except:
                            pass
                        try:
                            filedetailinfo = filedetailinfo.decode("gb2312")
                        except:
                            pass			
                            #PLOG.debug("decode failed! %s is not encoded by gbk")
                        jsFileInfo = json.loads(filedetailinfo,'utf8')
                    if jsFileInfo !=None :
                        if jsFileInfo.has_key("file"):
                            primaryFilename = jsFileInfo["file"]  
                        else :
                            PLOG.debug('not find "file" node in info file %s , skip it' %(fileitem))
                    else:
                        PLOG.error('js file %s is null,maybe path error! skip it' %(fileitem))
                    break
            if jsFileInfo != None and jsFileInfo != "" :
                if primaryFilename != "" :
                    try:  		
                        timestamp = []
                        self.retrlines("LIST %s"%root+filedir+'/'+primaryFilename,lambda x:timestamp.append(self.separateFileTime(x))) 
                        primaryFileSize = self.size(root+filedir+'/'+primaryFilename)
                        primaryFileTime = timestamp.pop()
                        jsFileInfo["filesize"] = primaryFileSize
                        jsFileInfo["filetime"] = primaryFileTime
                        jsFileInfo["id"] = str(uuid.uuid1())
                        filerelativedir = filedir + '/'
                        if jsFileInfo.has_key("file") :
                            jsFileInfo["file"] = filerelativedir +jsFileInfo["file"]
                        if jsFileInfo.has_key("poster") :
                            jsFileInfo["poster"] = filerelativedir +jsFileInfo["poster"]
                        if jsFileInfo.has_key("thumbnail") :
                            jsFileInfo["thumbnail"] = filerelativedir +jsFileInfo["thumbnail"]
                        if jsFileInfo.has_key("extend") :
                            jsextend = jsFileInfo["extend"]
                            if jsextend.has_key("screenshot") :
                                jsscreenshottmp = []
                                for picture in jsextend["screenshot"] :
                                    picture = filerelativedir + picture
                                    jsscreenshottmp.append(picture)
                                jsextend["screenshot"] =jsscreenshottmp
                        allJsonInfo["list"].append(jsFileInfo)
                        PLOG.debug('generate file info of dir "%s" success'%(root+filedir))
                    except:   
                        PLOG.warn('retr %s except! skip it !' %(root+filedir+'/'+primaryFilename))
                        PLOG.debug("generate file info of dir %s failed,not find primary File %s" % (root+filedir,primaryFilename))
                else:
                    PLOG.debug("generate file info of dir %s failed,primary File name is empty"% (root+filedir))
            else:
                PLOG.debug("generate file info of dir %s failed,not find js info file"% (root+filedir))              
        if(outputjsfilename == ""):
            PLOG.debug("unkown file type!")
            return 0

        with open(outputjsfilename, "w") as f:
            json.dump(allJsonInfo, f,indent=4,ensure_ascii=False)   
        # 将json文件传到ftpserver
        ttt = len(outputjsfilename)
        with open(outputjsfilename,"r") as f:
            try:  
                outputdirtmp=conf.ftpJsonOutputPath.replace("ftp://","")
                outputdir = outputdirtmp[outputdirtmp.find("/")+1:]		
                self.storlines("STOR %s"%outputdir+outputjsfilename,f)  
                PLOG.debug('upload json file %s success !'%outputjsfilename)
            except:    
                PLOG.warn('upload json file %s failed,exception !'%outputjsfilename)
        PLOG.debug('Type["%s"] file crawl dir %s finished' %(filetype,root))

    def login(self):  
        try:  
            FTP.connect(self,self.host,timeout=10)  
        except:  
            PLOG.warn('Can not connect to ftp server "%s"' % self.host) 
            return False  
        try:  
            FTP.login(self,self.user,self.pwd)  
        except:  
            PLOG.warn('Login ftp server "%s" failed ,username or password error' % self.host)
            return False  
        return True  

    def listFile(self,path): 
        fileitems = []
        fileitems = self.nlst(path)
        return fileitems

    def separateFileTime(self,line):
        pattern=re.compile(".{10}\s+\d+\s+\d+\s+\d+\s+\d+\s+(?P<mon>\w{3})\s+(?P<day>\d{2})\s+(?P<time>\d{2}:?\d{2})\s+.*")
        m=pattern.search(line)
        month = 1
        day = 1
        hour = 0
        minute = 0
        if m != None :
            if   cmp( m.group('mon'),'Jan') == 0 : month = 1
            elif cmp( m.group('mon'),'Feb') == 0 : month = 2
            elif cmp( m.group('mon'),'Mar') == 0 : month = 3
            elif cmp( m.group('mon'),'Apr') == 0 : month = 4
            elif cmp( m.group('mon'),'May') == 0 : month = 5
            elif cmp( m.group('mon'),'Jun') == 0 : month = 6
            elif cmp( m.group('mon'),'Jul') == 0 : month = 7
            elif cmp( m.group('mon'),'Aug') == 0 : month = 8
            elif cmp( m.group('mon'),'Sep') == 0 : month = 9
            elif cmp( m.group('mon'),'Oct') == 0 : month = 10
            elif cmp( m.group('mon'),'Nov') == 0 : month = 11
            elif cmp( m.group('mon'),'Dec') == 0 : month = 12
            day = int(m.group('day'))  
            if m.group('time').find(':') != -1 :
                timedetail = m.group('time')
                hour = int(timedetail[:timedetail.find(":")])
                minute = int(timedetail[timedetail.find(":")+1:])
        time = datetime.datetime(datetime.datetime.now().year,month,day,hour,minute)
        timestampstr = time.strftime("%Y-%m-%d %H:%M:%S")
        return timestampstr

    def listdir(self,root):  
        def setDirList(line,dirlist):
            #筛除文件,只留目录
            if(line[0] == 'd'):
                tmp = line.split(' ')
                dirname = tmp[-1]
                dirname = dirname.strip()
                if dirname != "." and dirname != ".." :    
                    dirlist.append(dirname)
        dirList = []	
        self.dir(root,lambda x:setDirList(x,dirList))   
        return dirList            

class filecrawlerDaemon(daemon):
    #def crawlFile(self):      
    def run(self):
        init()   
        nowTime = datetime.datetime.now()
        secondWaitTime=0
        ftpServerMTmp=conf.ftpServerMovieSource.replace("ftp://","")
        ftpServerHost = ftpServerMTmp[:ftpServerMTmp.find("/")]
        ftpServerMovieDir = ftpServerMTmp[ftpServerMTmp.find("/")+1:]
        ftpServerATmp=conf.ftpServerAppSource.replace("ftp://","")
        ftpServerHost = ftpServerATmp[:ftpServerATmp.find("/")]
        ftpServerAppDir = ftpServerATmp[ftpServerATmp.find("/")+1:]
        if not ftpServerMovieDir.endswith("/") : ftpServerMovieDir += "/"
        if not ftpServerAppDir.endswith("/") : ftpServerAppDir += "/"
        while 1:
            time.sleep(secondWaitTime)        
            # 爬取文件,生成最终json文件 start
            # ftpHandler处理对象
            ftphandler = FtpHandler(ftpServerHost,conf.ftpServerUser,conf.ftpServerPwd)
            # 连接ftp server
            ret = ftphandler.login()
            if not ret :
                continue
            # 连接ftp server success,开始爬取
            # Movie          
            ftphandler.scanFtpServerFiles(ftpServerMovieDir,"movie")
            # App
            ftphandler.scanFtpServerFiles(ftpServerAppDir,"app")
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
    conf.ftpServerMovieSource=config.getstr("system","ftpServerMovieSource",conf.ftpServerMovieSource)
    conf.ftpServerAppSource=config.getstr("system","ftpServerAppSource",conf.ftpServerAppSource)
    conf.ftpServerUser=config.getstr("system","ftpServerUser",conf.ftpServerUser)
    conf.ftpServerPwd=config.getstr("system","ftpServerPwd",conf.ftpServerPwd)
    conf.ftpJsonOutputPath=config.getstr("system","ftpJsonOutputPath",conf.ftpJsonOutputPath)
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

