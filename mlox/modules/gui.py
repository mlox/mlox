
from __future__ import print_function
import locale
import os
import sys
import re
import codecs
import traceback
import StringIO
import logging

import wx
import wx.richtext as rt
import webbrowser
webbrowser.PROCESS_CREATION_DELAY = 0

import modules.version as version
from modules.loadOrder import loadorder

gui_logger = logging.getLogger('mlox.gui')

#Resource files
program_path     = os.path.realpath(sys.path[0])
resources_path   = os.path.join(program_path,"Resources")
translation_file = os.path.join(resources_path,"mlox.msg")
gif_file         = os.path.join(resources_path,"mlox.gif")

clip_file = "mlox_clipboard.out"
debug_output = "mlox_debug.out"

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
        re.compile(r'^(ERROR:.*)', re.MULTILINE): error,
        re.compile(r'^(\*\d+\*\s\S*\.es[mp])', re.MULTILINE): medium         #Changed mod order
        }
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
    lo = None     #Load order

    def __init__(self):
        self.Dbg = StringIO.StringIO()     # debug output
        self.New = StringIO.StringIO()     # new sorted loadorder
        self.Old = StringIO.StringIO()     # old original loadorder
        self.Stats = StringIO.StringIO()   # stats output
        self.Msg = StringIO.StringIO()     # messages output

        #Set up logging
        dbg_formatter = logging.Formatter('%(levelname)s (%(name)s): %(message)s')
        dbg_log_stream = logging.StreamHandler(stream=self.Dbg)
        dbg_log_stream.setFormatter(dbg_formatter)
        dbg_log_stream.setLevel(logging.DEBUG)
        logging.getLogger('').addHandler(dbg_log_stream)
        gui_formatter = logging.Formatter('%(levelname)s: %(message)s')
        gui_log_stream = logging.StreamHandler(stream=self.Stats)
        gui_log_stream.setFormatter(gui_formatter)
        gui_log_stream.setLevel(logging.WARNING)
        logging.getLogger('').addHandler(gui_log_stream)
        #This is a little cheat so the INFO messages still display, but without the tag
        class filterInfo():
            def filter(self,record):
                return record.levelno == logging.INFO
        info_formatter = logging.Formatter('%(message)s')
        gui_info_stream = logging.StreamHandler(stream=self.Stats)
        gui_info_stream.setFormatter(info_formatter)
        gui_info_stream.setLevel(logging.INFO)
        gui_info_stream.addFilter(filterInfo())
        logging.getLogger('').addHandler(gui_info_stream)

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
        self.frame = wx.Frame(None, wx.ID_ANY, ("mlox %s" % version.Version))
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
        self.txt_new = rt.RichTextCtrl(self.split2, -1, "", style=wx.TE_READONLY|wx.TE_MULTILINE|wx.HSCROLL|wx.TE_RICH2)
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
        err_frame = wx.Frame(None, wx.ID_ANY, (_["%s - Error"] % version.full_version()))
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
        err_txt.SetValue(version.version_info() + "\n" + "".join(traceback.format_exception(type, value, tb)))
        err_frame.SetSizer(err_frame_vbox)
        err_frame_vbox.Fit(err_frame)
        err_frame.Show(True)
        self.app.MainLoop()

    def click_url(self, e):
        the_url = e.GetString()
        webbrowser.open(the_url)

    #Display output messages on the gui panels (and disable/enable btn_update if appropriate)
    def display(self):
        if self.can_update:
            self.btn_update.Enable()
        else:
            self.btn_update.Disable()
        display_colored_text(self.Stats.getvalue(),self.txt_stats)
        display_colored_text(self.Msg.getvalue(),self.txt_msg)
        display_colored_text(self.New.getvalue(),self.txt_new)
        self.txt_cur.SetValue(self.Old.getvalue())
        self.label_cur.SetLabel(self.lo.origin)
        self.cur_vbox.Layout()

    def analyze_loadorder(self, fromfile):
        #Clear all the outputs (except Dbg)
        self.New.truncate(0)
        self.Old.truncate(0)
        self.Stats.truncate(0)
        self.Msg.truncate(0)

        gui_logger.info("Version: %s\t\t\t\t %s " % (version.full_version(), _["Hello!"]))
        self.lo = loadorder()
        if fromfile != None:
            self.lo.read_from_file(fromfile)
        else:
            self.lo.get_active_plugins()
            if self.lo.order == []:
                self.lo.get_data_files()
        progress = wx.ProgressDialog("Progress", "", 100, None,
                                         wx.PD_AUTO_HIDE|wx.PD_APP_MODAL|wx.PD_ELAPSED_TIME)
        print(self.lo.update(progress), file=self.Msg)
        progress.Destroy()
        for p in self.lo.get_original_order():
            self.Old.write(p+'\n')
        for p in self.lo.get_new_order():
            self.New.write(p+'\n')
        if self.lo.is_sorted:
            self.can_update = False

        #Go ahead and display everything
        self.display()

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
        self.lo.write_new_order()
        gui_logger.info("[LOAD ORDER UPDATED!]")
        self.can_update = False
        self.display()

    def on_close(self, e):
        self.on_quit(e)

    def bugdump(self):
        try:
            out = open(debug_output, 'w')
        except IOError:
            gui_logger.error("Unable to write to debug output file:  {0}".format(debug_output))
        print(self.Dbg.getvalue().encode("utf-8"), file=out)
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
                    try:
                        out = open(clip_file, 'w')
                    except IOError:
                        gui_logger.error("Unable to open temporary clipboard file:  {0}".format(clip_file))
                        wx.TheClipboard.Close()
                        return
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
        dbg_frame = wx.Frame(None, wx.ID_ANY, (_["%s - Debug Output"] % version.full_version()))
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
        dbg_txt.SetValue(self.Dbg.getvalue())
        dbg_frame.SetSizer(dbg_frame_vbox)
        dbg_frame_vbox.Fit(dbg_frame)
        dbg_frame.Show(True)
        self.bugdump()
