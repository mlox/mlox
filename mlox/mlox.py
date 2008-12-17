#!/usr/bin/python
# -*- mode: python -*-
# Copyright 2008 John Moonsugar <john.moonsugar@gmail.com>
# License: MIT License (see the file: License.txt)
Version = "0.31"

import sys

"""
mlox - elder scrolls mod load order eXpert
"""

import os
import re
import wx
from pprint import PrettyPrinter
from getopt import getopt, GetoptError
from time import time

Message = {}

class dynopt(dict):
    def __getattr__(self, item):
        return self.__getitem__(item)
    def __setattr__(self, item, value):
        self.__setitem__(item, value)

Opt = dynopt()

# command line options
Opt.BaseOnly = False
Opt.DBG = False
Opt.Explain = None
Opt.FromFile = False
Opt.GUI = False
Opt.GetAll = False
Opt.ParseDBG = False
Opt.Quiet = False
Opt.Update = False
Opt.WarningsOnly = False

# comments start with ';'
re_comment = re.compile(r'(?:^|\s);.*$')
# re_rule matches the start of a rule.
re_rule = re.compile(r'^\[(version|order|nearend|nearstart|conflict|note|patch|requires)((?:\s+.[^\]]*)?)\](.*)$', re.IGNORECASE)
re_base_version = re.compile(r'^\[version\s+([^\]]*)\]', re.IGNORECASE)
# line for multiline messages
re_message = re.compile(r'^\s')
# pattern matching a plugin in Morrowind.ini
re_gamefile = re.compile(r'GameFile\d+=([^\r\n]*)', re.IGNORECASE)
# pattern to match plugins in FromFile (somewhat looser than re_gamefile)
# this may be too sloppy, we could also look for the same prefix pattern,
# and remove that if present on all lines.
re_sloppy_plugin = re.compile(r'^(?:(?:DBG:\s+)?[_\*]\d\d\d[_\*]\s+|GameFile\d+=|\d{1,3} {1,2}|Plugin\d+\s*=\s*)?(.+\.es[mp]\b)', re.IGNORECASE)
# pattern used to match a string that should only contain a plugin name, no slop
re_plugin = re.compile(r'^(\S[^\[]*?\.es[mp]\b)([\s]*)', re.IGNORECASE)
# set of characters that are not allowed to occur in plugin names.
# (we allow '*' and '?' for filename matching).
re_plugin_illegal = re.compile(r'[\"\[\]\\/=+<>:;|\^]')
re_plugin_meta = re.compile(r'([*?])')
# for recognizing our functions:
re_start_fun = re.compile(r'^\[(ALL|ANY|NOT|DESC|VER)\s*', re.IGNORECASE)
re_end_fun = re.compile(r'^\]\s*')
re_desc_fun = re.compile(r'\[DESC\s*(!?)/([^/]+)/\s*([^\]]+)\]', re.IGNORECASE)
# for parsing a version number
ver_delim = r'[_.-]'
re_ver_delim = re.compile(ver_delim)
plugin_version = r'(\d(?:%s?\d+)*[a-zA-Z]?)' % ver_delim
re_alpha_tail = re.compile(r'(\d+)([a-z])', re.IGNORECASE)
re_ver_fun = re.compile(r'\[VER\s*([=<>])\s*%s\s*([^\]]+)\]' % plugin_version, re.IGNORECASE)
# for grabbing version numbers from filenames
re_filename_version = re.compile(r'\D%s\D*\.es[mp]' % plugin_version)
# for grabbing version numbers from plugin header description fields
re_header_version = re.compile(r'version\b\D+%s' % plugin_version, re.IGNORECASE)

# for cleaning up pretty printer
re_notstr = re.compile(r"\s*'NOT',")
re_anystr = re.compile(r"\s*'ANY',")
re_allstr = re.compile(r"\s*'ALL',")
re_indented = re.compile(r'^', re.MULTILINE)


full_version = ""
clip_file = "mlox_clipboard.out"
old_loadorder_output = "current_loadorder.out"
new_loadorder_output = "mlox_new_loadorder.out"
debug_output = "mlox_debug.out"
min_plugin_size = 362           # minimum size for a TES plugin

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
        return("\n".join(self.log) + "\n").decode("ascii", "replace").encode("ascii", "replace")

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
        if Opt.ParseDBG:
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

    def __init__(self, dir):
        self.dir = dir
        self.files = {}
        for f in [p for p in os.listdir(dir)]:
            self.files[f.lower()] = f

    def find_file(self, file):
        return(self.files.get(file.lower(), None))

    def find_path(self, file):
        f = file.lower()
        if f in self.files:
            return(os.path.join(self.dir, self.files[f]))
        return(None)

    def dirpath(self):
        return(self.dir)

    def filelist(self):
        return(self.files.values())


# Utility functions
def format_version(ver):
    #print "DBG: input ver = %s" % ver
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
    v.append(alpha)
    #print "DBG: v = %s" % PrettyPrinter(indent=2).pformat(v)
    return("%05d.%05d.%05d.%s" % (v[0], v[1], v[2], v[3]))

def loadup_msg(msg, count, what):
    Stats.add("%-50s (%3d %s)" % (msg, count, what))

def myopen_file(filename, mode):
    try:
        return(open(filename, mode))
    except IOError, (errno, strerror):
        if Opt.DBG:
            mode_str = "input" if mode == 'r' else "output"
            Dbg.add("Error opening \"%s\" for %s (%s)" % (filename, mode_str, strerror))
    return(None)

def plugin_description(plugin):
    if os.path.getsize(plugin) < min_plugin_size:
        Dbg.add("plugin_description(%s): file too short, returning NULL string" % plugin)
        return("")
    inp = myopen_file(plugin, 'r')
    inp.seek(64,0)
    desc = inp.read(260)
    inp.close()
    return(desc[0:desc.find("\x00")])

def find_appdata():
    if os.name == "posix":
        # Linux - total hack for finding plugins.txt
        # find where we are now, then walk the tree upwards to find system.reg
        # then grovel around in system.reg until we find the localappdata path
        # and then fake it like a Republican
        #"LOCALAPPDATA"
        path = os.path.normpath(os.path.abspath("."))
        return(None)
    # Windows
    try:
        import _winreg
        try:
            key = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER,
                                  r'Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders')
            ret = _winreg.QueryValueEx(key, 'Personal')
        except WindowsError:
            return None
        else:
            key.Close()
        return(os.path.expandvars(ret[0]))
    except ImportError:
        return None

class rule_parser:
    """A simple recursive descent rule parser, for evaluating nested boolean expressions."""
    def __init__(self, active, graph, datadir):
        self.active = active
        self.graph = graph
        self.datadir = datadir
        self.line_num = 0
        self.rule_file = None
        self.input_handle = None
        self.buffer = ""        # the parsing buffer
        self.message = []       # the comment for the current rule
        self.curr_rule = ""     # name of the current rule we are parsing

    def readline(self):
        """reads a line into the current parsing buffer"""
        if self.input_handle == None:
            return(False)
        try:
            while True:
                line = self.input_handle.next()
                self.line_num += 1
                line = re_comment.sub('', line) # remove comments
                line = line.rstrip() # strip whitespace from end of line, include CRLF
                if line != "":
                    self.buffer = line
                    ParseDbg.add("readline returns: %s" % line)
                    return(True)
        except StopIteration:
            ParseDbg.add("EOF")
            self.buffer = ""
            self.input_handle.close()
            self.input_handle = None
            return(False)

    def where(self):
        return("%s:%d" % (self.rule_file, self.line_num))

    def parse_error(self, what):
        Msg.add("%s: Parse Error(%s), %s" % (self.where(), self.curr_rule, what))

    def parse_message_block(self):
        while self.readline():
            if re_message.match(self.buffer):
                self.message.append(self.buffer)
            else:
                return

    def parse_plugin_name(self):
        buff = self.buffer.strip()
        ParseDbg.add("parse_plugin_name buff=%s" % buff)
        plugin_match = re_plugin.match(buff)
        if plugin_match:
            plugin_name = C.cname(plugin_match.group(1))
            ParseDbg.add("parse_plugin_name name=%s" % plugin_name)
            pos = plugin_match.span(2)[1]
            self.buffer = buff[pos:].lstrip()
            # if the plugin name contains metacharacters, do filename expansion
            if re_plugin_meta.search(plugin_name) != None:
                pat = plugin_name
                ParseDbg.add("parse_plugin_name name has META: %s" % pat)
                matches = []
                pat = re_plugin_meta.sub(r".\1", pat)
                ParseDbg.add("parse_plugin_name new RE pat: %s" % pat)
                re_namepat = re.compile(pat, re.IGNORECASE)
                for p in self.active:
                    if re_namepat.match(p):
                        matches.append(p)
                        ParseDbg.add("parse_plugin_name matching name: %s" % p)
                if len(matches) > 0:
                    plugin_name = matches.pop(0)
                    ParseDbg.add("parse_plugin_name new name=%s" % plugin_name)
                    if len(matches) > 0:
                        self.buffer = " ".join(matches) + " " + self.buffer
            ParseDbg.add("parse_plugin_name new buff=\"%s\"" % self.buffer)
            exists = plugin_name in self.active
            return(exists, plugin_name)
        else:
            self.parse_error("expected a plugin name: \"%s\"" % buff)
            self.buffer = ""
            return(None, None)

    def parse_ordering(self, rule):
        prev = None
        n_order = 0
        while self.readline():
            if re_rule.match(self.buffer):
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
                Msg.add("Warning: %s: ORDER rule has no entries" % (self.where()))
            elif n_order == 1:
                Msg.add("Warning: %s: ORDER rule skipped because it only has one entry: %s" % (self.where(), C.truename(prev)))

    def parse_ver(self):
        match = re_ver_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            ParseDbg.add("parse_ver new buffer = %s" % self.buffer)
            op = match.group(1)
            orig_ver = match.group(2)
            ver = format_version(orig_ver)
            plugin = C.cname(match.group(3))
            expr = "[VER %s %s %s]" % (op, orig_ver, plugin)
            ParseDbg.add("parse_ver, expr=%s ver=%s" % (expr, ver))
            if not plugin in self.active:
                ParseDbg.add("parse_ver [VER] \"%s\" not active" % plugin)
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks
                return(True, expr)
            desc = plugin_description(self.datadir.find_path(plugin))
            match = re_header_version.search(desc)
            if match:
                p_ver_orig = match.group(1)
                p_ver = format_version(p_ver_orig)
                ParseDbg.add("parse_ver (header) version(%s) = %s (%s)" % (plugin, p_ver_orig, p_ver))
            else:
                match = re_filename_version.search(plugin)
                if match:
                    p_ver_orig = match.group(1)
                    p_ver = re_ver_delim.split(p_ver_orig)
                    ParseDbg.add("parse_ver (filename) version(%s) = %s (%s)" % (plugin, p_ver_orig, p_ver))
                else:
                    ParseDbg.add("parse_ver no version for %s" % plugin)
                    return(False, expr)
            ParseDbg.add("parse_ver compare  p_ver=%s %s ver=%s" % (p_ver, op, ver))
            if op == '=':
                return(p_ver == ver, expr)
            elif op == '<':
                return(p_ver < ver, expr)
            elif op == '>':
                return(p_ver > ver, expr)
            else:
                self.parse_error("Invalid [VER] operator: %s" %  self.buffer)
                return(None, None)
        self.parse_error("Invalid [VER] function: %s" %  self.buffer)
        return(None, None)

    def parse_desc(self):
        """match patterns against the description string in the plugin header."""
        match = re_desc_fun.match(self.buffer)
        if match:
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            ParseDbg.add("parse_desc new buffer = %s" % self.buffer)
            bang = match.group(1) # means to invert the meaning of the match
            pat = match.group(2)
            plugin = C.cname(match.group(3))
            expr = "[DESC %s/%s/ %s]" % (bang, pat, plugin)
            ParseDbg.add("parse_desc, expr=%s" % expr)
            if not plugin in self.active:
                ParseDbg.add("parse_desc [DESC] \"%s\" not active" % plugin)
                return(False, expr) # file does not exist
            if self.datadir == None:
                # this case is reached when doing fromfile checks,
                # which do not have access to the datadir, and hence
                # to the plugin header, so we always assume the test
                # is merely for file existence, to err on the side of
                # caution
                return(True, expr)
            re_pat = re.compile(pat)
            desc = plugin_description(self.datadir.find_path(plugin))
            bool = (re_pat.search(desc) != None)
            if bang == "!": bool = not bool
            ParseDbg.add("parse_desc [DESC] returning: (%s, %s)" % (bool, expr))
            return(bool, expr)
        self.parse_error("Invalid [DESC] function: %s" %  self.buffer)
        return(None, None)

    def parse_expression(self, prune=False):
        self.buffer = self.buffer.strip()
        if self.buffer == "":
            if self.readline():
                if re_rule.match(self.buffer):
                    ParseDbg.add("parse_expression new line started new rule, returning None")
                    return(None, None)
                self.buffer = self.buffer.strip()
            else:
                ParseDbg.add("parse_expression EOF, returning None")
                return(None, None)
        ParseDbg.add("parse_expression, start buffer: \"%s\"" % self.buffer)
        match = re_start_fun.match(self.buffer)
        if match:
            fun = match.group(1).upper()
            if fun == "DESC":
                ParseDbg.add("parse_expression calling parse_desc()")
                return(self.parse_desc())
            elif fun == "VER":
                ParseDbg.add("parse_expression calling parse_ver()")
                return(self.parse_ver())
            # otherwise it's a boolean function ...
            ParseDbg.add("parse_expression parsing expression: \"%s\"" % self.buffer)
            p = match.span(0)[1]
            self.buffer = self.buffer[p:]
            ParseDbg.add("fun = %s" % fun)
            vals = []
            exprs = []
            bool_end = re_end_fun.match(self.buffer)
            ParseDbg.add("self.buffer 1 =\"%s\"" % self.buffer)
            while not bool_end:
                (bool, expr) = self.parse_expression(prune)
                exprs.append(expr)
                vals.append(bool)
                ParseDbg.add("self.buffer 2 =\"%s\"" % self.buffer)
                bool_end = re_end_fun.match(self.buffer)
            pos = bool_end.span(0)[1]
            self.buffer = self.buffer[pos:]
            ParseDbg.add("self.buffer 3 =\"%s\"" % self.buffer)
            if fun == "ALL":
                # prune out uninteresting expressions from ANY results
                exprs = [e for e in exprs if not(isinstance(e, list) and e == [])]
                return(all(vals), exprs[0] if len(exprs) == 1 else ["ALL"] + exprs)
            if fun == "ANY":
                # prune out uninteresting expressions from ANY results
                if prune:
                    exprs = [e for e in exprs if not(isinstance(e, str) and e[0:8] == "MISSING(")]
                return(any(vals), exprs[0] if len(exprs) == 1 else ["ANY"] + exprs)
            if fun == "NOT":
                return(not(all(vals)), ["NOT"] + exprs)
            else:
                # should not be reached due to match on re_start_fun
                Msg.add("Program Error: %s: expected Boolean function (ALL, ANY, NOT): \"%s\"" % (self.where(), buff))
                return(None, None)
            ParseDbg.add("parse_expression NOTREACHED")
        else:
            ParseDbg.add("parse_expression parsing plugin: \"%s\"" % self.buffer)
            (exists, p) = self.parse_plugin_name()
            if exists != None and p != None:
                p = C.truename(p) if exists else ("MISSING(%s)" % C.truename(p))
            return(exists, p)
        ParseDbg.add("parse_expression NOTREACHED(2)")

    def pprint(self, expr, prefix):
        """pretty printer for parsed expressions"""
        formatted = PrettyPrinter(indent=2).pformat(expr)
        formatted = re_notstr.sub("NOT", formatted)
        formatted = re_anystr.sub("ANY", formatted)
        formatted = re_allstr.sub("ALL", formatted)
        return(re_indented.sub(prefix, formatted))

    def parse_statement(self, rule, msg, expr):
        ParseDbg.add("parse_statement(%s, %s, %s)" % (rule, msg, expr))
        expr = expr.strip()
        if msg == "":
            if expr == "":
                self.parse_message_block()
                expr = self.buffer
        else:
            self.message = [msg]
        if expr == "":
            if not self.readline():
                return
        else:
            self.buffer = expr
        msg = "" if self.message == [] else " |" + "\n |".join(self.message) # no ending LF
        if rule == "CONFLICT":  # takes any number of exprs
            exprs = []
            ParseDbg.add("before conflict parse_expr() expr=%s line=%s" % (expr, self.buffer))
            (bool, expr) = self.parse_expression()
            ParseDbg.add("conflict parse_expr()1 bool=%s bool=%s" % (bool, expr))
            while bool != None:
                if bool:
                    exprs.append(expr)
                (bool, expr) = self.parse_expression()
                ParseDbg.add("conflict parse_expr()N bool=%s bool=%s" % ("True" if bool else "False", expr))
            if len(exprs) > 1:
                Msg.add("[CONFLICT]")
                for e in exprs:
                    Msg.add(self.pprint(e, " > "))
                if msg != "": Msg.add(msg)
        elif rule == "NOTE":    # takes any number of exprs
            ParseDbg.add("function NOTE: %s" % msg)
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
            if bool1 != None:
                (bool2, expr2) = self.parse_expression()
            if bool2 == None:
                Msg.add("Warning: %s: PATCH rule must have 2 conditions" % (self.where()))
                return
            if bool1 and not bool2:
                # case where the patch is present but the thing to be patched is missing
                Msg.add("[PATCH]\n%s is missing some pre-requisites:\n%s" %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": Msg.add(msg)
            if bool2 and not bool1:
                # case where the patch is missing for the thing to be patched
                Msg.add("[PATCH]\n%s for:\n%s" %
                        (self.pprint(expr1, " !!"), self.pprint(expr2, " ")))
                if msg != "": Msg.add(msg)
        elif rule == "REQUIRES": # takes 2 exprs
            (bool1, expr1) = self.parse_expression(prune=True)
            if bool1 != None:
                (bool2, expr2) = self.parse_expression()
                ParseDbg.add("REQ expr2 == %s" % expr2)
                if bool2 == None:
                    self.parse_error("REQUIRES rule must have 2 conditions")
                    return
            if bool1 and not bool2:
                Msg.add("[REQUIRES]\n%s Requires:\n%s" %
                        (self.pprint(expr1, " !!!"), self.pprint(expr2, " > ")))
                if msg != "": Msg.add(msg)
        ParseDbg.add("parse_statement RETURNING")

    def read_rules(self, rule_file):
        """Read rules from rule files (e.g., mlox_user.txt or mlox_base.txt),
        add order rules to graph, and print warnings."""
        self.rule_file = rule_file
        ParseDbg.add("READING RULES FROM: \"%s\"" % self.rule_file)
        self.input_handle = myopen_file(self.rule_file, 'r')
        if self.input_handle == None:
            return False
        self.line_num = 0
        n_rules = 0
        while True:
            if self.buffer == "":
                if not self.readline():
                    break
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
                    self.parse_error("read_rules failed sanity check, unknown rule %s" % self.buffer)
                    self.buffer = ""
            else:
                self.parse_error("expected start of rule: \"%s\"" % self.buffer)
                self.buffer = ""
        loadup_msg("Read rules from: \"%s\"" % self.rule_file, n_rules, "rules")
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
            cycle_detected = "Warning: %s: Cycle detected, not adding: \"%s\" -> \"%s\"" % (where, C.truename(plug1), C.truename(plug2))
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
        print """Ordering Explanation:
This is a picture of all the plugins mlox thinks should follow %s
Child plugins are indented with respect to their parents
Lines beginning with '=' are plugins you don't have.
Lines beginning with '+' are plugins you do have.\n""" % what
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
            Msg.add("Error: Topological Sort Failed!")
            Dbg.add(PrettyPrinter(indent=4).pformat(self.nodes.items()))
            return None
        return sorted


class loadorder:
    """Class for reading plugin mod times (load order), and updating them based on rules"""
    def __init__(self):
        # order is the list of plugins in Data Files, ordered by mtime
        self.active = {}                   # current active plugins
        self.order = []                    # the load order
        self.game = None                   # Morrowind or Oblivion
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

    def find_parent_dir(self, file):
        """return the caseless_dirlist of the directory that contains file,
        starting from cwd and working back towards root."""
        path = os.getcwd()
        prev = None
        while path != prev:
            dl = caseless_dirlist(path)
            if dl.find_file(file):
                return(dl)
            prev = path
            path = os.path.split(path)[0]
        return(None)

    def find_game_dirs(self):
        self.gamedir = self.find_parent_dir("Morrowind.exe")
        if self.gamedir != None:
            self.game = "Morrowind"
            self.datadir = caseless_dirlist(self.gamedir.find_path("Data Files"))
        else:
            self.gamedir = self.find_parent_dir("Oblivion.exe")
            if self.gamedir != None:
                self.game = "Oblivion"
                self.datadir = caseless_dirlist(self.gamedir.find_path("Data"))
            else:
                self.game = "None"
                self.datadir = caseless_dirlist(".")
                self.gamedir = caseless_dirlist("..")
        Dbg.add("plugin directory: \"%s\"" % self.datadir.dirpath())

    def get_active_plugins(self):
        """Get the active list of plugins from the game configuration. Updates
        self.active and self.order and sorts in load order."""
        files = []
        # we look for the list of currently active plugins
        source = "Morrowind.ini"
        if self.game == "Morrowind":
            # find Morrowind.ini for Morrowind
            ini_path = self.gamedir.find_path(source)
            if ini_path == None:
                Msg.add("[%s not found, assuming running outside Morrowind directory]" % source)
                return
            ini = myopen_file(ini_path, 'r')
            if ini == None:
                return
            for line in ini:
                line.rstrip()
                gamefile = re_gamefile.match(line)
                if gamefile:
                    # we use caseless_dirlist.find_file(), so that the
                    # stored name of the plugin does not have to
                    # match the actual capitalization of the
                    # plugin name
                    f = self.datadir.find_file(gamefile.group(1))
                    # f will be None if the file has been removed from
                    # Data Files but still exists in the Morrowind.ini
                    # [Game Files] section
                    if f != None:
                        files.append(f)
            ini.close()
        else:
            # TBD
            appdata = find_appdata()
            if appdata == None:
                Dbg.add("Application data directory not found")
                return
            # TBD - verify location
            plugins_txt_path = os.path.join(appdata, "Oblivion", "Saves", "plugins.txt")
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
        (esm_files, esp_files) = self.partition_esps_and_esms(files)
        # sort the plugins into load order by modification date
        plugins = [C.cname(f) for f in self.sort_by_date(esm_files) + self.sort_by_date(esp_files)]
        loadup_msg("Getting active plugins from: \"%s\"" % source, len(plugins), "plugins")
        self.order = plugins
        for p in self.order:
            self.active[p] = True
        self.origin = "Active Plugins"

    def get_data_files(self):
        """Get the list of plugins from the data files directory. Updates self.active.
        If called,"""
        files = [f for f in self.datadir.filelist() if os.path.isfile(self.datadir.find_path(f))]
        (esm_files, esp_files) = self.partition_esps_and_esms(files)
        # sort the plugins into load order by modification date
        self.order = [C.cname(f) for f in self.sort_by_date(esm_files) + self.sort_by_date(esp_files)]
        loadup_msg("Getting list of plugins from plugin directory", len(self.order), "plugins")
        for p in self.order:
            self.active[p] = True
        self.origin = "Installed Plugins"

    def listversions(self):
        self.find_game_dirs()
        self.get_data_files()
        for p in self.order:
            match = re_filename_version.search(p)
            file_ver = match.group(1) if match else None
            desc = plugin_description(self.datadir.find_path(p))
            match = re_header_version.search(desc)
            desc_ver = match.group(1) if match else None
            print "%10s %10s    %s" % (file_ver, desc_ver, p)

    def read_from_file(self, fromfile):
        """Get the load order by reading an input file. This is mostly to help
        others debug their load order."""
        file = myopen_file(fromfile, 'r')
        if fromfile == None:
            return
        self.order = []
        for line in file.readlines():
            plugin_match = re_sloppy_plugin.match(line)
            if plugin_match:
                p = plugin_match.group(1)
                self.order.append(C.cname(p))
        Stats.add("%-50s (%3d plugins)" % ("\nReading plugins from file: \"%s\"" % fromfile, len(self.active)))
        for p in self.order:
            self.active[p] = True
        self.origin = "Plugin List from %s" % fromfile

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
        if self.game == "Morrowind":
            mtime_first = 1026943162 # Morrowind.esm
        else: # self.game == Oblivion
            mtime_first = 1165600070 # Oblivion.esm
        if len(files) > 1:
            mtime_last = int(time()) # today
            # sanity check
            if mtime_last < 1228683562: # Sun Dec  7 14:59:56 CST 2008
                mtime_last = 1228683562
            loadorder_mtime_increment = (mtime_last - mtime_first) / len(files)
            mtime = mtime_first
            for p in files:
                os.utime(self.datadir.find_path(p), (-1, mtime))
                mtime += loadorder_mtime_increment

    def save_order(self, filename, order, what):
        out = myopen_file(filename, 'w')
        if out == None:
            return
        for p in order:
            print >> out, p
        out.close()
        Msg.add("%s saved to: %s" % (what, filename))

    def update(self, fromfile):
        """Update the load order based on input rules."""
        Msg.flush()
        Stats.flush()
        New.flush()
        Old.flush()
        Stats.add("Version: %s" % full_version)
        if Opt.FromFile:
            self.read_from_file(fromfile)
            if len(self.order) == 0:
                Msg.add("No plugins detected. mlox.py understands lists of plugins in the format")
                Msg.add("used by Morrowind.ini or Wrye Mash. Is that what you used for input?")
                return(self)
        else:
            self.find_game_dirs()
            if Opt.GetAll:
                self.get_data_files()
            else:
                self.get_active_plugins()
                if self.order == []:
                    self.get_data_files()
            if self.order == []:
                Msg.add("No plugins detected! mlox needs to run somewhere under where the game is installed.")
                return(self)
        if Opt.DBG:
            Dbg.add("initial load order")
            for p in self.order:
                Dbg.add(p)
        # read rules from 3 sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        # primary rules are from mlox_user.txt
        parser = rule_parser(self.active, self.graph, self.datadir)
        parser.read_rules("mlox_user.txt")
        # secondary rules from mlox_base.txt
        if not parser.read_rules("mlox_base.txt"):
            Msg.add("Error: unable to open mlox_base.txt. You must run mlox in the directory where mlox_base.txt lives.")
            return(self)
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
            Msg.add("[Plugins already in sorted order. No sorting needed!]")
            self.sorted = True

        # print out the new load order
        if len(new_order_cname) != len(self.order):
            Msg.add("Program Error: sanity check: len(new_order_truename %d) != len(self.order %d)" % (len(new_order_truename), len(self.order)))
        if not Opt.FromFile:
            # these are things we do not want to do if just testing a load
            # order from a file (FromFile)
            if Opt.Update:
                self.update_mod_times(new_order_truename)
                Msg.add("[LOAD ORDER UPDATED!]")
                self.sorted = True
            else:
                if not Opt.GUI:
                    Msg.add("[Load Order NOT updated.]")
            # save the load orders to file for future reference
            self.save_order(old_loadorder_output, [C.truename(p) for p in self.order], "current")
            self.save_order(new_loadorder_output, new_order_truename, "mlox sorted")
        if not Opt.WarningsOnly:
            if Opt.GUI == False:
                if Opt.Update:
                    Msg.add("\n[UPDATED] New Load Order:\n---------------")
                else:
                    Msg.add("\n[Proposed] New Load Order:\n---------------")
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
        return(self)


class mlox_gui(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        self.can_update = True
        self.dir = os.getcwd()
        # setup widgets
        default_font = wx.Font(-1, family=wx.FONTFAMILY_DEFAULT, style=wx.FONTSTYLE_NORMAL,
                                weight=wx.FONTWEIGHT_NORMAL, underline=False, face="",
                                encoding=wx.FONTENCODING_SYSTEM)
        self.frame = wx.Frame(None, wx.ID_ANY, ("mlox %s" % Version))
        self.frame.SetSizeHints(800,600)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.logo = wx.Panel(self.frame, -1)
        wx.StaticBitmap(self.logo, bitmap=wx.BitmapFromImage(wx.Image("mlox.gif", wx.BITMAP_TYPE_GIF)))
        self.label_stats = wx.StaticText(self.frame, -1, Message["statistics"])
        self.txt_stats = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.label_msg = wx.StaticText(self.frame, -1, Message["messages"])
        self.txt_msg = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_msg.SetFont(default_font)
        self.label_cur = wx.StaticText(self.frame, -1, Message["current_load_order"])
        self.txt_cur = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL)
        self.label_cur_bottom = wx.StaticText(self.frame, -1, Message["click for options"])
        self.label_new = wx.StaticText(self.frame, -1, Message["new_load_order"])
        self.label_new_bottom = wx.StaticText(self.frame, -1, "")
        self.txt_new = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        # see if setting the font fixes display problems on Windows
        self.txt_new.SetFont(default_font)
        self.btn_update = wx.Button(self.frame, -1, Message["update"], size=(90,60))
        self.btn_quit = wx.Button(self.frame, -1, Message["quit"], size=(90,60))
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        self.btn_quit.Bind(wx.EVT_BUTTON, self.on_quit)
        # arrange widgets
        self.frame_vbox = wx.BoxSizer(wx.VERTICAL)
        self.frame_vbox.Add(self.label_stats, 0, wx.ALL)
        # top box for stats and logo
        self.top_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.top_hbox.Add(self.txt_stats, 1, wx.EXPAND)
        self.top_hbox.Add(self.logo, 0, wx.EXPAND)
        self.frame_vbox.Add(self.top_hbox, 0, wx.EXPAND)
        # box for message output
        self.msg_vbox = wx.BoxSizer(wx.VERTICAL)
        self.msg_vbox.Add(self.label_msg, 0, wx.ALL)
        self.msg_vbox.Add(self.txt_msg, 1, wx.EXPAND)
        self.frame_vbox.Add(self.msg_vbox, 1, wx.EXPAND)
        # box for load orders output
        self.lo_box = wx.BoxSizer(wx.HORIZONTAL)
        self.cur_vbox = wx.BoxSizer(wx.VERTICAL)
        self.cur_vbox.Add(self.label_cur, 0, wx.ALL|wx.CENTER)
        self.cur_vbox.Add(self.txt_cur, 4, wx.EXPAND)
        self.cur_vbox.Add(self.label_cur_bottom, 0, wx.ALL|wx.CENTER)
        self.lo_box.Add(self.cur_vbox, 4, wx.EXPAND)
        self.new_vbox = wx.BoxSizer(wx.VERTICAL)
        self.new_vbox.Add(self.label_new, 0, wx.ALL|wx.CENTER)
        self.new_vbox.Add(self.txt_new, 4, wx.EXPAND)
        self.new_vbox.Add(self.label_new_bottom, 0, wx.ALL|wx.CENTER)
        self.lo_box.Add(self.new_vbox, 4, wx.EXPAND)
        self.frame_vbox.Add(self.lo_box, 3, wx.EXPAND)
        # bottom box for buttons
        self.button_box = wx.BoxSizer(wx.HORIZONTAL)
        self.button_box.Add(self.btn_update, 4)
        self.button_box.Add(self.btn_quit, 0)
        self.frame_vbox.Add(self.button_box, 0, wx.EXPAND)
        # put em all together and that spells GUI
        self.frame.SetSizer(self.frame_vbox)
        self.frame_vbox.Fit(self.frame)
        # setup up rightclick menu handler for original load order pane
        self.txt_cur.Bind(wx.EVT_RIGHT_DOWN, self.right_click_handler)

    def highlight_warnings(self, txt):
        # highlight warnings in message window to help convey urgency
        # highlight styles:
        low = wx.TextAttr(colBack=wx.Colour(125,220,240))
        medium = wx.TextAttr(colBack=wx.Colour(255,255,180))
        high = wx.TextAttr(colBack=wx.Colour(255,180,180))
        happy = wx.TextAttr(colBack=wx.Colour(145,240,180))
        highlighters = {
            re.compile(r'^\[conflict\]', re.IGNORECASE): medium,
            re.compile(r'\[Plugins already in sorted order. No sorting needed!\]', re.IGNORECASE): happy }
        text = Msg.get()
        # for special highlighting
        for (re_pat, style) in highlighters.items():
            for match in re.finditer(re_pat, text):
                (start, end) = match.span()
                txt.SetStyle(start, end, style)
        # for leveled highlighting
        for (level, style) in (('!', low), ('!!', medium), ('!!!', high)):
            re_pat = re.compile("^ (?:\\| )?(%s.*)$" % level, re.MULTILINE)
            for match in re.finditer(re_pat, text):
                (start, end) = match.span()
                txt.SetStyle(start, end, style)

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
        self.txt_stats.SetValue(Stats.get())
        self.txt_msg.SetValue(Msg.get())
        self.highlight_warnings(self.txt_msg)
        self.txt_cur.SetValue(Old.get())
        self.txt_new.SetValue(New.get())
        self.label_cur.SetLabel(lo.origin)
        self.highlight_moved(self.txt_new)

    def start(self):
        self.frame.Show(True)
        self.analyze_loadorder(None)
        self.MainLoop()

    def on_quit(self, e):
        sys.exit(0)

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
        print >> out, Dbg.get()
        out.close()

    def right_click_handler(self, e):
        menu = wx.Menu()
        menu_items = [("Select All", self.menu_select_all_handler),
                      ("Paste", self.menu_paste_handler),
                      ("Open File", self.menu_open_file_handler),
                      ("Debug", self.menu_debug_handler)]
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
                        out.write(data.GetText().encode("utf-8"))
                        out.close()
                        Opt.FromFile = True
                        self.analyze_loadorder(clip_file)
            wx.TheClipboard.Close()

    def menu_open_file_handler(self, e):
        self.can_update = False
        dialog = wx.FileDialog(self.frame, message="Input from File", defaultDir=self.dir, defaultFile="", style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.dir = dialog.GetDirectory()
            Opt.FromFile = True
            self.analyze_loadorder(dialog.GetPath())

    def menu_debug_handler(self, e):
        # pop up a window containing the debug output
        dbg_frame = wx.Frame(None, wx.ID_ANY, ("%s - Debug Output" % full_version))
        dbg_frame.SetSizeHints(500,800)
        dbg_label = wx.StaticText(dbg_frame, -1, "[Debug Output Saved to \"%s\"]" % debug_output)
        dbg_txt = wx.TextCtrl(dbg_frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        dbg_btn_close = wx.Button(dbg_frame, -1, Message["close"], size=(90,60))
        dbg_btn_close.Bind(wx.EVT_BUTTON, lambda x: dbg_frame.Destroy())
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
    return("")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        Opt.GUI = True
    Dbg.add("\nmlox DEBUG DUMP:\n")
    # read in message strings
    def splitter(s): return(map(lambda x: x.strip("\n"), s.split("]]\n")))
    Message = dict(map(splitter, file("mlox.msg", 'r').read().split("\n[["))[1:])
    def usage(status):
        print Message["usage"]
        sys.exit(status)
    # Check Python version
    Dbg.add("Python Version: %s" % sys.version[:3])
    if float(sys.version[:3]) < 2.5:
        print Message["requiresPython25"]
        sys.exit(1)
    # run under psyco if available
    do_psyco = False
    try:
        import psyco
        psyco.full()
        do_psyco = True
        Dbg.add("Running under Pysco!")
    except:
        pass
    # process command line arguments
    Dbg.add("Command line: %s" % " ".join(sys.argv))
    try:
        opts, args = getopt(sys.argv[1:], "acde:fhlpquvw",
                            ["all", "base-only", "check", "debug", "explain", "fromfile", "help", 
                             "listversions", "parsedebug", "quiet", "update", "version", "warningsonly"])
    except GetoptError, err:
        print str(err)
        usage(2)                # exits
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
        elif opt in ("-e", "--explain"):
            Opt.Explain = arg
            Msg.prints = False
            Stats.prints = False
        elif opt in ("-f", "--fromfile"):
            Opt.FromFile = True
        elif opt in ("-h", "--help"):
            usage(0)            # exits
        elif opt in ("-l", "--listversions"):
            loadorder().listversions()
            sys.exit(0)
        elif opt in ("-p", "--parsedebug"):
            Opt.ParseDBG = True
        elif opt in ("-q", "--quiet"):
            Opt.Quiet = True
        elif opt in ("-u", "--update"):
            Opt.Update = True
        elif opt in ("-v", "--version"):
            print full_version
            sys.exit(0)
        elif opt in ("-w", "--warningsonly"):
            Opt.WarningsOnly = True

    if Opt.FromFile:
        if len(args) == 0:
            print "Error: -f specified, but no files on command line."
            usage(2)            # exits
        for file in args:
            loadorder().update(file)
    elif Opt.GUI == True:
        # run with gui
        Opt.DBG = True
        mlox_gui().start()
    else:
        # run with command line arguments
        loadorder().update(None)

