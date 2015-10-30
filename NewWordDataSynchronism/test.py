#!/usr/bin/env python
#coding=utf8
import subprocess
child = subprocess.Popen(["ping","-c","5","www.google.com"])
print("parent process")