#!/usr/bin/python3
import sys
import io
import logging
import traceback
import tempfile
import re
from PyQt5.QtCore import QUrl, QObject, pyqtSignal, pyqtSlot, Qt, QSize
from PyQt5.QtGui import QImage, QIcon, QPixmap
from PyQt5.QtQuick import QQuickImageProvider
from PyQt5.QtWidgets import QApplication, QDialog, QProgressDialog, QPlainTextEdit, QMessageBox
from PyQt5.QtQml import QQmlApplicationEngine
from mlox.resources import resource_manager
from mlox.loadOrder import loadorder
from mlox import version

gui_logger = logging.getLogger('mlox.gui')


def colorize_text(text):
    """
    Some things are better in color.
    This function takes normal text, and applies html style tags where appropriate.
    """
    bg_colors = {
        "low":      "<span style='background-color: rgb(125,220,240);'>\g<0></span>",
        "medium":   "<span style='background-color: rgb(255,255,180);'>\g<0></span>",
        "high":     "<span style='background-color: rgb(255,180,180);'>\g<0></span>",
        "green":    "<span style='background-color: green;'>\g<0></span>",
        "yellow":   "<span style='background-color: yellow;'>\g<0></span>",
        "red":      "<span style='background-color: red;'>\g<0></span>"
    }

    highlighters = [
        (re.compile(r'<hide>(.*)</hide>'),"<span style='color: black; background-color: black;'>\g<1></span>"),         # Spoilers require Highlighting
        (re.compile(r'^(\[CONFLICT\])', re.MULTILINE), bg_colors["red"]),
        (re.compile(r'(https?://[^\s]*)', re.IGNORECASE), "<a href='\g<0>'>\g<0></a>"),                                 # URLs
        (re.compile(r"^(\s*\|?\s*!{1}[^!].*)$", re.MULTILINE), bg_colors["low"]),                                       # '!' in mlox_base.txt
        (re.compile(r"^(\s*\|?\s*!{2}.*)$", re.MULTILINE), bg_colors["medium"]),                                        # '!!' in mlox_base.txt
        (re.compile(r"^(\s*\|?\s*!{3}.*)$", re.MULTILINE), bg_colors["high"]),                                          # '!!!' in mlox_base.txt
        (re.compile(r'^(WARNING:.*)', re.MULTILINE),bg_colors["yellow"]),
        (re.compile(r'^(ERROR:.*)', re.MULTILINE),bg_colors["red"]),
        (re.compile(r'(\[Plugins already in sorted order. No sorting needed!\])', re.IGNORECASE), bg_colors["green"]),
        (re.compile(r'^(\*\d+\*\s.*\.es[mp])', re.MULTILINE), bg_colors["yellow"])                                     # Changed mod order
    ]
    for (regex,replacement_string) in highlighters:
        text = regex.sub(replacement_string, text)

    text = text.replace('\n', '<br>\n')
    return text


class PkgResourcesImageProvider(QQuickImageProvider):
    """
    Load an appropriate image from mlox.static

    Props to https://stackoverflow.com/a/47504480/11521987
    """
    #
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)

    def requestImage(self, p_str, size: QSize):
        image_data: bytes = resource_manager.resource_string("mlox.static", p_str)
        image = QImage()
        image.loadFromData(image_data)
        return image, image.size()


class ScrollableDialog(QDialog):
    "A dialog box that contains scrollable text."
    def __init__(self):
        QDialog.__init__(self)
        self.setModal(False)

        self.inner_text = QPlainTextEdit(self)
        self.inner_text.setReadOnly(True)

        self.setFixedSize(400, 600)
        self.inner_text.setFixedSize(400, 600)

    def setText(self, new_text):
        self.inner_text.setPlainText(new_text)


class CustomProgressDialog(QProgressDialog):
    """
    A custom version of the progress dialog
    It's designed to have the same update mechanism as a wx.ProgressDialog
    """

    def __init__(self):
        QProgressDialog.__init__(self)
        self.setCancelButton(None)
        self.forceShow()
        self.open()

    def Update(self, percent, label):
        self.setLabelText(label)
        self.setValue(percent)


def error_handler(type, value, tb):
    """
    Since a command line is not normally available to a GUI application, we need to display errors to the user.
    These are only errors that would cause the program to crash, so have the program exit when the dialog box is closed.
    """
    error_box = ScrollableDialog()
    error_box.setText(version.version_info() + "\n" + "".join(traceback.format_exception(type, value, tb)))
    error_box.exec_()
    sys.exit(1)


class MloxGui(QObject):
    """Mlox's GUI (Using PyQt5)"""

    lo = None  # Load order

    # Signals (use emit(...) to change values)
    enable_updateButton = pyqtSignal(bool, arguments=['is_enabled'])
    set_status = pyqtSignal(str, arguments=['text'])
    set_message = pyqtSignal(str, arguments=['text'])
    set_new = pyqtSignal(str, arguments=['text'])
    set_old = pyqtSignal(str, arguments=['text'])

    def __init__(self):
        QObject.__init__(self)
        self.Dbg = io.StringIO()  # debug output
        self.Stats = io.StringIO()  # status output
        self.New = ""  # new sorted loadorder
        self.Old = ""  # old original loadorder
        self.Msg = ""  # messages output
        self.can_update = True  # If the load order can be saved or not

        # Set up logging
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

        # This is a little cheat so the INFO messages still display, but without the tag
        class filterInfo():
            def filter(self, record):
                return record.levelno == logging.INFO

        info_formatter = logging.Formatter('%(message)s')
        gui_info_stream = logging.StreamHandler(stream=self.Stats)
        gui_info_stream.setFormatter(info_formatter)
        gui_info_stream.setLevel(logging.INFO)
        gui_info_stream.addFilter(filterInfo())
        logging.getLogger('').addHandler(gui_info_stream)

    def start(self):
        """Display the GUI"""
        myApp = QApplication(sys.argv)
        sys.excepthook = lambda typ, val, tb: error_handler(typ, val, tb)

        myApp.setOrganizationDomain('mlox')
        myApp.setOrganizationName('mlox')

        icon_data: bytes = resource_manager.resource_string("mlox.static", "mlox.ico")
        icon = QIcon()
        pixmap = QPixmap()
        pixmap.loadFromData(icon_data)
        icon.addPixmap(pixmap)
        myApp.setWindowIcon(icon)

        myEngine = QQmlApplicationEngine()
        # Need to set these before loading
        myEngine.rootContext().setContextProperty("python", self)
        myEngine.addImageProvider('static', PkgResourcesImageProvider())

        qml: bytes = resource_manager.resource_string("mlox.static", "window.qml")
        myEngine.loadData(qml)

        # These two are hacks, because getting them in the __init__ and RAII working isn't
        self.debug_window = ScrollableDialog()
        self.clipboard = myApp.clipboard()

        self.analyze_loadorder()

        sys.exit(myApp.exec())

    def display(self):
        "Update the GUI after an operation"
        self.debug_window.setText(self.Dbg.getvalue())
        self.enable_updateButton.emit(self.can_update)
        self.set_status.emit(colorize_text(self.Stats.getvalue()))
        self.set_message.emit(colorize_text(self.Msg))
        self.set_new.emit(colorize_text(self.New))
        self.set_old.emit(colorize_text(self.Old))

    def analyze_loadorder(self, fromfile = None):
        """
        This is where the magic happens
        If fromfile is None, then it operates out of the current directory.
        """

        # Clear all the outputs (except Dbg)
        self.Stats.truncate(0)
        self.Stats.seek(0)
        self.New = ""
        self.Old = ""
        self.Msg = ""

        gui_logger.info("Version: %s\t\t\t\t %s " % (version.full_version(), "Hello!"))
        self.lo = loadorder()
        if fromfile != None:
            self.lo.read_from_file(fromfile)
        else:
            self.lo.get_active_plugins()
        progress = CustomProgressDialog()
        self.Msg = self.lo.update(progress)
        # TODO: Have update always return as string, so this isn't needed
        if not self.Msg:
            self.Msg = ""
        for p in self.lo.get_original_order():
            self.Old += p + '\n'
        for p in self.lo.get_new_order():
            self.New += p + '\n'
        if self.lo.is_sorted:
            self.can_update = False

        # Go ahead and display everything
        self.display()

    @pyqtSlot()
    def show_debug_window(self):
        """
        Updates the text of the debug window, then shows it.
        Note:  The debug window is also updated every time `self.display()` is called
        """
        self.debug_window.setText(self.Dbg.getvalue())
        self.debug_window.open()

    @pyqtSlot()
    def paste_handler(self):
        """Open a load order from the clipboard"""
        file_handle = tempfile.NamedTemporaryFile()
        file_handle.write(self.clipboard.text().encode('utf8'))
        file_handle.seek(0)
        self.analyze_loadorder(file_handle.name)

    @pyqtSlot(str)
    def open_file(self, file_path):
        """Analyze the file passed in"""
        file_path = QUrl(file_path).path()  # Adjust from a file:// format to a regular path
        self.analyze_loadorder(file_path)

    @pyqtSlot()
    def reload(self):
        self.can_update = True
        # TODO:  Properly handle reloading from a file
        self.analyze_loadorder()

    @pyqtSlot()
    def commit(self):
        """Write the requested changes to the file/directory"""
        if not self.can_update:
            gui_logger.error("Attempted an update, when no update is possible/needed.")
            self.display()
            return
        self.lo.write_new_order()
        gui_logger.info("[LOAD ORDER UPDATED!]")
        self.can_update = False
        self.display()

    @pyqtSlot()
    def about_handler(self):
        """
        Show information about mlox
        """
        about_box = QMessageBox()
        about_box.setText(version.about())
        about_box.exec_()
