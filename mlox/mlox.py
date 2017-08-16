#!/usr/bin/python
# -*- mode: python -*-
# mlox - the elder scrolls Mod Load Order eXpert
#Copyright (c) 2009-2017
#    John Moonsugar, an alias
#    dragon32
#    Arthur Moore
# Distributed as part of the mlox project:
#   http://sourceforge.net/p/mlox/
# under the MIT License:
#   https://sourceforge.net/projects/mlox/files/License.txt

import os
import sys
import re
from getopt import getopt, GetoptError
import logging
import StringIO
import modules.update as update
import modules.version as version
from modules.loadOrder import loadorder
from modules.gui import _

class dynopt(dict):
    def __getattr__(self, item):
        return self.__getitem__(item)
    def __setattr__(self, item, value):
        self.__setitem__(item, value)

Opt = dynopt()

# command line options
Opt.BaseOnly = False
Opt.Explain = None
Opt.FromFile = False
Opt.GUI = False
Opt.GetAll = False
Opt.Profile = False
Opt.Quiet = False
Opt.Update = False
Opt.WarningsOnly = False
Opt.NoUpdate = False

#Configure logging from python module
class colorFormatConsole(logging.Formatter):
    levels = {
        'DEBUG'    : '',
        'INFO'     : '',
        'WARNING'  : '\x1b[0;30;43m',  #Yellow (ish)
        'ERROR'    : '\x1b[0;30;41m',  #Red (ish)
        'CRITICAL' : '\x1b[0;30;41m'   #Red (ish)
    }
    def __init__(self,msg):
        logging.Formatter.__init__(self, msg)
    def format(self,record):
        return self.levels[record.levelname] + logging.Formatter.format(self, record) +'\x1b[0m'

logging.getLogger('').setLevel(logging.DEBUG)
color_formatter = colorFormatConsole('%(levelname)s (%(name)s): %(message)s')
console_log_stream = logging.StreamHandler()
console_log_stream.setLevel(logging.INFO)
console_log_stream.setFormatter(color_formatter)
logging.getLogger('').addHandler(console_log_stream)

#Disable parse debug logging unless the user asks for it (It's so much it actually slows the program down)
logging.getLogger('mlox.parser').setLevel(logging.INFO)

def main():
    if Opt.NoUpdate == False:
            update.update_mloxdata()
    if Opt.GUI == True:
        # run with gui
        from modules.gui import mlox_gui
        mlox_gui().start()
    #Running in command line mode
    logging.info("Version: %s\t\t\t\t %s " % (version.full_version(), _["Hello!"]))
    if Opt.FromFile:
        if len(args) == 0:
            print _["Error: -f specified, but no files on command line."]
            usage(2)            # exits
        for fromfile in args:
            l = loadorder()
            l.read_from_file(fromfile)
            if Opt.Explain != None:
                print l.explain(Opt.Explain,Opt.BaseOnly)
                #Only expain for first input file
                sys.exit(0)
            if Opt.Quiet:
                l.update(StringIO.StringIO())
            else:
                l.update()
            #We never actually write anything if reading from file(s)
            if not Opt.WarningsOnly:
                print "[Proposed] New Load Order:\n---------------"
            for p in l.get_new_order():
                print p
    else:
        # run with command line arguments
        l = loadorder()
        if Opt.GetAll:
                l.get_data_files()
        else:
            l.get_active_plugins()
            if l.order == []:
                l.get_data_files()
        if Opt.Explain != None:
            print l.explain(Opt.Explain,Opt.BaseOnly)
            sys.exit(0)
        if Opt.Quiet:
            l.update(StringIO.StringIO())
        else:
            l.update()
        if not Opt.WarningsOnly:
            if Opt.Update:
                print "[UPDATED] New Load Order:\n---------------"
                l.write_new_order()
                print "[LOAD ORDER UPDATED!]"
            else:
                print "[Proposed] New Load Order:\n---------------"
        for p in l.get_new_order():
            print p

if __name__ == "__main__":
    logging.debug("\nmlox DEBUG DUMP:\n")
    def usage(status):
        print _["Usage"]
        sys.exit(status)
    # Check Python version
    pyversion = sys.version[:3]
    logging.debug(version.version_info())
    if float(pyversion) < 2.5:
        logging.error("This program requires at least Python version 2.5.")
        sys.exit(1)
    # process command line arguments
    logging.debug("Command line: %s" % " ".join(sys.argv))
    try:
        opts, args = getopt(sys.argv[1:], "acde:fhlnpquvw",
                            ["all", "base-only", "check", "debug", "explain=", "fromfile", "gui", "help",
                             "listversions", "nodownload", "parsedebug", "profile", "quiet", "translations=",
                             "update", "version", "warningsonly"])
    except GetoptError, err:
        print str(err)
        usage(2)                # exits
    if len(sys.argv) == 1:
        Opt.GUI = True
    for opt, arg in opts:
        if opt in   ("-a", "--all"):
            Opt.GetAll = True
        elif opt in ("-c", "--check"):
            Opt.Update = False
        elif opt in ("--base-only"):
            Opt.BaseOnly = True
        elif opt in ("-d", "--debug"):
            console_log_stream.setLevel(logging.DEBUG)
        elif opt in ("-e", "--explain"):
            Opt.Explain = arg
            Opt.Quiet = True
            console_log_stream.setLevel(logging.WARNING)
        elif opt in ("-f", "--fromfile"):
            Opt.FromFile = True
        elif opt in ("--gui"):
            Opt.GUI = True
        elif opt in ("-h", "--help"):
            usage(0)            # exits
        elif opt in ("-l", "--listversions"):
            l = loadorder()
            l.get_data_files()
            print l.listversions()
            sys.exit(0)
        elif opt in ("-p", "--parsedebug"):
            logging.getLogger('mlox.parser').setLevel(logging.DEBUG)
            console_log_stream.setLevel(logging.DEBUG)
        elif opt in ("--profile"):
            Opt.Profile = True
        elif opt in ("-q", "--quiet"):
            Opt.Quiet = True
            console_log_stream.setLevel(logging.WARNING)
        elif opt in ("--translations"):
            # dump the translation dictionary
            print "Languages translations for: %s" % arg
            for k, v in (load_translations(arg).items()):
                print "%s:" % k
                print " -> %s" % v.encode("utf-8")
            sys.exit(0)
        elif opt in ("-u", "--update"):
            Opt.Update = True
        elif opt in ("-v", "--version"):
            print version_info()
            sys.exit(0)
        elif opt in ("-w", "--warningsonly"):
            Opt.WarningsOnly = True
        elif opt in ("-n", "--nodownload"):
            Opt.NoUpdate = True

    if Opt.Profile:
        import hotshot, hotshot.stats
        prof = hotshot.Profile("mlox.prof")
        time = prof.runcall(main)
        prof.close()
        stats = hotshot.stats.load("mlox.prof")
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(20)
    else:
        main()
