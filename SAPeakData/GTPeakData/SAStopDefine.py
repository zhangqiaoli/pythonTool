#coding=utf8
import os;
import threading;
import datetime;
import SAPeakDataPublic;
import MySQLdb;
from pysmartac.log import PLOG;

dayarraylength=24*60

class StopDC(object):
    def __init__(self):
        self.objectName="stopDC"
        self.stops={}
    def reloadStop(self):
        querystopsql = 'SELECT a.innerid,a.`name` FROM sa_region AS a LEFT JOIN sa_region AS b ON b.parentid=a.innerid WHERE b.parentid IS NULL'
        stopresultls = SAPeakDataPublic.querysql(querystopsql)
        if stopresultls!=None and len(stopresultls)>0:
            for row in stopresultls:
                stop = Stop(row[0],row[1])
                if stop != None:
                    self.stops[row[0]] = stop
                    PLOG.debug("load stop %s,id=%s"%(row[1],row[0]))
        else:
            PLOG.debug("load stop failed!")
            return False         
        return True  
#全局对象
stopDc=StopDC()

class Stop():
    def __init__(self,guid,name):
        # 数组保持一天24小时每分钟的数据,每个元素为一个数组,(在线人数,带宽)
        self.dayArray=[]
        self.name=name
        self.guid=guid
        self.peakonlinenum=0
        self.peakbandwidth=0
        self.peakonlinetime=datetime.datetime.now()
        self.peakbandwidthtime=datetime.datetime.now()
    def resetdata(self):
        if len(self.dayArray)>0:
            self.dayArray=[]
        for i in range(dayarraylength):
            peakdata=[]
            for j in range(2):
                peakdata.append(0)
            self.dayArray.append(peakdata)
        self.peakbandwidth=0
        self.peakonlinenum=0