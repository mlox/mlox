#!/usr/bin/python

#A quick and dirty program to set file modified times based on an input file
#  This does NOT take anything else into account

# Input:  A file containing a list of plugins.  One per line, with no encoding

# Output: Files successfully modified.

# Usage: loadorder2files.py <load_order_file>

import os
import sys
inp = open(sys.argv[1], 'r')
mtime = 1200000000
for plugin in inp.readlines():
    plugin = plugin.strip("\n")
    if( os.path.isfile( plugin) ):
        print "file = %s" % plugin
        os.utime(plugin, (-1, mtime))
        mtime += 86400
