# Utilities to help deal with Morrowind Plugins
This folder contains all sorts of utilities.  Some are Windows only, and some are Linux only.  Many are meant for testing, and are not useful for end users.

It's important to remember that Morrowind loads plugins based on the file modification timestamp.  Many of these utilities are small helpers to read or modify those timestamps.

## Windows Only
### get_current_load_order.bat
Run this program from the directory containing plugin files.
It will create a file containing the order in which those plugins will be loaded, and will also display the results.
This assumes the program loading the files always loads `esm` files before `esp` files.

## Linux Only
### lo
Run this program from the directory containing plugin files.
It will display the order in which those plugins will be loaded.
This assumes the program loading the files always loads `esm` files before `esp` files.

Note:  It will NOT create a file with this output

## Testing Related
### scramble_plugins.py
Run this program from the directory containing plugin files.
This will re-arange the load order of all plugins (`esp` and `esm`) randomly.

### loadorder2files.py
Run this program from the directory containing plugin files.
Give it a text file containing a list of plugins, with one on each line.
It will modify the plugins dates to match the load order in the input file.
Only plugins given in the input file are modified.
The program will inform the user of which files have been modified.

## Others
### tes3cmd
`tes3cmd` is a command-line tool for examining and modifying TES3 plugins in various ways. It can also do things like make a patch for various problems and merge leveled lists, and so on. It is written in Perl and runs natively on Windows or Linux.
### tes3lint
`tes3lint` is a command-line tool for investigating potential problems in TES3 plugins. It is written in Perl and runs natively on Windows or Linux.
