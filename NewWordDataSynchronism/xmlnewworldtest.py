#!/usr/bin/python
import pika
import MySQLdb
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
body = """<CRMInfo Mac="AABBCCDDEEFF" UserID="13812345678"> 
  <VipWiFiLoginResult> 
    <header> 
      <responsecode>0</responsecode>  
      <responsemessage/>  
      <pagerecords>0</pagerecords>  
      <pageno>0</pageno>  
      <updatecount>0</updatecount>  
      <maxrecords>0</maxrecords>  
      <maxpageno>0</maxpageno>  
      <messagetype/>  
      <messageid/>  
      <version/> 
    </header>  
    <vip> 
      <vipcode>123456</vipcode>  
      <surname>zqltest</surname>  
      <gender>M</gender>  
      <vipid>421683199011285532</vipid>  
      <telephone>13814584627</telephone> 
    </vip> 
  </VipWiFiLoginResult> 
</CRMInfo>"""

root = ET.fromstring(body)
# or 
#tree = ET.parse('newworld.xml')
#root = tree.getroot()  
mac = root.attrib['Mac']
userid = root.attrib['UserID']
vip = root.find('VipWiFiLoginResult/vip')
vipcode = vip.find('vipcode').text  
surname = vip.find('surname').text
vipid = vip.find('vipid').text
telephone = vip.find('telephone').text
print mac,userid,vipcode,surname,vipid,telephone    
# 执行sql语句,将数据插入mysql数据库
    