

import logging
import re
import os
from functools import reduce

config_logger = logging.getLogger('mlox.configHandler')

def caseless_uniq(un_uniqed_files):
    """
    Given a list, return a list of unique strings, and a list of duplicates.
    This is a caseless comparison, so 'Test' and 'test' are considered duplicates.
    """
    lower_files = []    # Use this to allow for easy use of the 'in' keyword
    unique_files = []   # Guaranteed case insensitive unique
    filtered = []       # any duplicates from the input

    for aFile in un_uniqed_files:
        if aFile.lower() in lower_files:
            filtered.append(aFile)
        else:
            unique_files.append(aFile)
            lower_files.append(aFile.lower())
    return(unique_files, filtered)


def partition_esps_and_esms(filelist):
    """Split filelist into separate lists for esms and esps, retaining order."""
    esm_files = []
    esp_files = []
    for filename in filelist:
        ext = filename[-4:].lower()
        if ext == ".esp":
            esp_files.append(filename)
        elif ext == ".esm":
            esm_files.append(filename)
    return(esm_files, esp_files)

# Handle reading and writing plugin configurations
class configHandler():
    # pattern matching a plugin in Morrowind.ini
    re_gamefile = re.compile(r'(?:GameFile\d+=)(.*)', re.IGNORECASE)
    # pattern to match plugins in FromFile (somewhat looser than re_gamefile)
    # this may be too sloppy, we could also look for the same prefix pattern,
    # and remove that if present on all lines.
    re_sloppy_plugin = re.compile(r'^(?:(?:DBG:\s+)?[_\*]\d\d\d[_\*]\s+|GameFile\d+=|content=|\d{1,3} {1,2}|Plugin\d+\s*=\s*)?(.+\.es[mp]\b)', re.IGNORECASE)
    # pattern used to match a string that should only contain a plugin name, no slop
    re_plugin = re.compile(r'^(\S.*?\.es[mp]\b)([\s]*)', re.IGNORECASE)
    #The regular expressions used to parse the file
    read_regexes = {
        "Morrowind" : re_gamefile,
        "Oblivion"  : re_plugin,
        None        : re_sloppy_plugin
    }
    #The path to the configuration file
    configFile = None
    #The type of config file (Is it a 'Morrowind.ini', raw, or something else?)
    fileType = None

    def __init__(self,configFile,fileType = None):
        self.configFile = configFile
        try:
            self.read_regexes[fileType]
            self.fileType = fileType
        except:
            config_logger.warn("\"{0}\" is not a recognized file type!".format(fileType))

    #Returns a list of plugins in a config file
    def read(self):
        files = []
        regex = self.read_regexes[self.fileType]
        try:
            file_handle = open(self.configFile, 'r')
        except IOError:
            config_logger.error("Unable to open config file: {0}".format(self.configFile))
            return []
        for line in file_handle:
            line.strip()
            line.strip('\r\n')
            gamefile = regex.match(line)
            if gamefile:
                f = gamefile.group(1).strip()
                files.append(f)
        file_handle.close()
        # Deal with duplicates
        (files, dups) = caseless_uniq(files)
        for f in dups:
            config_logger.debug("Duplicate plugin found in config file: {0}".format(f))
        return files

    #Remove all plugins from the config file
    def clear(self):
        section_re = re.compile("^(\[.*\])\s*$", re.MULTILINE);

        config_logger.debug("Clearing config file: {0}".format(self.configFile))

        #Only handling Morrowind.ini right now
        if (self.fileType != "Morrowind"):
            config_logger.error("Can not clear non Morrowind.ini config files.")
            return False

        #Read the file to a buffer
        try:
            file_handle = open(self.configFile, 'r')
        except IOError:
            config_logger.error("Unable to open config file: {0}".format(self.configFile))
            return False
        file_buffer = file_handle.read()
        file_handle.close()

        #Remove the data from '[Game Files]'
        sections = section_re.split(file_buffer)
        try:
            config_index = sections.index('[Game Files]')
        except:
            config_logger.error("Config file does not have a '[Game Files]' section!")
            return False
        sections[config_index+1] = '\n'
        file_buffer =  reduce(lambda x,y: x+y,sections)


        #Write the buffer to the file
        try:
            file_handle = open(self.configFile, 'w')
        except IOError:
            config_logger.error("Unable to open config file: {0}".format(self.configFile))
            return False
        file_handle.write(file_buffer)
        file_handle.close()

        return True

    #Write a plugin list to the config file
    def write(self,files):
        section_re = re.compile("^(\[.*\])\s*$", re.MULTILINE);

        config_logger.debug("Writing config file: {0}".format(self.configFile))

        #Only handling Morrowind.ini right now
        if (self.fileType != "Morrowind"):
            config_logger.error("Can not write non Morrowind.ini config files.")
            return False

        #Read the file to a buffer
        try:
            file_handle = open(self.configFile, 'r')
        except IOError:
            config_logger.error("Unable to open config file: {0}".format(self.configFile))
            return False
        file_buffer = file_handle.read()
        file_handle.close()

        #Generate the plugins string
        out_str = "\n"
        for i in range(0,len(files)):
            out_str += "GameFile{index}={plugin}\n".format(index=i,plugin=files[i])

        #Remove the data from '[Game Files]'
        sections = section_re.split(file_buffer)
        try:
            config_index = sections.index('[Game Files]')
        except:
            config_logger.error("Config file does not have a '[Game Files]' section!")
            return False
        sections[config_index+1] = out_str
        file_buffer =  reduce(lambda x,y: x+y,sections)


        #Write the buffer to the file
        try:
            file_handle = open(self.configFile, 'w')
        except IOError:
            config_logger.error("Unable to open config file: {0}".format(self.configFile))
            return False
        file_handle.write(file_buffer)
        file_handle.close()

        return True

# Handle reading and updating the load order for the plugins in the data directory
class dataDirHandler:
    path = None

    def __init__(self, data_files_path):
        self.path = data_files_path

    #Get the directory name in a printable form
    def getDir(self):
        return self.path

    def _full_path(self,a_file):
        """Convenience function to return the full path to a file."""
        return os.path.join(self.path,a_file)

    # Sort a list of plugin files by modification date
    def _sort_by_date(self, plugin_files):
        dated_plugins = [(os.path.getmtime(self._full_path(aPlugin)), aPlugin) for aPlugin in plugin_files]
        dated_plugins.sort()
        return([x[1] for x in dated_plugins])

    #Get all config files from the data directory
    def read(self):
        files = [f for f in os.listdir(self.path) if os.path.isfile(self._full_path(f))]
        (files, dups) = caseless_uniq(files)
        # Deal with duplicates
        for f in dups:
            logging.warn("Duplicate plugin found in data directory: {0}".format(f))
        # sort the plugins into load order by modification date (esm's first)
        (esm_files, esp_files) = partition_esps_and_esms(files)
        files =  self._sort_by_date(esm_files)
        files += self._sort_by_date(esp_files)
        return files

    def write(self,files):
        """Change the modification times of files to be in order of file list, oldest to newest
           There are six files with fixed times, the bsa files depend on the esm files being present.
           These files are fixed to be compatible with tes3cmd resetdates"""
        tes3cmd_resetdates_morrowind_mtime = 1024695106 # Fri Jun 21 17:31:46 2002
        tes3cmd_resetdates_tribunal_mtime  = 1035940926 # Tue Oct 29 20:22:06 2002
        tes3cmd_resetdates_bloodmoon_mtime = 1051807050 # Thu May  1 12:37:30 2003

        mtime = tes3cmd_resetdates_morrowind_mtime
        try:
            for p in files:
                if p.lower() == "morrowind.esm":
                    mtime = tes3cmd_resetdates_morrowind_mtime
                    os.utime(self._full_path("Morrowind.bsa"), (-1, mtime))
                elif p.lower() == "tribunal.esm":
                    mtime = tes3cmd_resetdates_tribunal_mtime
                    os.utime(self._full_path("Tribunal.bsa"), (-1, mtime))
                elif p.lower() == "bloodmoon.esm":
                    mtime = tes3cmd_resetdates_bloodmoon_mtime
                    os.utime(self._full_path("Bloodmoon.bsa"), (-1, mtime))
                else:
                    mtime += 60 # standard 1 minute Mash step
                os.utime(self._full_path(p), (-1, mtime))
        except TypeError:
            config_logger.error(
                """
                Could not update load order!
                Are you sure you have \"Morrowind.bsa\", \"Tribunal.bsa\", and/or \"Bloodmoon.bsa\" in your data file directory?
                """)
            return False
        return True
