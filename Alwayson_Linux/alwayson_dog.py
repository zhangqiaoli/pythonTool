#!/usr/bin/python
# -*- coding: utf-8 -*-
import ConfigParser
import threading
import time
import os
import subprocess
import sys
import socket
# import pysmartac
# import pysmartac.configer
import pysmartac.assistant as assistant
from pysmartac.log import PLOG
# inifile="/etc/alwayson.conf"
'''    def start(self):
        
        None
    def stop(self,waittime):
        None
    '''
checkinterval = 5;
parentpid = 0


def check_pid(pid):        
    """ Check For the existence of a unix pid. """
    if pid == 0:return False
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    else:
        return True
    
class program(threading.Thread):
    def __init__(self, name):
        threading.Thread.__init__(self, name=name)
        self.setDaemon(True)
        self.name = name
        self.command = ""
        self.runpath = ""
        # self.matchingregular=False
        self.matchingstring = ""
        self.pidfile = ""
        self.bootwait = 10
        self.rebootwait = 1
        self.enabled = True
        self.thread_stop = False
        self._pid = 0
        self._manager = None
        self.status = "unknow"
        self.processHandle=None
    def init(self, manager):
        self._manager = manager
    def getCommandForPID(self, pid):
        cmd = None
        try:
            processList = assistant.getProcessList()
            for p in processList:
                if p[0] == pid:
                    cmd = p[1]
                    break
            del processList
        except Exception, e:
            PLOG.error("%s getCommandForPID except:%s" % (self.name, e))
        return cmd
    def getPIDForString(self, s):
        pid = None
        try:
            processList = assistant.getProcessList()
            for p in processList:
                if p[1].find(s) != -1:
                    pid = p[0]
                    break
            del processList
        except Exception, e:
            PLOG.error("%s getPIDForString except:%s" % (self.name, e))

        return pid
    def update_pid(self):
        try:
            self._pid = 0
            if len(self.pidfile) > 0:
                pidfile = open(self.pidfile, 'r')
                pid = int(pidfile.readline())
                if pid != 0:
                    if self.getCommandForPID(pid) != None:
                        self._pid = pid
                        PLOG.info("%s PID confim for pid:%d" % (self.name, pid))
            elif len(self.matchingstring) > 0:
                pid = self.getPIDForString(self.matchingstring)
                if pid != None:
                    self._pid = pid
                    PLOG.info("%s PID confim for regular:%d" % (self.name, pid))
            else:
                PLOG.error("%s Unknow check type!!!" % self.name)
        except Exception, e:
            PLOG.error("%s update_pid except!err=%s" % (self.name, e))
        #PLOG.info("%s PID=%d" % (self.name, self._pid))
    def run(self):
        self.status = "waiting start"
        if not self.enabled:
            self.status = "disabled"
            return
        if self.bootwait > 0:time.sleep(self.bootwait)
        while not self.thread_stop:
            self.status = "checking"
            # print '%s start checking at %s ...\n' %(self.name,time.ctime())
            if self.processHandle!=None and self.processHandle.poll()!=None:
                print "recycle %s" % (self.name)
                self.processHandle=None
            if not check_pid(self._pid):self.update_pid()
            if not check_pid(self._pid):self._pid = 0
            if self._pid == 0:
                self.processHandle=None
                PLOG.warn("%s check failed!restarting ..." % (self.name))
                if self.rebootwait > 0:
                    self.status = "waiting restart"
                    PLOG.info("%s restarting wait %d second..." % (self.name, self.rebootwait))
                    time.sleep(self.rebootwait)
                try:
                    self.status = "starting"
                    # 修改当前路径
                    if len(self.runpath) > 0:
                        try:
                            if not os.path.isdir(self.runpath):os.makedirs(self.runpath)
                            if not os.path.isdir(self.runpath):
                                self.enabled = False
                                PLOG.error("%s run path invalid!"%(self.name))
                                break
                            os.chdir(self.runpath)
                        except Exception, e:
                            PLOG.error("%s restart failed!change current path failed!err=%s" % (self.name, e))
                    PLOG.info("%s execute command:'%s'"%(self.name,self.command))
                    self.processHandle=subprocess.Popen(self.command, bufsize=0, executable=None, stdin=None,
                                stdout=None,
                                stderr=None,
                                preexec_fn=None,
                                close_fds=False,
                                shell=True,
                                cwd=self.runpath, env=None,
                                universal_newlines=False,
                                startupinfo=None,
                                creationflags=0)
                    self._pid=self.processHandle.pid
                except Exception, e:
                    PLOG.error("%s restart failed!err=%s" % (self.name, e))
            else:
                print "%s is OK!" % self.name
                self.status = "runing"
            time.sleep(checkinterval)
        None
        
class manager:
    def __init__(self):
        self.programlist = []
        self.processList = []
    def load(self):
        config = ConfigParser.ConfigParser()
        conf1 = assistant.SF("%s/alwayson.conf" % (os.path.dirname(__file__)))
        conf2 = assistant.SF("%s/alwayson.conf" % (os.getcwd()))
        conf3 = "/etc/alwayson.conf"
        if os.path.isfile(conf1):conf = conf1
        elif os.path.isfile(conf2):conf = conf2
        else:conf = conf3
        PLOG.info("using configer file:%s" % conf)
        config.readfp(open(conf1, "rb"))
        checkinterval = config.getint("alwayson", "interval")
        for section in config.sections():
            try:
                if section == "alwayson":continue
                name = section
                newprog = program(name)
                newprog.command = config.get(section, "command")
                newprog.runpath = config.get(section, "runpath")
                # newprog.matchingregular=config.get(section, "matchingregular")
                newprog.matchingstring = config.get(section, "matchingstring")
                newprog.pidfile = config.get(section, "pidfile")
                newprog.bootwait = config.getint(section, "bootwait")
                newprog.rebootwait = config.getint(section, "rebootwait")
                newprog.enabled = config.getboolean(section, "enabled")
                newprog.init(self);
                PLOG.info("confim:%s" % name)
            except:
                PLOG.error("read configerfile failed!program=%s,Pass!" % name)
                continue
            self.programlist.append(newprog)

    def startall(self):
        for p in self.programlist:
            p.start()
    def stopall(self, waittime):
        for p in self.programlist:
            p.thread_stop = True
        for p in self.programlist:
            p.stop(waittime)
            
    def start(self, name):
        NotImplemented
        
    def stop(self, name):
        NotImplemented

    def processRPC(self, msg):
        ret = ""
        PLOG.info("RPC:\n%s" % msg)
        if msg == "status":
            ret = "alwayson working...\n"
            items = []
            for p in self.programlist:
                items.append((p.name, p.status))
            fmt = '%-40s %9s'
            ret = '\n'.join([fmt % (x, '[%s]' % y) for x, y in items])
            PLOG.info("report runing status:\n%s" % ret)
        elif msg == "stop":
            pass
        return ret
class CF:
    pass
if __name__ == "__main__":
    conf = CF()
    conf.host = "127.0.0.1"
    conf.port = 24001
    PLOG.trace(assistant.SF("%s/log/ALS_$(Date8)_$(filenumber2).log" % (os.path.dirname(__file__))))
    PLOG.enableFilelog("%s/log/ALS_$(Date8)_$(filenumber2).log" % (os.path.dirname(__file__)))
    try:
        parentpid = os.getppid()
    except:
        print "no parent id!"
        sys.exit(1)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((conf.host, conf.port))
        s.settimeout(1)
    except Exception, e:
        print("绑定UDP端口失败,Host=%s,Port=%d,err=%s" % (conf.host, conf.port, e))
        sys.exit(1)
    print ("Start listen UDP[%s:%d]..." % (conf.host, conf.port))
    print "alwayson dog starting..."
    m = manager()
    m.load()
    m.startall()
    while check_pid(parentpid):
        try:
            msg , addr = s.recvfrom(65500)
        except Exception, e:
                # print "continue"
            continue
        reply = m.processRPC(msg)
        if len(reply):s.sendto(reply, addr)
    print "parent exit! dog stoped!"

