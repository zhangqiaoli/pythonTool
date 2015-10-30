#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys,os
import io
import json
import re
import ConfigParser
import pysmartac
import pysmartac.configer
import pysmartac.assistant as assistant
from pysmartac.log import PLOG
import SAPeakDataPublic
import SAStopDefine
import MySQLdb
import datetime
import time
from DBHelper import DBOperater

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

startdate=datetime.datetime.strptime(datetime.datetime.now().strftime("%Y%m%d"), '%Y%m%d')-datetime.timedelta(days=1)
enddate=datetime.datetime.strptime( (datetime.datetime.now()).strftime("%Y%m%d"), '%Y%m%d')
        
def loadconfig():
    config = ConfigParser.ConfigParser()
    configfile = assistant.SF("%s/SAPeakData.conf" % (os.path.dirname(__file__)))

    PLOG.info("Load configer file:%s" % configfile)
    config.readfp(open(configfile, "rb"))
    SAPeakDataPublic.st.loglevel = config.get("system", "loglevel")
    SAPeakDataPublic.st.queryunit = config.getint("system", "queryunit")
    SAPeakDataPublic.st.queryrepeattimes = config.getint("system", "queryrepeattimes")
    if 24%SAPeakDataPublic.st.queryunit != 0:
        PLOG.debug("queryunit is invalid,please check config!")
        sys.exit(2)
    SAPeakDataPublic.sadb.host = config.get("system", "datasource")
    SAPeakDataPublic.sadb.dbuser = config.get("system", "dbuser") 
    SAPeakDataPublic.sadb.dbpwd = config.get("system", "dbpwd")
    SAPeakDataPublic.sadb.dbname = config.get("system", "dbname")  
    SAPeakDataPublic.sadb.tablename = config.get("system", "tablename") 

def statisticsCurrentDayData(daydate) :
    nextday = daydate+datetime.timedelta(days=1)
    startquerytime = daydate
    endquerytime = daydate+datetime.timedelta(hours=SAPeakDataPublic.st.queryunit)
    while endquerytime<=nextday:
        acctquerysql = "select acctinputoctets,acctoutputoctets,acctstarttime,acctstoptime,regionid from %s where acctstarttime>='%s' and acctstarttime<'%s'"%\
                   (SAPeakDataPublic.sadb.tablename,startquerytime.strftime('%Y-%m-%d %H:%M:%S'),endquerytime.strftime('%Y-%m-%d %H:%M:%S')) 
        PLOG.debug("sql=%s"%acctquerysql)
        startquerytime=endquerytime
        endquerytime=endquerytime+datetime.timedelta(hours=SAPeakDataPublic.st.queryunit)
        i = 0
        while i<SAPeakDataPublic.st.queryrepeattimes:            
            res = SAPeakDataPublic.querysql(acctquerysql)
            if res!=None:
                break
            else:
                i = i+1
        if i==3 or res==None:
            print("%s statistics data failed! db query appear error %d consecutive times,please execute again later!"%(daydate.strftime('%Y-%m-%d'),SAPeakDataPublic.st.queryrepeattimes))
            PLOG.info("%s statistics data failed! db query appear error %d consecutive times,please execute again later!"%(daydate.strftime('%Y-%m-%d'),SAPeakDataPublic.st.queryrepeattimes))
            return
        # 统计数据
        PLOG.trace("start statistics...")
        for row in res:
            if row[2] ==None or row[3] ==None or row[4] ==None:
                PLOG.warn("lack essential data!skip this data")
                continue          
            regionid = row[4]
            totalflow = 0
            if row[0]!=None:
                totalflow += row[0]
            if row[1]!=None:
                totalflow += row[1]
            if row[3].day > row[2].day:
                # 跨天
                endMinute = 23*60+59
            elif row[3].day < row[2].day:
                PLOG.info("stoptime day less than starttime day,invalid data,skip")
            else:
                endMinute = row[3].hour*60+row[3].minute 
            startMinute = row[2].hour*60+row[2].minute       
            #startMinute = datetime.datetime.strptime(row[2],'%Y-%m-%d %H:%M:%S')
            #endMinute = datetime.datetime.strptime(row[3],'%Y-%m-%d %H:%M:%S')
            totalMinute = endMinute-startMinute + 1
            if totalMinute <=0:
                PLOG.info("stoptime less than starttime,invalid data,skip")
                continue 
            if SAStopDefine.stopDc.stops.has_key(regionid):
                stop = SAStopDefine.stopDc.stops[regionid] 
                startindex = startMinute
                endindex = endMinute
                flowOneMinute = float(totalflow)/totalMinute/1024/1024
                index = startindex
                while index <= endindex:
                    stop.dayArray[index][0] += 1
                    stop.dayArray[index][1] += flowOneMinute
                    if stop.dayArray[index][0] > stop.peakonlinenum: 
                        stop.peakonlinenum = stop.dayArray[index][0]
                        stop.peakonlinetime = datetime.datetime(daydate.year,daydate.month,daydate.day,index/60,index%60)
                    if stop.dayArray[index][0] > stop.peakbandwidth:
                        stop.peakbandwidth = stop.dayArray[index][1]
                        stop.peakbandwidthtime = datetime.datetime(daydate.year,daydate.month,daydate.day,index/60,index%60)
                    index += 1
        PLOG.trace("statistics end")
    # 数据处理结束,输出各站点峰值数据
    for stopid,stop in stopsCentor.stops.items():
        peakbandwidth = stop.peakbandwidth*8/60
        print("%s %s %d %.2f"%(daydate.strftime('%Y-%m-%d'),stop.name,stop.peakonlinenum,peakbandwidth))
        PLOG.debug("%s %s %d %.2f %s %s"%(daydate.strftime('%Y-%m-%d'),stop.name,stop.peakonlinenum,peakbandwidth,stop.peakonlinetime.strftime('%H:%M'),stop.peakbandwidthtime.strftime('%H:%M')))
        
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print ("没有输入起始和结束统计时间,默认只统计昨天数据,想要统计特定日期内的数据,请输入起始和结束时间(包含起始日期和结束日期),例如:20150210 20150224")
    elif len(sys.argv)>=2 and len(sys.argv)<3:
        print ("没有结束统计时间,默认统计至今天(包括今天),想要统计特定日期内的数据,请输入起始和结束时间(包含起始日期和结束日期),例如:20150210 20150224")
        startdate=datetime.datetime.strptime(sys.argv[1], '%Y%m%d')
        enddate=enddate+datetime.timedelta(days=1)
    else:
        try:           
            startdate=datetime.datetime.strptime(sys.argv[1], '%Y%m%d')
            enddate=datetime.datetime.strptime(sys.argv[2], '%Y%m%d')+datetime.timedelta(days=1)
        except:
            print ("输入时间参数解析失败,参数格式不对,例:20150210")
            sys.exit(1)  
    PLOG.enableControllog(False)
    PLOG.enableFilelog("%s/log/SARPT_$(Date8)_$(filenumber2).log"%(os.path.dirname(__file__)))
    loadconfig()
    PLOG.setlevel(SAPeakDataPublic.st.loglevel)
    # 加载基础数据,建立区域关系
    stopsCentor=SAStopDefine.stopDc
    if not stopsCentor.reloadStop():
        PLOG.error("加载站点基础数据失败!")
        sys.exit(1) 
    while startdate<enddate:
        # 站点天数组数据重置
        for stopid,stop in stopsCentor.stops.items():
            stop.resetdata()
        # 统计startdate当天数据
        statisticsCurrentDayData(startdate)
        startdate = startdate + datetime.timedelta(days=1)
      
    



