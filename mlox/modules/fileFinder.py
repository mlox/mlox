

# Utility classes For doing caseless filename processing:
# caseless_filename uses a dictionary that stores the truename of a
# plugin by its canonical lowercased form (cname). We only use the
# truename for output, in all other processing, we use the cname so
# that all processing of filenames is caseless.

# Note that the first function to call cname() is get_data_files()
# this ensures that the proper truename of the actual file in the
# filesystem is stored in our dictionary. cname() is subsequently
# called for all filenames mentioned in rules, which may differ by
# case, since human input is inherently sloppy.

import os
import re
import logging

file_logger = logging.getLogger('mlox.fileFinder')

class caseless_filenames:

    def __init__(self):
        self.truenames = {}

    def cname(self, truename):
        the_cname = truename.lower()
        if not the_cname in self.truenames:
            self.truenames[the_cname] = truename
        return(the_cname)

    def truename(self, cname):
        return(self.truenames[cname])


class caseless_dirlist:

    def __init__(self, dir=os.getcwd()):
        self.files = {}
        if dir == None:
            return
        if isinstance(dir,caseless_dirlist):
            self.dir = dir.dirpath()
        else:
            self.dir = os.path.normpath(os.path.abspath(dir))
        for f in [p for p in os.listdir(self.dir)]:
            self.files[f.lower()] = f

    def find_file(self, file):
        return(self.files.get(file.lower(), None))

    def find_path(self, file):
        f = file.lower()
        if f in self.files:
            return(os.path.join(self.dir, self.files[f]))
        return(None)

    def find_parent_dir(self, file):
        """return the caseless_dirlist of the directory that contains file,
        starting from self.dir and working back towards root."""
        path = self.dir
        prev = None
        while path != prev:
            dl = caseless_dirlist(path)
            if dl.find_file(file):
                return(dl)
            prev = path
            path = os.path.split(path)[0]
        return(None)

    def dirpath(self):
        return(self.dir)

    def filelist(self):
        return(self.files.values())


# given a list of files, return a new list without dups (caseless), plus a list of any dups
def filter_dup_files(files):
    tmpfiles = []               # new list
    filtered = []               # any filtered dups from original list
    seen = {}
    C = caseless_filenames()
    for f in files:
        c = C.cname(f)
        if c in seen:
            filtered.append(f)
        else:
            tmpfiles.append(f)
        seen[c] = True
    return(tmpfiles, filtered)


def _find_appdata():
    """a somewhat hacky function for finding where Oblivion's Application Data lives.
    Hopefully works under Windows, Wine, and native Linux."""
    if os.name == "posix":
        # Linux - total hack for finding plugins.txt
        # we assume we're running under a wine tree somewhere. so we
        # find where we are now, then walk the tree upwards to find system.reg
        # then grovel around in system.reg until we find the localappdata path
        # and then fake it like a Republican
        re_appdata = re.compile(r'"LOCALAPPDATA"="([^"]+)"', re.IGNORECASE)
        regdir = caseless_dirlist().find_parent_dir("system.reg")
        if regdir == None:
            return(None)
        regpath = regdir.find_path("system.reg")
        if regpath == None:
            return(None)
        inp = myopen_file(regpath, 'r')
        if inp != None:
            for line in inp:
                match = re_appdata.match(line)
                if match:
                    path = match.group(1)
                    path = path.split(r'\\')
                    drive = "drive_" + path.pop(0).lower()[0]
                    appdata = "/".join([regdir.dirpath(), drive, "/".join(path)])
                    inp.close()
                    return(appdata)
            inp.close()
            return(None)
        return(None)
    # Windows
    try:
        import _winreg
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                  r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders')
            vals = _winreg.QueryValueEx(key, 'Local AppData')
        except WindowsError:
            return None
        else:
            key.Close()
        re_env = re.compile(r'%([^|<>=^%]+)%')
        appdata = re_env.sub(lambda m: os.environ.get(m.group(1), m.group(0)), vals[0])
        return(os.path.expandvars(appdata))
    except ImportError:
        return None

def _get_Oblivion_plugins_file():
    appdata = _find_appdata()
    if appdata == None:
        file_logger.warn("Application data directory not found")
        return(None)
    return os.path.join(appdata, "Oblivion", "Plugins.txt")

# Attempt to find the plugin file and directory for Morrowind and Oblivion
# This will attempt to find Morrowind's files first
def find_game_dirs():
    game = "None"
    datadir = None
    list_file = None

    cwd = caseless_dirlist() # start our search in our current directory
    gamedir = cwd.find_parent_dir("Morrowind.ini")
    if gamedir != None:
        game = "Morrowind"
        list_file = gamedir.find_path("Morrowind.ini")
        datadir = caseless_dirlist(gamedir.find_path("Data Files"))
    else:
        gamedir = cwd.find_parent_dir("Oblivion.ini")
        if gamedir != None:
            game = "Oblivion"
            list_file = _get_Oblivion_plugins_file()
            datadir = caseless_dirlist(gamedir.find_path("Data"))
        else:
            # Not running under a game directory, so we're probably testing
            # assume plugins live in current directory.
            datadir = caseless_dirlist("..")
    file_logger.debug("Found Game:  {0}".format(game))
    file_logger.debug("Plugins file at:  {0}".format(list_file))
    file_logger.debug("Data Files at: {0}".format(datadir.dirpath()))
    return (game,list_file,datadir)
