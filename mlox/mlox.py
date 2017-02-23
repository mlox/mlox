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
import StringIO
import modules.update as update
import modules.fileFinder as fileFinder
import modules.pluggraph as pluggraph
import modules.configHandler as configHandler

#Resource files
program_path = os.path.realpath(sys.path[0])
translation_file = os.path.join(program_path,"mlox.msg")
base_file = os.path.join(program_path,"mlox_base.txt")
user_file = os.path.join(program_path,"mlox_user.txt")
gif_file = os.path.join(program_path,"mlox.gif")


#HACK
C = fileFinder.caseless_filenames()

class dynopt(dict):
    def __getattr__(self, item):
        return self.__getitem__(item)
    def __setattr__(self, item, value):
        self.__setitem__(item, value)

Opt = dynopt()

# command line options
Opt.AutoFocus = True
Opt.BaseOnly = False
Opt.Explain = None
Opt.FromFile = False
Opt.GUI = False
Opt.GetAll = False
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

    # These two allow the use of python's default logging
    def write(self, message):
        self.add(message)
    def flush(self):
        pass

    def add(self, message):
        self.log.append(message.strip())
        for c in self.cohort:
            c.add(message.strip())
        if self.prints and Opt.GUI == False:
            print message

    def insert(self, message):
        self.log.insert(0, message.strip())
        for c in self.cohort:
            c.insert(message.strip())
        if self.prints and Opt.GUI == False:
            print message

    def get(self):
        return("\n".join(map(unify, self.log)) + "\n")

    def get_u(self):
        return("\n".join(self.log) + "\n")

    def clear(self):
        self.log = []

class debug_logger(logger):
    def __init__(self):
        logger.__init__(self, False)

    def add(self, message):
        if Opt.GUI:
            self.log.append(message.strip())

Dbg = debug_logger()            # debug output
New = logger(True, Dbg)         # new sorted loadorder
Old = logger(False)             # old original loadorder
Stats = logger(True, Dbg)       # stats output
Msg = logger(True, Dbg)         # messages output

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
formatter = logging.Formatter('%(levelname)s (%(name)s): %(message)s')
color_formatter = colorFormatConsole('%(levelname)s (%(name)s): %(message)s')
console_log_stream = logging.StreamHandler()
console_log_stream.setLevel(logging.INFO)
console_log_stream.setFormatter(color_formatter)
logging.getLogger('').addHandler(console_log_stream)
gui_dbg_log_stream = logging.StreamHandler(stream=Dbg)
gui_dbg_log_stream.setFormatter(formatter)
gui_dbg_log_stream.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(gui_dbg_log_stream)
gui_msg_log_stream = logging.StreamHandler(stream=Msg)
gui_msg_log_stream.setFormatter(formatter)
gui_msg_log_stream.setLevel(logging.INFO)
logging.getLogger('').addHandler(gui_msg_log_stream)

#Disable parse debug logging unless the user asks for it (It's so much it actually slows the program down)
logging.getLogger('mlox.parser').setLevel(logging.INFO)

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
    return(dyndict(map(splitter, codecs.open(translation_file, 'r', "utf-8").read().split("\n[["))[1:]))

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
        mode_str = _["input"] if mode == 'r' else _["output"]
        logging.debug(_["Problem opening \"%s\" for %s (%s)"] % (filename, mode_str, strerror))
    return(None)

def plugin_description(plugin):
    """Read the description field of a TES3/TES4 plugin file header"""
    try:
        inp = open(plugin, 'rb')
    except IOError:
        logging.warn("Unable to open plugin file:  {0}".format(plugin))
        return("")
    block = inp.read(4096)
    inp.close()
    if block[0:4] == "TES3":    # Morrowind
        if len(block) < tes3_min_plugin_size:
            logging.warn("Cannot read plugin description(%s): file too short, returning NULL string" % plugin)
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

parse_logger = logging.getLogger('mlox.parser')

class rule_parser:
    """A simple recursive descent rule parser, for evaluating rule statements containing nested boolean expressions."""
    def __init__(self, active, graph, datadir,out_stream,name_converter):
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
        self.out_stream = out_stream
        self.name_converter = name_converter

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
                    parse_logger.debug("readline returns: %s" % line)
                    return(True)
        except StopIteration:
            parse_logger.debug("EOF")
            self.buffer = ""
            self.input_handle.close()
            self.input_handle = None
            return(False)

    def where(self):
        return("%s:%d" % (self.rule_file, self.line_num))

    def parse_error(self, what):
        """print a message about current parsing error, and blow away the
        current parse buffer so next parse starts on next input line."""
        parse_logger("%s: Parse Error(%s), %s [Buffer=%s]" % (self.where(), self.curr_rule, what, self.buffer))
        self.buffer = ""
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]

    def parse_message_block(self):
        while self.readline():
            if re_message.match(self.buffer):
                self.message.append(self.buffer)
            else:
                return

    def expand_filename(self, plugin):
        parse_logger.debug("expand_filename, plugin=%s" % plugin)
        pat = "^%s$" % re_escape_meta.sub(r'\\\1', plugin)
        # if the plugin name contains metacharacters, do filename expansion
        subbed = False
        if re_plugin_meta.search(plugin) != None:
            parse_logger.debug("expand_filename name has META: %s" % pat)
            pat = re_plugin_meta.sub(r'.\1', pat)
            subbed = True
        if re_plugin_metaver.search(plugin) != None:
            parse_logger.debug("expand_filename name has METAVER: %s" % pat)
            pat = re_plugin_metaver.sub(plugin_version, pat)
            subbed = True
        if not subbed:        # no expansions made
            return([plugin] if plugin.lower() in self.active else [])
        parse_logger.debug("expand_filename new RE pat: %s" % pat)
        matches = []
        re_namepat = re.compile(pat, re.IGNORECASE)
        for p in self.active:
            if re_namepat.match(p):
                matches.append(p)
                parse_logger.debug("expand_filename: %s expands to: %s" % (plugin, p))
        return(matches)

    def parse_plugin_name(self):
        self.parse_dbg_indent += "  "
        buff = self.buffer.strip()
        parse_logger.debug("parse_plugin_name buff=%s" % buff)
        plugin_match = re_plugin.match(buff)
        if plugin_match:
            plugin_name = self.name_converter.cname(plugin_match.group(1))
            parse_logger.debug("parse_plugin_name name=%s" % plugin_name)
            pos = plugin_match.span(2)[1]
            self.buffer = buff[pos:].lstrip()
            matches = self.expand_filename(plugin_name)
            if matches != []:
                plugin_name = matches.pop(0)
                parse_logger.debug("parse_plugin_name new name=%s" % plugin_name)
                if len(matches) > 0:
                    self.buffer = " ".join(matches) + " " + self.buffer
                return(True, plugin_name)
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, plugin_name)
        else:
            self.parse_error("expected a plugin name")
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
                parse_logger.warning("%s: ORDER rule has no entries" % (self.where()))
            elif n_order == 1:
                parse_logger.warning("%s: ORDER rule skipped because it only has one entry: %s" % (self.where(), self.name_converter.truename(prev)))

    def parse_ver(self):
        self.parse_dbg_indent += "  "
        match = re_ver_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("parse_ver new buffer = %s" % self.buffer)
            op = match.group(1)
            if op not in version_operators:
                self.parse_error("Invalid [VER] operator")
                return(None, None)
            orig_ver = match.group(2)
            ver = format_version(orig_ver)
            plugin_name = match.group(3)
            expanded = self.expand_filename(plugin_name)
            expr = "[VER %s %s %s]" % (op, orig_ver, plugin_name)
            parse_logger.debug("parse_ver, expr=%s ver=%s" % (expr, ver))
            if len(expanded) == 1:
                expr = "[VER %s %s %s]" % (op, orig_ver, expanded[0])
            elif expanded == []:
                parse_logger.debug("parse_ver [VER] \"%s\" not active" % plugin_name)
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if self.datadir == None:
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
                plugin = self.name_converter.cname(xp)
                plugin_t = self.name_converter.truename(plugin)
                desc = plugin_description(self.datadir.find_path(plugin))
                match = re_header_version.search(desc)
                if match:
                    p_ver_orig = match.group(1)
                    p_ver = format_version(p_ver_orig)
                    parse_logger.debug("parse_ver (header) version(%s) = %s (%s)" % (plugin_t, p_ver_orig, p_ver))
                else:
                    match = re_filename_version.search(plugin)
                    if match:
                        p_ver_orig = match.group(1)
                        p_ver = format_version(p_ver_orig)
                        parse_logger.debug("parse_ver (filename) version(%s) = %s (%s)" % (plugin_t, p_ver_orig, p_ver))
                    else:
                        parse_logger.debug("parse_ver no version for %s" % plugin_t)
                        return(False, expr)
                parse_logger.debug("parse_ver compare  p_ver=%s %s ver=%s" % (p_ver, op, ver))
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
        self.parse_error("Invalid [VER] function")
        return(None, None)

    def parse_desc(self):
        """match patterns against the description string in the plugin header."""
        self.parse_dbg_indent += "  "
        match = re_desc_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("parse_desc new buffer = %s" % self.buffer)
            bang = match.group(1) # means to invert the meaning of the match
            pat = match.group(2)
            plugin_name = match.group(3)
            expr = "[DESC %s/%s/ %s]" % (bang, pat, plugin_name)
            parse_logger.debug("parse_desc, expr=%s" % expr)
            expanded = self.expand_filename(plugin_name)
            if len(expanded) == 1:
                expr = "[DESC %s/%s/ %s]" % (bang, pat, expanded[0])
            elif expanded == []:
                parse_logger.debug("parse_desc [DESC] \"%s\" not active" % plugin_name)
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks,
                # which do not have access to the actual plugin, so we
                # always assume the test is merely for file existence,
                # to err on the side of caution
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(True, expr)
            for xp in expanded:
                plugin = self.name_converter.cname(xp)
                plugin_t = self.name_converter.truename(plugin)
                re_pat = re.compile(pat)
                desc = plugin_description(self.datadir.find_path(plugin))
                bool = (re_pat.search(desc) != None)
                if bang == "!": bool = not bool
                parse_logger.debug("parse_desc [DESC] returning: (%s, %s)" % (bool, expr))
                if bool:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[DESC %s/%s/ %s]" % (bang, pat, plugin_t))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error("Invalid [DESC] function")
        return(None, None)

    def parse_size(self):
        """check the given size of the plugin."""
        self.parse_dbg_indent += "  "
        match = re_size_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("parse_size new buffer = %s" % self.buffer)
            bang = match.group(1) # means "is not this size"
            wanted_size = int(match.group(2))
            plugin_name = match.group(3)
            expr = "[SIZE %s%d %s]" % (bang, wanted_size, plugin_name)
            parse_logger.debug("parse_size, expr=%s" % expr)
            expanded = self.expand_filename(plugin_name)
            if len(expanded) == 1:
                expr = "[SIZE %s%d %s]" % (bang, wanted_size, expanded[0])
            elif expanded == []:
                parse_logger.debug("parse_size [SIZE] \"%s\" not active" % match.group(3))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks,
                # which do not have access to the actual plugin, so we
                # always assume the test is merely for file existence,
                # to err on the side of caution
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(True, expr)
            for xp in expanded:
                plugin = self.name_converter.cname(xp)
                plugin_t = self.name_converter.truename(plugin)
                actual_size = os.path.getsize(self.datadir.find_path(plugin))
                bool = (actual_size == wanted_size)
                if bang == "!": bool = not bool
                parse_logger.debug("parse_size [SIZE] returning: (%s, %s)" % (bool, expr))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                if bool:
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(True, "[SIZE %s%d %s]" % (bang, wanted_size, plugin_t))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(False, expr)
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        self.parse_error("Invalid [SIZE] function")
        return(None, None)

    def parse_expression(self, prune=False):
        self.parse_dbg_indent += "  "
        self.buffer = self.buffer.strip()
        if self.buffer == "":
            if self.readline():
                if re_rule.match(self.buffer):
                    parse_logger.debug("parse_expression new line started new rule, returning None")
                    self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                    return(None, None)
                self.buffer = self.buffer.strip()
            else:
                parse_logger.debug("parse_expression EOF, returning None")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(None, None)
        parse_logger.debug("parse_expression, start buffer: \"%s\"" % self.buffer)
        match = re_fun.match(self.buffer)
        if match:
            fun = match.group(1).upper()
            if fun == "DESC":
                parse_logger.debug("parse_expression calling parse_desc()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_desc())
            elif fun == "VER":
                parse_logger.debug("parse_expression calling parse_ver()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_ver())
            elif fun == "SIZE":
                parse_logger.debug("parse_expression calling parse_size()")
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return(self.parse_size())
            # otherwise it's a boolean function ...
            parse_logger.debug("parse_expression parsing expression: \"%s\"" % self.buffer)
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            parse_logger.debug("fun = %s" % fun)
            vals = []
            exprs = []
            bool_end = re_end_fun.match(self.buffer)
            parse_logger.debug("self.buffer 1 =\"%s\"" % self.buffer)
            while not bool_end:
                (bool, expr) = self.parse_expression(prune)
                if bool == None:
                    self.parse_error("[%s] Invalid boolean arguments" % fun)
                    return(None, None)
                exprs.append(expr)
                vals.append(bool)
                parse_logger.debug("self.buffer 2 =\"%s\"" % self.buffer)
                bool_end = re_end_fun.match(self.buffer)
            pos = bool_end.span(0)[1]
            self.buffer = self.buffer[pos:]
            parse_logger.debug("self.buffer 3 =\"%s\"" % self.buffer)
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
                self.parse_error("Expected Boolean function (ALL, ANY, NOT)")
                return(None, None)
            parse_logger.debug("parse_expression NOTREACHED")
        else:
            if re_fun.match(self.buffer):
                self.parse_error("Invalid function expression")
                return(None, None)
            parse_logger.debug("parse_expression parsing plugin: \"%s\"" % self.buffer)
            (exists, p) = self.parse_plugin_name()
            if exists != None and p != None:
                p = self.name_converter.truename(p) if exists else ("MISSING(%s)" % self.name_converter.truename(p))
            self.parse_dbg_indent = self.parse_dbg_indent[:-2]
            return(exists, p)
        parse_logger.debug("parse_expression NOTREACHED(2)")

    def pprint(self, expr, prefix):
        """pretty printer for parsed expressions"""
        formatted = PrettyPrinter(indent=2).pformat(expr)
        formatted = re_notstr.sub("NOT", formatted)
        formatted = re_anystr.sub("ANY", formatted)
        formatted = re_allstr.sub("ALL", formatted)
        return(re_indented.sub(prefix, formatted))

    #Remove the missing plugins from the 'ANY' expression
    def _prune_any(self,item):
        #Don't operate on simple strings
        if isinstance(item,list) == False:
            return item
        #Recursive search to make sure we get any nested expressions
        for i in range(0,len(item)):
            item[i] = self._prune_any(item[i])
        #Prune all the missing plugins
        if item[0] == 'ANY':
            return filter(lambda x: x.find('MISSING(') == -1, item)
        return item

    def parse_statement(self, rule, msg, expr):
        self.parse_dbg_indent += "  "
        parse_logger.debug("parse_statement(%s, %s, %s)" % (rule, msg, expr))
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
            parse_logger.debug("before conflict parse_expr() expr=%s line=%s" % (expr, self.buffer))
            (bool, expr) = self.parse_expression()
            parse_logger.debug("conflict parse_expr()1 bool=%s bool=%s" % (bool, expr))
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression()
                parse_logger.debug("conflict parse_expr()N bool=%s bool=%s" % ("True" if bool else "False", expr))
            if len(exprs) > 1:
                self.out_stream.write("[CONFLICT]")
                for e in exprs:
                    self.out_stream.write(self.pprint(self._prune_any(e), " > "))
                if msg != "": self.out_stream.write(msg)
        elif rule == "NOTE":    # takes any number of exprs
            parse_logger.debug("function NOTE: %s" % msg)
            exprs = []
            (bool, expr) = self.parse_expression(prune=True)
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression(prune=True)
            if len(exprs) > 0:
                self.out_stream.write("[NOTE]")
                for e in exprs:
                    self.out_stream.write(self.pprint(e, " > "))
                if msg != "": self.out_stream.write(msg)
        elif rule == "PATCH":   # takes 2 exprs
            (bool1, expr1) = self.parse_expression()
            if bool1 == None:
                parse_logger.warning("%s: PATCH rule invalid first expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                parse_logger.warning("%s: PATCH rule invalid second expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            if bool1 and not bool2:
                # case where the patch is present but the thing to be patched is missing
                self.out_stream.write("[PATCH]\n%s is missing some pre-requisites:\n%s" %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": self.out_stream.write(msg)
            if bool2 and not bool1:
                # case where the patch is missing for the thing to be patched
                self.out_stream.write("[PATCH]\n%s for:\n%s" %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": self.out_stream.write(msg)
        elif rule == "REQUIRES": # takes 2 exprs
            (bool1, expr1) = self.parse_expression(prune=True)
            if bool1 == None:
                parse_logger.warning("%s: REQUIRES rule invalid first expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                parse_logger.warning("%s: REQUIRES rule invalid second expression" % (self.where()))
                self.parse_dbg_indent = self.parse_dbg_indent[:-2]
                return
            if bool1 and not bool2:
                expr2_str = self.pprint(expr2, " > ")
                self.out_stream.write("[REQUIRES]\n%s Requires:\n%s" %
                        (self.pprint(expr1, " !!!"), expr2_str))
                if msg != "": self.out_stream.write(msg)
                match = re_filename_version.search(expr2_str)
                if match:
                    self.out_stream.write(" | [Note that you may see this message if you have an older version of one\n | of the pre-requisites. In that case, it is suggested that you upgrade\n | to the newer version].")
        self.parse_dbg_indent = self.parse_dbg_indent[:-2]
        parse_logger.debug("parse_statement RETURNING")

    def read_rules(self, rule_file, progress = None):
        """Read rules from rule files (e.g., mlox_user.txt or mlox_base.txt),
        add order rules to graph, and print warnings."""
        n_rules = 0
        self.rule_file = rule_file

        pmsg = "Loading: %s" % rule_file

        parse_logger.debug("Reading rules from: \"{0}\"".format(self.rule_file))
        try:
            self.input_handle = open(self.rule_file, 'r')
            inputsize = os.path.getsize(self.rule_file)
        except IOError, OSError:
            #This can't be too important, because we try to read the user rules file, and it doesn't exist for most people (TODO:  Move file existance checking somewhere else, and change this from info to error)
            parse_logger.info("Unable to open rules file:  {0}".format(self.rule_file))
            return False

        self.line_num = 0
        while True:
            if self.buffer == "":
                if not self.readline():
                    break
            if progress != None and inputsize > 0:
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
                    self.parse_error("read_rules failed sanity check, unknown rule")
            else:
                self.parse_error("expected start of rule")
        parse_logger.info("Read {0} rules from: \"{1}\"".format(n_rules, self.rule_file))
        return True

class loadorder:
    """Class for reading plugin mod times (load order), and updating them based on rules"""
    def __init__(self):
        # order is the list of plugins in Data Files, ordered by mtime
        self.active = {}                   # current active plugins
        self.order = []                    # the load order
        self.datadir = None                # where plugins live
        self.plugin_file = None            # Path to the file containing the plugin list
        self.graph = pluggraph.pluggraph()
        self.sorted = False
        self.origin = None      # where plugins came from (active, installed, file)

        Opt._Game, self.plugin_file, self.datadir = fileFinder.find_game_dirs()

    def get_active_plugins(self):
        """Get the active list of plugins from the game configuration. Updates self.active and self.order."""
        if self.plugin_file == None:
            Msg.add(_["{0} config file not found!"].format(Opt._Game))
            return

        # Get all the plugins
        configFiles = configHandler.configHandler(self.plugin_file,Opt._Game).read()
        dirFiles = configHandler.dataDirHandler(self.datadir).read()

        # Remove plugins not in the data directory (and correct capitalization)
        configFiles = map(str.lower, configFiles)
        self.order = filter(lambda x: x.lower() in configFiles, dirFiles)

        #Convert the files to lowercase, while storing them in a global (WARNING:  Use a global here)
        self.order = map(C.cname,self.order)

        loadup_msg(_["Getting active plugins from: {0}".format(self.plugin_file)], len(self.order), "plugins")
        for p in self.order:
            self.active[p] = True
        self.origin = _["Active Plugins"]

    def get_data_files(self):
        """Get the load order from the data files directory. Updates self.active and self.order."""
        self.order = configHandler.dataDirHandler(self.datadir).read()

        #Convert the files to lowercase, while storing them in a global (WARNING:  Use a global here)
        self.order = map(C.cname,self.order)

        loadup_msg(_["Getting list of plugins from plugin directory"], len(self.order), "plugins")
        for p in self.order:
            self.active[p] = True
        self.origin = _["Installed Plugins"]

    def listversions(self):
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

    def read_from_file(self, fromfile):
        """Get the load order by reading an input file. Updates self.active and self.order."""
        self.order = configHandler.configHandler(fromfile).read()

        #Convert the files to lowercase, while storing them in a global (WARNING:  Use a global here)
        self.order = map(C.cname,self.order)

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
        logging.debug("adding edges from CURRENT ORDER")
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
        Msg.clear()
        Stats.clear()
        New.clear()
        Old.clear()
        Stats.add("Version: %s\t\t\t\t %s " % (full_version, _["Hello!"]))
        if Opt.FromFile:
            self.datadir = None #This tells the parser to not worry about things like [SIZE] checks
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
        logging.debug("Initial load order:")
        for p in self.order:
            logging.debug("  " + p)
        # read rules from various sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        # primary rules are from mlox_user.txt
        parser = None
        if Opt.Quiet:
            #Print output to an unused buffer
            parser = rule_parser(self.active, self.graph, self.datadir,StringIO.StringIO(),C)
        else:
            parser = rule_parser(self.active, self.graph, self.datadir,Msg,C)
        progress = None
        if Opt.GUI:
            progress = wx.ProgressDialog("Progress", "", 100, None,
                                         wx.PD_AUTO_HIDE|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        parser.read_rules(user_file, progress)

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
        if not parser.read_rules(base_file, progress):
            Msg.add(_["Error: unable to open mlox_base.txt database."])
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
        (esm_files, esp_files) = configHandler.partition_esps_and_esms(sorted_datafiles)
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
                if configHandler.dataDirHandler(self.datadir).write(new_order_truename):
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
        img = wx.Image(gif_file, wx.BITMAP_TYPE_GIF).ConvertToBitmap()
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
            warning = rt.RichTextAttr(); warning.SetBackgroundColour('YELLOW')
            error = rt.RichTextAttr()  ; error.SetBackgroundColour('RED')
        except:
            low = rt.TextAttrEx()    ; low.SetBackgroundColour(wx.Colour(125,220,240))
            medium = rt.TextAttrEx() ; medium.SetBackgroundColour(wx.Colour(255,255,180))
            high = rt.TextAttrEx()   ; high.SetBackgroundColour(wx.Colour(255,180,180))
            happy = rt.TextAttrEx()  ; happy.SetBackgroundColour(wx.Colour(145,240,180))
            hide = rt.TextAttrEx()   ; hide.SetBackgroundColour(wx.BLACK)
            url = rt.TextAttrEx()    ; url.SetTextColour(wx.BLUE) ; url.SetFontUnderlined(True)
            warning = rt.TextAttrEx(); warning.SetBackgroundColour('YELLOW')
            error = rt.TextAttrEx()  ; error.SetBackgroundColour('RED')
        highlighters = {
            re.compile(r'http://\S+', re.IGNORECASE): url,
            re.compile(r'^\[CONFLICT\]', re.MULTILINE): medium,
            re.compile(r'\[Plugins already in sorted order. No sorting needed!\]', re.IGNORECASE): happy,
            re.compile("^ (?:\\| )?(!.*)$", re.MULTILINE): low,             #Handle '!' in mlox_base.txt
            re.compile("^ (?:\\| )?(!!.*)$", re.MULTILINE): medium,         #Handle '!!' in mlox_base.txt
            re.compile("^ (?:\\| )?(!!!.*)$", re.MULTILINE): high,          #Handle '!!!' in mlox_base.txt
            re.compile(r'^WARNING \(.*\):.*', re.MULTILINE): warning,
            re.compile(r'^ERROR \(.*\):.*', re.MULTILINE): error }
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
    base = myopen_file(base_file, 'r')
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
        mlox_gui().start()
    else:
        # run with command line arguments
        loadorder().update(None)

if __name__ == "__main__":
    logging.debug("\nmlox DEBUG DUMP:\n")
    def usage(status):
        print _["Usage"]
        sys.exit(status)
    # Check Python version
    pyversion = sys.version[:3]
    logging.debug("Python Version: %s" % pyversion)
    if float(pyversion) < 2.5:
        print _["This program requires Python version 2.5."]
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
            console_log_stream.setLevel(logging.DEBUG)
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
            logging.getLogger('mlox.parser').setLevel(logging.DEBUG)
            console_log_stream.setLevel(logging.DEBUG)
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
