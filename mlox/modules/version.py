
import os
import sys
import locale
Version = "0.62"

def version_info():
    try:
        import wx.__version__ as wx_version
    except:
        wx_version = "Not Installed"
    return "%s (%s/%s)\nPython Version: %s\nwxPython Version: %s\n" % (full_version(), locale.getdefaultlocale()[0], locale.getpreferredencoding(), sys.version[:3], wx_version)

def full_version():
    return "{0} {1}".format(os.path.basename(sys.argv[0]), Version)
