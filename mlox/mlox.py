#!/usr/bin/python
# -*- mode: python -*-
# Copyright 2008 John Moonsugar <john.moonsugar@gmail.com>
# License: MIT License (see the file: License.txt)
Version = "0.21"

import sys

"""
mlox - elder scrolls mod load order eXpert
"""

import getopt
import os
import re
import time
import pprint
import wx

Message = {}

class dynopt(dict):
    def __getattr__(self, item):
        return self.__getitem__(item)
    def __setattr__(self, item, value):
        self.__setitem__(item, value)

Opt = dynopt()

# command line options
Opt.GUI = False
Opt.DBG = False
Opt.FromFile = False
Opt.Update = False
Opt.Quiet = False
Opt.GetAll = False
Opt.WarningsOnly = False

# re_rule matches the start of a rule. We use a general pattern,
# instead of specifically testing each of the allowed commands, so the
# construction of the previous rule will still stop at the recognition
# of a new rule, even if it is misspelled.
re_rule = re.compile(r'\[([a-z]+)\]\s*$', re.IGNORECASE)
# re_ignore matches lines that we ignore, like blank lines
re_ignore = re.compile(r'^\s*$')
# line for multiline messages
re_message = re.compile(r'^\s')
# pattern matching a plugin in Morrowind.ini
re_gamefile = re.compile(r'GameFile\d+=([^\r\n]*)', re.IGNORECASE)
# pattern to match plugins in FromFile (somewhat looser than re_gamefile)
# this may be too sloppy, we could also look for the same prefix pattern,
# and remove that if present on all lines.
re_sloppy_plugin = re.compile(r'^(?:GameFile\d+=|\d{1,3} {1,2}|Plugin\d+\s*=\s*)?(.+\.es[mp])', re.IGNORECASE)
# pattern used to match a string that should only contain a plugin name, no slop
re_plugin = re.compile(r'^\S.*\.es[mp]$', re.IGNORECASE)

# output file for new load order
clip_file = "mlox_clip.txt"
old_loadorder_output = "current_loadorder.out"
new_loadorder_output = "mlox_new_loadorder.out"
debug_output = "mlox_debug.out"

class logger:
    def __init__(self, prints, *cohorts):
        self.log = []
        self.prints = prints
        self.cohorts = cohorts

    def add(self, message):
        self.log.append(message)
        for c in self.cohorts:
            c.add(message)
        if self.prints and Opt.GUI == False:
            print message

    def get(self):
        return("\n".join(self.log) + "\n").decode("ascii", "replace").encode("ascii", "replace")

    def flush(self):
        self.log = []

Dbg = logger(False)             # debug output
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
                if Opt.DBG:
                    Dbg.add(cycle_detected)
            else:
                Msg.add(cycle_detected)
            return False
        self.nodes.setdefault(plug1, [])
        if plug2 in self.nodes[plug1]: # edge already exists
            if Opt.DBG:
                Dbg.add("DBG: %s: Dup Edge: \"%s\" -> \"%s\"" % (where, C.truename(plug1), C.truename(plug2)))
            return True
        # add plug2 to the graph as a child of plug1
        self.nodes[plug1].append(plug2)
        self.incoming_count[plug2] = self.incoming_count.setdefault(plug2, 0) + 1
        if Opt.DBG:
            Dbg.add("DBG: adding edge: %s -> %s" % (plug1, plug2))
        return(True)

    def topo_sort(self):
        """topological sort, based on http://www.bitformation.com/art/python_toposort.html"""

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
            Dbg.add("DBG: graph before sort (node: children)")
            Dbg.add(pprint.PrettyPrinter(indent=4).pformat(self.nodes))
            Dbg.add("\nDBG: roots:\n  %s" % ("\n  ".join(roots)))
        if len(roots) > 0:
            # use the nearstart information to pull preferred plugins to top of load order
            (top_roots, roots) = remove_roots(roots, self.nearstart)
            # use the nearend information to pull those plugins to bottom of load order
            (bottom_roots, roots) = remove_roots(roots, self.nearend)
            middle_roots = roots        # any leftovers go in the middle
            roots = top_roots + middle_roots + bottom_roots
            if Opt.DBG:
                Dbg.add("DBG: nearstart:\n  %s" % ("\n  ".join(self.nearstart)))
                Dbg.add("DBG: top roots:\n  %s" % ("\n  ".join(top_roots)))
                Dbg.add("DBG: nearend:\n  %s" % ("\n  ".join(self.nearend)))
                Dbg.add("DBG: bottom roots:\n  %s" % ("\n  ".join(bottom_roots)))
                Dbg.add("DBG: middle roots:\n  %s" % ("\n  ".join(middle_roots)))
                Dbg.add("DBG: newroots:\n  %s" % ("\n  ".join(roots)))
        if Opt.DBG:
            Dbg.add("========== END TOPOLOGICAL SORT DEBUG INFO ==========\n")
        # now do the actual topological sort
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
            if Opt.DBG:
                Dbg.add(pprint.PrettyPrinter(indent=4).pformat(self.nodes.items()))
            return None
        return sorted


class loadorder:
    """Class for reading plugin mod times (load order), and updating them based on rules"""
    def __init__(self):
        # order is the list of plugins in Data Files, ordered by mtime
        self.active = []                   # current active plugins
        self.order = []                    # current datafiles, in load order
        self.msg_any = {}                  # [MsgAny] rules
        self.msg_all = []                  # [MsgAll] rules
        self.conflicts = {}                # [Conflict] rules
        self.reqall = []                   # [ReqAll] rules
        self.reqany = []                   # [ReqAny] rules
        self.allreq = []                   # [AllReq] rules
        self.anyreq = []                   # [AnyReq] rules
        self.patchxy = []                  # [PatchXY] rules
        self.game = None                   # Morrowind or Oblivion
        self.gamedir = None                # where game is installed
        self.datadir = None                # where plugins live
        self.graph = pluggraph()
        self.sorted = False

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

    def loadup_msg(self, msg, count, what):
        Stats.add("%-50s (%3d %s)" % (msg, count, what))

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
        if Opt.DBG:
            Dbg.add("plugin directory: \"%s\"" % self.datadir.dirpath())

    def get_active_plugins(self):
        """Get the active list of plugins from the game configuration. Updates
        self.active and self.order."""
        files = []
        # we look for the list of currently active plugins
        source = "Morrowind.ini"
        if self.game == "Morrowind":
            # find Morrowind.ini for Morrowind
            ini_path = self.gamedir.find_path(source)
            if ini_path == None:
                Msg.add("[%s not found, assuming running outside Morrowind directory]" % source)
                return
            try:
                ini = open(ini_path, 'r')
            except IOError, (errno, strerror):
                Msg.add("Error opening \"%s\" for input (%s)" % (source, strerror))
                return
            for line in ini.readlines():
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
            source = "Plugins.txt"
            return
        (esm_files, esp_files) = self.partition_esps_and_esms(files)
        # sort the plugins into load order by modification date
        plugins = [C.cname(f) for f in self.sort_by_date(esm_files) + self.sort_by_date(esp_files)]
        self.loadup_msg("Getting active plugins from: \"%s\"" % source, len(plugins), "plugins")
        self.active = plugins
        if self.order == []:
            self.order = plugins

    def get_data_files(self):
        """Get the list of plugins from the data files directory. Updates self.order.
        If called,"""
        files = []
        files = [f for f in self.datadir.filelist() if os.path.isfile(self.datadir.find_path(f))]
        (esm_files, esp_files) = self.partition_esps_and_esms(files)
        # sort the plugins into load order by modification date
        plugins = [C.cname(f) for f in self.sort_by_date(esm_files) + self.sort_by_date(esp_files)]
        self.loadup_msg("Getting list of plugins from plugin directory", len(plugins), "plugins")
        self.order = plugins
        if self.active == []:
            self.active = self.order

    def read_from_file(self, fromfile):
        """Get the load order by reading an input file. This is mostly to help
        others debug their load order."""
        try:
            file = open(fromfile, 'r')
        except IOError, (errno, strerror):
            Msg.add("Error opening \"%s\" for input (%s)" % (fromfile, strerror))
            return
        for line in file.readlines():
            plugin_match = re_sloppy_plugin.match(line)
            if plugin_match:
                p = plugin_match.group(1)
#                p_ascii = p.decode("ascii", "replace").encode("ascii", "replace")
#                if p != p_ascii:
#                    Msg.add("Warning: removed non-ascii characters from filename: %s" % p_ascii)
                self.order.append(C.cname(p))
        Stats.add("%-50s (%3d plugins)" % ("\nReading plugins from file: \"%s\"" % fromfile, len(self.order)))
        if self.active == []:
            self.active = self.order

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
        if Opt.DBG:
            Dbg.add("DBG: adding edges from CURRENT ORDER")
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

    def add_conflicts(self, message, conflicts):
        """Add new conflict rule information."""
        conflicts.sort()
        con2 = conflicts[:]
        for p1 in conflicts[:-1]:
            con2.pop(0)
            self.conflicts.setdefault(p1, {})
            for p2 in con2:
                if p1 != p2:
                    self.conflicts[p1][p2] = message

    def add_conflictsany(self, message, conflicts):
        """Add new conflict rule information."""
        p1 = conflicts[0]
        self.conflicts.setdefault(p1, {})
        for p2 in conflicts[1:]:
            self.conflicts[p1][p2] = message

    def check_conflicts(self):
        """Check for and print out known conflicts in active plugins."""
        for p1 in self.active:
            if p1 in self.conflicts:
                for (p2, msg) in self.conflicts[p1].items():
                    if p2 in self.active:
                        Msg.add("CONFLICT[\"%s\" <-> \"%s\"]%s" % (C.truename(p1), C.truename(p2),
                                                                   ":\n"+msg if msg != "" else ""))

    def check_reqall(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, p_reqs) in self.reqall:
            p = p_reqs.pop(0)
            if p in self.active:
                missing_reqs = [r for r in p_reqs if not r in self.active]
                if len(missing_reqs) == 0:
                    return
                Msg.add("REQALL[\"%s\"]: requires all of the following:" % C.truename(p))
                for r in missing_reqs:
                    Msg.add(" > %s" % C.truename(r))
                if msg != "":
                    Msg.add(msg)

    def check_reqany(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, p_reqs) in self.reqany:
            p = p_reqs.pop(0)
            if p in self.active:
                missing_reqs = [r for r in p_reqs if not r in self.active]
                if len(p_reqs) != len(missing_reqs):
                    return
                Msg.add("REQANY[\"%s\"]: requires at least one of the following:" % C.truename(p))
                for r in missing_reqs:
                    Msg.add(" > %s" % C.truename(r))
                if msg != "":
                    Msg.add(msg)

    def check_allreq(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, deps) in self.allreq:
            req = deps.pop()
            if all(p in self.active for p in deps):
                if not req in self.active:
                    plural = "" if len(deps) == 1 else "s"
                    Msg.add("ALLREQ[\"%s\"]: is required due to the following dependent%s:" % (C.truename(req), plural))
                    for r in deps:
                        Msg.add(" > %s" % C.truename(r))
                    if msg != "":
                        Msg.add(msg)

    def check_anyreq(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, deps) in self.anyreq:
            req = deps.pop()
            if any(p in self.active for p in deps):
                if not req in self.active:
                    plural = "" if len(deps) == 1 else "s"
                    Msg.add("ANYREQ[\"%s\"]: is required due to the following dependent%s:" % (C.truename(req), plural))
                    for r in deps:
                        if r in self.active:
                            Msg.add(" > %s" % C.truename(r))
                    if msg != "":
                        Msg.add(msg)

    def check_patchxy(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, plugins) in self.patchxy:
            # plugins is [ patch, plug_A, plug_B1, ... plug_BN ]
            patch = plugins[0]
            have_patch = patch in self.active
            plugA = plugins[1]
            have_plugA = plugA in self.active
            plugsB = plugins[2:]
            have_plugsB = any(p in self.active for p in plugsB)
            sufficient_reqs = have_plugA and have_plugsB
            #Msg.add("DBG: patch=%s(%s)  plugA=%s(%s)  plugsB=%s(%s)" % (patch, "T" if have_patch else "F", plugA, "T" if have_plugA else "F", ", ".join(plugsB), "T" if have_plugsB else "F"))
            if have_patch and not sufficient_reqs:
                Msg.add("PATCHXY[\"%s\"]: is missing some pre-requisites:" % C.truename(patch))
                if not have_plugA:
                    Msg.add(" > %s" % C.truename(plugA))
                if not have_plugsB:
                    if not have_plugA and len(plugsB) > 1:
                        Msg.add(" And any of these:")
                    for r in plugsB:
                        Msg.add(" > %s" % C.truename(r))
            if sufficient_reqs and not have_patch:
                Msg.add("PATCHXY[\"%s\"]: patch missing for these plugins:" % C.truename(patch))
                Msg.add(" > %s" % C.truename(plugA))
                for r in [p for p in plugsB if p in self.active]:
                    Msg.add(" > %s" % C.truename(r))

    def check_msg_any(self):
        """Check for and print out messages for active plugins."""
        for p in self.active:
            if p in self.msg_any:
                Msg.add("NOTE[\"%s\"]:\n%s" % (C.truename(p), self.msg_any[p]))

    def check_msg_all(self):
        """Check for and print out messages for groups of plugins in active plugins."""
        def addlen(x, y): return(x + len(y))
        for (msg, plist) in self.msg_all:
            if all (p in self.active for p in plist):
                if reduce(addlen, plist, 0) < 70:
                    Msg.add("NOTE[\"%s\"]\n%s" % ("\", \"".join([C.truename(p) for p in plist]), msg))
                else:
                    p = plist.pop(0)
                    note = "NOTE[\"%s\"" % C.truename(p)
                    while len(plist) > 0:
                        p = plist.pop(0)
                        note += (",\n     \"%s\"" % C.truename(p))
                    note += ("]\n%s" % msg)
                    Msg.add(note)

    def read_rules(self, rule_file):
        """Read rules from rule files (mlox_user.txt or mlox_base.txt), and add order rules
        to graph."""
        if Opt.DBG:
            Dbg.add("DBG: READING RULES FROM: \"%s\"" % rule_file)

        def check_plugin_name(name):
            if not re_plugin.match(name):
                Msg.add("Error: %s, expected a plugin name: %s" % (where, name))
                return(name)
            else:
                return(C.cname(name))

        def indent(msg):
            return("" if msg == [] else " |" + "\n |".join(msg))

        plugins = []
        curr_rule = None
        message = []
        n_order = 0
        prev = ""
        where = ""
        # check_end_conditions() is a closure over the preceding variables
        # and is merely used to avoid code duplication as it is used twice
        # below since a rule ends when a new one starts or at EOF
        def check_end_conditions():
            msg = indent(message)
            if (curr_rule in ("MSGALL", "MSGANY") and len(plugins) == 0):
                Msg.add("Warning: %s: %s rule needs at least 2 plugin arguments" % (where, curr_rule))
                return
            if (curr_rule in ("CONFLICT", "CONFLICTANY", "REQALL", "REQANY", "ALLREQ", "ANYREQ") and
                len(plugins) < 2):
                Msg.add("Warning: %s: %s rule needs at least 2 plugin arguments" % (where, curr_rule))
                return
            if curr_rule == "CONFLICT":
                self.add_conflicts(msg, plugins)
            elif curr_rule == "CONFLICTANY":
                self.add_conflictsany(msg, plugins)
            elif curr_rule == "MSGALL":
                self.msg_all.append((msg, plugins))
            elif curr_rule == "MSGANY":
                for p in plugins:
                    self.msg_any[p] = indent(message)
            elif curr_rule == "PATCHXY":
                if len(plugins) < 3:
                    Msg.add("Warning: %s: PatchXY rule needs at least 3 plugin arguments" % where)
                    return
                self.patchxy.append((msg, plugins))
            elif curr_rule == "REQALL":
                self.reqall.append((msg, plugins))
            elif curr_rule == "REQANY":
                self.reqany.append((msg, plugins))
            elif curr_rule == "ALLREQ":
                self.allreq.append((msg, plugins))
            elif curr_rule == "ANYREQ":
                self.anyreq.append((msg, plugins))
            elif curr_rule == "ORDER":
                if n_order == 0:
                    Msg.add("Warning: %s: ORDER rule has no entries" % (where))
                elif n_order == 1:
                    Msg.add("Warning: %s: ORDER rule skipped because it only has one entry: %s" % (where, C.truename(prev)))

        try:
            rules = open(rule_file, 'r')
        except IOError, (errno, strerror):
            if Opt.DBG:
                Dbg.add("Error opening \"%s\" for input (%s)" % (rule_file, strerror))
            return False

        line_num = 0
        n_rules = 0
        for line in rules.readlines():
            line = line.split('#')[0] # remove all comments
            line = line.rstrip()
            line_num += 1
            if re_ignore.match(line):
                continue        # next line
            new_rule = re_rule.match(line)
            if new_rule:        # start a new rule
                check_end_conditions()
                n_rules += 1
                where = ("%s:%d" % (rule_file, line_num))
                plugins = []
                curr_rule = new_rule.group(1).upper()
                message = []
                n_order = 0
                prev = ""
                if not curr_rule in ("CONFLICT", "CONFLICTANY", "MSGALL", "MSGANY",
                                     "ORDER", "NEAREND", "NEARSTART", "PATCHXY",
                                     "REQALL", "REQANY", "ANYREQ", "ALLREQ", ):
                    Msg.add("Error: %s, unknown rule: %s" % (where, line))
                continue        # next line
            if curr_rule == "ORDER":
                n_order += 1
                cn = check_plugin_name(line)
                if prev != "":
                    self.graph.add_edge(where, prev, cn)
                prev = cn
            elif curr_rule == "NEARSTART":
                p = check_plugin_name(line)
                self.graph.nearstart.append(p)
                self.graph.nodes.setdefault(p, [])
            elif curr_rule == "NEAREND":
                p = check_plugin_name(line)
                self.graph.nearend.append(p)
                self.graph.nodes.setdefault(p, [])
            elif curr_rule in ("REQALL", "REQANY", "ALLREQ", "ANYREQ", "PATCHXY", "MSGALL", "MSGANY", "CONFLICT", "CONFLICTANY"):
                if re_message.match(line):
                    message.append(line)
                else:
                    plugins.append(check_plugin_name(line))
        check_end_conditions()
        rules.close()
        self.loadup_msg("Reading rules from: \"%s\"" % rule_file, n_rules, "rules")
        return True             # read_rules()

    def update_mod_times(self, files):
        """change the modification times of files to be in order of file list,
        oldest to newest"""
        if self.game == "Morrowind":
            mtime_first = 1026943162 # Morrowind.esm
        else: # self.game == Oblivion
            mtime_first = 1165600070 # Oblivion.esm
        if len(files) > 1:
            mtime_last = int(time.time()) # today
            # sanity check
            if mtime_last < 1228683562: # Sun Dec  7 14:59:56 CST 2008
                mtime_last = 1228683562
            loadorder_mtime_increment = (mtime_last - mtime_first) / len(files)
            mtime = mtime_first
            for p in files:
                os.utime(self.datadir.find_path(p), (-1, mtime))
                mtime += loadorder_mtime_increment

    def save_order(self, filename, order, what):
        try:
            out = open(filename, 'w')
            for p in order:
                print >> out, p
            out.close()
        except IOError, (errno, strerror):
            Msg.add("Error opening \"%s\" for output (%s)" % (filename, strerror))
            return
        Msg.add("%s saved to: %s" % (what, filename))

    def update(self, fromfile):
        """Update the load order based on input rules."""
        Msg.flush()
        Stats.flush()
        New.flush()
        Old.flush()
        if Opt.FromFile:
            self.read_from_file(fromfile)
            if len(self.order) == 0:
                Msg.add("No plugins detected. mlox.py understands lists of plugins in the format")
                Msg.add("used by Morrowind.ini or Wrye Mash. Is that what you used for input?")
                return(self)
        else:
            self.find_game_dirs()
            self.get_data_files()
            if not Opt.GetAll:
                self.get_active_plugins()
            if len(self.order) == 0:
                Msg.add("No plugins detected! mlox needs to run somewhere under where the game is installed.")
                return(self)
        if Opt.DBG:
            Dbg.add("DBG: initial load order")
            for p in self.order:
                Dbg.add(p)
        # read rules from 3 sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        self.read_rules("mlox_user.txt")  # primary rules are from mlox_user.txt
        if not self.read_rules("mlox_base.txt"):  # secondary rules from mlox_base.txt
            Msg.add("Error: unable to open mlox_base.txt. You must run mlox in the directory where mlox_base.txt lives.")
            return(self)
        self.add_current_order()       # tertiary rules from current load order
        # now do the topological sort of all known plugins (rules + load order)
        sorted = self.graph.topo_sort()
        # the "sorted" list will be a superset of all known plugin files,
        # inluding those in our Data Files directory.
        # but we only want to update plugins that are in our current "Data Files"
        datafiles = {}
        n = 1
        orig_index = {}
        for p in self.order:
            datafiles[p] = True
            orig_index[p] = n
            Old.add("_%03d_ %s" % (n, C.truename(p)))
            n += 1
        sorted_datafiles = [f for f in sorted if f in datafiles]
        (esm_files, esp_files) = self.partition_esps_and_esms(sorted_datafiles)
        new_order_cname = [p for p in esm_files + esp_files]
        new_order_truename = [C.truename(p) for p in new_order_cname]

        if self.order == new_order_cname:
            Msg.add("[Plugins already in sorted order. No sorting needed!")
            self.sorted = True

        # print out detected missing requisites
        self.check_patchxy()
        self.check_reqall()
        self.check_reqany()
        self.check_allreq()
        self.check_anyreq()
        # print out detected conflicts
        self.check_conflicts()
        if not Opt.Quiet:
            # print out applicable messages
            self.check_msg_any()
            self.check_msg_all()
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
        self.frame = wx.Frame(None, wx.ID_ANY, ("mlox %s" % Version))
        self.frame.SetSizeHints(800,600)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.logo = wx.Panel(self.frame, -1)
        wx.StaticBitmap(self.logo, bitmap=wx.BitmapFromImage(wx.Image("mlox.gif", wx.BITMAP_TYPE_GIF)))
        self.label_stats = wx.StaticText(self.frame, -1, Message["statistics"])
        self.txt_stats = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_NO_VSCROLL)
        self.label_msg = wx.StaticText(self.frame, -1, Message["messages"])
        self.txt_msg = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.label_cur = wx.StaticText(self.frame, -1, Message["current_load_order"])
        self.txt_cur = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.label_cur_bottom = wx.StaticText(self.frame, -1, Message["click for options"])
        self.label_new = wx.StaticText(self.frame, -1, Message["new_load_order"])
        self.label_new_bottom = wx.StaticText(self.frame, -1, "")
        self.txt_new = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
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

    def highlight_moved(self, txt):
        # hightlight background color for changed items in txt widget
        highlight = wx.TextAttr(colBack=wx.Colour(255,255,180))
        re_start = re.compile(r'[^_]\d+[^_][^\n]+')
        text = New.get()
        for m in re.finditer(re_start, text):
            (start, end) = m.span()
            if text[start] == '*': txt.SetStyle(start, end, highlight)

    def analyze_loadorder(self, fromfile):
        if loadorder().update(fromfile).sorted:
            self.can_update = False
        if not self.can_update:
            self.btn_update.Disable()
        self.txt_stats.SetValue(Stats.get())
        self.txt_msg.SetValue(Msg.get())
        self.txt_cur.SetValue(Old.get())
        self.txt_new.SetValue(New.get())
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
        loadorder().update(None)
        self.txt_stats.SetValue(Stats.get())
        self.txt_msg.SetValue(Msg.get())
        self.txt_new.SetValue(New.get())
        self.highlight_moved(self.txt_new)
        self.can_update = False
        self.btn_update.Disable()

    def on_close(self, e):
        self.on_quit(e)

    def bugdump(self):
        try:
            out = open(debug_output, 'w')
            print >> out, Dbg.get()
            out.close()
        except IOError, (errno, strerror):
            print >> sys.stderr, "Error opening \"%s\" for output (%s)" % (debug_output, strerror)
            return

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
                    out = open(clip_file, 'w')
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
        dbg_frame = wx.Frame(None, wx.ID_ANY, ("mlox %s - Debug Output" % Version))
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
        opts, args = getopt.getopt(sys.argv[1:], "acdfhquvw",
                                   ["all", "check", "debug", "fromfile", "help",
                                    "quiet", "update", "version", "warningsonly"])
    except getopt.GetoptError, err:
        print str(err)
        usage(2)                # exits
    for opt, arg in opts:
        if opt in   ("-a", "--all"):
            Opt.GetAll = True
        elif opt in ("-c", "--check"):
            Opt.Update = False
        elif opt in ("-d", "--debug"):
            Opt.DBG = True
        elif opt in ("-f", "--fromfile"):
            Opt.FromFile = True
        elif opt in ("-h", "--help"):
            usage(0)            # exits
        elif opt in ("-q", "--quiet"):
            Opt.Quiet = True
        elif opt in ("-u", "--update"):
            Opt.Update = True
        elif opt in ("-v", "--version"):
            print "mlox Version: %s" % Version
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
    if Opt.DBG and not Opt.GUI:
        print >> sys.stderr, Dbg.get()
