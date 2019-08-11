
import os
import subprocess
import sys
import locale
Version = "1.0"


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


def requirement_status() -> dict:
    """
    :return: A dict containing the requirements to run/do certain things
    """
    output = {}
    try:
        from PyQt5.QtCore import QT_VERSION_STR
        output["PyQt5"] = "Version: {0}".format(QT_VERSION_STR)
    except ImportError:
        output["PyQt5"] = None
    try:
        from appdirs import __version_info__ as appdirs_version
        output["appdirs"] = "Version: {0}".format(".".join(list(map(str,appdirs_version))))
    except ImportError:
        output["appdirs"] = None
    try:
        import py7zr
        output["py7zr"] = "Installed"
    except ImportError:
        output["py7zr"] = None
    try:
        import libarchive
        output["libarchive"] = "Installed"
    except (ImportError, TypeError, OSError):
        # TypeError happens when libarchive-c can't find the library.
        # OSError is the base of PyInstallerImportError, which is what a compiled exe throws
        output["libarchive"] = None
    try:
        with open(os.devnull, 'w') as devnull:
            subprocess.check_call('7za', stdout=devnull)
            output["7-Zip"] = "Installed"
    except subprocess.CalledProcessError:
        output["7-Zip"] = None
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
    for requirement, status in requirement_status().items():
        status = status or "Not Installed"
        output += "{}: {}\n".format(requirement, status)

    return output


def full_version():
    return "{0} {1}".format(os.path.basename(sys.argv[0]), Version)
