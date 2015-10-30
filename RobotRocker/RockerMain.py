import serial
import sys,os
import time
import json
import websocket
import thread
import pysmartac
import pysmartac.assistant as assistant
from pysmartac.daemon import daemon
from pysmartac.log import PLOG


#log settings
PLOG.setlevel('D')
PLOG.enableFilelog("%s/log/Rocker_$(Date8)_$(filenumber2).log"%(os.path.dirname(__file__)))

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)
    
ser = serial.Serial('COM6',9600, timeout=1)
###################ws 相关全局变量##############
ws = None
logined = False
###################ws 相关全局变量##############

admissibleError = 15
lastSendTime = 0
lastActive = ""
#----------------------------------------------------------------------
def run():
    time.sleep(5)
    global logined
    if logined:
        global ser
        while (ser.isOpen()):    
            text = ser.readline()          # read one, with timout
            if text:                    # check if not timeout
                n = ser.inWaiting()
                while n >0:
                     # look if there is more to read
                    text = text + ser.readline() #get it   
                    n = ser.inWaiting()
                PLOG.debug( text)
                if logined :
                    processData(text)
            
            # 50ms 读取一次数据
            time.sleep(0.05)
    ser.close()

def processData(text):
    #提取最后一次摇杆位置坐标
    index = text.rfind("(")
    indexEnd = text.rfind(")")
    PLOG.debug( "last location is "+text[index:indexEnd+1])
    text = text[index:indexEnd+1]
    text = text.replace("(","")
    text = text.replace(")","")
    arr = text.split(',')
    x = int(arr[0])
    y = int(arr[1])
    z = int(arr[2])
    #根据坐标判断是哪种运动状态
    vx = x - 512
    vy = y - 512
    active_operation = ""
    if abs(vx) < admissibleError and abs(vy) < admissibleError:
        active_operation = "stop"
        PLOG.debug( "stop")
    elif abs(vx) < 512*1.414/2:
        if vy >0 and vy -admissibleError > 0:    
            active_operation = "up"
            PLOG.debug( "up")
        else:
            active_operation = "down"
            PLOG.debug( "down" )  
    elif abs(vy) < 512*1.414/2:
        if vx >0 and vx -admissibleError > 0:  
            active_operation = "spin_right"
            PLOG.debug( "spin_right")
        else:
            active_operation = "spin_left"
            PLOG.debug( "spin_left")
    """
    {
	"invoke_id":"调用ID",
	// 消息ID
	"msgid":"active_robot",
	// 机器人id
	"robot_id":"1212",
	// 运动模式
	"active_mode":{
		"operation":"spin", // up-前进,down-后退,spin_up-调头前进,spin_left-左旋转,spin_right-右旋转
		"distance":10,  // 单位cm  移动距离(up和down时有此参数)
		"angle":180		// 旋转角度 (spin时有此参数)
	}
    }"""
    if active_operation is not "":    
        now = int(time.time()*1000)
        global lastSendTime
        global lastActive

        if active_operation != lastActive or now - lastSendTime >= 950:
            global logined
            if not logined: 
                login()
            msg = {}
            msg["invoke_id"] = "1"
            msg["msgid"] = "active_robot"
            msg["robot_id"] = "37bf0a26359e37d"
            msg["active_mode"] = {}
            msg["active_mode"]["operation"] = active_operation
            strmsg = json.dumps(msg)
            global ws
            ws.send(strmsg)
            PLOG.debug( "Send: "+strmsg )
            lastSendTime = now
            lastActive = active_operation
            #result = ws.recv()
            #print "Recv: "+result

def login():
    global logined
    if not logined:
        msg = {}
        msg["invoke_id"] = "1"
        msg["msgid"] = "login"
        msg["userid"] = "robot_test"
        msg["password"] = "smartac2015"
        strmsg = json.dumps(msg)    
        global ws
        ws.send(strmsg)

###########websocket client callback################ 
def on_message(ws, message):
    PLOG.debug( "Recv: "+message)
    msgJson = json.loads(message)
    global logined
    if msgJson["msgid"] == "login":
        if msgJson["errcode"] == 0:
            logined = True
        else:
            PLOG.debug("Userid is wrong,exit")
            #ws.close()
            sys.exit(0)
     
def on_error(ws, error):
    PLOG.debug(error)
    # 连接出错,可能连接状态不佳,隔一段时间再连接
    time.sleep(5)
 
def on_close(ws):
    PLOG.debug("### closed ###" )
    
 
def on_open(ws):
    login()   
###########websocket client callback################  

def connection():
    global ws
    while(True):
        ws = websocket.WebSocketApp("ws://172.16.5.16:18030/ws",
                                  on_open = on_open,
                                  on_message = on_message,
                                  on_error = on_error,
                                  on_close = on_close)
        ws.run_forever()  
        PLOG.debug("ws may break")
 
if __name__ == "__main__":
    thread.start_new_thread(run, ())
    connection()
    