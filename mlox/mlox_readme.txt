Name: mlox
Version: 0.59
Copyright 2014 John Moonsugar <john.moonsugar@gmail.com>
License: MIT License (see the file: License.txt)
----------------------------------------------------------------------
        mlox - the elder scrolls Mod Load Order eXpert
----------------------------------------------------------------------
This is mlox_readme.txt, which gives basic information on what mlox is
and how to use it.
See mlox_rules_guide.txt for a description of the rules and rule-base.
See mlox_guts.txt for a discussion of mlox's inner workings.
----------------------------------------------------------------------

Contents
o Features
o Installation and quick start
o Support
o Introduction - Why mlox?
o Origins of mlox
o What mlox does, operational details
o Note to mod Authors
o On the Importance of the output warnings
o Testing
o Note to Wrye Mash users
o Usage
oo The mlox GUI
o Known Issues
o ChangeLog

------------------------------------------------------------
o Features

- optimally reorders your load order to avoid known problems, where
"optimally" is relative to the quality and coverage of the rule-base.
- warns about missing pre-requisites
- warns about plugin conflicts
- prints notes for things you might want to know about a mod, but may
have overlooked in the Readme, or things discussed in forum posts you
may have missed.
- mlox is customizable via a separate user rules file.
- can also check someone else's load list, you can paste their load ordr into
the mlox GUI, or load it from a file.
- it runs on Windows or Linux! :)

(Note that mlox does not tell you if you have missing Meshes or Textures, it
is only a load order tool, and does not report problems with resources).

------------------------------------------------------------
o Installation and Quick Start

oo Requirements

- mlox.py is written using Python with wxWidgets, just like Wrye Mash.
  (For Windows, there is a stand-alone executable that does not
  require these pre-requisites). You do need to install Python
  and wxWidgets if you wish to run the script form of the program.
  You can do this Windows if you install the following two packages:

  https://www.python.org/ftp/python/2.6.5/python-2.6.5.msi
    [install this version or newer as earlier versions only support US version of
    Windows and code page 437]
  http://downloads.sourceforge.net/wxpython/wxPython2.8-win32-ansi-2.8.7.1-py25.exe
    [there are later versions of wxPython but mlox needs the ANSI version]

  (Please note that the version of wxWidgets necessary for mlox is slightly
  newer than the one recommended for Mash, but will work for both
  applications. mlox will not work with wxPython 2.8.0.1, which is the
  version recommended by Mash!).

- It is STRONGLY RECOMMENDED that you install Hrnchamd's MCP
  ("Morrowind Code Patch"):
  http://www.nexusmods.com/morrowind/mods/19510
  The MCP makes it safer to change your load order in an existing
  savegame, amongst many other wonderful fixes it does.
  You are also encouraged to use Wrye Mash to manage your plugins:
  http://wryemusings.com/Wrye%20Mash.html

- mlox.py has 2 modes, GUI and command line. When executed with no
  command line switches it starts in GUI mode, when executed with
  the switch -h, it displays command line usage help.

- Unpack the mlox application archive somewhere under your Morrowind game
  directory. If you don't have a place decided, I suggest you unpack in
  the Morrowind directory. A new directory called "mlox" will be
  created containing all the files.

- The rule-base is released as a separate archive (mlox-data_<DATE>.7z),
  unpack this archive in the mlox directory created when you unpacked the
  application.
  Version 0.59 added an automated downloader for updating the mlos rule-base.

- A quick explanation of the included batch files for Windows (unless
  otherwise specified, run these batch files from the mlox directory):

  locheck - run mlox in command-line mode to check (not update).
  lofix - run mlox in command-line mode to update your load order.
  lo - (run this in "Data Files") just prints your current load order.

- On Windows, run mlox.exe. On Linux, run: mlox.py
  On Windows, if you have set up files that end in ".py" to be executed by
  Python, then just double-clicking on mlox.py would start the GUI.

- Note: On Windows 7 (and maybe Vista), if you installed Morrowind in the
  default location "C:\Program Files\...", you may need to turn off UAC to get
  mlox to recognize your activated plugins in Morrowind.ini.

- mlox always assumes that the rule-base files (mlox_base.txt and optionally:
  mlox_user.txt) are in the current working directory (the directory where you
  run mlox) so you should run mlox in the directory where those two files
  live.

------------------------------------------------------------
o Support

If you run into a problem with mlox, the best thing to do to get help
is to post on the BethSoft Morrowind Mods forums:
http://forums.bethsoft.com/forum/12-morrowind-mods/
You can search for the latest mlox thread by using the forum Search function.

If you get a popup error window, please include the contents in your report.

Please report all Windows usability problems to me. I'm not a Windows user, so
as a programmer, I may make mistakes about how Windows is supposed to work.

------------------------------------------------------------
o Introduction - Why mlox?

mlox runs on a little rule-based engine that takes rules from 2 input files:
mlox_base.txt, which contains general community knowledge, and mlox_user.txt
(if you have created one), which you can edit to contain local knowledge of
your personal load order situation. You may completely ignore mlox_user.txt if
you don't want to be bothered with it. It's main audience will be the "power
user".

Why mlox? Well, because getting your load order "sorted" (also in the sense of
"working correctly") can be a tedious, error-prone job. So why not automate
it? mlox can help in a variety of situations:

- It's not rare that a user will post on a TES forum asking for load order
help, and it is readily apparent that they have not read the Readmes for the
mods they are using. For example, sometimes a Readme will say to activate only
one of a set of plugins, but they have inadvertently activated them all. Then
they ask why it's not working. The answer is simply: "run mlox".

- There's also the situation where a power user with hundreds of mods may want
to re-install from scratch, but they have so many mods, they've forgotten
about some of the pre-reqs, incompatibilities and orderings, so they end up
making little mistakes during the re-install. Sadly, this has happened to me
:) With the mlox knowledge base, you don't have to remember these details, you
just write a rule and the rule remembers for you. mlox will not forget.

- If you are a modder, and you are tired of hearing people having the same
installation problems over and over again with your mod, or hearing about
alleged problems with your mod that are actually known conflicts with other
mods, you might consider contributing rules to the mlox rule-base that
describe orderings, conflicts, and dependencies for your mod. Then when people
have problems, you can tell them to run mlox.

So mlox is potentially for everybody.

That's the theory. Of course, it will take a lot of work to add rules for the
many existing mods. Currently mlox is aware of many popular mods, but there is
still much more work to be done to fill out the rule-base. If mlox succeeds,
it will be due to the effort of many. No one person could do it all.

mlox works by matching filenames specified in rules against the plugins you
actually have installed and active. If you have merged many plugins with the
Construction Set, and no longer use the original plugin filenames, mlox will
not know this and will not be able to order them or tell you dependencies for
your merged plugins. Of course, if you like, you can write rules yourself and
put them in mlox_user.txt to cover these situations.

------------------------------------------------------------
o Origins of mlox

mlox is inspired by Random007's BOSS (formerly FCOMhelper) project, (see:
https://boss-developers.github.io/ ). BOSS (Better Oblivion Sorting Software)
is truly invaluable for Oblivion, because Oblivion is particularly susceptible
to crashing if the load order isn't correct, and some mod projects, notably
FCOM, require a very large and complicated load ordering that can be difficult
to get right. After BOSS came along, when people post about Oblivion load order
problems, the answer to them simply became: "run BOSS". Hopefully, mlox will
become as useful for Morrowind.

However, I decided to take a different approach in the design than the
approach used in BOSS. BOSS uses a "total order" approach, every plugin in the
database knows its ordering relationship with every other plugin, mlox uses a
"partial order" approach, the rules specify a minimal set of orderings. If it
does not matter whether 2 plugins are in a particular order, there is no
ordering specified for them.

BOSS also sometimes requires a second step: every time you run it, all the
plugins it doesn't know about end up at the end of the order and must be
re-ordered by hand. (While BOSS knows about a vast number of mods, you may use
some it doesn't know about. Also, experienced users often have some home-grown
plugins and patches which BOSS couldn't know about). mlox uses your current
load order as a set of "pseudo-rules", so plugin orderings that are unknown by
the rule-base are filled in by what mlox knows about your current order. If
that's too confusing, I'll put it this way, mlox normally only has one step,
and you don't need to do any manual reordering afterwards. If you don't like
the order mlox produces, you can add new rules in the mlox_user.txt, but this
only has to be done once, from then on it's all automatic.

Finally, I wanted to have a set of rules that could easily express
relationships between plugins: A depends on B, X conflicts with Y, and so on.
This would require writing a simple rule-base system.

Don't take this explanation of the differences as a negative view of BOSS. I
have used BOSS and it really has been invaluable in setting up a working load
order for Oblivion. There's a lot to be said for the simple approach it takes.
For example, the BOSS rule-base is trivial to understand, while the mlox
rule-base in comparison is quite complicated and that can potentially lead to
errors and behavior that is not understood. So you can't really say one
approach is better than the other. I just prefer to be able to write rules to
customize my load order, and to be able to express dependencies and conflicts,
and these are things that really need a little rule-based engine. So that's
why I wrote mlox.

------------------------------------------------------------
o Note to mod Authors

It is my hope that the users of your mod will benefit from using mlox, and
also that maybe mlox will help reduce mod conflicts, and support questions for
your mod due to misconfiguration. It is a grand goal (I hope), and there are
some things we can do together to see it happen.

The first thing is versioning of your mod. If mlox can tell what version of
your mod the user is using, it can give more accurate advice. mlox can get the
version of a plugin from its header description field (preferred), or from the
plugin filename.

So, if the filename stays the same from version to version, then if the
description field of the plugin contains a version string:

Version: 0.57

(on a line by itself) mlox will be able to use it. (Wrye Mash can report that
version too, so it's just a generally useful thing to have in the description).

mlox can also tell the version from the filename. So, for example, this works:

Plugin_V1.0.esp

The next thing is teaching mlox about your mod. If you like, you can ask for
rules to be added for you, post on the Bethsoft forums and they'll be added
into the next release of the rule-base.
If you're adventurous and know about Subversion, you can ask for write access
to the rule-base, and I'll let you make changes to the rule-base directly.
The more mlox knows, the more useful it is, and people will have fewer load
order problems.

------------------------------------------------------------
o On the Importance of the output warnings

[REQUIRES] warnings specify missing pre-requisites, this is usually very
important, and normally you can consider these "errors" that should be fixed.
But in some case, they are warnings about patches that are available to make
two plugins work better together.

[PATCH] warnings specify mutual dependencies as in the case of a patch plugin
where you'd like to know if the patch is missing or if the thing that's
supposed to be patched is missing. These are usually pretty important warnings
since proper functioning of a mod sometimes means getting patches properly
installed.

[CONFLICT] warnings specify situations where plugins conflict and generally
speaking, these are "warnings". When 2 plugins conflict, the second one in the
load order wins, because it overrides objects it has in common with the first.
In some cases, the game will still play, but you will not see some of the
content of the first plugin. In other cases, conflicts will break your game.
The comments printed by the conflict rules will try to tell you how important
the conflict is so you can decide which plugin to load last, or which to omit,
depending on what you want to see in your game.

[NOTE] warnings print information that may be of use to you. They may tell you
that a particular plugin is known to have evil GMSTs, or whether or not it is
a good idea to include it in "Merged Objects.esp" if you have that. They are
like annotations for all your plugins. In command-line mode, you can always
turn off the printing of NOTEs with the (-q) command line option if you don't
want to see them.

------------------------------------------------------------
o Testing

Before you start testing how mlox works on your load order, I recommend using
Wrye Mash to save your current load order: In the plugin pane under Mash's
"Mods" tab: right click on a column header, choose "Load" -> "Save List...",
and enter a name for your saved load order so that you can revert back to it
later should you decide that you do not like the results you get from mlox.

mlox only updates your load order in GUI mode if you press the update button,
(or in command-line mode if you use the -u switch). So you should let mlox
tell you what it's going to do first, then decide whether or not you like the
results before you actually let mlox update your load order.

------------------------------------------------------------
o Note to Wrye Mash users

If you use the "Lock Times" feature of Wrye Mash, then you'll need to turn it
off *before* you use mlox to sort your load order, otherwise Mash will just
undo any load order changes mlox makes when it runs. After you have changed
your load order with mlox, then you can turn "Lock Times" back on.

------------------------------------------------------------
o Usage

On Windows, run mlox.exe or if you have the .py file association set-up
double-click mlox.py
On Linux, run the python script: mlox.py

These commands will start mlox in GUI mode. If the proposed load order looks
good to you, press the "Update Load Order" button.

Here is the full command-line usage for mlox from "mlox -h" (You can ignore
this if you only want to run mlox in GUI mode) (Note that the .exe version
does not support command line mode):

Usage: mlox [OPTIONS]

 OPTIONS
 -a|--all
	Print warnings for all plugins, otherwise warning messages are
	only printed for active plugins.
    --base-only
        Use this with the --explain option to exclude the current load
        order from the graph explanation.
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
	Print this help.
 -l|--listversions
        Use this to list the version numbers parsed from your plugins.
        The output is in 2 columns, the first is the version from the
        plugin filename, if present, the second is from the plugin header,
        if present. Naturally, many plugins do not use version numbers so
        results are spotty. This information can be used to write rules
        using the [VER] predicate.
 -n|--nodownload
	Do not automatically download and update the mlox rules.
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

Here's an example command line to get an explanation of why a plugin
has it's position in the load order:

mlox.py --explain=plugin.esp --base-only

If you want to see the effect of adding in what mlox knows about your
current load order, then leave off the --base-only switch.

----------------------------------------------------------------------
oo The mlox GUI

The mlox GUI displays 4 text panes. The top text pane shows the rules files
that have been loaded and their stats. The middle text pane shows messages
and warnings. And the 2 lower panes that are side by side show the original
load order on the left, and the mlox sorted load order to the right. Plugins
that have moved up due to sorting are highlighted in the mlox sorted order.

To update your load order to the new sorted order, simply press the button
labeled: "Update Load Order".

Right click on the original load order to get a context menu for advanced
options. These options are:

- Select All: allows you to select the text of the plugin order so you can
copy and paste it somewhere.

- Paste: allows you to paste a list of plugins into mlox so you can, for
example, analyze the plugin list posted by someone in a forum post. Input
formats can be: Morrowind.ini [Game Files] section format, the format from
Wrye Mash's "Copy List" function, or the output of Reorder Mods++. NOTE: when
you paste in a list of plugins, mlox assumes they are all active! Also, some
of the rule functions like testing plugin size obviously won't work when
you're pasting in from a list, and in these cases to be on the safe side, the
rules will return a positive result, meaning that you will likely see false
positives. For example, with a rule checking if you have a plugin containing
GMSTs it would normally do that by checking the size of the plugin you have
installed. But when you paste in from a list, mlox cannot check the size, so
if it just sees the name of the plugin it will report that it may have GMSTs
in it, whereas in reality it's possible that the user has cleaned that plugin,
which would change its size.

- Open File: this option allows you to input a list of plugins from a file,
instead of from pasting them. See the Paste option above for input formats and
caveats.

- Debug: this will pop up a window containing a list of debugging output (and
automatically copy the contents to a file: mlox_debug.out). If you run into
problems with mlox, I may need you to send me this bugdump so I can figure out
what happened.

----------------------------------------------------------------------
o Known Issues

- Updating does not immediately refresh [mlox-base YYYY-MM-DD HH:MM:SS (UTC)]
  string in the top text pane, although the update is effective.

- There appear to be compatiblity issues with Yacoby's Wrye Mash Standalone.
  If you are using Yacoby's mash.exe avoid using these options:
    Mlox\Sort using mlox
    Mlox\revert changes
  Instead, use:
    1 - Mash\Lock times off
    2 - Mlox\Launch mlox
    3 - Sort mods using the mlox GUI
    4 - Mash\lock times on

==================================================
o ChangeLog

Version 0.59 - 2014/07/06
	* Fix conflict with tes3cmd's resetdates and only redate files if
          necessary [abot]
	* Automatic checking for and downloading of new rule-base [abot]
Version 0.58 - 2011/02/16 [Not released]
	* Fix for parsing [SIZE] predicate with plugin names that contain
          brackets
	* Added Melchor's workaround for problem displaying different
          encodings in wx.
Version 0.57 - 2009/11/03
	* Added a check for max progress value in the progress dialog
Version 0.56 - 2009/10/29
	* Use a popup error window instead of mlox.err
	* Logo is now a button that does a refresh
	* Added a progress dialog when reading the rule-base
Version 0.55 - 2009/03/16
	* Documentation update: DOS line endings.
Version 0.54 - 2009/03/14
	* Now official .esms are automagically moved to top of load order.
Version 0.52 - 2009/01/08
	* Implemented spoiler hiding for messages with <hide></hide>
Version 0.51 - 2009/01/08
	* Fixed a few bugs in how filenames are expanded.
	* Small GUI presentation tweak to ensure the labels at the bottom of
	  the load order panes don't collide when the sash is adjusted all the
	  way down.
Version 0.50 - 2009/01/06
	* Beta release. Documentation has been edited to be current. No new
	  application functionality from version 0.41.