#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys,os
import logging
import datetime
import thread
import assistant
"""
%a Locale’s abbreviated weekday name.   
%A Locale’s full weekday name.   
%b Locale’s abbreviated month name.   
%B Locale’s full month name.   
%c Locale’s appropriate date and time representation.   
%d Day of the month as a decimal number [01,31].   
%H Hour (24-hour clock) as a decimal number [00,23].   
%I Hour (12-hour clock) as a decimal number [01,12].   
%j Day of the year as a decimal number [001,366].   
%m Month as a decimal number [01,12].   
%M Minute as a decimal number [00,59].   
%p Locale’s equivalent of either AM or PM. (1) 
%S Second as a decimal number [00,61]. (2) 
%U Week number of the year (Sunday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Sunday are considered to be in week 0. (3) 
%w Weekday as a decimal number [0(Sunday),6].   
%W Week number of the year (Monday as the first day of the week) as a decimal number [00,53]. All days in a new year preceding the first Monday are considered to be in week 0. (3) 
%x Locale’s appropriate date representation.   
%X Locale’s appropriate time representation.   
%y Year without century as a decimal number [00,99].   
%Y Year with century as a decimal number.   
%Z Time zone name (no characters if no time zone exists).   
%% A literal '%' character. 

"""
TRACE='T'
DEBUG='D'
INFORMATION='I'
WARNING='W'
ERROR='E'
NONE='N'

def convLevel(level):
    logLevel=logging.NOTSET
    if level==NONE:
        logLevel=logging.NOTSET
    elif level==TRACE or level==DEBUG:
        logLevel=logging.DEBUG
    elif level==INFORMATION:
        logLevel=logging.INFO
    elif level==WARNING:
        logLevel=logging.WARNING
    elif level==ERROR:
        logLevel=logging.ERROR
    else:
        logLevel=logging.NOTSET
    return logLevel

logging.addLevelName(logging.DEBUG, "D")
#logging.addLevelName(logging.DEBUG, "D")
#logging.addLevelName(logging.DEBUG, "D")
#logging.addLevelName(logging.DEBUG, "D")
class salog:
    def __init__(self,name=None):
        self._obj=logging.getLogger(name)
        self._formater=logging.Formatter("%(message)s")
        self.setlevel(DEBUG)
        self._handle_control=None
        self._handle_file=None
    def setlevel(self,level):
        self._obj.setLevel(convLevel(level))
        #logging.debug(msg)
    def enableControllog(self,enable):
        if enable:
            if not self._handle_control:
                self._handle_control=logging.StreamHandler()
                self._handle_control.setFormatter(self._formater)
                self._obj.addHandler(self._handle_control)
        else:
            if self._handle_control:
                self._obj.removeHandler(self._handle_control)
                del self._handle_control
                self._handle_control=None
    def enableFilelog(self,filename):
        if len(filename)>0:
            if self._handle_file:
                self._obj.removeHandler(self._handle_file)
            self._filetemple=filename
            realfilename=assistant.SF(filename)
            if not os.path.exists(os.path.dirname(realfilename)):
                os.makedirs(os.path.dirname(realfilename), mode=0777)
            self._handle_file=logging.FileHandler(realfilename,encoding='utf-8')
            self._handle_file.setFormatter(self._formater)
            self._handle_file.day=datetime.datetime.now().day
            self._obj.addHandler(self._handle_file)
        else:
            if self._handle_file:
                self._obj.removeHandler(self._handle_file)
            self._filetemple=""
    def _output(self,level,msg):
        now=datetime.datetime.now()
        if self._handle_file and self._handle_file.day!=now.day:
            self.enableFilelog(self._filetemple)
        s="[%s] %04d-%02d-%02d %02d:%02d:%02d.%03d (0x%04X):%s"%(level,now.year,now.month,now.day,now.hour,now.minute,now.second,now.microsecond/1000,thread.get_ident()&0xffff,msg)
        fn=logging.NOTSET
        if level==NONE:
            fn=None
        elif level==TRACE or level==DEBUG:
            fn=self._obj.debug
        elif level==INFORMATION:
            fn=self._obj.info
        elif level==WARNING:
            fn=self._obj.warn
        elif level==ERROR:
            fn=self._obj.error
        else:
            fn=self._obj.critical
        
        if fn!=None:fn(s)
    def trace(self,msg):
        self._output(TRACE,msg)
    def debug(self,msg):
        self._output(DEBUG, msg)
    def info(self,msg):
        self._output(INFORMATION, msg)
    def warn(self,msg):
        self._output(WARNING, msg)
    def error(self,msg):
        self._output(ERROR, msg)
    def log(self,level,msg):
        self._output(level, msg)
PLOG=salog()

PLOG.enableControllog(True)


