#!/usr/bin/python
# -*- coding: utf-8 -*-
import os, sys, inspect
import datetime
import signal

# function: get directory of current script, if script is built
#   into an executable file, get directory of the excutable file
def current_file_directory():
    path = os.path.realpath(sys.path[0])        # interpreter starter's path
    if os.path.isfile(path):                    # starter is excutable file
        path = os.path.dirname(path)
        path = os.path.abspath(path)            # return excutable file's directory
    else:                                       # starter is python script
        caller_file = inspect.stack()[0][1]     # function caller's filename
        path = os.path.abspath(os.path.dirname(caller_file))# return function caller's file's directory
    if path[-1]!=os.path.sep:path+=os.path.sep
    return path

"""格式化字符串"""
def formatString(string,*argv):
    string=string%argv
    if string.find('$(scriptpath)')>=0:
        string=string.replace('$(scriptpath)',current_file_directory())
    if string.find('$(filenumber2)')>=0:
        i=0
        path=""
        while True:
            path=string.replace('$(scriptpath)',"%02d"%i)
            if not os.path.lexists(path):break
            i+=1
        string=path
    #8位日期（20140404）
    if string.find('$(Date8)')>=0:
        now=datetime.datetime.now()
        string=string.replace('$(Date8)', now.strftime("%Y%m%d"))
    #文件编号2位（必须在最后）
    if string.find('$(filenumber2)')>=0:
        i=0
        path=""
        while True:
            path=string.replace('$(filenumber2)',"%02d"%i)
            if not os.path.lexists(path):break
            i+=1
        string=path
    #文件编号3位（必须在最后）
    if string.find('$(filenumber3)')>=0:
        i=0
        path=""
        while True:
            path=string.replace('$(filenumber3)',"%03d"%i)
            if not os.path.lexists(path):break
            i+=1
        string=path
    return string
  
"""
    取得进程列表
    格式：(PID,cmd)
""" 
def getProcessList():
    processList = []
    try:
        for line in os.popen("ps xa"):
            fields = line.split()
            # spid = fields[0]
            pid = 0
            try:pid = int(fields[0])
            except:None
            cmd = line[27:-1]
            # print "PS:%d,%s"%(npid,process)
            if pid != 0 and len(cmd) > 0:
                processList.append((pid, cmd))
    except Exception, e:
        print("getProcessList except:%s" % (e))
    return processList
def killCommand(cmd):
    try:
        processList = getProcessList()
        for p in processList:
            if p[1].find(cmd) != -1:
                pid = p[0]
                os.kill(pid, signal.SIGKILL)
    except Exception, e:
        print("killCommand ‘%s’ except:%s" % (cmd,e))

def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    if pid == 0:return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True
    
SF=formatString