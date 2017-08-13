#!/usr/bin/python
import os
import random
import time
for f in os.listdir("."):
    ext = f[-4:].lower()
    if (os.path.isfile(f) and (ext == '.esp' or ext == '.esm')):
        mtime = random.randrange(1200000000, int(time.time()), 100)
        #print "setting mtime of %s to %f" % (f, mtime)
        os.utime(f, (-1, mtime))
