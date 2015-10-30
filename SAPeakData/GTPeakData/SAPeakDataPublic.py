#coding=utf8
import datetime
import time
from pysmartac.log import PLOG
import MySQLdb
import DBHelper
from DBHelper import DBOperater 
class CONF:
    None
#实时统计间隔
st=CONF()
#数据查询最小粒度(单位为小时,仅支持1,2,3,4,6,8,12,24)
st.queryunit=24
st.loglevel=24
st.queryrepeattimes=3

#SA DB连接信息
sadb=CONF()
sadb.host="172.16.2.76"
sadb.dbname="saradius"
sadb.tablename="sa_acct_local"
sadb.dbuser="develop"
sadb.dbpwd="develop"

def openmysqlconn():
    dboperater =None
    try:
        dboperater = DBOperater()
        dboperater.createconnection(host=sadb.host,user=sadb.dbuser,passwd=sadb.dbpwd,dbname=sadb.dbname)
    except MySQLdb.Error,e:
        PLOG.debug("Mysql Error %d: %s" %(e.args[0], e.args[1]))   
    return dboperater

def closemysqlconn(dboperater):
    if dboperater!=None and isinstance(dboperater,DBOperater):
        try:
            dboperater.closeconnection()
        except MySQLdb.Error,e:
            PLOG.debug("Mysql Error %d: %s" %(e.args[0], e.args[1]))   

def executearrsql(sqltext,dboperater=None,arrsql=None,sqlnum=100,mode = DBHelper.CURSOR_MODE):
    try:
        if dboperater == None:
            dboperater = DBOperater()
        if dboperater.conn == None:
            dboperater.createconnection(host=sadb.host,user=sadb.dbuser,passwd=sadb.dbpwd,dbname=sadb.dbname) #数据库连接
        if arrsql!=None and len(arrsql)>0:
            totalnum = len(arrsql)
            if totalnum%sqlnum == 0:
                foocount = totalnum/sqlnum
            else:
                foocount = totalnum/sqlnum+1
            i = 0
            while i<foocount:
                arr = arrsql[i*sqlnum:(i+1)*sqlnum]
                dboperater.execute(sqltext,args=arr,mode=mode,many=True)#执行SQL语句
                dboperater.conn.commit() #提交SQL语句
                i+=1  
        else:
            # 执行单条sql语句
            dboperater.execute(sqltext,mode=mode)
            dboperater.conn.commit()
    except MySQLdb.Error,e:
        PLOG.debug("Mysql Error %d: %s,sql=%s" %(e.args[0], e.args[1],sqltext))  

def querysql(sqltext,dboperater=None,how = 0):
    resultls = []
    try:
        if dboperater == None:
            dboperater = DBOperater()
        if dboperater.conn == None:
            dboperater.createconnection(host=sadb.host,user=sadb.dbuser,passwd=sadb.dbpwd,dbname=sadb.dbname) #数据库连接
        rowNum, result = dboperater.query(sqltext)
        PLOG.trace("%s query finish"%(sqltext))
        resultls = dboperater.fetch_queryresult(result,rowNum, how = how) 
    except MySQLdb.Error,e:
        PLOG.debug("Mysql Error %d: %s,sql=%s" %(e.args[0], e.args[1],sqltext)) 
        return None
    PLOG.trace("%s query return"%(sqltext))
    return resultls

def executeproc(procsqlname,dboperater=None,args=None):
    resultls = []
    try:
        if dboperater == None:
            dboperater = DBOperater()
        if dboperater.conn == None:
            dboperater.createconnection(host=sadb.host,user=sadb.dbuser,passwd=sadb.dbpwd,dbname=sadb.dbname) #数据库连接
        cur = dboperater.conn.cursor()
        cur.callproc(procsqlname,args)
        dboperater.conn.commit() #提交SQL语句
        cur.close()
    except MySQLdb.Error,e:
        PLOG.debug("Mysql Error %d: %s,sql=%s" %(e.args[0], e.args[1],procsqlname)) 