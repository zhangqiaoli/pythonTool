import logging
import os.path
import uuid
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
import json
import sys
import pysmartac
import pysmartac.assistant as assistant
from pysmartac.daemon import daemon
from pysmartac.log import PLOG
import datetime
import threading
import uuid

lastpageuri = "file:///E:/PythonCode/ExchangeDemo/websocketA.html"
port = 8888

#log settings
PLOG.setlevel('D')
PLOG.enableFilelog("%s/log/Demo_$(Date8)_$(filenumber2).log"%(os.path.dirname(__file__)))

reload(sys)
sys.setdefaultencoding("utf-8")

def HandleSetURI(uri):
    res = {}
    res["msgid"] = "setpage"
    res["uri"] = uri
    jsres = json.dumps(res)
    for wsname,ws in WSManager.websockets.items():    
        ws.write_message(jsres)

class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")
    
class SetPageHandler(BaseHandler):
    def get(self):
        result = ""
        jsresult = {}
        cmdlist = self.get_query_arguments("cmd")
        for cmd in cmdlist:
            PLOG.debug("Receive msg %s"%cmd)
            if len(cmd) >0 :
                js = json.loads(cmd.decode('utf8'))
                if js.has_key('msgid') :
                    msg = js["msgid"]
                    if msg == "seturi":
                        if js.has_key('body'):
                            body = js["body"]
                            if body.has_key('uri'):
                                uri = body["uri"]
                                if len(uri) >0:
                                    global lastpageuri
                                    lastpageuri = uri
                                    HandleSetURI(uri)
                                    jsresult["errmsg"] = "OK"
                                else:
                                    jsresult["errmsg"] = "uri is empty!"
                            else:
                                jsresult["errmsg"] = "msg seturi body has no uri,invalid msg"
                        else:
                            jsresult["errmsg"] = "msg seturi has no body,invalid msg"                        
                    else:
                        jsresult["errmsg"] = "not support msgid " + msg
            self.write(json.dumps(jsresult))         

class WebSocketManager():
    def __init__(self):
        self.websockets = {}
        self.timer = threading.Timer(5.0, self.CheckWSHeartbeat)
        self.timer.start()
    def AddWebSocket(self,wsconn):
        wsname = wsconn.wsname   
        if self.websockets.has_key(wsname) :
            PLOG.debug("Already has ws connect %s,close old connect"%wsname)
            self.websockets[wsname].close()
        self.websockets[wsname] = wsconn     
        PLOG.debug("ws manager add %s"%wsname)
        
    def RemoveWebSocket(self,wsstr):
        self.websockets.pop(wsstr)
        PLOG.debug("ws manager remove %s"%wsstr)
    
    def CheckWSHeartbeat(self):
        for wsname,wsconn in self.websockets.items():
            if wsconn != None:
                wsconn.heartbeatCheck()
        self.timer = threading.Timer(5.0, self.CheckWSHeartbeat)
        self.timer.start()        

class WebSocketConnection():
    def __init__(self,wsHandler):
        self.createtime = datetime.datetime.now()
        self.lastactivetime = datetime.datetime.now()
        self.wsname = wsHandler.request.remote_ip
    def updateActiveTime():
        self.lastactivetime = datetime.datetime.now()
    def isTimeOut():
        if (datetime.datetime.now() - self.lastactivetime).seconds > 10 :
            return True
        else:
            return False
    def heartbeatCheck(self):
        if self.isTimeOut():
            PLOG.debug("%s websocket timeout,disconnect it"%wsname)
        
                                  
class PageWebSocketHandler(tornado.websocket.WebSocketHandler):    
    def __init__(self,application, request,**kwargs):
        tornado.websocket.WebSocketHandler.__init__(self, application, request,
                                            **kwargs)        
        self.createtime = datetime.datetime.now()
        self.lastactivetime = datetime.datetime.now()
        self.wsname = self.request.remote_ip        
    def check_origin(self, origin):
        return True
    def open(self):
        WSManager.AddWebSocket(self) 
        HandleSetURI(lastpageuri)
        
    def on_message(self, message):
        PLOG.trace("receive msg %s"%message)
        self.updateActiveTime()
    def on_close(self):
        remoteip = self.request.remote_ip      
        WSManager.RemoveWebSocket(remoteip)
    def on_pong(self,data):
        PLOG.trace("receive pong")
        self.updateActiveTime()
        
    def updateActiveTime(self):
        self.lastactivetime = datetime.datetime.now()
    def isTimeOut(self):
        if (datetime.datetime.now() - self.lastactivetime).seconds > 20 :
            return True
        else:
            return False
    def heartbeatCheck(self):
        if self.isTimeOut():
            PLOG.debug("%s websocket timeout,disconnect it"%self.wsname) 
            self.close()
            WSManager.RemoveWebSocket(self.wsname)
        else:
            PLOG.trace("send ping")
            self.ping("ping")


WSManager = WebSocketManager()
def main():
    app = tornado.web.Application([
        (r'/ws', PageWebSocketHandler),
        (r"/setpage", SetPageHandler)
    ])
    app.listen(port)
    tornado.ioloop.IOLoop.instance().start()    
if __name__ == '__main__':
    main()