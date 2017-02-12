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
print dir_list.find_file("module_TEST.PY")
print dir_list.find_path("module_TEST.PY")
print dir_list.find_parent_dir("reaDme.mD").dirpath()
print fileFinder.filter_dup_files(dir_list.filelist())
