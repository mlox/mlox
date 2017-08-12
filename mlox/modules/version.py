
import os
import sys
import re
import locale
import logging
from modules.loadOrder import base_file

version_logger = logging.getLogger('mlox.version')

Version = "0.61"

re_base_version = re.compile(r'^\[version\s+([^\]]*)\]', re.IGNORECASE)
full_version = ""

def version_info():
    try:
        import wx.__version__ as wx_version
    except:
        wx_version = "Not Installed"
    return "%s (%s/%s)\nPython Version: %s\nwxPython Version: %s\n" % (full_version(), locale.getdefaultlocale()[0], locale.getpreferredencoding(), sys.version[:3], wx_version)

def get_mlox_base_version():
    try:
        base = open(base_file, 'r')
    except IOError:
        version_logger.error("Unable to get rules file version from:  {0}".format(base_file))
        return("(Not Found)")
    for line in base:
        m = re_base_version.match(line)
        if m:
            base.close()
            return(m.group(1))
    base.close()
    return("(Not Found)")

def full_version():
    return "%s %s [mlox-base %s]" % (os.path.basename(sys.argv[0]), Version, get_mlox_base_version())
