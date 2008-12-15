
[[usage]]
Usage: mlox [OPTIONS]

 OPTIONS
 -a|--all
	Print warnings for all plugins, otherwise warning messages are
	only printed for active plugins.
 -c|--check
	Check mode, do not update the load order.
 -d|--debug
	Turn on debug output.
 -e|--explain plugin
	Print an explanation of the dependency graph for plugin
	this can help you understand why a plugin was moved in your
	load order.
 -f|--fromfile file1... fileN
	File processing mode, at least one input file must follow on
	command line, each file contains a list of plugins which is
	used instead of reading the list of plugins from the data file
	directory. File formats accepted: Morrowind.ini, load order
	output of Wrye Mash, and Reorder Mods++.
 -h|--help
	print this help.
 -p|--parsedebug
	Turn on debugging for the rules parser. (This can generate a
	fair amount of output).
 -q|--quiet
	Run more quietly (does not print out NOTEs).
 -u|--update
	Update mode, updates the load order.
 -v|--version
	Print version and exit.
 -w|--warningsonly
	Warnings only, do not display the new load order.

when invoked with no options, mlox runs in GUI mode.

mlox is intended to be run from somewhere under your game directory.
mlox runs under Windows or Linux.

mlox sorts your plugin load order using rules from input files
(mlox_base.txt and mlox_user.txt, if it exists). A copy of the
newly generated load order is saved in mlox_loadorder.out.

Note: if you use Wrye Mash's "lock times" feature and you want mlox to
update your load order, you need to run Mash first and turn it off.
Otherwise, the next time you run Mash, it will undo all the changes in
your load order made by mlox.

[[statistics]]
Statistics

[[messages]]
Messages

[[current_load_order]]
Current Load Order

[[new_load_order]]
Proposed Load Order Sorted by mlox

[[quit]]
Quit

[[update]]
Update Load Order

[[requiresPython25]]
This program requires Python version 2.5 or later.

[[close]]
close

[[click for options]]
[Right click in this pane for options]
