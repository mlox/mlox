
import os
import sys
import locale
Version = "0.62"


def about():
    """
    :return: a nice statement about the program
    """
    output  = "mlox - the elder scrolls Mod Load Order eXpert\n"
    output += "Copyright (c) 2009-2017\n John Moonsugar, an alias\n Dragon32\n Arthur Moore\n"
    output += "Distributed as part of the mlox project:\n https://github.com/mlox/mlox\n"
    output += "under the MIT License:\n https://github.com/mlox/mlox/blob/master/License.txt\n"
    output += "\n" + version_info()
    return output


def version_info():
    """
    :return: a human readable multi-line string containing the program's version information
    """
    output = "{program} ({locale}/{encoding})\n".format(
        program=full_version(),
        locale=locale.getdefaultlocale()[0],
        encoding=locale.getpreferredencoding(),
        python_version=sys.version[:3]
    )
    try:
        from PyQt5.QtCore import QT_VERSION_STR
        output += "PyQt5 Version: {0}\n".format(QT_VERSION_STR)
    except ImportError:
        output += "PyQt5 Not Installed!\n"

    try:
        from appdirs import __version_info__ as appdirs_version
        output += "appdirs Version: {0}\n".format(".".join(list(map(str,appdirs_version))))
    except ImportError:
        output += "appdirs Not Installed!\n"

    try:
        import libarchive
        output += "libarchive Installed.\n"
    except ImportError:
        output += "libarchive Not Installed!\n"

    return output

def full_version():
    return "{0} {1}".format(os.path.basename(sys.argv[0]), Version)
