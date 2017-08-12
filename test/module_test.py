#! /usr/bin/python

# A test script to make sure all the modules work

#Basic setup for logging
import sys
import os
import logging
import unittest
sys.path.append( os.path.abspath('../mlox/') )
logging.basicConfig(level=logging.DEBUG)

term_color ={
    'red': '\x1b[0;30;41m',
    'clear': '\x1b[0m'
}

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
handleri = configHandler.configHandler("No File")
handler0 = configHandler.configHandler("./userfiles/zinx.txt","Morrowind")
handler1 = configHandler.configHandler("./userfiles/zinx.txt","Invalid")
handler2 = configHandler.configHandler("./userfiles/zinx.txt")
handler3 = configHandler.configHandler("./userfiles/zinx.txt","Oblivion")
print term_color['red'] + "Reading handleri" + term_color['clear']
print handleri.read()
print term_color['red'] + "Reading handler0" + term_color['clear']
print handler0.read()
print term_color['red'] + "Reading handler1" + term_color['clear']
print handler1.read()
print term_color['red'] + "Reading handler2" + term_color['clear']
print handler2.read()
print term_color['red'] + "Reading handler3" + term_color['clear']
print handler3.read()

dirHandler = configHandler.dataDirHandler("./test1.data/")
print term_color['red'] + "Reading dirHandler" + term_color['clear']
plugins = dirHandler.read()
print plugins
print term_color['red'] + "Writing dirHandler" + term_color['clear']
dirHandler.write(plugins)


logging.getLogger('').setLevel(logging.INFO)

#Parser, ang pluggraph
import modules.ruleParser as ruleParser
import modules.pluggraph as pluggraph
print term_color['red'] + "Testing parser on dirHandler plugins" + term_color['clear']
graph = pluggraph.pluggraph()
myParser = ruleParser.rule_parser(plugins,graph,"./test1.data/",sys.stdout,file_names)
myParser.read_rules("./test1.data/mlox_base.txt")
print graph.topo_sort()
print term_color['red'] + "Testing filename version" + term_color['clear']
(f_ver,d_ver) = ruleParser.get_version("BB_Clothiers_of_Vvardenfell_v1.1.esp","./test1.data/")
print (f_ver,d_ver,"BB_Clothiers_of_Vvardenfell_v1.1.esp")

#Load order
from modules.loadOrder import loadorder
print term_color['red'] + "Testing loadorder 1" + term_color['clear']
l1 = loadorder()
l1.datadir = fileFinder.caseless_dirlist("./test1.data/")
l1.plugin_file = "./userfiles/abot.txt"
l1.game_type = None
l1.get_active_plugins()
l1.update()
print l1.listversions()
print term_color['red'] + "Testing loadorder 2" + term_color['clear']
l2 = loadorder()
l2.datadir = fileFinder.caseless_dirlist("./test1.data/")
l2.get_data_files()
l2.update()
print term_color['red'] + "Testing loadorder 3" + term_color['clear']
l3 = loadorder()
l3.read_from_file("./userfiles/abot.txt")
l3.update()
print l3.explain("Morrowind.esm")
print l3.explain("Morrowind.esm",True)


logging.getLogger('').setLevel(logging.DEBUG)

#Version
import modules.version as version
print term_color['red'] + "Testing Version" + term_color['clear']
print version.Version
print version.version_info()

#Updater
class update_test(unittest.TestCase):
    temp_dir = ""

    def setUp(self):
        import tempfile
        self.temp_dir = tempfile.mkdtemp()

    #Make sure basic updator works
    def testUpdater(self):
        sys.path[0]= self.temp_dir
        import modules.update as update
        update.update_mloxdata()

        self.assertTrue(os.path.isfile(self.temp_dir+'/mlox-data.7z'),term_color['red']+"Unable to download mlox-data.7z"+term_color['clear'])
        self.assertTrue(os.path.isfile(self.temp_dir+'/mlox_base.txt'),term_color['red']+"Unable to extract mlox_base.txt"+term_color['clear'])

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

unittest.main()
