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


class configHandler():
    """
    A class for handling plugin configuration files.

    A configuration file is a text file containing an ordered list of plugins.
    For example 'Morrowind.ini' is a configuration File.
    This allows for reading and writing to those files.
    """

    # A section of a configuration file
    section_re = re.compile("^(\[.*\])\s*$", re.MULTILINE)
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
        "raw"       : re_plugin,
        None        : re_sloppy_plugin
    }
    #The path to the configuration file
    configFile = None
    #The type of config file (Is it a 'Morrowind.ini', raw, or something else?)
    fileType = None

    def __init__(self, configFile, fileType = None):
        self.configFile = configFile
        try:
            self.read_regexes[fileType] # Note:  This might not seem to do anything, but it serves as a runtime check that fileType is an accepted value.
            self.fileType = fileType
        except:
            config_logger.warning("\"{0}\" is not a recognized file type!".format(fileType))


    def read(self):
        """
        Read a configuration file

        :return: An ordered list of plugins
        """
        files = []
        regex = self.read_regexes[self.fileType]
        try:
            file_handle = open(self.configFile, 'r')
            for line in file_handle:
                gamefile = regex.match(line.strip())
                if gamefile:
                    f = gamefile.group(1).strip()
                    files.append(f)
            file_handle.close()
        except IOError:
            config_logger.error("Unable to open configuration file: {0}".format(self.configFile))
            return []
        except UnicodeDecodeError:
            config_logger.error("Bad Characters in configuration file: {0}".format(self.configFile))
            return []
        # Deal with duplicates
        (files, dups) = caseless_uniq(files)
        for f in dups:
            config_logger.debug("Duplicate plugin found in config file: {0}".format(f))
        return files

    def clear(self):
        """
        Remove all the plugin lines from a configuration file.

        :return: True on success, or False on failure
        """
        config_logger.debug("Clearing configuration file: {0}".format(self.configFile))
        return self.write([])

    def write(self, list_of_plugins):
        """
        Write a list of plugins to a configuration file

        :return: True on success, or False on failure
        """
        config_logger.debug("Writing configuration file: {0}".format(self.configFile))

        if self.fileType == "Morrowind":
            return self._write_morrowind(list_of_plugins)

        if self.fileType == "raw":
            return self._write_raw(list_of_plugins)

        config_logger.error("Can not write to %s configuration files.",self.fileType)
        return False

    def _write_morrowind(self, list_of_plugins):
        """
        Write a list of plugins to a Morrowind.ini file

        We don't just use `configparser` because it breaks on reading Morrowind.ini files :/

        :return: True on success, or False on failure
        """
        # Generate the plugins string
        out_str = "\n"
        for i in range(0, len(list_of_plugins)):
            out_str += "GameFile{index}={plugin}\n".format(index=i, plugin=list_of_plugins[i])

        # Open and read a configuration file, splitting the result into multiple sections.
        try:
            file_handle = open(self.configFile, 'r')
        except IOError:
            config_logger.error("Unable to open configuration file: {0}".format(self.configFile))
            return False
        file_buffer = file_handle.read()
        file_handle.close()
        sections = self.section_re.split(file_buffer)

        # Replace the data in the '[Game Files]' section with the generated plugins string
        try:
            config_index = sections.index('[Game Files]')
        except IndexError:
            config_logger.error("Configuration file does not have a '[Game Files]' section!")
            return False
        sections[config_index+1] = out_str
        file_buffer = reduce(lambda x,y: x+y,sections)

        # Write the modified buffer to the configuration file
        try:
            file_handle = open(self.configFile, 'w')
        except IOError:
            config_logger.error("Unable to open configuration file: {0}".format(self.configFile))
            return False
        file_handle.write(file_buffer)
        file_handle.close()

        return True

    def _write_raw(self, list_of_plugins):
        """
        Write a list of plugins to a raw file

        That is a file containing nothing but plugins.  One per line

        :return: True on success, or False on failure
        """
        try:
            file_handle = open(self.configFile, 'w')
        except IOError:
            config_logger.error("Unable to open configuration file: {0}".format(self.configFile))
            return False

        for a_plugin in list_of_plugins:
            print(a_plugin, file=file_handle)
        file_handle.close()

        return True


class dataDirHandler:
    """
    A class for handling a directory containing plugin files.

    Plugin files are loaded by Morrowind.exe in the order of their modification timestamp.
    With the oldest being loaded first.
    This allows for reading and setting the plugin order using the same interface as configHandler.
    """
    path = None

    def __init__(self, data_files_path):
        self.path = data_files_path

    #Get the directory name in a printable form
    def getDir(self):
        return self.path

    def _full_path(self,a_file):
        """Convenience function to return the full path to a file."""
        return os.path.join(self.path,a_file)

    def _sort_by_date(self, list_of_plugins):
        """Sort a list of plugin files by modification date"""
        dated_plugins = [(os.path.getmtime(self._full_path(a_plugin)), a_plugin) for a_plugin in list_of_plugins]
        dated_plugins.sort()
        return([x[1] for x in dated_plugins])

    def read(self):
        """
        Obtain an ordered list of plugins from a directory.

        Note:  Unlike configHandler.read(), ESM files will always be at the front of the returned list.
        :return: An ordered list of plugins
        """
        files = [f for f in os.listdir(self.path) if os.path.isfile(self._full_path(f))]
        (files, dups) = caseless_uniq(files)
        # Deal with duplicates
        for f in dups:
            logging.warning("Duplicate plugin found in data directory: {0}".format(f))
        # sort the plugins into load order by modification date (esm's first)
        (esm_files, esp_files) = partition_esps_and_esms(files)
        files  = self._sort_by_date(esm_files)
        files += self._sort_by_date(esp_files)
        return files

    def write(self, list_of_plugins):
        """
        Change the modification times of plugin files to be in order of file list, oldest to newest

        There are six files with fixed times, the bsa files depend on the esm files being present.
        These files are fixed to be compatible with `tes3cmd resetdates`.
        :return: True on success, or False on failure
        """
        tes3cmd_resetdates_morrowind_mtime = 1024695106 # Fri Jun 21 17:31:46 2002
        tes3cmd_resetdates_tribunal_mtime  = 1035940926 # Tue Oct 29 20:22:06 2002
        tes3cmd_resetdates_bloodmoon_mtime = 1051807050 # Thu May  1 12:37:30 2003

        mtime = tes3cmd_resetdates_morrowind_mtime
        try:
            for a_plugin in list_of_plugins:
                if a_plugin.lower() == "morrowind.esm":
                    mtime = tes3cmd_resetdates_morrowind_mtime
                    os.utime(self._full_path("Morrowind.bsa"), (-1, mtime))
                elif a_plugin.lower() == "tribunal.esm":
                    mtime = tes3cmd_resetdates_tribunal_mtime
                    os.utime(self._full_path("Tribunal.bsa"), (-1, mtime))
                elif a_plugin.lower() == "bloodmoon.esm":
                    mtime = tes3cmd_resetdates_bloodmoon_mtime
                    os.utime(self._full_path("Bloodmoon.bsa"), (-1, mtime))
                else:
                    mtime += 60 # standard 1 minute Mash step
                os.utime(self._full_path(a_plugin), (-1, mtime))
        except TypeError:
            config_logger.error(
                """
                Could not update load order!
                Are you sure you have \"Morrowind.bsa\", \"Tribunal.bsa\", and/or \"Bloodmoon.bsa\" in your data file directory?
                """)
            return False
        return True
