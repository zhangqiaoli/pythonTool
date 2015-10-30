#!/usr/bin/python
#coding: UTF-8
import pika
import MySQLdb
import ConfigParser
import sys
import time
import os
import logging
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
reload(sys)
sys.setdefaultencoding("utf-8")
# 配置文件信息
# 数据源
DATASOURCE = "localhost"
# 数据库用户名
DBUSER = "root"
# 数据库用户密码
DBPWD = "1234"
# 数据库名称
DBNAME = "zqltest"
# MQURL
MQURL = "192.168.99.46"
# Exchange名称
EXCHANGE = "sc.loc.newworld"
# Queue名称
QUEUE = "NewWorld_CRM_Queue"
# TenantID 固定
TENANTID = 1
# ShopID 固定
SHOPID = ''

procSql = """DROP PROCEDURE IF EXISTS CUSTOMER_WORK;
CREATE PROCEDURE CUSTOMER_WORK(in Tenant int,in Shop varchar(50),in Mac bigint,in Tel varchar(20),in IsVip smallint,in CustName varchar(50),in Sex int,in VipCode varchar(50),in VipId varchar(50))
BEGIN
DECLARE custId varchar(50);
DECLARE nowTime datetime;
SET nowTime = NOW();
SELECT CustMac_uni_CustID INTO custId FROM tbCust_CustMac WHERE CustMac_int_CustRadMacId = Mac;

if ISNULL(custId) THEN
	set @custId=UUID();
        insert INTO tbCust_Customer (InnerID,TenantID,Cust_uni_ShopID,Cust_var_Mobile,Cust_var_Name,Cust_slt_IsVIP,Cust_int_SexCode,Cust_var_CardNo,Cust_var_IDNumber,Cust_slt_IsDeleted,CreatedOn)values(@custId,Tenant,Shop,Tel,CustName,IsVip,Sex,VipCode,VipId,0,nowTime);
				insert INTO tbCust_CustMac(InnerID,TenantID,CustMac_int_Type,CustMac_int_CustRadMacId,CustMac_int_LoginName,CustMac_uni_CustID,CustMac_int_IsDelete,CreateOn)values(UUID(),Tenant,0,Mac,Tel,@custId,0,nowTime);
ELSE
	update tbCust_CustMac set CustMac_int_LoginName=Tel,ModifiedOn=nowTime where CustMac_int_CustRadMacId = Mac;
	update tbCust_Customer set Cust_var_Mobile=Tel,Cust_var_Name=CustName,Cust_slt_IsVIP=IsVip,Cust_int_SexCode=Sex,Cust_var_CardNo=VipCode,Cust_var_IDNumber=VipId,ModifiedOn=nowTime where InnerID=custId;
END IF; 
END"""

# 全局变量定义
logger = None
db = None
connection = None
channel = None  
# 全局变量定义 end

def LoadConfig():   
    global DATASOURCE
    global DBUSER
    global DBPWD
    global DBNAME
    global MQURL
    global EXCHANGE
    global QUEUE
    global TENANTID
    global SHOPID
    if not os.path.exists('NewWorld.ini'):
        writeConfig()
    else:
        config=ConfigParser.ConfigParser()  
        try:
            with open('NewWorld.ini','r') as cfgfile:
                config.readfp(cfgfile)    
        except IOError,e:
            logger.debug("Config file read failed! %d : %s! Program exit..." ,e.args[0], e.args[1])
            sys.exit(1)
        else:   
            if not config.has_section('system'):
                config.add_section('system')
            else:
                if config.has_option('system','datasource'):        
                    DATASOURCE=config.get('system','datasource')
                    logger.debug("Load datasource = %s",DATASOURCE)
                if config.has_option('system','dbuser'):
                    DBUSER=config.get('system','dbuser')
                    logger.debug("Load dbuser = %s" ,DBUSER)
                if config.has_option('system','dbpwd'):
                    DBPWD=config.get('system','dbpwd')
                    logger.debug("Load dbpwd = %s" ,DBPWD)
                if config.has_option('system','dbname'):
                    DBNAME=config.get('system','dbname')
                    logger.debug("Load dbname = %s",DBNAME)
                if config.has_option('system','mqurl'):
                    MQURL=config.get('system','mqurl')
                    logger.debug("Load mqurl = %s",MQURL )
                if config.has_option('system','exchange'):
                    EXCHANGE=config.get('system','exchange')
                    logger.debug("Load exchange = %s" ,EXCHANGE )
                if config.has_option('system','queue'):
                    QUEUE=config.get('system','queue')
                    logger.debug("Load queue = %s" ,QUEUE)
                if config.has_option('system','tenantid'):
                    TENANTID=config.get('system','tenantid')
                    logger.debug("Load tenantid = %s" ,TENANTID) 
                if config.has_option('system','shopid'):
                    SHOPID=config.get('system','shopid')
                    logger.debug("Load queue = %s" ,SHOPID)                
            # 写回配置文件
            writeConfig()
            # 写回配置文件 End          
    
# 写配置文件
def writeConfig():
    config=ConfigParser.ConfigParser()
    config.add_section('system')
    config.set('system','datasource', DATASOURCE) 
    config.set('system','dbuser',DBUSER)
    config.set('system','dbpwd',DBPWD)
    config.set('system','dbname',DBNAME)
    config.set('system','mqurl',MQURL)
    config.set('system','exchange',EXCHANGE) 
    config.set('system','queue',QUEUE)  
    config.set('system','tenantid',TENANTID)
    config.set('system','shopid',SHOPID)
    with open('NewWorld.ini','w+') as cfgfile:
        config.write (cfgfile)    
        
def processMQMsg(body):
    # 获取数据  MAC UserID vipcode surname vipid telephone
    root = ET.fromstring(body)   
    mac = root.attrib['Mac']
    userid = root.attrib['UserID']
    isVip = root.attrib['IsVip']
    vip = None
    if isVip == '1':
        vip = root.find('VipWiFiLoginResult/vip')   
    iMac = int(mac,16)
    if vip is None:
        try:  
            cursors=db.cursor()            
            cursors.callproc("CUSTOMER_WORK",(TENANTID,SHOPID,iMac,userid,0,'',0,'',''))
            logger.debug("mac=%s,userid=%s",mac,userid)
        except MySQLdb.Error,e:
            logger.debug("Mysql Error %d: %s" ,e.args[0], e.args[1])                   
    else:
        vipcodenode = vip.find('vipcode')
        namenode = vip.find('name')
        gendernode = vip.find('gender')
        vipidnode = vip.find('vipid')
        telephonenode =  vip.find('telephone')
        vipcode=""
        name=""
        gender=""
        vipid=""
        telephone=""
        if vipcodenode is not None:
            vipcode = vipcodenode.text 
        if namenode is not None:
            name = namenode.text
        if gendernode is not None:
            gender = gendernode.text
        if vipidnode is not None:
            vipid = vipidnode.text
        if telephonenode is not None:
            telephone = telephonenode.text
        sex = 0
        if gender == 'M':
            sex = 1
        #cursors=db.cursor()
        #cursors.callproc("CUSTOMER_WORK",(TENANTID,SHOPID,iMac,userid,1,name,sex,vipcode,vipid))
        try:  
            cursors=db.cursor()            
            cursors.callproc("CUSTOMER_WORK",(TENANTID,SHOPID,iMac,userid,1,name,sex,vipcode,vipid))
        except MySQLdb.Error,e:
            logger.debug("Mysql Error %d: %s" ,e.args[0], e.args[1])     
            if e.args[0]==2006:
                sys.exit(6)
        #except:
            #logger.debug("Process msg Error")
        logger.debug("mac=%s,userid=%s,vipcode=%s,name=%s,vipid=%s,tel=%s" ,mac,userid,vipcode,name,vipid,telephone)       

def callback(ch, method, properties, body):
    #body=body[0:-1]
    #body=body.decode('gb2312','ignore')
    logger.debug(" [x] Received %r" % (body))
    processMQMsg(body)

def ConnectMQ(MQurl,IsFailExit):
    #连接MQ
    global connection
    global channel
    connection = None
    channel = None     
    logger.debug("Connect MQ...")
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(MQurl))
    except:
        if IsFailExit:
            logger.debug("MQ link exception!Please check config file!Program exit...")
            sys.exit(3)     
    else:
        channel = connection.channel()
        channel.exchange_declare(EXCHANGE,"fanout",durable=True,auto_delete=False)
        channel.queue_declare(queue=QUEUE,durable=True,auto_delete=False)
        channel.queue_bind(exchange=EXCHANGE,queue=QUEUE)
        logger.debug("MQ Connect successfully" )   
 

def SetLogConfig():
    global logger
    logger = logging.getLogger('newworld')
    logger.setLevel(logging.DEBUG)
    # 写入日志文件
    fh = logging.FileHandler(os.path.join(os.getcwd(), 'NewWorld.log'))
    fh.setLevel(logging.DEBUG)
    # 再创建一个handler，用于输出到控制台  
    ch = logging.StreamHandler()  
    ch.setLevel(logging.DEBUG)     
    # 定义handler的输出格式  
    formatter = logging.Formatter('[%(levelname).1s] %(asctime).19s.%(msecs)03d (0x%(thread)04X):%(message)s\r')  
    fh.setFormatter(formatter)     
    ch.setFormatter(formatter)
    # 给logger添加handler  
    logger.addHandler(fh) 
    logger.addHandler(ch)

def StartConsumeMsg():
    #开始接收
    channel.basic_consume(callback, queue=QUEUE, no_ack=True)
    
    logger.debug('Waiting for messages. To exit press CTRL+C')
    #try:
    channel.start_consuming()
    """
    except pika.exceptions.ConnectionClosed:
        #连接意外断开 重连
        count = 0;
        while count<3: 
             time.sleep(5)  
             ConnectMQ(MQURL,False)
             count+=1
             if channel is not None:
                 break
        if channel is None:
            logger.debug("Cann't connect MQ 5 times,Check MQ!Program exit...")
            sys.exit(4)
        else:
            StartConsumeMsg()
    except:
        logger.debug("Consum MSG exception!Program exit...")
    sys.exit(5)    
    """

    
# 设定日志
SetLogConfig()
# 读取配置文件
LoadConfig() 


# 打开数据库连接
logger.debug("Connect DB...")
try:
    db = MySQLdb.connect(DATASOURCE,DBUSER,DBPWD,DBNAME,charset="utf8" )
except:
    logger.debug("Cann't Connect DB,Please check config file!Program exit...")
    sys.exit(1)
else:
    # 使用cursor()方法获取操作游标 
    cursor = db.cursor()
    logger.debug("DB Connected")    
    try:
        # 执行SQL语句
        cursor.execute(procSql)
        cursor.close()
    except:
        logger.debug("Error: unable to Create Procedure!Program exit...") 
        sys.exit(2)  

ConnectMQ(MQURL, True)  
StartConsumeMsg()


# 关闭数据库连接
db.close()