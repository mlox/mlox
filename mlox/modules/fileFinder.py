

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
        self.dir = os.path.normpath(os.path.abspath(dir))
        for f in [p for p in os.listdir(dir)]:
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
