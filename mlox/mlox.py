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
Version = "0.61"

import locale
import os
import sys
import re
import codecs
from time import time
import traceback
from pprint import PrettyPrinter
from getopt import getopt, GetoptError
import cPickle
import logging
import modules.update as update

logging.basicConfig(level=logging.INFO)

class dynopt(dict):
    def __getattr__(self, item):
        return self.__getitem__(item)
    def __setattr__(self, item, value):
        self.__setitem__(item, value)

Opt = dynopt()

# command line options
Opt.AutoFocus = True
Opt.BaseOnly = False
Opt.DBG = False
Opt.Explain = None
Opt.FromFile = False
Opt.GUI = False
Opt.GetAll = False
Opt.ParseDBG = False
Opt.Profile = False
Opt.Quiet = False
Opt.Update = False
Opt.WarningsOnly = False
Opt._Game = None
Opt.NoUpdate = False

if __name__ == "__main__":
    if len(sys.argv) == 1:
        Opt.GUI = True
        import wx
        import wx.richtext as rt
        import webbrowser
        webbrowser.PROCESS_CREATION_DELAY = 0

# comments start with ';'
re_comment = re.compile(r'(?:^|\s);.*$')
# re_rule matches the start of a rule.
# TBD: check end-bracket pattern
re_rule = re.compile(r'^\[(version|order|nearend|nearstart|conflict|note|patch|requires)((?:\s+.[^\]]*)?)\](.*)$', re.IGNORECASE)
re_base_version = re.compile(r'^\[version\s+([^\]]*)\]', re.IGNORECASE)
# line for multiline messages
re_message = re.compile(r'^\s')
# pattern matching a plugin in Morrowind.ini
re_gamefile = re.compile(r'(?:GameFile\d*|content)+=(.*)', re.IGNORECASE)
# pattern to match plugins in FromFile (somewhat looser than re_gamefile)
# this may be too sloppy, we could also look for the same prefix pattern,
# and remove that if present on all lines.
re_sloppy_plugin = re.compile(r'^(?:(?:DBG:\s+)?[_\*]\d\d\d[_\*]\s+|GameFile\d+=|content=|\d{1,3} {1,2}|Plugin\d+\s*=\s*)?(.+\.es[mp]\b)', re.IGNORECASE)
# pattern used to match a string that should only contain a plugin name, no slop
re_plugin = re.compile(r'^(\S.*?\.es[mp]\b)([\s]*)', re.IGNORECASE)
# set of characters that are not allowed to occur in plugin names.
# (we allow '*' and '?' for filename matching).
re_plugin_illegal = re.compile(r'[\"\\/=+<>:;|\^]')
# metacharacters for filename expansion
re_plugin_meta = re.compile(r'([*?])')
re_plugin_metaver = re.compile(r'(<VER>)', re.IGNORECASE)
re_escape_meta = re.compile(r'([()+.])')
# for recognizing our functions:
re_fun = re.compile(r'^\[(ALL|ANY|NOT|DESC|VER|SIZE)\s*', re.IGNORECASE)
re_end_fun = re.compile(r'^\]\s*')
re_desc_fun = re.compile(r'\[DESC\s*(!?)/([^/]+)/\s+([^\]]+)\]', re.IGNORECASE)
# for parsing a size predicate
re_size_fun = re.compile(r'\[SIZE\s*(!?)(\d+)\s+(\S.*?\.es[mp]\b)\s*\]', re.IGNORECASE)
# for parsing a version number
ver_delim = r'[_.-]'
re_ver_delim = re.compile(ver_delim)
plugin_version = r'(\d+(?:%s?\d+)*[a-zA-Z]?)' % ver_delim
re_alpha_tail = re.compile(r'(\d+)([a-z])', re.IGNORECASE)
re_ver_fun = re.compile(r'\[VER\s*([=<>])\s*%s\s*([^\]]+)\]' % plugin_version, re.IGNORECASE)
# for grabbing version numbers from filenames
re_filename_version = re.compile(r'\D%s\D*\.es[mp]' % plugin_version, re.IGNORECASE)
# for grabbing version numbers from plugin header description fields
re_header_version = re.compile(r'\b(?:version\b\D+|v(?:er)?\.?\s*)%s' % plugin_version, re.IGNORECASE)

# for cleaning up pretty printer
re_notstr = re.compile(r"\s*'NOT',")
re_anystr = re.compile(r"\s*'ANY',")
re_allstr = re.compile(r"\s*'ALL',")
re_indented = re.compile(r'^', re.MULTILINE)

version_operators = {'=': True, '<': True, '>': True}

full_version = ""
clip_file = "mlox_clipboard.out"
old_loadorder_output = "current_loadorder.out"
new_loadorder_output = "mlox_new_loadorder.out"
debug_output = "mlox_debug.out"
tes3_min_plugin_size = 362

class logger:
    def __init__(self, prints, *cohort):
        self.log = []
        self.prints = prints
        self.cohort = cohort

    def add(self, message):
        self.log.append(message)
        for c in self.cohort:
            c.add(message)
        if self.prints and Opt.GUI == False:
            print message

    def insert(self, message):
        self.log.insert(0, message)
        for c in self.cohort:
            c.insert(message)
        if self.prints and Opt.GUI == False:
            print message

    def get(self):
        return("\n".join(map(unify, self.log)) + "\n")

    def get_u(self):
        return("\n".join(self.log) + "\n")

    def flush(self):
        self.log = []

class debug_logger(logger):
    def __init__(self):
        logger.__init__(self, False)

    def add(self, message):
        if Opt.DBG:
            msg = "DBG: " + message
            if Opt.GUI:
                self.log.append(msg)
            else:
                print >> sys.stderr, msg

class parse_debug_logger(logger):
    def __init__(self):
        logger.__init__(self, False)

    def add(self, message):
        msg = "DBG: " + message
        if Opt.GUI:
            self.log.append(msg)
        else:
            print >> sys.stderr, msg

ParseDbg = parse_debug_logger() # debug output for parser
Dbg = debug_logger()            # debug output
New = logger(True, Dbg)         # new sorted loadorder
Old = logger(False)             # old original loadorder
Stats = logger(True, Dbg)       # stats output
Msg = logger(True, Dbg)         # messages output

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

C = caseless_filenames()

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


# Utility functions
Lang = locale.getdefaultlocale()[0]
Lang = "en" if Lang == None or len(Lang) < 2 else Lang[0:2]
Encoding = locale.getpreferredencoding()

class dyndict(dict):
    """if item is in dict, return value, otherwise return item. for soft failure when looking up translations."""
    def __getitem__(self, item):
        return(super(dyndict, self).__getitem__(item) if item in self else item)
def load_translations(lang):
    """double-de-bungify the translation dictionary."""
    def splitter(x):
        s = x.split("]]")
        (key, val) = (s[0] if len(s) > 0 else "", s[1] if len(s) > 1 else "")
        trans = dict(map(lambda y: y.split('`'), val.split("\n`"))[1:])
        return(key, trans[lang].rstrip() if lang in trans else key)
    return(dyndict(map(splitter, codecs.open("mlox.msg", 'r', "utf-8").read().split("\n[["))[1:]))

_ = load_translations(Lang)


def unify(s):
    """For GUI text areas that may contain filenames, we guess at the encoding."""
    #using melchor's workaround:
    return(s.decode("ascii", "replace").encode("ascii", "replace"))

def format_version(ver):
    """convert something we think is a version number into a canonical form that can be used for comparison"""
    v = re_ver_delim.split(ver, 3)
    match = re_alpha_tail.match(v[-1])
    alpha = "_"
    if match:
        v[-1] = match.group(1)
        alpha = match.group(2)
    for i in range(0, len(v)):
        v[i] = int(v[i])
    while len(v) < 3:
        v.append(0)
    return("%05d.%05d.%05d.%s" % (v[0], v[1], v[2], alpha))

def loadup_msg(msg, count, what):
    Stats.add("%-50s (%3d %s)" % (msg, count, what))

def myopen_file(filename, mode, encoding=None):
    try:
        return(codecs.open(filename, mode, encoding))
    except IOError, (errno, strerror):
        if Opt.DBG:
            mode_str = _["input"] if mode == 'r' else _["output"]
            Dbg.add(_["Error opening \"%s\" for %s (%s)"] % (filename, mode_str, strerror))
    return(None)

def plugin_description(plugin):
    """Read the description field of a TES3/TES4 plugin file header"""
    inp = myopen_file(plugin, 'rb')
    if inp == None: return("")
    block = inp.read(4096)
    inp.close()
    if block[0:4] == "TES3":    # Morrowind
        if len(block) < tes3_min_plugin_size:
            Dbg.add("plugin_description(%s): file too short, returning NULL string" % plugin)
            return("")
        desc = block[64:block.find("\x00", 64)]
        return(desc)
    elif block[0:4] == "TES4":  # Oblivion
        # This is very cheesy.
        pos = block.find("SNAM", 0)
        if pos == -1: return("")
        desc_start = block.find("\x00", pos) + 1
        if desc_start == -1: return("")
        desc_end = block.find("\x00", desc_start)
        if desc_end == -1: return("")
        desc = block[desc_start:desc_end]
        return(desc)
    else:
        return("")

def find_appdata():
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

# given a list of files, return a new list without dups (caseless), plus a list of any dups
def filter_dup_files(files):
    tmpfiles = []               # new list
    filtered = []               # any filtered dups from original list
    seen = {}
    for f in files:
        c = C.cname(f)
        if c in seen:
            filtered.append(f)
        else:
            tmpfiles.append(f)
        seen[c] = True
    return(tmpfiles, filtered)

class rule_parser:
    """A simple recursive descent rule parser, for evaluating rule statements containing nested boolean expressions."""
    def __init__(self, active, graph, datadir):
        self.active = active
        self.graph = graph
        self.datadir = datadir
        self.line_num = 0
        self.rule_file = None
        self.bytesread = 0
        self.input_handle = None
        self.buffer = ""        # the parsing buffer
        self.message = []       # the comment for the current rule
        self.curr_rule = ""     # name of the current rule we are parsing
        self.parse_dbg_indent = ""

    def pdbg(self, msg):
        ParseDbg.add(self.parse_dbg_indent + msg)

    def readline(self):
        """reads a line into the current parsing buffer"""
        if self.input_handle == None:
            return(False)
        try:
            while True:
                line = self.input_handle.next()
                self.bytesread += len(line)
                self.line_num += 1
                line = re_comment.sub('', line) # remove comments
                line = line.rstrip() # strip whitespace from end of line, include CRLF
                if line != "":
                    self.buffer = line
                    if Opt.ParseDBG: self.pdbg("readline returns: %s" % line)
                    return(True)
        except StopIteration:
            if Opt.ParseDBG: self.pdbg("EOF")
            self.buffer = ""
            self.input_handle.close()
            self.input_handle = None
            return(False)

    def where(self):
        return("%s:%d" % (self.rule_file, self.line_num))

    def parse_error(self, what):
        """print a message about current parsing error, and blow away the
        current parse buffer so next parse starts on next input line."""
        Msg.add(_["%s: Parse Error(%s), %s [Buffer=%s]"] % (self.where(), self.curr_rule, what, self.buffer))
        self.buffer = ""
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]

    def parse_message_block(self):
        while self.readline():
            if re_message.match(self.buffer):
                self.message.append(self.buffer)
            else:
                return

    def expand_filename(self, plugin):
        if Opt.ParseDBG: self.pdbg("expand_filename, plugin=%s" % plugin)
        pat = "^%s$" % re_escape_meta.sub(r'\\\1', plugin)
        # if the plugin name contains metacharacters, do filename expansion
        subbed = False
        if re_plugin_meta.search(plugin) != None:
            if Opt.ParseDBG: self.pdbg("expand_filename name has META: %s" % pat)
            pat = re_plugin_meta.sub(r'.\1', pat)
            subbed = True
        if re_plugin_metaver.search(plugin) != None:
            if Opt.ParseDBG: self.pdbg("expand_filename name has METAVER: %s" % pat)
            pat = re_plugin_metaver.sub(plugin_version, pat)
            subbed = True
        if not subbed:        # no expansions made
            return([plugin] if plugin.lower() in self.active else [])
        if Opt.ParseDBG: self.pdbg("expand_filename new RE pat: %s" % pat)
        matches = []
        re_namepat = re.compile(pat, re.IGNORECASE)
        for p in self.active:
            if re_namepat.match(p):
                matches.append(p)
                if Opt.ParseDBG: self.pdbg("expand_filename: %s expands to: %s" % (plugin, p))
        return(matches)
                
    def parse_plugin_name(self):
        self.parse_dbg_indent += "  "
        buff = self.buffer.strip()
        if Opt.ParseDBG: self.pdbg("parse_plugin_name buff=%s" % buff)
        plugin_match = re_plugin.match(buff)
        if plugin_match:
            plugin_name = C.cname(plugin_match.group(1))
            if Opt.ParseDBG: self.pdbg("parse_plugin_name name=%s" % plugin_name)
            pos = plugin_match.span(2)[1]
            self.buffer = buff[pos:].lstrip()
            matches = self.expand_filename(plugin_name)
            if matches != []:
                plugin_name = matches.pop(0)
                if Opt.ParseDBG: self.pdbg("parse_plugin_name new name=%s" % plugin_name)
                if len(matches) > 0:
                    self.buffer = " ".join(matches) + " " + self.buffer
                return(True, plugin_name)
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, plugin_name)
        else:
            self.parse_error(_["expected a plugin name"])
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(None, None)

    def parse_ordering(self, rule):
        self.parse_dbg_indent += "  "
        prev = None
        n_order = 0
        while self.readline():
            if re_rule.match(self.buffer):
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            p = self.parse_plugin_name()[1]
            if p == None:
                continue
            n_order += 1
            if rule == "ORDER":
                if prev != None:
                    self.graph.add_edge(self.where(), prev, p)
                prev = p
            elif rule == "NEARSTART":
                self.graph.nearstart.append(p)
                self.graph.nodes.setdefault(p, [])
            elif rule == "NEAREND":
                self.graph.nearend.append(p)
                self.graph.nodes.setdefault(p, [])
        if rule == "ORDER":
            if n_order == 0:
                Msg.add(_["Warning: %s: ORDER rule has no entries"] % (self.where()))
            elif n_order == 1:
                Msg.add(_["Warning: %s: ORDER rule skipped because it only has one entry: %s"] % (self.where(), C.truename(prev)))

    def parse_ver(self):
        self.parse_dbg_indent += "  "
        match = re_ver_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            if Opt.ParseDBG: self.pdbg("parse_ver new buffer = %s" % self.buffer)
            op = match.group(1)
            if op not in version_operators:
                self.parse_error(_["Invalid [VER] operator"])
                return(None, None)
            orig_ver = match.group(2)
            ver = format_version(orig_ver)
            plugin_name = match.group(3)
            expanded = self.expand_filename(plugin_name)
            expr = "[VER %s %s %s]" % (op, orig_ver, plugin_name)
            if Opt.ParseDBG: self.pdbg("parse_ver, expr=%s ver=%s" % (expr, ver))
            if len(expanded) == 1:
                expr = "[VER %s %s %s]" % (op, orig_ver, expanded[0])
            elif expanded == []:
                if Opt.ParseDBG: self.pdbg("parse_ver [VER] \"%s\" not active" % plugin_name)
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if Opt.FromFile:
                # this case is reached when doing fromfile checks
                # and we do not have the actual plugin to check, so
                # we assume that the plugin matches the given version
                if op == '=':
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, expr)
                else:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(False, expr)
            for xp in expanded:
                plugin = C.cname(xp)
                plugin_t = C.truename(plugin)
                desc = plugin_description(self.datadir.find_path(plugin))
                match = re_header_version.search(desc)
                if match:
                    p_ver_orig = match.group(1)
                    p_ver = format_version(p_ver_orig)
                    if Opt.ParseDBG: self.pdbg("parse_ver (header) version(%s) = %s (%s)" % (plugin_t, p_ver_orig, p_ver))
                else:
                    match = re_filename_version.search(plugin)
                    if match:
                        p_ver_orig = match.group(1)
                        p_ver = format_version(p_ver_orig)
                        if Opt.ParseDBG: self.pdbg("parse_ver (filename) version(%s) = %s (%s)" % (plugin_t, p_ver_orig, p_ver))
                    else:
                        if Opt.ParseDBG: self.pdbg("parse_ver no version for %s" % plugin_t)
                        return(False, expr)
                if Opt.ParseDBG: self.pdbg("parse_ver compare  p_ver=%s %s ver=%s" % (p_ver, op, ver))
                result = True
                if op == '=':
                    result = (p_ver == ver)
                elif op == '<':
                    result = (p_ver < ver)
                elif op == '>':
                    result = (p_ver > ver)
                if result:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[VER %s %s %s]" % (op, orig_ver, plugin))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error(_["Invalid [VER] function"])
        return(None, None)

    def parse_desc(self):
        """match patterns against the description string in the plugin header."""
        self.parse_dbg_indent += "  "
        match = re_desc_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            if Opt.ParseDBG: self.pdbg("parse_desc new buffer = %s" % self.buffer)
            bang = match.group(1) # means to invert the meaning of the match
            pat = match.group(2)
            plugin_name = match.group(3)
            expr = "[DESC %s/%s/ %s]" % (bang, pat, plugin_name)
            if Opt.ParseDBG: self.pdbg("parse_desc, expr=%s" % expr)
            expanded = self.expand_filename(plugin_name)
            if len(expanded) == 1:
                expr = "[DESC %s/%s/ %s]" % (bang, pat, expanded[0])
            elif expanded == []:
                if Opt.ParseDBG: self.pdbg("parse_desc [DESC] \"%s\" not active" % plugin_name)
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if Opt.FromFile:
                # this case is reached when doing fromfile checks,
                # which do not have access to the actual plugin, so we
                # always assume the test is merely for file existence,
                # to err on the side of caution
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(True, expr)
            for xp in expanded:
                plugin = C.cname(xp)
                plugin_t = C.truename(plugin)
                re_pat = re.compile(pat)
                desc = plugin_description(self.datadir.find_path(plugin))
                bool = (re_pat.search(desc) != None)
                if bang == "!": bool = not bool
                if Opt.ParseDBG: self.pdbg("parse_desc [DESC] returning: (%s, %s)" % (bool, expr))
                if bool:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[DESC %s/%s/ %s]" % (bang, pat, plugin_t))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error(_["Invalid [DESC] function"])
        return(None, None)

    def parse_size(self):
        """check the given size of the plugin."""
        self.parse_dbg_indent += "  "
        match = re_size_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            if Opt.ParseDBG: self.pdbg("parse_size new buffer = %s" % self.buffer)
            bang = match.group(1) # means "is not this size"
            wanted_size = int(match.group(2))
            plugin_name = match.group(3)
            expr = "[SIZE %s%d %s]" % (bang, wanted_size, plugin_name)
            if Opt.ParseDBG: self.pdbg("parse_size, expr=%s" % expr)
            expanded = self.expand_filename(plugin_name)
            if len(expanded) == 1:
                expr = "[SIZE %s%d %s]" % (bang, wanted_size, expanded[0])
            elif expanded == []:
                if Opt.ParseDBG: self.pdbg("parse_size [SIZE] \"%s\" not active" % match.group(3))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if Opt.FromFile:
                # this case is reached when doing fromfile checks,
                # which do not have access to the actual plugin, so we
                # always assume the test is merely for file existence,
                # to err on the side of caution
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(True, expr)
            for xp in expanded:
                plugin = C.cname(xp)
                plugin_t = C.truename(plugin)
                actual_size = os.path.getsize(self.datadir.find_path(plugin))
                bool = (actual_size == wanted_size)
                if bang == "!": bool = not bool
                if Opt.ParseDBG: self.pdbg("parse_size [SIZE] returning: (%s, %s)" % (bool, expr))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                if bool:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[SIZE %s%d %s]" % (bang, wanted_size, plugin_t))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error(_["Invalid [SIZE] function"])
        return(None, None)

    def parse_expression(self, prune=False):
        self.parse_dbg_indent += "  "
        self.buffer = self.buffer.strip()
        if self.buffer == "":
            if self.readline():
                if re_rule.match(self.buffer):
                    if Opt.ParseDBG: self.pdbg("parse_expression new line started new rule, returning None")
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(None, None)
                self.buffer = self.buffer.strip()
            else:
                if Opt.ParseDBG: self.pdbg("parse_expression EOF, returning None")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(None, None)
        if Opt.ParseDBG: self.pdbg("parse_expression, start buffer: \"%s\"" % self.buffer)
        match = re_fun.match(self.buffer)
        if match:
            fun = match.group(1).upper()
            if fun == "DESC":
                if Opt.ParseDBG: self.pdbg("parse_expression calling parse_desc()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_desc())
            elif fun == "VER":
                if Opt.ParseDBG: self.pdbg("parse_expression calling parse_ver()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_ver())
            elif fun == "SIZE":
                if Opt.ParseDBG: self.pdbg("parse_expression calling parse_size()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_size())
            # otherwise it's a boolean function ...
            if Opt.ParseDBG: self.pdbg("parse_expression parsing expression: \"%s\"" % self.buffer)
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            if Opt.ParseDBG: self.pdbg("fun = %s" % fun)
            vals = []
            exprs = []
            bool_end = re_end_fun.match(self.buffer)
            if Opt.ParseDBG: self.pdbg("self.buffer 1 =\"%s\"" % self.buffer)
            while not bool_end:
                (bool, expr) = self.parse_expression(prune)
                if bool == None:
                    self.parse_error(_["[%s] Invalid boolean arguments"] % fun)
                    return(None, None)
                exprs.append(expr)
                vals.append(bool)
                if Opt.ParseDBG: self.pdbg("self.buffer 2 =\"%s\"" % self.buffer)
                bool_end = re_end_fun.match(self.buffer)
            pos = bool_end.span(0)[1]
            self.buffer = self.buffer[pos:]
            if Opt.ParseDBG: self.pdbg("self.buffer 3 =\"%s\"" % self.buffer)
            if fun == "ALL":
                # prune out uninteresting expressions from ANY results
                exprs = [e for e in exprs if not(isinstance(e, list) and e == [])]
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(all(vals), exprs[0] if len(exprs) == 1 else ["ALL"] + exprs)
            if fun == "ANY":
                # prune out uninteresting expressions from ANY results
                if prune:
                    exprs = [e for e in exprs if not(isinstance(e, str) and e[0:8] == "MISSING(")]
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(any(vals), exprs[0] if len(exprs) == 1 else ["ANY"] + exprs)
            if fun == "NOT":
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(not(all(vals)), ["NOT"] + exprs)
            else:
                # should not be reached due to match on re_fun
                self.parse_error(_["Expected Boolean function (ALL, ANY, NOT)"])
                return(None, None)
            if Opt.ParseDBG: self.pdbg("parse_expression NOTREACHED")
        else:
            if re_fun.match(self.buffer):
                self.parse_error(_["Invalid function expression"])
                return(None, None)
            if Opt.ParseDBG: self.pdbg("parse_expression parsing plugin: \"%s\"" % self.buffer)
            (exists, p) = self.parse_plugin_name()
            if exists != None and p != None:
                p = C.truename(p) if exists else ("MISSING(%s)" % C.truename(p))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(exists, p)
        if Opt.ParseDBG: self.pdbg("parse_expression NOTREACHED(2)")

    def pprint(self, expr, prefix):
        """pretty printer for parsed expressions"""
        formatted = PrettyPrinter(indent=2).pformat(expr)
        formatted = re_notstr.sub("NOT", formatted)
        formatted = re_anystr.sub("ANY", formatted)
        formatted = re_allstr.sub("ALL", formatted)
        return(re_indented.sub(prefix, formatted))

    def parse_statement(self, rule, msg, expr):
        self.parse_dbg_indent += "  "
        if Opt.ParseDBG: self.pdbg("parse_statement(%s, %s, %s)" % (rule, msg, expr))
        expr = expr.strip()
        if msg == "":
            if expr == "":
                self.parse_message_block()
                expr = self.buffer
        else:
            self.message = [msg]
        if expr == "":
            if not self.readline():
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
        else:
            self.buffer = expr
        msg = "" if self.message == [] else " |" + "\n |".join(self.message) # no ending LF
        if rule == "CONFLICT":  # takes any number of exprs
            exprs = []
            if Opt.ParseDBG: self.pdbg("before conflict parse_expr() expr=%s line=%s" % (expr, self.buffer))
            (bool, expr) = self.parse_expression()
            if Opt.ParseDBG: self.pdbg("conflict parse_expr()1 bool=%s bool=%s" % (bool, expr))
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression()
                if Opt.ParseDBG: self.pdbg("conflict parse_expr()N bool=%s bool=%s" % ("True" if bool else "False", expr))
            if len(exprs) > 1:
                Msg.add("[CONFLICT]")
                for e in exprs:
                    Msg.add(self.pprint(e, " > "))
                if msg != "": Msg.add(msg)
        elif rule == "NOTE":    # takes any number of exprs
            if Opt.ParseDBG: self.pdbg("function NOTE: %s" % msg)
            exprs = []
            (bool, expr) = self.parse_expression(prune=True)
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression(prune=True)
            if not Opt.Quiet and len(exprs) > 0:
                Msg.add("[NOTE]")
                for e in exprs:
                    Msg.add(self.pprint(e, " > "))
                if msg != "": Msg.add(msg)
        elif rule == "PATCH":   # takes 2 exprs
            (bool1, expr1) = self.parse_expression()
            if bool1 == None:
                Msg.add(_["Warning: %s: PATCH rule invalid first expression"] % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                Msg.add(_["Warning: %s: PATCH rule invalid second expression"] % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            if bool1 and not bool2:
                # case where the patch is present but the thing to be patched is missing
                Msg.add(_["[PATCH]\n%s is missing some pre-requisites:\n%s"] %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": Msg.add(msg)
            if bool2 and not bool1:
                # case where the patch is missing for the thing to be patched
                Msg.add(_["[PATCH]\n%s for:\n%s"] %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": Msg.add(msg)
        elif rule == "REQUIRES": # takes 2 exprs
            (bool1, expr1) = self.parse_expression(prune=True)
            if bool1 == None:
                Msg.add(_["Warning: %s: REQUIRES rule invalid first expression"] % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                Msg.add(_["Warning: %s: REQUIRES rule invalid second expression"] % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            if bool1 and not bool2:
                expr2_str = self.pprint(expr2, " > ")
                Msg.add(_["[REQUIRES]\n%s Requires:\n%s"] %
                        (self.pprint(expr1, " !!!"), expr2_str))
                if msg != "": Msg.add(msg)
                match = re_filename_version.search(expr2_str)
                if match:
                    Msg.add(_[" | [Note that you may see this message if you have an older version of one\n | of the pre-requisites. In that case, it is suggested that you upgrade\n | to the newer version]."])
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        if Opt.ParseDBG: self.pdbg("parse_statement RETURNING")

    def read_rules(self, rule_file, progress):
        """Read rules from rule files (e.g., mlox_user.txt or mlox_base.txt),
        add order rules to graph, and print warnings."""
        n_rules = 0
        self.rule_file = rule_file

        inputsize = 0
        try:
            inputsize = os.path.getsize(rule_file)
        except: 
            pass
        pmsg = "Loading: %s" % rule_file

        if Opt.ParseDBG: self.pdbg("READING RULES FROM: \"%s\"" % self.rule_file)
        self.input_handle = myopen_file(self.rule_file, 'r')
        if self.input_handle == None:
            return False
        self.line_num = 0
        while True:
            if self.buffer == "":
                if not self.readline():
                    break
            if progress != None:
                pct = int(100*self.bytesread/inputsize)
                if pct % 3 == 0 and pct < 100:
                    progress.Update(pct, pmsg)
            self.parse_dbg_indent = ""
            self.curr_rule = ""
            new_rule = re_rule.match(self.buffer)
            if new_rule:        # start a new rule
                n_rules += 1
                self.curr_rule = new_rule.group(1).upper()
                self.message = []
                if self.curr_rule == "VERSION":
                    self.buffer = ""
                elif self.curr_rule in ("ORDER", "NEAREND", "NEARSTART"):
                    self.parse_ordering(self.curr_rule)
                elif self.curr_rule in ("CONFLICT", "NOTE", "PATCH", "REQUIRES"):
                    self.parse_statement(self.curr_rule, new_rule.group(2), new_rule.group(3))
                else:
                    # we should never reach here, since re_rule only matches known rules
                    self.parse_error(_["read_rules failed sanity check, unknown rule"])
            else:
                self.parse_error(_["expected start of rule"])
        loadup_msg(_["Read rules from: \"%s\""] % self.rule_file, n_rules, "rules")
        return True


class pluggraph:
    """A graph structure built from ordering rules which specify plugin load (partial) order"""
    def __init__(self):
        # nodes is a dictionary of lists, where each key is a plugin, and each
        # value is a list of the children of that plugin in the graph
        # that is, if we have "foo.esp" -> "bar.esp" and "foo.esp" -> "baz.esp"
        # where "->" is read "is a parent of" and means "preceeds in load order"
        # the data structure will contain: {"foo.esp": ["bar.esp", "baz.esp"]}
        self.nodes = {}
        # incoming_count is a dictionary of that keeps track of the count of
        # how many incoming edges a plugin node in the graph has.
        # incoming_count["bar.esp"] == 1 means that bar.esp only has one parent
        # incoming_count["foo.esp"] == 0 means that foo.esp is a root node
        self.incoming_count = {}
        # nodes (plugins) that should be pulled nearest to top of load order,
        # if possible.
        self.nearstart = []
        # nodes (plugins) that should be pushed nearest to bottom of load order,
        # if possible.
        self.nearend = []

    def can_reach(self, startnode, plugin):
        """Return True if startnode can reach plugin in the graph, False otherwise."""
        stack = [startnode]
        seen = {}
        while stack != []:
            p = stack.pop()
            if p == plugin:
                return(True)
            seen[p] = True
            if p in self.nodes:
                stack.extend([child for child in self.nodes[p] if not child in seen])
        return(False)

    def add_edge(self, where, plug1, plug2):
        """Add an edge to our graph connecting plug1 to plug2, which means
        that plug2 follows plug1 in the load order. Since we check every new
        edge to see if it will make a cycle, the process of adding all edges
        will be O(square(n)/2) in the worst case of a totally ordered
        set. This could mean a long run-time for the Oblivion data, which
        is currently a total order of a set of about 5000 plugins."""
        # before adding edge from plug1 to plug2 (meaning plug1 is parent of plug2),
        # we look to see if plug2 is already a parent of plug1, if so, we have
        # detected a cycle, which we disallow.
        if self.can_reach(plug2, plug1):
            # (where == "") when adding edges from psuedo-rules we
            # create from our current plugin list, We ignore cycles in
            # this case because they do not matter.
            # (where != "") when it is an edge from a rules file, and in
            # that case we do want to see cycle errors.
            cycle_detected = _["Warning: %s: Cycle detected, not adding: \"%s\" -> \"%s\""] % (where, C.truename(plug1), C.truename(plug2))
            if where == "":
                Dbg.add(cycle_detected)
            else:
                Msg.add(cycle_detected)
            return False
        self.nodes.setdefault(plug1, [])
        if plug2 in self.nodes[plug1]: # edge already exists
            Dbg.add("%s: Dup Edge: \"%s\" -> \"%s\"" % (where, C.truename(plug1), C.truename(plug2)))
            return True
        # add plug2 to the graph as a child of plug1
        self.nodes[plug1].append(plug2)
        self.incoming_count[plug2] = self.incoming_count.setdefault(plug2, 0) + 1
        Dbg.add("adding edge: %s -> %s" % (plug1, plug2))
        return(True)

    def explain(self, what, active):
        seen = {}
        print _["Ordering_Explanation"] % what
        print what
        def explain_rec(indent, n):
            if n in seen:
                return
            seen[n] = True
            if n in self.nodes:
                for child in self.nodes[n]:
                    prefix = indent.replace(" ", "+") if child in active else indent.replace(" ", "=")
                    print "%s%s" % (prefix, C.truename(child))
                    explain_rec(" " + indent, child)
        explain_rec(" ", what.lower())

    def topo_sort(self):
        """topological sort"""

        def remove_roots(roots, which):
            """This function is used to yank roots out of the main list of graph roots to
            support the NearStart and NearEnd rules."""
            removed = []
            for p in which:
                leftover = []
                while len(roots) > 0:
                    r = roots.pop(0)
                    if self.can_reach(r, p):
                        removed.append(r)
                    else:
                        leftover.append(r)
                roots = leftover
            return(removed, roots)

        # find the roots of the graph
        roots = [node for node in self.nodes if self.incoming_count.get(node, 0) == 0]
        if Opt.DBG:
            Dbg.add("\n========== BEGIN TOPOLOGICAL SORT DEBUG INFO ==========")
            Dbg.add("graph before sort (node: children)")
            Dbg.add(PrettyPrinter(indent=4).pformat(self.nodes))
            Dbg.add("\nDBG: roots:\n  %s" % ("\n  ".join(roots)))
        if len(roots) > 0:
            # use the nearstart information to pull preferred plugins to top of load order
            (top_roots, roots) = remove_roots(roots, self.nearstart)
            bottom_roots = roots        # any leftovers go at the end
            roots = top_roots + bottom_roots
            if Opt.DBG:
                Dbg.add("nearstart:\n  %s" % ("\n  ".join(self.nearstart)))
                Dbg.add("top roots:\n  %s" % ("\n  ".join(top_roots)))
                Dbg.add("nearend:\n  %s" % ("\n  ".join(self.nearend)))
                Dbg.add("bottom roots:\n  %s" % ("\n  ".join(bottom_roots)))
                Dbg.add("newroots:\n  %s" % ("\n  ".join(roots)))
        Dbg.add("========== END TOPOLOGICAL SORT DEBUG INFO ==========\n")
        # now do the actual topological sort
        # based on http://www.bitformation.com/art/python_toposort.html
        roots.reverse()
        sorted = []
        while len(roots) != 0:
            root = roots.pop()
            sorted.append(root)
            if not root in self.nodes:
                continue
            for child in self.nodes[root]:
                self.incoming_count[child] -= 1
                if self.incoming_count[child] == 0:
                    roots.append(child)
            del self.nodes[root]
        if len(self.nodes.items()) != 0:
            Msg.add(_["Error: Topological Sort Failed!"])
            Dbg.add(PrettyPrinter(indent=4).pformat(self.nodes.items()))
            return None
        return sorted


class loadorder:
    """Class for reading plugin mod times (load order), and updating them based on rules"""
    def __init__(self):
        # order is the list of plugins in Data Files, ordered by mtime
        self.active = {}                   # current active plugins
        self.order = []                    # the load order
        self.gamedir = None                # where game is installed
        self.datadir = None                # where plugins live
        self.graph = pluggraph()
        self.sorted = False
        self.origin = None      # where plugins came from (active, installed, file)

    def sort_by_date(self, plugin_files):
        """Sort input list of plugin files by modification date."""
        dated_plugins = [[os.path.getmtime(self.datadir.find_path(file)), file] for file in plugin_files]
        dated_plugins.sort()
        return([x[1] for x in dated_plugins])

    def partition_esps_and_esms(self, filelist):
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

    def find_game_dirs(self):
        cwd = caseless_dirlist() # start our search in our current directory
        self.gamedir = cwd.find_parent_dir("Morrowind.ini")
        if self.gamedir != None:
            Opt._Game = "Morrowind"
            self.datadir = caseless_dirlist(self.gamedir.find_path("Data Files"))
        else:
            self.gamedir = cwd.find_parent_dir("Oblivion.ini")
            if self.gamedir != None:
                Opt._Game = "Oblivion"
                self.datadir = caseless_dirlist(self.gamedir.find_path("Data"))
            else:
                # Not running under a game directory, so we're probably testing
                # assume plugins live in current directory.
                Opt._Game = "None"
                self.datadir = cwd
                self.gamedir = caseless_dirlist("..")
        Dbg.add("Data directory: \"%s\"" % self.datadir.dirpath())
        #Stats.add("Data Directory: \"%s\"" % self.datadir.dirpath())

    def get_active_plugins(self):
        """Get the active list of plugins from the game configuration. Updates
        self.active and self.order and sorts in load order."""
        files = []
        # we look for the list of currently active plugins
        if Opt._Game == "Morrowind":
            source = "Morrowind.ini"
            # find Morrowind.ini for Morrowind
            ini_path = self.gamedir.find_path(source)
            if ini_path == None:
                Msg.add(_["[%s not found, assuming running outside Morrowind directory]"] % source)
                return
            ini = myopen_file(ini_path, 'r')
            if ini == None:
                return
            for line in ini:
                line.strip()
                line.strip('\r\n')
                gamefile = re_gamefile.match(line)
                if gamefile:
                    # we use caseless_dirlist.find_file(), so that the
                    # stored name of the plugin does not have to
                    # match the actual capitalization of the
                    # plugin name
                    f = self.datadir.find_file(gamefile.group(1).strip())
                    # f will be None if the file has been removed from
                    # Data Files but still exists in the Morrowind.ini
                    # [Game Files] section
                    if f != None:
                        files.append(f)
            ini.close()
        elif Opt._Game == "Oblivion":
            source = "Oblivion/Plugins.txt"
            appdata = find_appdata()
            if appdata == None:
                Dbg.add("Application data directory not found")
                return
            plugins_txt_path = os.path.join(appdata, "Oblivion", "Plugins.txt")
            Msg.add("plugins.txt = %s" % plugins_txt_path)
            inp = myopen_file(plugins_txt_path, 'r')
            if inp == None:
                Msg.add("Plugins.txt not found")
                return
            for line in inp:
                line.strip()
                plugin = re_plugin.match(line)
                if plugin:
                    f = self.datadir.find_file(plugin.group(1))
                    if f != None:
                        files.append(f)
            inp.close()
        else:
            # not running under a game directory (e.g.: doing testing)
            return
        (files, dups) = filter_dup_files(files)
        for f in dups:
            Dbg.add("get_active_plugins: dup plugin: %s" % f)
        (esm_files, esp_files) = self.partition_esps_and_esms(files)
        # sort the plugins into load order by modification date
        plugins = [C.cname(f) for f in self.sort_by_date(esm_files) + self.sort_by_date(esp_files)]
        loadup_msg(_["Getting active plugins from: \"%s\""] % source, len(plugins), "plugins")
        self.order = plugins
        for p in self.order:
            self.active[p] = True
        self.origin = _["Active Plugins"]

    def get_data_files(self):
        """Get the list of plugins from the data files directory. Updates self.active.
        If called,"""
        files = [f for f in self.datadir.filelist() if os.path.isfile(self.datadir.find_path(f))]
        (files, dups) = filter_dup_files(files)
        for f in dups:
            Dbg.add("get_data_files: dup plugin: %s" % f)
        (esm_files, esp_files) = self.partition_esps_and_esms(files)
        # sort the plugins into load order by modification date
        self.order = [C.cname(f) for f in self.sort_by_date(esm_files) + self.sort_by_date(esp_files)]
        loadup_msg(_["Getting list of plugins from plugin directory"], len(self.order), "plugins")
        for p in self.order:
            self.active[p] = True
        self.origin = _["Installed Plugins"]

    def listversions(self):
        self.find_game_dirs()
        self.get_data_files()
        for p in self.order:
            match = re_filename_version.search(p)
            file_ver = match.group(1) if match else None
            desc = plugin_description(self.datadir.find_path(p))
            if desc == None:
                desc == ""
            match = re_header_version.search(desc)
            desc_ver = match.group(1) if match else None
            print "%10s %10s    %s" % (file_ver, desc_ver, C.truename(p))
        if Opt.DBG: print Dbg.get()

    def read_from_file(self, fromfile):
        """Get the load order by reading an input file. This is mostly to help
        others debug their load order."""
        file = myopen_file(fromfile, 'r')
        if file == None:
            Dbg.add("Failed to open input file: %s" % fromfile)
            return
        files = []
        for line in file:
            plugin_match = re_sloppy_plugin.match(line)
            if plugin_match:
                p = plugin_match.group(1)
                cname = C.cname(p)
                files.append(cname)
        (self.order, dups) = filter_dup_files(files)
        for f in dups:
            Dbg.add("read_from_file: dup plugin: %s" % f)
        Stats.add("%-50s (%3d plugins)" % (_["Reading plugins from file: \"%s\""] % fromfile, len(self.order)))
        for p in self.order:
            self.active[p] = True
        self.origin = "Plugin List from %s" % os.path.basename(fromfile)

    def add_current_order(self):
        """We treat the current load order as a sort of preferred order in
        the case where there are no rules. However, we have to be careful
        when there exists a [NEARSTART] or [NEAREND] rule for a plugin,
        that we do not introduce a new edge, we only add the node itself.
        This allows us to move unconnected nodes to the top or bottom of
        the roots calculated in the topo_sort routine, depending on
        whether they show up in [NEARSTART] or [NEAREND] rules,
        respectively"""
        if len(self.order) < 2:
            return
        Dbg.add("adding edges from CURRENT ORDER")
        # make ordering pseudo-rules for esms to follow official .esms
        if Opt._Game == "Morrowind":
            self.graph.add_edge("", "morrowind.esm", "tribunal.esm")
            self.graph.add_edge("", "tribunal.esm", "bloodmoon.esm")
            for p in self.active: # foreach of the user's .esms
                if p[-4:] == ".esm":
                    if p not in ("morrowind.esm", "tribunal.esm", "bloodmoon.esm"):
                        self.graph.add_edge("", "bloodmoon.esm", p)
        # make ordering pseudo-rules from nearend info
        kingyo_fun = [x for x in self.graph.nearend if x in self.active]
        for p_end in kingyo_fun:
            for p in [x for x in self.order if x != p_end]:
                self.graph.add_edge("", p, p_end)
        # make ordering pseudo-rules from current load order.
        prev_i = 0
        self.graph.nodes.setdefault(self.order[prev_i], [])
        for curr_i in range(1, len(self.order)):
            self.graph.nodes.setdefault(self.order[curr_i], [])
            if (self.order[curr_i] not in self.graph.nearstart and
                self.order[curr_i] not in self.graph.nearend):
                # add an edge, on any failure due to cycle detection, we try
                # to make an edge between the current plugin and the first
                # previous ancestor we can succesfully link and edge from.
                for i in range(prev_i, 0, -1):
                    if (self.order[i] not in self.graph.nearstart and
                        self.order[i] not in self.graph.nearend):
                        if self.graph.add_edge("", self.order[i], self.order[curr_i]):
                            break
            prev_i = curr_i

    def update_mod_times(self, files):
        """change the modification times of files to be in order of file list,
        oldest to newest"""
        if Opt._Game == "Morrowind":
            mtime_first = 1024695106 # Fri Jun 21 17:31:46 2002 # Morrowind.esm, made compatible with tes3cmd resetdates
        else: # Opt._Game == Oblivion
            mtime_first = 1165600070 # Oblivion.esm
        if len(files) > 1:
            mtime_last = int(time()) # today
            # sanity check
            if mtime_last < 1228683562: # Sun Dec  7 14:59:56 CST 2008
                mtime_last = 1228683562
            loadorder_mtime_increment = (mtime_last - mtime_first) / len(files)

            tes3cmd_resetdates_morrowind_mtime = 1024695106 # Fri Jun 21 17:31:46 2002
            tes3cmd_resetdates_tribunal_mtime  = 1035940926 # Tue Oct 29 20:22:06 2002
            tes3cmd_resetdates_bloodmoon_mtime = 1051807050 # Thu May  1 12:37:30 2003

            lastmtime = tes3cmd_resetdates_morrowind_mtime
            for p in files:
                change = False
                if p == "morrowind.esm":
                    mtime = tes3cmd_resetdates_morrowind_mtime
                    change = True
                    os.utime(self.datadir.find_path("morrowind.bsa"), (-1, mtime))
                elif p == "tribunal.esm":
                    mtime = tes3cmd_resetdates_tribunal_mtime
                    change = True
                    os.utime(self.datadir.find_path("tribunal.bsa"), (-1, mtime))
                elif p == "bloodmoon.esm":
                    mtime = tes3cmd_resetdates_bloodmoon_mtime
                    change = True
                    os.utime(self.datadir.find_path("bloodmoon.bsa"), (-1, mtime))
                else:
                    mtime = os.path.getmtime(self.datadir.find_path(p))
                    if mtime <= lastmtime:
                        mtime = lastmtime + 5 # fraction of standard 1 minute Mash step, hopefully avoid redating some mods
                        change = True
                if change:
                    os.utime(self.datadir.find_path(p), (-1, mtime))
                lastmtime = mtime

    def save_order(self, filename, order, what):
        out = myopen_file(filename, 'w')
        if out == None:
            return
        for p in order:
            print >> out, p
        out.close()
        Msg.add(_["%s saved to: %s"] % (what, filename))

    def update(self, fromfile):
        """Update the load order based on input rules."""
        Msg.flush()
        Stats.flush()
        New.flush()
        Old.flush()
        Stats.add("Version: %s\t\t\t\t %s " % (full_version, _["Hello!"]))
        self.find_game_dirs()
        if Opt.FromFile:
            Msg.add("(Note that when the load order input is from an external source, the [SIZE] predicate cannot check the plugin filesizes, so it defaults to True).")
            self.read_from_file(fromfile)
            if len(self.order) == 0:
                Msg.add(_["No plugins detected. mlox.py understands lists of plugins in the format\nused by Morrowind.ini or Wrye Mash. Is that what you used for input?"])
                return(self)
        else:
            if Opt.GetAll:
                self.get_data_files()
            else:
                self.get_active_plugins()
                if self.order == []:
                    self.get_data_files()
            if self.order == []:
                Msg.add(_["No plugins detected! mlox needs to run somewhere under where the game is installed."])
                return(self)
        if Opt.DBG:
            Dbg.add("initial load order")
            for p in self.order:
                Dbg.add(p)
        # read rules from various sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        # primary rules are from mlox_user.txt
        parser = rule_parser(self.active, self.graph, self.datadir)
        progress = None
        if Opt.GUI:
            progress = wx.ProgressDialog("Progress", "", 100, None,
                                         wx.PD_AUTO_HIDE|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        parser.read_rules("mlox_user.txt", progress)

        # for reading mod-specific rules from "Data Files/mlox/*.txt"
        # possible problems:
        # mod author includes rules about other mods for which they should not publish rules
        # mod author gratuitously forces their mod to load last.
#        mod_rules_dir = caseless_dirlist(self.datadir.find_path("mlox"))
#        mod_rules_files = [f for f in mod_rules_dir.filelist()
#                           if os.path.isfile(mod_rules_dir.find_path(f)) and
#                           os.path.splitext(f)[1] == '.txt']
#        for f in mod_rules_files:
#            parser.read_rules(mod_rules_dir.find_path(f), progress)

        # last rules from mlox_base.txt
        if not parser.read_rules("mlox_base.txt", progress):
            Msg.add(_["Error: unable to open mlox_base.txt database. You must run mlox in the directory where mlox_base.txt lives. If you have not already done so, please download it from http://sourceforge.net/projects/mlox/files/mlox/ and install mlox_base.txt in your mlox directory."])
            progress.Destroy()
            return(self)
        if progress != None:
            progress.Destroy()
        # now do the topological sort of all known plugins (rules + load order)
        if Opt.Explain == None:
            self.add_current_order() # tertiary order "pseudo-rules" from current load order
            sorted = self.graph.topo_sort()
        else:
            # print an explanation of where the given plugin is in the graph and exit
            if not Opt.BaseOnly:
                self.add_current_order() # tertiary order "pseudo-rules" from current load order
            self.graph.explain(Opt.Explain, self.active)
            sys.exit(0)
        # the "sorted" list will be a superset of all known plugin files,
        # inluding those in our Data Files directory.
        # but we only want to update plugins that are in our current "Data Files"
        n = 1
        orig_index = {}
        for p in self.order:
            orig_index[p] = n
            Old.add("_%03d_ %s" % (n, C.truename(p)))
            n += 1
        sorted_datafiles = [f for f in sorted if f in self.active]
        (esm_files, esp_files) = self.partition_esps_and_esms(sorted_datafiles)
        new_order_cname = [p for p in esm_files + esp_files]
        new_order_truename = [C.truename(p) for p in new_order_cname]

        if self.order == new_order_cname:
            Msg.add(_["[Plugins already in sorted order. No sorting needed!]"])
            self.sorted = True

        # print out the new load order
        if len(new_order_cname) != len(self.order):
            Msg.add(_["Program Error: sanity check: len(new_order_truename %d) != len(self.order %d)"] % (len(new_order_truename), len(self.order)))
        if not Opt.FromFile:
            # these are things we do not want to do if just testing a load
            # order from a file (FromFile)
            if Opt.Update:
                self.update_mod_times(new_order_truename)
                Msg.add(_["[LOAD ORDER UPDATED!]"])
                self.sorted = True
            else:
                if not Opt.GUI:
                    Msg.add(_["[Load Order NOT updated.]"])
            # save the load orders to file for future reference
            self.save_order(old_loadorder_output, [C.truename(p) for p in self.order], _["current"])
            self.save_order(new_loadorder_output, new_order_truename, _["mlox sorted"])
        if not Opt.WarningsOnly:
            if Opt.GUI == False:
                if Opt.Update:
                    Msg.add(_["\n[UPDATED] New Load Order:\n---------------"])
                else:
                    Msg.add(_["\n[Proposed] New Load Order:\n---------------"])
            # highlight mods that have moved up in the load order
            highlight = "_"
            for i in range(0, len(new_order_truename)):
                p = new_order_truename[i]
                curr = p.lower()
                if (orig_index[curr] - 1) > i: highlight = "*"
                New.add("%s%03d%s %s" % (highlight, orig_index[curr], highlight, p))
                if highlight == "*":
                    if i < len(new_order_truename) - 1:
                        next = new_order_truename[i+1].lower()
                    if (orig_index[curr] > orig_index[next]):
                        highlight = "_"
        if Opt.GUI == False:
            Msg.add("")
        return(self)


class mlox_gui():
    def __init__(self):
        wx.Locale(wx.LOCALE_LOAD_DEFAULT)
        self.app = wx.App(True, None)
        sys.excepthook = lambda typ, val, tb: self.error_handler(typ, val, tb)
        self.can_update = True
        self.dir = os.getcwd()
        # setup widgets
        default_font = wx.Font(-1, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL,
                                weight=wx.FONTWEIGHT_NORMAL, underline=False, face="",
                                encoding=wx.FONTENCODING_SYSTEM)
        size = default_font.GetPointSize()
        self.label_font = wx.Font(size + 2, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD)
        self.button_font = wx.Font(size + 6, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD)
        self.frame = wx.Frame(None, wx.ID_ANY, ("mlox %s" % Version))
        self.frame.SetSizeHints(800,600)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        # logo doubles as a "reload" button
        img = wx.Image("mlox.gif", wx.BITMAP_TYPE_GIF).ConvertToBitmap()
        self.logo = wx.BitmapButton(self.frame, -1, img, (0,0), (img.GetWidth()+5, img.GetHeight()+5))
        self.logo.Bind(wx.EVT_BUTTON, self.on_reload)
        self.logo.SetToolTip(wx.ToolTip(_["Click to Reload"]))
        self.label_stats = wx.StaticText(self.frame, -1, _["Statistics"])
        self.label_stats.SetFont(self.label_font)
        self.txt_stats = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_RICH2)
        self.txt_stats.SetFont(default_font)
        if Opt.AutoFocus:
            self.txt_stats.Bind(wx.EVT_ENTER_WINDOW, lambda e: self.txt_stats.SetFocus())

        self.splitter = wx.SplitterWindow(self.frame, -1)

        self.split1 = wx.Panel(self.splitter, -1)
        self.label_msg = wx.StaticText(self.split1, -1, _["Messages"])
        self.label_msg.SetFont(self.label_font)
        self.txt_msg = rt.RichTextCtrl(self.split1, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_msg.SetFont(default_font)
        self.txt_msg.Bind(wx.EVT_TEXT_URL, self.click_url)
        if Opt.AutoFocus:
            self.txt_msg.Bind(wx.EVT_ENTER_WINDOW, lambda e: self.txt_msg.SetFocus())

        self.split2 = wx.Panel(self.splitter, -1)
        self.label_cur = wx.StaticText(self.split2, -1, _["Current Load Order"])
        self.label_cur.SetFont(self.label_font)
        self.txt_cur = wx.TextCtrl(self.split2, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_cur.SetFont(default_font)
        if Opt.AutoFocus:
            self.txt_cur.Bind(wx.EVT_ENTER_WINDOW, lambda e: self.txt_cur.SetFocus())
        self.label_cur_bottom = wx.StaticText(self.frame, -1, _["(Right click in this pane for options)"])
        self.label_new = wx.StaticText(self.split2, -1, _["Proposed Load Order Sorted by mlox"])
        self.label_new.SetFont(self.label_font)
        self.label_new_bottom = wx.StaticText(self.frame, -1, "")
        self.txt_new = wx.TextCtrl(self.split2, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_new.SetFont(default_font)
        if Opt.AutoFocus:
            self.txt_new.Bind(wx.EVT_ENTER_WINDOW, lambda e: self.txt_new.SetFocus())

        self.btn_update = wx.Button(self.frame, -1, _["Update Load Order"], size=(90,60))
        self.btn_update.SetFont(self.button_font)
        self.btn_quit = wx.Button(self.frame, -1, _["Quit"], size=(90,60))
        self.btn_quit.SetFont(self.button_font)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_quit.Bind(wx.EVT_BUTTON, self.on_quit)
        # arrange widgets

        # top box for stats and logo
        self.top_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.top_hbox.Add(self.txt_stats, 1, wx.EXPAND)
        self.top_hbox.Add(self.logo, 0, wx.EXPAND)

        # box for message output, in top split
        self.msg_vbox = wx.BoxSizer(wx.VERTICAL)
        self.msg_vbox.Add(self.label_msg, 0, wx.ALL)
        self.msg_vbox.Add(self.txt_msg, 1, wx.EXPAND)
        self.split1.SetSizer(self.msg_vbox)

        # box for load orders output, in bottom split
        self.lo_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.cur_vbox = wx.BoxSizer(wx.VERTICAL)
        self.cur_vbox.Add(self.label_cur, 0, wx.ALL|wx.CENTER)
        self.cur_vbox.Add(self.txt_cur, 4, wx.EXPAND)
        self.lo_hbox.Add(self.cur_vbox, 1, wx.EXPAND)
        self.new_vbox = wx.BoxSizer(wx.VERTICAL)
        self.new_vbox.Add(self.label_new, 0, wx.ALL|wx.CENTER)
        self.new_vbox.Add(self.txt_new, 4, wx.EXPAND)
        self.lo_hbox.Add(self.new_vbox, 1, wx.EXPAND)
        self.split2.SetSizer(self.lo_hbox)

        # box to hold labels at bottom of load order panes
        self.lo_labels_hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.label_cur_bottom, 0, wx.ALL|wx.CENTER)
        self.lo_labels_hbox.Add(vbox, 1, wx.EXPAND)
        self.lo_labels_hbox.Add(self.label_new_bottom, 1, wx.EXPAND)

        # bottom box for buttons
        self.button_box = wx.BoxSizer(wx.HORIZONTAL)
        self.button_box.Add(self.btn_update, 4)
        self.button_box.Add(self.btn_quit, 0)

        # put em all together and that spells GUI
        self.frame_vbox = wx.BoxSizer(wx.VERTICAL)
        self.frame_vbox.Add(self.label_stats, 0, wx.ALL)
        self.frame_vbox.Add(self.top_hbox, 0, wx.EXPAND)
        self.frame_vbox.Add(self.splitter, 1, wx.EXPAND)
        self.frame_vbox.Add(self.lo_labels_hbox, 0, wx.EXPAND)
        self.frame_vbox.Add(self.button_box, 0, wx.EXPAND)
        self.frame.SetSizer(self.frame_vbox)
        self.frame_vbox.Fit(self.frame)
        # setup up rightclick menu handler for original load order pane
        self.txt_cur.Bind(wx.EVT_RIGHT_DOWN, self.right_click_handler)

    def error_handler(self, type, value, tb):
        # pop up a window containing the error output
        err_frame = wx.Frame(None, wx.ID_ANY, (_["%s - Error"] % full_version))
        err_frame.SetSizeHints(500,800)
        err_label = wx.StaticText(err_frame, -1, _["An Error ocurred."])
        err_label.SetFont(self.label_font)
        err_txt = wx.TextCtrl(err_frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        err_btn_close = wx.Button(err_frame, -1, _["Close"], size=(90,60))
        err_btn_close.Bind(wx.EVT_BUTTON, lambda x: err_frame.Destroy())
        err_btn_close.SetFont(self.button_font)
        err_frame_vbox = wx.BoxSizer(wx.VERTICAL)
        err_frame_vbox.Add(err_label, 0, wx.EXPAND)
        err_frame_vbox.Add(err_txt, 1, wx.EXPAND)
        err_frame_vbox.Add(err_btn_close, 0, wx.EXPAND)
        err_frame.Bind(wx.EVT_CLOSE, lambda x: err_frame.Destroy())
        err_txt.SetValue(version_info() + "\n" + "".join(traceback.format_exception(type, value, tb)))
        err_frame.SetSizer(err_frame_vbox)
        err_frame_vbox.Fit(err_frame)
        err_frame.Show(True)
        self.app.MainLoop()

    def highlight_hello(self, txt):
        happy = wx.TextAttr(colBack=wx.Colour(145,240,180))
        highlighters = { re.compile(r'Version[^\]]+\]\t+(.+)', re.IGNORECASE): happy }
        text = Stats.get_u()
        for (re_pat, style) in highlighters.items():
            for match in re.finditer(re_pat, text):
                (start, end) = match.span(1)
                txt.SetStyle(start, end, style)

    def click_url(self, e):
        the_url = e.GetString()
        webbrowser.open(the_url)

    def highlight_warnings(self, txt):
        # highlight warnings in message window to help convey urgency
        # highlight styles:
	# try coping with python changing function names between versions /abot
        try:
            low = rt.RichTextAttr()    ; low.SetBackgroundColour(wx.Colour(125,220,240))
            medium = rt.RichTextAttr() ; medium.SetBackgroundColour(wx.Colour(255,255,180))
            high = rt.RichTextAttr()   ; high.SetBackgroundColour(wx.Colour(255,180,180))
            happy = rt.RichTextAttr()  ; happy.SetBackgroundColour(wx.Colour(145,240,180))
            hide = rt.RichTextAttr()   ; hide.SetBackgroundColour(wx.BLACK)
            url = rt.RichTextAttr()    ; url.SetTextColour(wx.BLUE) ; url.SetFontUnderlined(True)
        except:
            low = rt.TextAttrEx()    ; low.SetBackgroundColour(wx.Colour(125,220,240))
            medium = rt.TextAttrEx() ; medium.SetBackgroundColour(wx.Colour(255,255,180))
            high = rt.TextAttrEx()   ; high.SetBackgroundColour(wx.Colour(255,180,180))
            happy = rt.TextAttrEx()  ; happy.SetBackgroundColour(wx.Colour(145,240,180))
            hide = rt.TextAttrEx()   ; hide.SetBackgroundColour(wx.BLACK)
            url = rt.TextAttrEx()    ; url.SetTextColour(wx.BLUE) ; url.SetFontUnderlined(True)
        highlighters = {
            re.compile(r'http://\S+', re.IGNORECASE): url,
            re.compile(r'^\[conflict\]', re.IGNORECASE): medium,
            re.compile(r'\[Plugins already in sorted order. No sorting needed!\]', re.IGNORECASE): happy }
        text = Msg.get()
        # for hiding spoilers
        hidden = []
        adjust = [0]            # use a mutable entity for closure "hider"
        def hider(match):
            (p1, p2) = match.span(0)
            delta = len(match.group(0)) - len(match.group(1))
            hidden.append((p1 - adjust[0], p2 - delta - adjust[0]))
            adjust[0] += delta
            return(match.group(1))
        re_hide = re.compile(r'<hide>(.*)</hide>', re.IGNORECASE)
        text = re_hide.sub(hider, text)
        txt.SetValue(text)
        for where in hidden:
            txt.SetStyle(where, hide)
        # for special highlighting
        for (re_pat, style) in highlighters.items():
            for match in re.finditer(re_pat, text):
                (start, end) = match.span()
                if style == url:
                    url.SetURL(text[start:end])
                txt.SetStyle((start, end), style)
        # for leveled highlighting
        for (level, style) in (('!', low), ('!!', medium), ('!!!', high)):
            re_pat = re.compile("^ (?:\\| )?(%s.*)$" % level, re.MULTILINE)
            for match in re.finditer(re_pat, text):
                (start, end) = match.span()
                txt.SetStyle((start, end), style)
        happy = wx.TextAttr(colBack=wx.Colour(145,240,180))

    def highlight_moved(self, txt):
        # highlight background color for changed items in txt widget
        highlight = wx.TextAttr(colBack=wx.Colour(255,255,180))
        re_start = re.compile(r'[^_]\d+[^_][^\n]+')
        text = New.get()
        for match in re.finditer(re_start, text):
            (start, end) = match.span()
            if text[start] == '*': txt.SetStyle(start, end, highlight)

    def analyze_loadorder(self, fromfile):
        lo = loadorder().update(fromfile)
        if lo.sorted:
            self.can_update = False
        if not self.can_update:
            self.btn_update.Disable()
        self.txt_stats.SetValue(Stats.get_u())
        self.highlight_hello(self.txt_stats)
        self.txt_msg.SetValue(Msg.get())
        self.highlight_warnings(self.txt_msg)
        self.txt_cur.SetValue(Old.get())
        self.txt_new.SetValue(New.get())
        self.label_cur.SetLabel(lo.origin)
        self.cur_vbox.Layout()
        self.highlight_moved(self.txt_new)

    def start(self):
        self.frame.Show(True)
        self.splitter.SetMinimumPaneSize(20)
        self.splitter.SplitHorizontally(self.split1, self.split2)
        self.analyze_loadorder(None)
        self.app.MainLoop()

    def on_quit(self, e):
        sys.exit(0)

    def on_reload(self, e):
        self.can_update = True
        Opt.FromFile = False
        self.analyze_loadorder(None)

    def on_update(self, e):
        if not self.can_update:
            return
        Opt.Update = True
        self.analyze_loadorder(None)
        self.can_update = False
        self.btn_update.Disable()

    def on_close(self, e):
        self.on_quit(e)

    def bugdump(self):
        out = myopen_file(debug_output, 'w')
        if out == None:
            return
        print >> out, Dbg.get().encode("utf-8")
        out.close()

    def right_click_handler(self, e):
        menu = wx.Menu()
        menu_items = [(_["Select All"], self.menu_select_all_handler),
                      (_["Paste"], self.menu_paste_handler),
                      (_["Open File"], self.menu_open_file_handler),
                      (_["Debug"], self.menu_debug_handler)]
        for name, handler in menu_items:
            id = wx.NewId()
            menu.Append(id, name)
            wx.EVT_MENU(menu, id, handler)
        self.frame.PopupMenu(menu)
        menu.Destroy()

    def menu_select_all_handler(self, e):
        self.txt_cur.SelectAll()

    def menu_paste_handler(self, e):
        self.can_update = False
        if wx.TheClipboard.Open():
            wx.TheClipboard.UsePrimarySelection(True)
            if wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT)):
                data = wx.TextDataObject()
                if wx.TheClipboard.GetData(data):
                    out = myopen_file(clip_file, 'w')
                    if out != None:
                        # sometimes some unicode muck can get in there, as when pasting from web pages.
                        # TBD, this needs review as pasting some encodings will dump
                        out.write(data.GetText().encode("utf-8"))
                        out.close()
                        Opt.FromFile = True
                        self.analyze_loadorder(clip_file)
            wx.TheClipboard.Close()

    def menu_open_file_handler(self, e):
        self.can_update = False
        dialog = wx.FileDialog(self.frame, message=_["Input Plugin List from File"], defaultDir=self.dir, defaultFile="", style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.dir = dialog.GetDirectory()
            Opt.FromFile = True
            self.analyze_loadorder(dialog.GetPath())

    def menu_debug_handler(self, e):
        # pop up a window containing the debug output
        dbg_frame = wx.Frame(None, wx.ID_ANY, (_["%s - Debug Output"] % full_version))
        dbg_frame.SetSizeHints(500,800)
        dbg_label = wx.StaticText(dbg_frame, -1, _["(Debug Output Saved to \"%s\")"] % debug_output)
        dbg_label.SetFont(self.label_font)
        dbg_txt = wx.TextCtrl(dbg_frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        dbg_btn_close = wx.Button(dbg_frame, -1, _["Close"], size=(90,60))
        dbg_btn_close.Bind(wx.EVT_BUTTON, lambda x: dbg_frame.Destroy())
        dbg_btn_close.SetFont(self.button_font)
        dbg_frame_vbox = wx.BoxSizer(wx.VERTICAL)
        dbg_frame_vbox.Add(dbg_label, 0, wx.EXPAND)
        dbg_frame_vbox.Add(dbg_txt, 1, wx.EXPAND)
        dbg_frame_vbox.Add(dbg_btn_close, 0, wx.EXPAND)
        dbg_frame.Bind(wx.EVT_CLOSE, lambda x: dbg_frame.Destroy())
        dbg_txt.SetValue(Dbg.get())
        dbg_frame.SetSizer(dbg_frame_vbox)
        dbg_frame_vbox.Fit(dbg_frame)
        dbg_frame.Show(True)
        self.bugdump()


def get_mlox_base_version():
    base = myopen_file("mlox_base.txt", 'r')
    if base != None:
        for line in base:
            m = re_base_version.match(line)
            if m:
                base.close()
                return(m.group(1))
        base.close()
    return(_["(Not Found)"])


def version_info():
    import wx.__version__
    return "%s (%s/%s)\nPython Version: %s\nwxPython Version: %s\n" % (full_version, Lang, Encoding, pyversion, wx.__version__)

def print_version():
    print version_info()

def main():
    if Opt.FromFile:
        if len(args) == 0:
            print _["Error: -f specified, but no files on command line."]
            usage(2)            # exits
        for file in args:
            loadorder().update(file)
    elif Opt.GUI == True:
        if Opt.NoUpdate == False:
            update.update_mloxdata()
        # run with gui
        Opt.DBG = True
        mlox_gui().start()
    else:
        # run with command line arguments
        loadorder().update(None)

if __name__ == "__main__":
    Dbg.add("\nmlox DEBUG DUMP:\n")
    def usage(status):
        print _["Usage"]
        sys.exit(status)
    # Check Python version
    pyversion = sys.version[:3]
    Dbg.add("Python Version: %s" % pyversion)
    if float(pyversion) < 2.5:
        print _["This program requires Python version 2.5."]
        sys.exit(1)
    # process command line arguments
    Dbg.add("Command line: %s" % " ".join(sys.argv))
    try:
        opts, args = getopt(sys.argv[1:], "acde:fhlnpquvw",
                            ["all", "base-only", "check", "debug", "explain=", "fromfile", "gui", "help",
                             "listversions", "nodownload", "parsedebug", "profile", "quiet", "translations=",
                             "update", "version", "warningsonly"])
    except GetoptError, err:
        print str(err)
        usage(2)                # exits
    # set the global full_version now
    full_version = "%s %s [mlox-base %s]" % (os.path.basename(sys.argv[0]), Version, get_mlox_base_version())
    for opt, arg in opts:
        if opt in   ("-a", "--all"):
            Opt.GetAll = True
        elif opt in ("-c", "--check"):
            Opt.Update = False
        elif opt in ("--base-only"):
            Opt.BaseOnly = True
        elif opt in ("-d", "--debug"):
            Opt.DBG = True
            logging.basicConfig(level=logging.DEBUG)
        elif opt in ("-e", "--explain"):
            Opt.Explain = arg
            Msg.prints = False
            Stats.prints = False
        elif opt in ("-f", "--fromfile"):
            Opt.FromFile = True
        elif opt in ("--gui"):
            Opt.GUI = True
        elif opt in ("-h", "--help"):
            usage(0)            # exits
        elif opt in ("-l", "--listversions"):
            loadorder().listversions()
            sys.exit(0)
        elif opt in ("-p", "--parsedebug"):
            Opt.ParseDBG = True
        elif opt in ("--profile"):
            Opt.Profile = True
        elif opt in ("-q", "--quiet"):
            Opt.Quiet = True
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
            print_version()
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
