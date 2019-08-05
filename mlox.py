#!/usr/bin/python3
# -*- mode: python -*-
# mlox - the elder scrolls Mod Load Order eXpert
# Copyright (c) 2009-2017
#    John Moonsugar, an alias
#    Dragon32
#    Arthur Moore
# Distributed as part of the mlox project:
#   https://github.com/mlox/mlox
# under the MIT License:
#   https://github.com/mlox/mlox/blob/master/License.txt

import sys
import logging
import argparse
import pprint
import re
import colorama
from colorama import Fore, Style

from mlox.resources import user_path, update_file, UPDATE_URL
from mlox.update import update_compressed_file
from mlox import version
from mlox.loadOrder import loadorder
from mlox.translations import dump_translations, _


def single_spaced(in_string):
    """
    Convert any instance of more than one space character to a single space in a string
    Also handles tabs, and removes whitespace at the beginning or end of a line
    """
    tmp_string = in_string
    tmp_string = re.sub('\t', ' ', tmp_string)
    tmp_string = re.sub(' +', ' ', tmp_string)
    tmp_string = re.sub('\n ', '\n', tmp_string)
    return tmp_string.strip()


class ColorFormatConsole(logging.Formatter):
    """Color code the logging information on Unix terminals"""
    levels = {
        'DEBUG':    '',
        'INFO':     '',
        'WARNING':  Fore.YELLOW,
        'ERROR':    Fore.RED,
        'CRITICAL': Fore.RED
    }

    def __init__(self, msg):
        colorama.init()
        logging.Formatter.__init__(self, msg)

    def format(self, record):
        return self.levels[record.levelname] + logging.Formatter.format(self, record) + Style.RESET_ALL


class ShowTranslations(argparse.Action):
    """Dump the translation dictionary for the specified language, then exit."""
    help = "Dump the translation dictionary for the specified language, then exit."

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS):
        super().__init__(option_strings=option_strings, dest=dest, default=default,
                         nargs=1, type=str, metavar='language', help=self.help)

    def __call__(self, parser, namespace, values, option_string=None):
        dump_translations(values)
        parser.exit()


class ListVersions(argparse.Action):
    """List the version information of the current data files, then exit"""
    help = single_spaced("""
               Use this to list the version numbers parsed from your plugins.
               The output is in 2 columns.\nThe first is the version from the plugin filename, if present.
               The second is from the plugin header, if present.
               Naturally, many plugins do not use version numbers so results are spotty.
               This information can be used to write rules using the [VER] predicate.
               """)

    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS):
        super().__init__(option_strings=option_strings, dest=dest, default=default, nargs=0, help=self.help)

    def __call__(self, parser, namespace, values, option_string=None):
        my_loadorder = loadorder()
        my_loadorder.get_data_files()
        print(my_loadorder.listversions())
        parser.exit()


def add_writer_group(parser):
    """
    Add the writer options for the parser
    Note:  This group does not actually display separately.
    """
    writer_group = parser.add_mutually_exclusive_group()
    # Check mode is actually the default behavior, so setting it doesn't do anything
    writer_group.add_argument("-c", "--check", help="Check mode, do not update the load order.  Default Behavior.",
                              action="store_true")
    writer_group.add_argument("-u", "--update", help="Update mode, updates the load order.", action="store_true")
    writer_group.add_argument("-w", "--warningsonly",
                              help="Warnings only, do not display the new load order.\nImplies --check.",
                              action="store_true")


def add_verbosity_group(parser):
    """ Add the verbosity options to the parser """
    # The strange double add is to make the exclusive group its own section in the help text
    verbosity_group = parser.add_argument_group('Verbosity Controls',
                                                'Select one of these to set how much output to receive.') \
        .add_mutually_exclusive_group()
    verbosity_group.add_argument("-p", "--parsedebug",
                                 help="Turn on debugging for the rules parser. "
                                      "(This can generate a fair amount of output).\nImplies --debug.",
                                 action="store_true")
    verbosity_group.add_argument("-d", "--debug", help="Turn on debug output.", action="store_true")
    verbosity_group.add_argument("-q", "--quiet",
                                 help=single_spaced("""
                Run more quietly (only re-order plugins, ignoring all notes, warnings, etc).
                Do not print out anything less than warning messages.
            """),
                                 action="store_true")


def add_developer_options(parser):
    """ Add developer options to the parser """
    developer_group = parser.add_argument_group('Developer Options', 'Options useful only to mlox developers.')
    developer_group.add_argument("-l", "--listversions", action=ListVersions)
    developer_group.add_argument("--translations", action=ShowTranslations)
    try:
        # Only show the profile option if hotshot is installed
        import hotshot
        developer_group.add_argument("--profile",
                                     help="Use hotshot to profile the application.",
                                     action="store_true")
    except ImportError:
        pass


def build_parser() -> argparse.ArgumentParser:
    """ Build an argparse parser for the application """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter,
        description='mlox - A tool for analyzing and sorting your Morrowind plugin load order',
        epilog=single_spaced("""
                When invoked with no options, mlox runs in GUI mode.

                mlox is intended to be run from somewhere under your game directory.

                mlox sorts your plugin load order using rules from input files
                (mlox_base.txt and mlox_user.txt, if it exists). A copy of the
                newly generated load order is saved in mlox_loadorder.out.

                Note: if you use Wrye Mash's "lock times" feature and you want mlox to update your load order, you need to run Mash first and turn it off.
                Otherwise, the next time you run Mash, it will undo all the changes in your load order made by mlox.
                """))

    parser.add_argument("-n", "--nodownload", help="Do not automatically download and update the mlox rules.",
                        action="store_true")
    parser.add_argument("-v", "--version", help="Print version and exit.", action="version", version=version.about())
    parser.add_argument("-a", "--all",
                        help=single_spaced("""
                            Handle for all plugins in the Data Directory.
                            Default is to only process active plugins (plugins in the Data directory, and also in Morrowind.ini.)
                            """),
                        action="store_true")
    parser.add_argument("-f", "--fromfile",
                        help=single_spaced("""File processing mode.
                            At least one input file must follow on command line.
                            Each file contains a list of plugins which is used instead of reading the list of plugins from the data file directory.
                            File formats accepted: Morrowind.ini, load order output of Wrye Mash, and Reorder Mods++.
                            """),
                        metavar='file',
                        nargs='+',
                        type=str)
    parser.add_argument("-e", "--explain",
                        help=single_spaced("""
                Print an explanation of the dependency graph for plugin.
                This can help you understand why a plugin was moved in your load order.
                Implies --quiet.
                """),
                        metavar='plugin',
                        nargs=1,
                        type=str)
    parser.add_argument("--base-only",
                        help="Use this with the --explain option to exclude the current load order from the graph explanation.",
                        action="store_true")
    parser.add_argument("--gui",
                        help="Run the GUI.\nDefault action if no arguments are given.",
                        action="store_true")
    add_writer_group(parser)
    add_verbosity_group(parser)
    add_developer_options(parser)
    return parser


def command_line_mode(args):
    """Run in command line mode.  This assumes log levels were properly set up beforehand"""
    logging.info("%s %s", version.full_version(), _["Hello!"])
    if args.fromfile:
        for fromfile in args.fromfile:
            my_loadorder = loadorder()
            my_loadorder.read_from_file(fromfile)
            process_load_order(my_loadorder, args)
        return
    my_loadorder = loadorder()
    if args.all:
        my_loadorder.get_data_files()
    else:
        my_loadorder.get_active_plugins()
    process_load_order(my_loadorder, args)


def process_load_order(a_loadorder, args):
    """
    Process a load order.
    These are things users can do or see with a load order.
    No matter how the list of plugins is obtained, what's done here stays the same.
    """
    if args.explain:
        print(a_loadorder.explain(args.explain[0], args.base_only))
        return
    if args.quiet:
        a_loadorder.update()
    else:
        print(a_loadorder.update())
    if args.warningsonly:
        return
    print("{0:-^80}".format('[New Load Order]'))
    for plugin in a_loadorder.get_new_order():
        print(plugin)
    if args.update:
        a_loadorder.write_new_order()
        print("{0:-^80}".format('[LOAD ORDER SAVED]'))
        return
    print("{0:-^80}".format('[END PROPOSED LOAD ORDER]'))


def main():
    # Configure logging from python module
    logging.getLogger('').setLevel(logging.DEBUG)
    color_formatter = ColorFormatConsole('%(levelname)s (%(name)s): %(message)s')
    console_log_stream = logging.StreamHandler()
    console_log_stream.setLevel(logging.INFO)
    console_log_stream.setFormatter(color_formatter)
    logging.getLogger('').addHandler(console_log_stream)
    # Disable parse debug logging unless the user asks for it (It's so much it actually slows the program down)
    logging.getLogger('mlox.parser').setLevel(logging.INFO)

    parser = build_parser()

    # parse command line arguments
    logging.debug("Command line: %s", " ".join(sys.argv))
    args = parser.parse_args()
    logging.debug("Parsed Arguments: %s", pprint.pformat(args))

    # Handle verbosity_group
    # Want to do this as early as possible so nothing is missed.
    if args.parsedebug:
        logging.getLogger('mlox.parser').setLevel(logging.DEBUG)
        args.debug = True
    if args.debug:
        console_log_stream.setLevel(logging.DEBUG)
    if args.quiet:
        console_log_stream.setLevel(logging.WARNING)
        # Not printing everything else is handled in process_load_order(...)

    # Check Python version
    logging.debug(version.version_info())
    logging.debug("Database Directory: %s", user_path)
    python_version = sys.version[:3]
    if float(python_version) < 3:
        logging.error("This program requires at least Python version 3.")
        parser.exit(1)

    # Download UPDATE_URL to user_path, then extract its contents there
    if not args.nodownload:
        logging.info('Checking for database update...')
        if update_compressed_file(update_file, UPDATE_URL, user_path):
            logging.info('Database updated from {0}'.format(update_file))

    # If no arguments are passed or if explicitly asked to, run the GUI
    noargs = True
    for i in vars(args).values():
        if i:
            noargs = False
            break
    if args.gui or noargs:
        from mlox.qtGui import MloxGui
        MloxGui().start()
        return

    if vars(args).get('profile', False):
        import hotshot
        import hotshot.stats
        prof = hotshot.Profile("mlox.prof")
        time = prof.runcall(command_line_mode, args=args)
        prof.close()
        stats = hotshot.stats.load("mlox.prof")
        stats.strip_dirs()
        stats.sort_stats('time', 'calls')
        stats.print_stats(20)
        return

    command_line_mode(args)


if __name__ == "__main__":
    main()
