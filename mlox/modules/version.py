
import os
import sys
import locale
Version = "0.62"

def version_info():
    "Returns a human readable multi-line string containting the program's version information"
    try:
        import wx.__version__ as wx_version
        gui_version = "wxPython Version: {0}".format(wx_version)
    except:
        gui_version = "wxPython Not Installed!"
    return "{program} ({locale}/{encoding})\nPython Version: {python_version}\n{gui_version}\n".format(
        program=full_version(),
        locale=locale.getdefaultlocale()[0],
        encoding=locale.getpreferredencoding(),
        python_version=sys.version[:3],
        gui_version=gui_version
    )

def full_version():
    return "{0} {1}".format(os.path.basename(sys.argv[0]), Version)
