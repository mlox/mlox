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
import modules.ruleParser as ruleParser

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
Opt.BaseOnly = False
Opt.Explain = None
Opt.FromFile = False
Opt.GUI = False
Opt.GetAll = False
Opt.Profile = False
Opt.Quiet = False
Opt.Update = False
Opt.WarningsOnly = False
Opt.NoUpdate = False

if __name__ == "__main__":
    if len(sys.argv) == 1:
        Opt.GUI = True
        import wx
        import wx.richtext as rt
        import webbrowser
        webbrowser.PROCESS_CREATION_DELAY = 0

re_base_version = re.compile(r'^\[version\s+([^\]]*)\]', re.IGNORECASE)

full_version = ""
clip_file = "mlox_clipboard.out"
old_loadorder_output = "current_loadorder.out"
new_loadorder_output = "mlox_new_loadorder.out"
debug_output = "mlox_debug.out"

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

Dbg = logger(False)     # debug output
New = logger(False)     # new sorted loadorder
Old = logger(False)     # old original loadorder
Stats = logger(False)   # stats output
Msg = logger(True)     # messages output

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
color_formatter = colorFormatConsole('%(levelname)s (%(name)s): %(message)s')
console_log_stream = logging.StreamHandler()
console_log_stream.setLevel(logging.INFO)
console_log_stream.setFormatter(color_formatter)
logging.getLogger('').addHandler(console_log_stream)
dbg_formatter = logging.Formatter('%(levelname)s (%(name)s): %(message)s')
dbg_log_stream = logging.StreamHandler(stream=Dbg)
dbg_log_stream.setFormatter(dbg_formatter)
dbg_log_stream.setLevel(logging.DEBUG)
logging.getLogger('').addHandler(dbg_log_stream)
gui_formatter = logging.Formatter('%(levelname)s: %(message)s')
gui_log_stream = logging.StreamHandler(stream=Stats)
gui_log_stream.setFormatter(gui_formatter)
gui_log_stream.setLevel(logging.WARNING)
logging.getLogger('').addHandler(gui_log_stream)

#This is a little cheat so the INFO messages still display, but without the tag
class filterInfo():
    def filter(self,record):
        return record.levelno == logging.INFO
info_formatter = logging.Formatter('%(message)s')
gui_info_stream = logging.StreamHandler(stream=Stats)
gui_info_stream.setFormatter(info_formatter)
gui_info_stream.setLevel(logging.INFO)
gui_info_stream.addFilter(filterInfo())
logging.getLogger('').addHandler(gui_info_stream)

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

def myopen_file(filename, mode, encoding=None):
    try:
        return(codecs.open(filename, mode, encoding))
    except IOError, (errno, strerror):
        mode_str = _["input"] if mode == 'r' else _["output"]
        logging.debug(_["Problem opening \"%s\" for %s (%s)"] % (filename, mode_str, strerror))
    return(None)

class loadorder:
    """Class for reading plugin mod times (load order), and updating them based on rules"""
    def __init__(self):
        # order is the list of plugins in Data Files, ordered by mtime
        self.active = {}                   # current active plugins
        self.order = []                    # the load order
        self.new_order = []                # the new load order
        self.datadir = None                # where plugins live
        self.plugin_file = None            # Path to the file containing the plugin list
        self.graph = pluggraph.pluggraph()
        self.is_sorted = False
        self.origin = None                 # where plugins came from (active, installed, file)
        self.game_type = None              # 'Morrowind', 'Oblivion', or None for unknown

        self.game_type, self.plugin_file, self.datadir = fileFinder.find_game_dirs()

    def get_active_plugins(self):
        """Get the active list of plugins from the game configuration. Updates self.active and self.order."""
        if self.plugin_file == None:
            logging.warning(_["{0} config file not found!"].format(self.game_type))
            return

        # Get all the plugins
        configFiles = configHandler.configHandler(self.plugin_file,self.game_type).read()
        dirFiles = configHandler.dataDirHandler(self.datadir).read()

        # Remove plugins not in the data directory (and correct capitalization)
        configFiles = map(str.lower, configFiles)
        self.order = filter(lambda x: x.lower() in configFiles, dirFiles)

        #Convert the files to lowercase, while storing them in a global (WARNING:  Use a global here)
        self.order = map(C.cname,self.order)

        logging.info("Found {0} plugins in: \"{1}\"".format(len(self.order), self.plugin_file))
        for p in self.order:
            self.active[p] = True
        self.origin = _["Active Plugins"]

    def get_data_files(self):
        """Get the load order from the data files directory. Updates self.active and self.order."""
        self.order = configHandler.dataDirHandler(self.datadir).read()

        #Convert the files to lowercase, while storing them in a global (WARNING:  Use a global here)
        self.order = map(C.cname,self.order)

        logging.info("Found {0} plugins in: \"{1}\"".format(len(self.order), self.datadir.dirpath()))
        for p in self.order:
            self.active[p] = True
        self.origin = _["Installed Plugins"]

    #List the versions of all plugins in the current load order
    def listversions(self):
        print "{0:20} {1:20} {2}".format("Name", "Description", "Plugin Name")
        for p in self.order:
            (file_ver, desc_ver) = ruleParser.get_version(p,self.datadir)
            print "{0:20} {1:20} {2}".format(file_ver, desc_ver, C.truename(p))

    def read_from_file(self, fromfile):
        """Get the load order by reading an input file.
        Clears self.game_type and self.datadir.
        Updates self.plugin_file, self.active, and self.order."""
        self.game_type = None
        self.datadir = None         #This tells the parser to not worry about things like [SIZE] checks, or trying to read the plugin descriptions
        self.plugin_file = fromfile

        self.order = configHandler.configHandler(fromfile).read()
        if len(self.order) == 0:
            logging.warning("No plugins detected.\nmlox understands lists of plugins in the format used by Morrowind.ini or Wrye Mash.\nIs that what you used for input?")

        #Convert the files to lowercase, while storing them in a global (WARNING:  Use a global here)
        self.order = map(C.cname,self.order)

        logging.info("Found {0} plugins in: \"{1}\"".format(len(self.order), self.plugin_file))
        for p in self.order:
            self.active[p] = True
        self.origin = "Plugin List from %s" % os.path.basename(fromfile)
        Msg.write("(Note: When the load order input is from an external source, the [SIZE] predicate cannot check the plugin filesizes, so it defaults to True).")

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
        if self.game_type == "Morrowind":
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
        try:
            out = open(filename, 'w')
        except IOError:
            logging.error("Unable to write to {0} file:  {1}".format(what,filename))
            return
        for p in order:
            print >> out, p
        out.close()
        Msg.write(_["%s saved to: %s"] % (what, filename))

    def get_original_order(self):
        """Get the original plugin order in a nice printable format"""
        formatted = []
        for n in range(1,len(self.order)+1):
            formatted.append("{0:0>3} {1}".format(n, C.truename(self.order[n-1])))
        return formatted

    def get_new_order(self):
        """Get the new plugin order in a nice printable format.
        Also, highlight mods that have moved up in the load order."""
        formatted = []
        orig_index = {}
        for n in range(1,len(self.order)+1):
            orig_index[self.order[n-1]] = n
        highlight = "_"
        for i in range(0, len(self.new_order)):
            p = self.new_order[i]
            curr = p.lower()
            if (orig_index[curr] - 1) > i: highlight = "*"
            formatted.append("%s%03d%s %s" % (highlight, orig_index[curr], highlight, p))
            if highlight == "*":
                if i < len(self.new_order) - 1:
                    next = self.new_order[i+1].lower()
                if (orig_index[curr] > orig_index[next]):
                    highlight = "_"
        return formatted

    def update(self):
        """Update the load order based on input rules."""
        logging.info("Version: %s\t\t\t\t %s " % (full_version, _["Hello!"]))
        if self.order == []:
            logging.error(_["No plugins detected! mlox needs to run somewhere under where the game is installed."])
            return
        logging.debug("Initial load order:")
        for p in self.get_original_order():
            logging.debug("  " + p)
        # read rules from various sources, and add orderings to graph
        # if any subsequent rule causes a cycle in the current graph, it is discarded
        # primary rules are from mlox_user.txt
        parser = None
        if Opt.Quiet:
            #Print output to an unused buffer
            parser = ruleParser.rule_parser(self.active, self.graph, self.datadir,StringIO.StringIO(),C)
        else:
            parser = ruleParser.rule_parser(self.active, self.graph, self.datadir,Msg,C)
        progress = None
        if Opt.GUI:
            progress = wx.ProgressDialog("Progress", "", 100, None,
                                         wx.PD_AUTO_HIDE|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        if os.path.exists(user_file):
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
        sorted_datafiles = [f for f in sorted if f in self.active]
        (esm_files, esp_files) = configHandler.partition_esps_and_esms(sorted_datafiles)
        new_order_cname = [p for p in esm_files + esp_files]
        self.new_order = [C.truename(p) for p in new_order_cname]

        logging.debug("New load order:")
        for p in self.get_new_order():
            logging.debug("  " + p)

        if len(self.new_order) != len(self.order):
            logging.error("sanity check: len(self.new_order %d) != len(self.order %d)" % (len(self.new_order), len(self.order)))
            self.new_order = []
            return

        if self.order == new_order_cname:
            Msg.add(_["[Plugins already in sorted order. No sorting needed!]"])
            self.is_sorted = True

        if self.datadir != None:
            # these are things we do not want to do if just testing a load order from a file
            if Opt.Update:
                if configHandler.dataDirHandler(self.datadir).write(self.new_order):
                    Msg.add(_["[LOAD ORDER UPDATED!]"])
                    self.is_sorted = True
            # save the load orders to file for future reference
            self.save_order(old_loadorder_output, [C.truename(p) for p in self.order], _["current"])
            self.save_order(new_loadorder_output, self.new_order, _["mlox sorted"])
        return(self)


def display_colored_text(in_text, out_RichTextCtrl):
    # Apply coloring to text, then display it on a wx.RichTextCtrl
    try:
        # try coping with python changing function names between versions /abot
        low = rt.RichTextAttr()
        medium = rt.RichTextAttr()
        high = rt.RichTextAttr()
        happy = rt.RichTextAttr()
        hide = rt.RichTextAttr()
        url = rt.RichTextAttr()
        warning = rt.RichTextAttr()
        error = rt.RichTextAttr()
    except:
        low = rt.TextAttrEx()
        medium = rt.TextAttrEx()
        high = rt.TextAttrEx()
        happy = rt.TextAttrEx()
        hide = rt.TextAttrEx()
        url = rt.TextAttrEx()
        warning = rt.TextAttrEx()
        error = rt.TextAttrEx()
    low.SetBackgroundColour(wx.Colour(125,220,240))
    medium.SetBackgroundColour(wx.Colour(255,255,180))
    high.SetBackgroundColour(wx.Colour(255,180,180))
    happy.SetBackgroundColour('GREEN')
    hide.SetBackgroundColour('BLACK'); hide.SetTextColour('BLACK')
    url.SetTextColour('BLUE') ; url.SetFontUnderlined(True)
    warning.SetBackgroundColour('YELLOW')
    error.SetBackgroundColour('RED')
    highlighters = {
        #Only highlights the text inside group 1
        re.compile(r'Version[^\]]+\]\t+(.+)', re.MULTILINE): happy,
        re.compile(r'(http://\S+)', re.IGNORECASE): url,
        re.compile(r'^(\[CONFLICT\])', re.MULTILINE): medium,
        re.compile(r'(\[Plugins already in sorted order. No sorting needed!\])', re.IGNORECASE): happy,
        re.compile(r"^(\s*\|?\s*!{1}[^!].*)$", re.MULTILINE): low,           #Handle '!' in mlox_base.txt
        re.compile(r"^(\s*\|?\s*!{2}[^!].*)$", re.MULTILINE): medium,        #Handle '!!' in mlox_base.txt
        re.compile(r"^(\s*\|?\s*!{3}.*)$", re.MULTILINE): high,              #Handle '!!!' in mlox_base.txt
        re.compile(r'^(WARNING:.*)', re.MULTILINE): warning,
        re.compile(r'^(ERROR:.*)', re.MULTILINE): error }
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
    in_text = re_hide.sub(hider, in_text)
    out_RichTextCtrl.SetValue(in_text)
    # for special highlighting
    for (re_pat, style) in highlighters.items():
        for match in re.finditer(re_pat, in_text):
            (start, end) = match.span(1)
            if style == url:
                url.SetURL(in_text[start:end])
            out_RichTextCtrl.SetStyle((start, end), style)
    for where in hidden:
        out_RichTextCtrl.SetStyle(where, hide)

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
        self.txt_stats = rt.RichTextCtrl(self.frame, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.TE_RICH2)
        self.txt_stats.SetFont(default_font)

        self.splitter = wx.SplitterWindow(self.frame, -1)

        self.split1 = wx.Panel(self.splitter, -1)
        self.label_msg = wx.StaticText(self.split1, -1, _["Messages"])
        self.label_msg.SetFont(self.label_font)
        self.txt_msg = rt.RichTextCtrl(self.split1, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_msg.SetFont(default_font)
        self.txt_msg.Bind(wx.EVT_TEXT_URL, self.click_url)

        self.split2 = wx.Panel(self.splitter, -1)
        self.label_cur = wx.StaticText(self.split2, -1, _["Current Load Order"])
        self.label_cur.SetFont(self.label_font)
        self.txt_cur = wx.TextCtrl(self.split2, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_cur.SetFont(default_font)
        self.label_cur_bottom = wx.StaticText(self.frame, -1, _["(Right click in this pane for options)"])
        self.label_new = wx.StaticText(self.split2, -1, _["Proposed Load Order Sorted by mlox"])
        self.label_new.SetFont(self.label_font)
        self.label_new_bottom = wx.StaticText(self.frame, -1, "")
        self.txt_new = wx.TextCtrl(self.split2, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
        self.txt_new.SetFont(default_font)

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

    def click_url(self, e):
        the_url = e.GetString()
        webbrowser.open(the_url)

    def highlight_moved(self, txt):
        # highlight background color for changed items in txt widget
        highlight = wx.TextAttr(colBack=wx.Colour(255,255,180))
        re_start = re.compile(r'[^_]\d+[^_][^\n]+')
        text = New.get()
        for match in re.finditer(re_start, text):
            (start, end) = match.span()
            if text[start] == '*': txt.SetStyle(start, end, highlight)

    def analyze_loadorder(self, fromfile):
        Msg.clear()
        Stats.clear()
        New.clear()
        Old.clear()
        lo = loadorder()
        if fromfile != None:
            lo.read_from_file(fromfile)
        else:
            if Opt.GetAll:
                lo.get_data_files()
            else:
                lo.get_active_plugins()
                if lo.order == []:
                    lo.get_data_files()
        lo.update()
        for p in lo.get_original_order():
            Old.write(p)
        for p in lo.get_new_order():
            New.write(p)
        if lo.is_sorted:
            self.can_update = False
        if not self.can_update:
            self.btn_update.Disable()
        display_colored_text(Stats.get_u(),self.txt_stats)
        display_colored_text(Msg.get(),self.txt_msg)
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
                        self.analyze_loadorder(clip_file)
            wx.TheClipboard.Close()

    def menu_open_file_handler(self, e):
        self.can_update = False
        dialog = wx.FileDialog(self.frame, message=_["Input Plugin List from File"], defaultDir=self.dir, defaultFile="", style=wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.dir = dialog.GetDirectory()
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
    if Opt.NoUpdate == False:
            update.update_mloxdata()
    if Opt.GUI == True:
        # run with gui
        mlox_gui().start()
    elif Opt.FromFile:
        if len(args) == 0:
            print _["Error: -f specified, but no files on command line."]
            usage(2)            # exits
        for fromfile in args:
            l = loadorder()
            l.read_from_file(fromfile)
            l.update()
            #We never actually write anything if reading from file(s)
            if not Opt.WarningsOnly:
                print "[Proposed] New Load Order:\n---------------"
            for p in l.get_new_order():
                print p
    else:
        # run with command line arguments
        l = loadorder()
        if Opt.GetAll:
                l.get_data_files()
        else:
            l.get_active_plugins()
            if l.order == []:
                l.get_data_files()
        l.update()
        if not Opt.WarningsOnly:
            if Opt.Update:
                print "[UPDATED] New Load Order:\n---------------"
            else:
                print "[Proposed] New Load Order:\n---------------"
        for p in l.get_new_order():
            print p

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
            Opt.Quiet = True
            console_log_stream.setLevel(logging.WARNING)
        elif opt in ("-f", "--fromfile"):
            Opt.FromFile = True
        elif opt in ("--gui"):
            Opt.GUI = True
        elif opt in ("-h", "--help"):
            usage(0)            # exits
        elif opt in ("-l", "--listversions"):
            l = loadorder()
            l.get_data_files()
            l.listversions()
            sys.exit(0)
        elif opt in ("-p", "--parsedebug"):
            logging.getLogger('mlox.parser').setLevel(logging.DEBUG)
            console_log_stream.setLevel(logging.DEBUG)
        elif opt in ("--profile"):
            Opt.Profile = True
        elif opt in ("-q", "--quiet"):
            Opt.Quiet = True
            console_log_stream.setLevel(logging.WARNING)
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
