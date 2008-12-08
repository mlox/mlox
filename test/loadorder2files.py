#!/usr/bin/python
import os
import random
import time
import sys
inp = open(sys.argv[1], 'r')
mtime = 1200000000
for file in inp.readlines():
    file = file.strip("\n")
    print "file = %s" % file
    out = open(file, "w")
    out.close
    os.utime(file, (-1, mtime))
    mtime += 86400
