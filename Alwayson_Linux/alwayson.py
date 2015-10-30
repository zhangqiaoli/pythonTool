#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
    Alwayson主程序,负责潜水和保持监视进程/服务进程 启动
'''
import sys
import time
import subprocess
import os
import pysmartac.configer
import pysmartac.assistant as assistant
from pysmartac.daemon import daemon
import socket 
conf=""
dog=""
class AlwaysonDaemon(daemon):
    def run(self):
        while True:
            assistant.killCommand("alwayson_dog.py")
            print "dog is die,restarting..."
            #os.system("killall '%s'"%cmd)
            try:
                p=subprocess.Popen("python "+dog+" %d"%os.getpid(),shell=True)
                p.wait()
                time.sleep(1)
                continue
            except  Exception,e:
                print "restart dog failed!err=%s"%e
                sys.exit(3)
            time.sleep(3)
def status():
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.sendto("status",("127.0.0.1",24001))
    msg ,_ = s.recvfrom(65500)
    print msg
if __name__ == "__main__":
    conf=""
    conf1=assistant.SF("%s/alwayson.conf"%(os.path.dirname(__file__)))
    conf2=assistant.SF("%s/alwayson.conf"%(os.getcwd()))
    conf3="/smartac/alwayson/alwayson.conf"
    if os.path.isfile(conf1):conf=conf1
    elif os.path.isfile(conf2):conf=conf2
    else:conf=conf3    
    
    print("alwayson config file is:%s"%conf)
    config=pysmartac.configer.openconfiger(conf)
    
    #configer
    pidfile=os.path.join(os.path.dirname(conf),"alwayson.py.pid")
    dog=os.path.join(os.path.dirname(conf),"alwayson_dog.py")
    daemon = AlwaysonDaemon(pidfile)
    try:
        if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                daemon.start()
            elif 'stop' == sys.argv[1]:
                daemon.stop()
            elif 'restart' == sys.argv[1]:
                daemon.restart()
            elif 'run' == sys.argv[1]:
                try:
                    oldpid=int(file(pidfile, 'r').read().strip())
                    if assistant.check_pid(oldpid):
                        print ("alwayson is running(pid:%d)\n"%(oldpid))
                        sys.exit(0)
                except Exception,e:
                    pass
                file(pidfile,'w+').write("%d\n" % os.getpid())
                daemon.run()
            elif 'status' == sys.argv[1]:
                status()
            else:
                print "Unknown command"
                sys.exit(2)
            sys.exit(0)
        else:
            print "usage: %s start|stop|restart|run|status" % sys.argv[0]
            sys.exit(2)
    except Exception,e:
        print("alwayson except error=%s"%e)
        sys.exit(3)
