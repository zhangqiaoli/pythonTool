#!/usr/bin/python
# -*- coding: utf-8 -*-
import MySQLdb
import MySQLdb.cursors
import pysmartac
from pysmartac.log import PLOG

STORE_RESULT_MODE = 0
USE_RESULT_MODE = 1

CURSOR_MODE = 0
DICTCURSOR_MODE = 1
SSCURSOR_MODE = 2
SSDICTCURSOR_MODE = 3

FETCH_ONE = 0
FETCH_MANY = 1
FETCH_ALL = 2

class DBOperater:
    def __init__(self):
        self.conn = None
    def createconnection(self, host, user, passwd, dbname):
        """
        创建一个新连接
        """
        self.conn = MySQLdb.Connect(host, user, passwd, dbname, charset="utf8")
        if False == self.conn.open:
            PLOG.error("DBOperater.createconnection error")
            return -1
        return 0
    def closeconnection(self):
        """
        关闭连接
        """
        if self.conn != None:
            self.conn.close()
        else:
            PLOG.error("DBOperater.closeconnection error, conn is none")
        return 0
    def query(self, sqltext, mode = STORE_RESULT_MODE):
        """
        作用：使用connection对象的query方法，并返回一个元组(影响行数(int),结果集(result))
        参数：sqltext：sql语句
        mode=STORE_RESULT_MODE（0） 表示返回store_result，mode=USESTORE_RESULT_MODE（1） 表示返回use_result
        返回：元组(影响行数(int),结果集(result)
        """  
        if None == self.conn or False == self.conn.open:
            return -1
        self.conn.query(sqltext)
        if 0 == mode:
            result = self.conn.store_result()
        elif 1 == mode:
            result = self.conn.use_result()
        else:
            PLOG.error("DBOperater.closeconnection error, mode value is wrong")
            return -1
        return (self.conn.affected_rows(), result)
    def fetch_queryresult(self, result, maxrows = 1, how = 0, moreinfo = False):
        """
        参数:result： query后的结果集合
            maxrows： 返回的最大行数
            how： 以何种方式存储结果(0：tuple,1：dictionaries with columnname,2：dictionaries with table.columnname)
            moreinfo: 表示是否获取更多额外信息（num_fields，num_rows,num_fields）
        返回：元组（数据集，附加信息（当moreinfo=False）或单一数据集（当moreinfo=True）
        """        
        if None == result:
            return None
        dataset = result.fetch_row(maxrows, how)
        if False == moreinfo:
            return dataset
        else:
            new_fields = result.num_fields()
            new_rows = result.num_rows()
            field_flags = result.field_flags()
            info = (num_fields, num_rows, field_flags)
            return (dataset, info)
    def execute(self, sqltext, args = None, mode = CURSOR_MODE, many = False):
        """
        作用：使用游标（cursor）的execute 执行query
        参数：sqltext： 表示sql语句
        args： sqltext的参数
        mode：以何种方式返回数据集
        CURSOR_MODE = 0 ：store_result , tuple
        DICTCURSOR_MODE = 1 ： store_result , dict
        SSCURSOR_MODE = 2 : use_result , tuple
        SSDICTCURSOR_MODE = 3 : use_result , dict
        many：是否执行多行操作（executemany）
        返回：元组（影响行数（int），游标（Cursor））
        """
        if CURSOR_MODE == mode:
            curclass = MySQLdb.cursors.Cursor
        elif DICTCURSOR_MODE == mode :
            curclass = MySQLdb.cursors.DictCursor
        elif SSCURSOR_MODE == mode:
            curclass = MySQLdb.cursors.SSCursor
        elif SSDICTCURSOR_MODE == mode:
            curclass = MySQLdb.cursors.SSDictCursor
        else :
            PLOG.error("DBOperater.closeconnection error, mode value is wrong")
            return -1
        cur = self.conn.cursor(cursorclass=curclass)
        line = 0
        if False == many:
            if None == args:
                line = cur.execute(sqltext)
            else :
                line = cur.execute(sqltext,args)
        else :
            if None == args:
                line = cur.executemany(sqltext)
            else :
                line = cur.executemany(sqltext,args)
        return (line , cur)
    def fetch_executeresult(self, cursor, mode = FETCH_ONE, rows = 1):
        """
        作用：提取cursor获取的数据集
        参数：cursor：游标
        mode：执行提取模式
        FETCH_ONE: 提取一个； FETCH_MANY :提取rows个 ；FETCH_ALL : 提取所有
        rows：提取行数
        返回：fetch数据集
        """
        if None == cursor:
            return
        if FETCH_ONE == mode:
            return cursor.fetchone()
        elif FETCH_MANY == mode:
            return cursor.fetchmany(rows)
        elif FETCH_ALL == mode:
            return cursor.fetchall()
if __name__ == "__main__":
    pass