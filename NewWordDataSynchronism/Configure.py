#!/usr/bin/python
import ConfigParser

config=ConfigParser.ConfigParser()  
config.read('simple.ini') 
name=config.get('info','name')  
age=config.get('info','age')  
print name  
print age  