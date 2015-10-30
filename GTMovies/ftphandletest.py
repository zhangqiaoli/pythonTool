# -*- coding:gbk -*-  
# Author:       ���  
# Created:      2012/3/28  
import thread  
from wx import _misc  
from ftplib import FTP  
import wx,os,uuid,socket,sys,time,re  
from twisted.python import log  
import wx.lib.agw.ultimatelistctrl as ULC  
from msgbox import *  
from db import Cfg  
from win32com.shell import shell, shellcon   
from win32con import FILE_ATTRIBUTE_NORMAL  
from base import PanelWarpCtrl,FileItem,FileImageList  
  
########################################################################  
class FtpHandler(FTP):  
    """ftp uploader handler"""  
    #blocksize=65536  
    def connect(self):  
        return self.login(Cfg.c_name,Cfg.c_pwd)  
  
    def login(self,name,pwd):  
        try:  
            FTP.connect(self,Cfg.c_ftpurl,int(Cfg.c_ftpport))  
        except:  
            log.err(sys.exc_info())  
            MessageBoxError('�޷������ϴ���������')  
            return False  
        try:  
            FTP.login(self,name,pwd)  
        except:  
            log.err(sys.exc_info())  
            MessageBoxError('�޷������ϴ���������\n�û������������')  
            return False  
        return True  
      
    def delete(self, filename):  
        '''''Delete a file.'''  
        self.sendcmd('DELE ' + filename)  
          
    def mlsd(self,callback = None):  
        self.retrlines('MLSD',callback)  
      
    def listdir(self,root):  
        items=[]  
        self.mlsd(lambda x:items.append(FileItem(x)))             
        return items  
      
    def deletedir(self,root):  
        def walk(root):  
            dirs = []  
            def ParseLine(line):  
                f=FileItem(line)  
                if f.isdir:  
                    dirs.append(os.path.join(root,f.fname))  
                else:  
                    self.delete(f.fname)  
            self.cwd(root)  
            self.mlsd(ParseLine)  
            for name in dirs:  
                new_path = os.path.join(root, name)  
                for x in walk(new_path):yield x   
            yield dirs    
  
        for dirs in walk(root):  
            for d in dirs:  
                self.rmd(d)  
        self.rmd(root)  

import wx  
import re,os  
from wx import MimeTypesManager  
from win32com.shell import shell, shellcon    
from win32con import FILE_ATTRIBUTE_NORMAL    
mimeTypeManager=MimeTypesManager()  
  
  
  
########################################################################  
class FileItem:  
    pattern=re.compile('modify=(?P<modify>\d+);perm=(?P<perm>\w+);size=(?P<size>\d+);type=(?P<type>\w+);\s(?P<filename>.*)')  
    def __init__(self,line):  
        m=FileItem.pattern.search(line)       
        self.isdir=m.group('type')=='dir'  
        self.size='' if self.isdir else m.group('size')  
        self.time='' if self.isdir else m.group('modify')  
        self.fname=m.group('filename')  
        self.ext=os.path.splitext(self.fname)[-1]                 
    def GetDesc(self):  
        desc=''  
        if self.isdir:  
            desc='�ļ���'  
        elif self.ext:  
            fileType=mimeTypeManager.GetFileTypeFromExtension(self.ext)  
            if fileType:  
                desc=fileType.GetDescription()  
                if desc is None:  
                    desc=''  
        return desc
    
    def scanFtpServerFiles():
        try:
            f = ftplib.FTP(conf.ftpServerHost)
        except ftplib.error_perm:
            print('�޷����ӵ�ftp server "%s"' % conf.ftpServerHost)
            return 0
        print('���ӵ�ftp server "%s"' % conf.ftpServerHost)
        
        try:
            #user��FTP�û�����pwd����������
            f.login(conf.ftpServerUser,conf.ftpServerPwd)
        except ftplib.error_perm:
            print('��¼ftp server "%s" ʧ��' % conf.ftpServerHost)
            f.quit()
            return 0
        print('��¼ftp server "%s" �ɹ�' % conf.ftpServerHost)    
        try:
           #�õ�DIRN�Ĺ���Ŀ¼
            f.cwd("YCommon")
        except ftplib.error_perm:
            print('�г���ǰĿ¼ʧ��')
            f.quit()
            return 0
      #f.dir()����һ����ǰĿ¼�µ��б��ظ�downloadlist
    downloadlist = ftplib.ftpRead()
    return downloadlist


    
    def convert(input):
        if isinstance(input, dict):
            return {convert(key): convert(value) for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [convert(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input