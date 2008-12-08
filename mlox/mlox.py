#!/usr/bin/python
# -*- mode: python -*-
# by John Moonsugar <john.moonsugar@gmail.com>
# License: this project is released in the Public Domain.
Version = "0.17"

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

class options:
    def __init__(self):
        self.options = {}
    def get(self, key):
        return(self.options[key])
    def set(self, key, val):
        self.options[key] = val

Opt = options()

# command line options
Opt.set("GUI", False)
Opt.set("DBG", False)
Opt.set("FromFile", False)
Opt.set("Update", False)
Opt.set("Quiet", False)
Opt.set("GetAll", False)
Opt.set("WarningsOnly", False)

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
old_loadorder_output = "current_loadorder.out"
new_loadorder_output = "mlox_new_loadorder.out"

class logger:
    def __init__(self, prints):
        self.log = []
        self.prints = prints

    def add(self, message):
        self.log.append(message)
        if self.prints and Opt.get("GUI") == False:
            print message

    def get(self):
        return("\n".join(self.log))

    def flush(self):
        self.log = []

New = logger(True)
Old = logger(False)
Stats = logger(True)
Warn = logger(True)


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
            if Opt.get("DBG") or where != "":
                Warn.add("Warning: %s: Cycle detected, not adding: \"%s\" -> \"%s\"" % (where, C.truename(plug1), C.truename(plug2)))
            return False
        self.nodes.setdefault(plug1, [])
        if plug2 in self.nodes[plug1]: # edge already exists
            if Opt.get("DBG"):
                Warn.add("DBG: %s: Dup Edge: \"%s\" -> \"%s\"" % (where, C.truename(plug1), C.truename(plug2)))
            return True
        # add plug2 to the graph as a child of plug1
        self.nodes[plug1].append(plug2)
        self.incoming_count[plug2] = self.incoming_count.setdefault(plug2, 0) + 1
        if Opt.get("DBG"):
            Warn.add("DBG: adding edge: %s -> %s" % (plug1, plug2))
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
        if Opt.get("DBG"):
            Warn.add("\n========== BEGIN TOPOLOGICAL SORT DEBUG INFO ==========")
            self.dump("DBG: graph before sort (node: children)")
            Warn.add("\nDBG: roots:\n  %s" % ("\n  ".join(roots)))
        if len(roots) > 0:
            # use the nearstart information to pull preferred plugins to top of load order
            (top_roots, roots) = remove_roots(roots, self.nearstart)
            # use the nearend information to pull those plugins to bottom of load order
            (bottom_roots, roots) = remove_roots(roots, self.nearend)
            middle_roots = roots        # any leftovers go in the middle
            roots = top_roots + middle_roots + bottom_roots
            if Opt.get("DBG"):
                Warn.add("DBG: nearstart:\n  %s" % ("\n  ".join(self.nearstart)))
                Warn.add("DBG: top roots:\n  %s" % ("\n  ".join(top_roots)))
                Warn.add("DBG: nearend:\n  %s" % ("\n  ".join(self.nearend)))
                Warn.add("DBG: bottom roots:\n  %s" % ("\n  ".join(bottom_roots)))
                Warn.add("DBG: middle roots:\n  %s" % ("\n  ".join(middle_roots)))
                Warn.add("DBG: newroots:\n  %s" % ("\n  ".join(roots)))
        if Opt.get("DBG"):
            Warn.add("========== END TOPOLOGICAL SORT DEBUG INFO ==========\n")
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
            Warn.add("Error: Topological Sort Failed!")
            Warn.add(pprint.PrettyPrinter(indent=4).pformat(self.nodes.items()))
            return None
        return sorted

    def dump(self, msg):
        """Dump our internal graph so we can look at it."""
        Warn.add(msg)
        Warn.add(pprint.PrettyPrinter(indent=4).pformat(self.nodes))

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
        if Opt.get("DBG"):
            Warn.add("plugin directory: \"%s\"" % self.datadir.dirpath())

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
                Warn.add("[%s not found, assuming running outside Morrowind directory]" % source)
                return
            try:
                ini = open(ini_path, 'r')
            except IOError, (errno, strerror):
                Warn.add("Error opening \"%s\" for input (%s)" % (source, strerror))
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
            Warn.add("Error opening \"%s\" for input (%s)" % (fromfile, strerror))
            return
        for line in file.readlines():
            plugin_match = re_sloppy_plugin.match(line)
            if plugin_match:
                self.order.append(C.cname(plugin_match.group(1)))
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
        if Opt.get("DBG"):
            Warn.add("DBG: ADDING RULES CURRENT ORDER")
        prev_i = 0
        self.graph.nodes.setdefault(self.order[0], [])
        for curr_i in range(1, len(self.order)):
            if (self.order[prev_i] in self.graph.nearstart or
                self.order[curr_i] in self.graph.nearstart or
                self.order[prev_i] in self.graph.nearend or
                self.order[curr_i] in self.graph.nearend):
                # just add a node
                self.graph.nodes.setdefault(self.order[curr_i], [])
            else:
                # add an edge, on any failure due to cycle detection, we try
                # to make an edge between the current plugin and the previous
                # "parent"
                for i in range(prev_i, prev_i - 5, -1):
                    if i < 1:
                        break
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
                        Warn.add("CONFLICT[\"%s\" <-> \"%s\"]%s" % (C.truename(p1), C.truename(p2),
                                                                   ":\n"+msg if msg != "" else ""))

    def check_reqall(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, p_reqs) in self.reqall:
            p = p_reqs.pop(0)
            if p in self.active:
                missing_reqs = [r for r in p_reqs if not r in self.active]
                if len(missing_reqs) == 0:
                    return
                Warn.add("REQALL[\"%s\"]: requires all of the following:" % C.truename(p))
                for r in missing_reqs:
                    Warn.add(" > %s" % C.truename(r))
                if msg != "":
                    Warn.add(msg)

    def check_reqany(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, p_reqs) in self.reqany:
            p = p_reqs.pop(0)
            if p in self.active:
                missing_reqs = [r for r in p_reqs if not r in self.active]
                if len(p_reqs) != len(missing_reqs):
                    return
                Warn.add("REQANY[\"%s\"]: requires at least one of the following:" % C.truename(p))
                for r in missing_reqs:
                    Warn.add(" > %s" % C.truename(r))
                if msg != "":
                    Warn.add(msg)

    def check_allreq(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, deps) in self.allreq:
            req = deps.pop()
            if all(p in self.active for p in deps):
                if not req in self.active:
                    plural = "" if len(deps) == 1 else "s"
                    Warn.add("ALLREQ[\"%s\"]: is required due to the following dependent%s:" % (C.truename(req), plural))
                    for r in deps:
                        Warn.add(" > %s" % C.truename(r))
                    if msg != "":
                        Warn.add(msg)

    def check_anyreq(self):
        """Check for and print out known missing pre-requisites for active plugins."""
        for (msg, deps) in self.anyreq:
            req = deps.pop()
            if any(p in self.active for p in deps):
                if not req in self.active:
                    plural = "" if len(deps) == 1 else "s"
                    Warn.add("ANYREQ[\"%s\"]: is required due to the following dependent%s:" % (C.truename(req), plural))
                    for r in deps:
                        if r in self.active:
                            Warn.add(" > %s" % C.truename(r))
                    if msg != "":
                        Warn.add(msg)

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
            #Warn.add("DBG: patch=%s(%s)  plugA=%s(%s)  plugsB=%s(%s)" % (patch, "T" if have_patch else "F", plugA, "T" if have_plugA else "F", ", ".join(plugsB), "T" if have_plugsB else "F"))
            if have_patch and not sufficient_reqs:
                Warn.add("PATCHXY[\"%s\"]: is missing some pre-requisites:" % C.truename(patch))
                if not have_plugA:
                    Warn.add(" > %s" % C.truename(plugA))
                if not have_plugsB:
                    if not have_plugA and len(plugsB) > 1:
                        Warn.add(" And any of these:")
                    for r in plugsB:
                        Warn.add(" > %s" % C.truename(r))
            if sufficient_reqs and not have_patch:
                Warn.add("PATCHXY[\"%s\"]: patch missing for these plugins:" % C.truename(patch))
                Warn.add(" > %s" % C.truename(plugA))
                for r in [p for p in plugsB if p in self.active]:
                    Warn.add(" > %s" % C.truename(r))

    def check_msg_any(self):
        """Check for and print out messages for active plugins."""
        for p in self.active:
            if p in self.msg_any:
                Warn.add("NOTE[\"%s\"]:\n%s" % (C.truename(p), self.msg_any[p]))

    def check_msg_all(self):
        """Check for and print out messages for groups of plugins in active plugins."""
        def addlen(x, y): return(x + len(y))
        for (msg, plist) in self.msg_all:
            if all (p in self.active for p in plist):
                if reduce(addlen, plist, 0) < 70:
                    Warn.add("NOTE[\"%s\"]\n%s" % ("\", \"".join([C.truename(p) for p in plist]), msg))
                else:
                    p = plist.pop(0)
                    note = "NOTE[\"%s\"" % C.truename(p)
                    while len(plist) > 0:
                        p = plist.pop(0)
                        note += (",\n     \"%s\"" % C.truename(p))
                    note += ("]\n%s" % msg)
                    Warn.add(note)

    def read_rules(self, rule_file):
        """Read rules from rule files (mlox_user.txt or mlox_base.txt), and add order rules
        to graph."""
        if Opt.get("DBG"):
            Warn.add("DBG: READING RULES FROM: \"%s\"" % rule_file)

        def check_plugin_name(name):
            if not re_plugin.match(name):
                Warn.add("Error: %s, expected a plugin name: %s" % (where, name))
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
                Warn.add("Warning: %s: %s rule needs at least 2 plugin arguments" % (where, curr_rule))
                return
            if (curr_rule in ("CONFLICT", "CONFLICTANY", "REQALL", "REQANY", "ALLREQ", "ANYREQ") and
                len(plugins) < 2):
                Warn.add("Warning: %s: %s rule needs at least 2 plugin arguments" % (where, curr_rule))
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
                    Warn.add("Warning: %s: PatchXY rule needs at least 3 plugin arguments" % where_rule)
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
                    Warn.add("Warning: %s: ORDER rule has no entries" % (where))
                elif n_order == 1:
                    Warn.add("Warning: %s: ORDER rule skipped because it only has one entry: %s" % (where, C.truename(prev)))

        try:
            rules = open(rule_file, 'r')
        except IOError, (errno, strerror):
            if Opt.get("DBG"):
                Warn.add("Error opening \"%s\" for input (%s)" % (rule_file, strerror))
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
                    Warn.add("Error: %s, unknown rule: %s" % (where, line))
                continue        # next line
            if curr_rule == "ORDER":
                n_order += 1
                cn = check_plugin_name(line)
                if prev != "":
                    self.graph.add_edge(where, prev, cn)
                prev = cn
            elif curr_rule == "NEARSTART":
                self.graph.nearstart.append(check_plugin_name(line))
            elif curr_rule == "NEAREND":
                self.graph.nearend.append(check_plugin_name(line))
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
            Warn.add("Error opening \"%s\" for output (%s)" % (filename, strerror))
            return
        Warn.add("%s saved to: %s" % (what, filename))

    def update(self, fromfile):
        """Update the load order based on input rules."""
        Warn.flush()
        Stats.flush()
        New.flush()
        Old.flush()
        if Opt.get("FromFile"):
            self.read_from_file(fromfile)
            if len(self.order) == 0:
                Warn.add("No plugins detected. mlox.py understands lists of plugins in the format")
                Warn.add("used by Morrowind.ini or Wrye Mash. Is that what you used for input?")
                return
        else:
            self.find_game_dirs()
            self.get_data_files()
            if not Opt.get("GetAll"):
                self.get_active_plugins()
            if len(self.order) == 0:
                Warn.add("No plugins detected! mlox needs to run somewhere under where the game is installed.")
                return
        if Opt.get("DBG"):
            Warn.add("DBG: initial load order")
            for p in self.order:
                Warn.add(p)
        # read rules from 3 sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        self.read_rules("mlox_user.txt")  # primary rules are from mlox_user.txt
        if not self.read_rules("mlox_base.txt"):  # secondary rules from mlox_base.txt
            Warn.add("Error: unable to open mlox_base.txt. You must run mlox in the directory where mlox_base.txt lives.")
            return
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
        # print out detected missing requisites
        self.check_patchxy()
        self.check_reqall()
        self.check_reqany()
        self.check_allreq()
        self.check_anyreq()
        # print out detected conflicts
        self.check_conflicts()
        if not Opt.get("Quiet"):
            # print out applicable messages
            self.check_msg_any()
            self.check_msg_all()
        # print out the new load order
        (esm_files, esp_files) = self.partition_esps_and_esms(sorted_datafiles)
        loadorder_files = [C.truename(p) for p in esm_files + esp_files]
        if len(loadorder_files) != len(self.order):
            Warn.add("Program Error: failed sanity check: len(loadorder_files) != len(self.order)")
        if not Opt.get("FromFile"):
            # these are things we do not want to do if just testing a load
            # order from a file (FromFile)
            if Opt.get("Update"):
                self.update_mod_times(loadorder_files)
                Warn.add("[LOAD ORDER UPDATED!]")
            else:
                if not Opt.get("GUI"):
                    Warn.add("[Load Order NOT updated.]")
            # save the load orders to file for future reference
            self.save_order(old_loadorder_output, self.order, "current")
            self.save_order(new_loadorder_output, loadorder_files, "mlox sorted")
        if not Opt.get("WarningsOnly"):
            if Opt.get("GUI") == False:
                if Opt.get("Update"):
                    Warn.add("\n[UPDATED] New Load Order:\n---------------")
                else:
                    Warn.add("\n[Proposed] New Load Order:\n---------------")
            # highlight mods that have moved up in the load order
            highlight = "_"
            for i in range(0, len(loadorder_files)):
                p = loadorder_files[i]
                curr = p.lower()
                if (orig_index[curr] - 1) > i: highlight = "*"
                New.add("%s%03d%s %s" % (highlight, orig_index[curr], highlight, p))
                if highlight == "*":
                    if i < len(loadorder_files) - 1:
                        next = loadorder_files[i+1].lower()
                    if (orig_index[curr] > orig_index[next]):
                        highlight = "_"

class mlox_gui(wx.App):
    def __init__(self):
        wx.App.__init__(self)
        self.can_update = True
        # setup widgets
        self.frame = wx.Frame(None, wx.ID_ANY, ("mlox %s" % Version))
        self.frame.SetSizeHints(800,600)
        self.frame.SetBackgroundColour(wx.SystemSettings.GetColour(wx.SYS_COLOUR_3DFACE))
        self.frame.panel_logo = wx.Panel(self.frame, -1)
        self.frame.image_logo = wx.Image("mlox.gif", wx.BITMAP_TYPE_GIF)
        self.frame.bmp_logo = wx.StaticBitmap(self.frame.panel_logo, bitmap=wx.BitmapFromImage(self.frame.image_logo))
        self.frame.label_stats = wx.StaticText(self.frame, -1, Message["statistics"])
        self.frame.txt_stats = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_NO_VSCROLL)
        self.frame.label_msg = wx.StaticText(self.frame, -1, Message["messages"])
        self.frame.txt_msg = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.frame.label_cur = wx.StaticText(self.frame, -1, Message["current_load_order"])
        self.frame.txt_cur = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.frame.label_new = wx.StaticText(self.frame, -1, Message["new_load_order"])
        self.frame.txt_new = wx.TextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE)
        self.frame.btn_update = wx.Button(self.frame, -1, Message["update"], size=(90,60))
        self.frame.btn_quit = wx.Button(self.frame, -1, Message["quit"], size=(90,60))
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.btn_update.Bind(wx.EVT_BUTTON, self.on_update)
        self.frame.btn_quit.Bind(wx.EVT_BUTTON, self.on_quit)
        # arrange widgets
        self.frame.frame_vbox = wx.BoxSizer(wx.VERTICAL)
        self.frame.frame_vbox.Add(self.frame.label_stats, 0, wx.ALL)
        # top box for stats and logo
        self.frame.top_hbox = wx.BoxSizer(wx.HORIZONTAL)
        self.frame.top_hbox.Add(self.frame.txt_stats, 1, wx.EXPAND)
        self.frame.top_hbox.Add(self.frame.panel_logo, 0, wx.EXPAND)
        self.frame.frame_vbox.Add(self.frame.top_hbox, 0, wx.EXPAND)
        # box for message output
        self.frame.msg_vbox = wx.BoxSizer(wx.VERTICAL)
        self.frame.msg_vbox.Add(self.frame.label_msg, 0, wx.ALL)
        self.frame.msg_vbox.Add(self.frame.txt_msg, 1, wx.EXPAND)
        self.frame.frame_vbox.Add(self.frame.msg_vbox, 1, wx.EXPAND)
        # box for load orders output
        self.frame.lo_box = wx.BoxSizer(wx.HORIZONTAL)
        self.frame.cur_vbox = wx.BoxSizer(wx.VERTICAL)
        self.frame.cur_vbox.Add(self.frame.label_cur, 0, wx.ALL|wx.CENTER)
        self.frame.cur_vbox.Add(self.frame.txt_cur, 4, wx.EXPAND)
        self.frame.lo_box.Add(self.frame.cur_vbox, 4, wx.EXPAND)
        self.frame.new_vbox = wx.BoxSizer(wx.VERTICAL)
        self.frame.new_vbox.Add(self.frame.label_new, 0, wx.ALL|wx.CENTER)
        self.frame.new_vbox.Add(self.frame.txt_new, 4, wx.EXPAND)
        self.frame.lo_box.Add(self.frame.new_vbox, 4, wx.EXPAND)
        self.frame.frame_vbox.Add(self.frame.lo_box, 3, wx.EXPAND)
        # bottom box for buttons
        self.frame.button_box = wx.BoxSizer(wx.HORIZONTAL)
        self.frame.button_box.Add(self.frame.btn_update, 4)
        self.frame.button_box.Add(self.frame.btn_quit, 0)
        self.frame.frame_vbox.Add(self.frame.button_box, 0, wx.EXPAND)
        # put em all together and that spells GUI
        self.frame.SetSizer(self.frame.frame_vbox)
        self.frame.frame_vbox.Fit(self.frame)

    def highlight_moved(self, txt):
        # hightlight background color for changed items in txt widget
        highlight = wx.TextAttr(colBack=wx.Colour(255,255,180))
        re_start = re.compile(r'[^_]\d+[^_][^\n]+')
        text = New.get()
        for m in re.finditer(re_start, text):
            (start, end) = m.span()
            if text[start] == '*': txt.SetStyle(start, end, highlight)

    def start(self):
        self.frame.Show(True)
        loadorder().update(None)
        self.frame.txt_stats.SetValue(Stats.get())
        self.frame.txt_msg.SetValue(Warn.get())
        self.frame.txt_cur.SetValue(Old.get())
        self.frame.txt_new.SetValue(New.get())
        self.highlight_moved(self.frame.txt_new)
        self.MainLoop()

    def on_quit(self, e):
        sys.exit(0)

    def on_update(self, e):
        if not self.can_update:
            return
        Opt.set("Update", True)
        loadorder().update(None)
        self.frame.txt_stats.SetValue(Stats.get())
        self.frame.txt_msg.SetValue(Warn.get())
        self.frame.txt_new.SetValue(New.get())
        self.highlight_moved(self.frame.txt_new)
        self.can_update = False
        # TBD disable update button

    def on_close(self, e):
        self.on_quit(e)


if __name__ == "__main__":
    # read in message strings
    def splitter(s): return(map(lambda x: x.strip("\n"), s.split("]]\n")))
    Message = dict(map(splitter, file("mlox.msg", 'r').read().split("\n[["))[1:])
    def usage(status):
        print Message["usage"]
        sys.exit(status)
    # Check Python version
    if float(sys.version[:3]) < 2.5:
        print Message["requiresPython25"]
        sys.exit(1)
    # run under psyco if available
    do_psyco = False
    try:
        import psyco
        psyco.full()
        do_psyco = True
    except:
        pass
    # process command line arguments
    try:
        opts, args = getopt.getopt(sys.argv[1:], "acdfhquvw",
                                   ["all", "check", "debug", "fromfile", "help",
                                    "quiet", "update", "version", "warningsonly"])
    except getopt.GetoptError, err:
        print str(err)
        usage(2)                # exits
    for opt, arg in opts:
        if opt in   ("-a", "--all"):
            Opt.set("GetAll", True)
        elif opt in ("-c", "--check"):
            Opt.set("Update", False)
        elif opt in ("-d", "--debug"):
            Opt.set("DBG", True)
        elif opt in ("-f", "--fromfile"):
            Opt.set("FromFile", True)
        elif opt in ("-h", "--help"):
            usage(0)            # exits
        elif opt in ("-q", "--quiet"):
            Opt.set("Quiet", True)
        elif opt in ("-u", "--update"):
            Opt.set("Update", True)
        elif opt in ("-v", "--version"):
            print "mlox Version: %s" % Version
            sys.exit(0)
        elif opt in ("-w", "--warningsonly"):
            Opt.set("WarningsOnly", True)

    if Opt.get("FromFile"):
        if len(args) == 0:
            print "Error: -f specified, but no files on command line."
            usage(2)            # exits
        for file in args:
            loadorder().update(file)
    elif len(sys.argv) == 1:
        Opt.set("GUI", True)
        # run with gui
        mlox_gui().start()
    else:
        # run with command line arguments
        loadorder().update(None)
