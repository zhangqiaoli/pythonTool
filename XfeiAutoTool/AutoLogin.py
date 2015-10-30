#  -*- coding: utf-8 -*-
# !/usr/bin/python

import urllib2
import urllib
import cookielib
import re
import os
import json

abnfdir = "E:\\PythonCode\\XfeiAutoTool\\abnf"
username = "762778958@qq.com"
password = "zql;901128"
app_id = "5628a07c"

auth_url = 'http://www.xfyun.cn'
#########################获取cookie存入文件###########################
def getCookieByLogin():   
    # 登陆用户名和密码
    data={
            "username":"762778958@qq.com",
            "password":"xunfei_zql"
    }
    # urllib进行编码
    post_data=urllib.urlencode(data)
    # 发送头信息
    headers ={
            "Host":"www.xfyun.cn", 
            "Referer": "http://www.xfyun.cn/index.php/default/login"
    }
    global auth_url
    req=urllib2.Request(auth_url,post_data,headers)
    req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    # 获取cookie
    ckjar = cookielib.MozillaCookieJar("cookie.txt") 
    ckproc = urllib2.HTTPCookieProcessor(ckjar)
    # 实例化一个全局opener
    opener = urllib2.build_opener(ckproc)
    
    f = opener.open(req) 
    htm = f.read() 
    #print("getCookieByLogin read %s"%htm)
    f.close()
    #将cookie保存到文件中
    ckjar.save(ignore_discard=True, ignore_expires=True)
    return ckjar

#########################获取cookie存入文件End###########################

#########################新建grammar###################################
def addGrammar(ckjar,grammaname): 
    #ckjar = cookielib.MozillaCookieJar(os.path.join('E:\PythonCode\XfeiAutoTool', 'cookie.txt'))
    #all_the_text = open(os.path.join('E:\\PythonCode\\XfeiAutoTool\\abnf', 'test1.abnf')).read() 
    global app_id
    addGrammar_data={
            "app_id":app_id,
            "gramma_name":grammaname,
            "gramma_descr":"测试"
    }
    req = urllib2.Request("http://osp.voicecloud.cn/index.php/ajax/gramma/addGramma", urllib.urlencode(addGrammar_data))
    
    req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar) )
    
    f = opener.open(req) 
    grammarid = f.read() 
    print("addGrammar read %s"%grammarid)
    f.close()
    if int(grammarid) < 0 :
        print("addGrammar by name'%s' failed!"%(grammaname))
        return ""
    
    return grammarid
#########################新建grammarEnd###################################

#########################编译grammar###################################
def compileGrammar(ckjar,abnffilepath,grammarid,grammaname): 
    #all_the_text = open(os.path.join('E:\\PythonCode\\XfeiAutoTool\\abnf', 'test1.abnf')).read() 
    all_the_text = open(abnffilepath).read() 
    global app_id
    data={
            "app_id":app_id,
            "gramma_id":grammarid,
            "gramma_name":grammaname,
            "gramma_content":all_the_text,
            "mode":"exp"
    }
    post_data=urllib.urlencode(data)
    req = urllib2.Request("http://osp.voicecloud.cn/index.php/ajax/gramma/compile", post_data)
    
    req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar) )
    
    f = opener.open(req) 
    htm = f.read() 
    print("compileGrammar read %s"%htm)
    f.close()
#########################编译grammarEnd###################################

#########################获取编译结果###################################
def getCompileResult(ckjar,grammarid): 
    global app_id
    data={
            "app_id":app_id,
            "gramma_id":grammarid
    }
    post_data=urllib.urlencode(data)
    req = urllib2.Request("http://osp.voicecloud.cn/index.php/ajax/gramma/getcompileresult", post_data)
    
    req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar) )
    
    f = opener.open(req) 
    htm = f.read() 
    print("getCompileResult read %s"%htm)
    f.close()
    return htm
#########################编译grammarEnd###################################

#########################发布grammer###################################
def publish(ckjar,grammarid): 
    data={
            "gramma_id":grammarid,
            "tag":"v1.0",
            "version_descr":"测试"
    }
    post_data=urllib.urlencode(data)
    req = urllib2.Request("http://osp.voicecloud.cn/index.php/ajax/gramma/publish", post_data)
    
    req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar) )
    
    f = opener.open(req) 
    htm = f.read() 
    print("publish read %s"%htm)
    f.close()
#########################发布grammer End###################################

#########################grammar在应用上生效###################################
def publishGrammar(ckjar,grammarid): 
    global app_id
    data={
            "app_id":app_id,
            "gramma_id":grammarid
    }
    post_data=urllib.urlencode(data)
    req = urllib2.Request("http://osp.voicecloud.cn/index.php/ajax/gramma/publishgramma", post_data)
    
    req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1)')
    
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(ckjar) )
    
    f = opener.open(req) 
    htm = f.read() 
    print("publishGrammar read %s"%htm)
    f.close()
#########################grammar在应用上生效End###################################

if __name__ == "__main__":
    cookie = getCookieByLogin()
    abnfinfo = {}
    #枚举abnf目录
    files = os.listdir(abnfdir)
    for f in files:
        subpath = os.path.join(abnfdir,f)
        if (os.path.isdir(subpath)):
            abnfFilePath = os.path.join(subpath,"main.abnf")
            grammaname = "q_" + f
            if (os.path.isfile(abnfFilePath)):
                # 有效的abnffile路径
                abnfinfo[grammaname] = abnfFilePath
            else:
                print("abnfdir'%s' has not main.abnf file"%subpath)
    
    for k,v in abnfinfo.items():            
        grammarid = addGrammar(cookie,k)
        if grammarid != "" :
            compileGrammar(cookie, v, grammarid, k)
            compileResult = getCompileResult(cookie, grammarid)
            compileResJson = json.loads(compileResult,'utf8')
            if compileResJson["flag"] != None and compileResJson["flag"] == 0:              
                if compileResJson["out"] == None or compileResJson["out"] != 0 :
                    print("Grammar'%s' invalid,Compile abnf file'%s' failed!,ret=%d,error='%s'"%(k,v,compileResJson["out"],compileResJson["msg"]))
                else:
                    publish(cookie, grammarid)
                    publishGrammar(cookie,grammarid)  
                    print("Grammar'%s' publish success,use abnf file'%s'"%(k,v))
            else:
                print("Grammar'%s' invalid,Compile abnf file'%s' failed!,flag=%d"%(k,v,compileResJson["flag"]))
    