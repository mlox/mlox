#! /usr/bin/python

# A test script to make sure all the modules work

import sys
import logging

sys.path.append('../mlox/')

logging.basicConfig(level=logging.DEBUG)

#Updater
import modules.update as update
update.update_mloxdata()

#File Finder
import modules.fileFinder as fileFinder
file_names = fileFinder.caseless_filenames()
dir_list = fileFinder.caseless_dirlist()
fileFinder.caseless_dirlist(dir_list)       #Make sure copy constructor works
print dir_list.find_file("module_TEST.PY")
print dir_list.find_path("module_TEST.PY")
print dir_list.find_parent_dir("reaDme.mD").dirpath()
print fileFinder.filter_dup_files(dir_list.filelist())
print fileFinder.find_game_dirs()

#Config Handler
import modules.configHandler as configHandler
print "\x1b[0;30;41m" + "Reading handleri" + '\x1b[0m'
handleri = configHandler.configHandler("No File")
print handleri.read()
print "\x1b[0;30;41m" + "Reading handler0" + '\x1b[0m'
handler0 = configHandler.configHandler("./userfiles/zinx.txt","Morrowind")
print handler0.read()
print "\x1b[0;30;41m" + "Reading handler1" + '\x1b[0m'
handler1 = configHandler.configHandler("./userfiles/zinx.txt","Invalid")
print handler1.read()
print "\x1b[0;30;41m" + "Reading handler2" + '\x1b[0m'
handler2 = configHandler.configHandler("./userfiles/zinx.txt")
print handler2.read()
print "\x1b[0;30;41m" + "Reading handler3" + '\x1b[0m'
handler3 = configHandler.configHandler("./userfiles/zinx.txt","Oblivion")
print handler3.read()
print "\x1b[0;30;41m" + "Reading/clearing/writing handlerM" + '\x1b[0m'
handlerM = configHandler.configHandler("./testM/Morrowind.ini","Morrowind")
plugins = handlerM.read()
print plugins
handlerM.clear()
print handlerM.read()
handlerM.write(plugins)
print handlerM.read()
dirHandler = configHandler.dataDirHandler("./test1.data/")
print "\x1b[0;30;41m" + "Reading dirHandler" + '\x1b[0m'
plugins = dirHandler.read()
print plugins
print "\x1b[0;30;41m" + "Writing dirHandler" + '\x1b[0m'
dirHandler.write(plugins)


logging.getLogger('').setLevel(logging.INFO)

#Parser, ang pluggraph
import modules.ruleParser as ruleParser
import modules.pluggraph as pluggraph
print "\x1b[0;30;41m" + "Testing parser on dirHandler plugins" + '\x1b[0m'
graph = pluggraph.pluggraph()
myParser = ruleParser.rule_parser(plugins,graph,"./test1.data/",sys.stdout,file_names)
myParser.read_rules("./test1.data/mlox_base.txt")
print graph.topo_sort()
print "\x1b[0;30;41m" + "Testing filename version" + '\x1b[0m'
(f_ver,d_ver) = ruleParser.get_version("BB_Clothiers_of_Vvardenfell_v1.1.esp","./test1.data/")
print (f_ver,d_ver,"BB_Clothiers_of_Vvardenfell_v1.1.esp")

#Load order
from modules.loadOrder import loadorder
print "\x1b[0;30;41m" + "Testing loadorder 1" + '\x1b[0m'
l1 = loadorder()
l1.datadir = fileFinder.caseless_dirlist("./test1.data/")
l1.plugin_file = "./userfiles/abot.txt"
l1.game_type = None
l1.get_active_plugins()
l1.update()
print l1.listversions()
print "\x1b[0;30;41m" + "Testing loadorder 2" + '\x1b[0m'
l2 = loadorder()
l2.datadir = fileFinder.caseless_dirlist("./test1.data/")
l2.get_data_files()
l2.update()
print "\x1b[0;30;41m" + "Testing loadorder 3" + '\x1b[0m'
l3 = loadorder()
l3.read_from_file("./userfiles/abot.txt")
l3.update()
print l3.explain("Morrowind.esm")
print l3.explain("Morrowind.esm",True)


logging.getLogger('').setLevel(logging.DEBUG)

#Version
import modules.version as version
print "\x1b[0;30;41m" + "Testing Version" + '\x1b[0m'
print version.Version
print version.version_info()
