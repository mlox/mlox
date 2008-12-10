Name: mlox
Version: 0.20
Copyright 2008 John Moonsugar <john.moonsugar@gmail.com>
License: MIT License (see the file: License.txt)
----------------------------------------------------------------------
mlox - the elder scrolls Mod Load Order eXpert
----------------------------------------------------------------------

======================================================================
Alpha Note: the initial release of mlox will be an Alpha release.
This means that virtually all aspects of the program may change, based
on feedback. So please read the section: "Alpha request for Comments"
======================================================================


Contents
o Alpha Request For Comments
o Features
o Installation and quick start
o Introduction - Why mlox?
o Origins of mlox
o What mlox does, operational details
o On the Importance of the output warnings
o Testing
o Note to Wrye Mash users
o Usage
oo The mlox GUI
o How Rules work
o The Rules
oo Ordering Rules
oo Warning Rules
o A couple things of technical note
o ChangeLog

------------------------------------------------------------
o Alpha Request For Comments

The Alpha release is intended to answer (at least) these questions:

- Is a load order sorting and annotation tool useful for Morrowind?
- Does the mlox implementation provide a good solution?
- The rule-base currently contains information I've gleaned from mod
Readmes, web pages and forum postings. In some cases information will
become obsolete quickly. Will the rule-base be able to keep up? Will
its advice be "reliable enough" to make it worth the effort to
maintain it?
- Is the rule-base maintainable into the future? Is it too complicated?
Too error-prone? Is it something that multiple maintainers can work
on?
- Suggestions for distribution and installation will be kindly
entertained. And I'd like to find a good public place to host the
rule-base where multiple editors could work on it at the same time, if
things happen to work out that way.
- Feel free to comment on any aspect of the design or implementation.

Your feedback will be appreciated.

------------------------------------------------------------
o Features

- optimally reorders your load order to avoid known problems, where
"optimally" is relative to the quality and coverage of the rule-base.
(Currently the rule-base needs lots of work, of course).
- warns about missing pre-requisites
- warns about plugin conflicts
- prints notes for things you might want to know about a mod, but were
too lazy to read the Readme, or even find the info in some post
somewhere in the Internets :)
- user customizable via a rules file
- can also check someone else's load list from a file:
   mlox.py -wf Morrowind.ini someones_load_order_posting.txt
  (it also understands output of Wrye Mash and Reorder Mods++)
- runs on Windows or Linux :)

------------------------------------------------------------
o Installation and quick start

- mlox.py has 2 modes, GUI and command line. When executed with no
  command line switches it starts in GUI mode, when executed with
  the switch -h, it displays command line usage help.

- mlox.py is written using Python 2.5 and wxWidgets, just like Wrye
  Mash. (For Windows, soon there will be a standalone executable that
  does not require these pre-requisites). You do need to install Python
  and wxWidgets if you wish to run the script form of the program. 
  For Windows you should install the following two packages:

  http://www.python.org/ftp/python/2.5/python-2.5.msi
  http://prdownloads.sourceforge.net/wxpython/wxPython2.8-win32-ansi-2.8.0.1-py25.exe

- Unpack the mlox appication archive somewhere under your game
  directory. If you don't have a place decided, I suggest you unpack in
  the Morrowind directory. A new directory called "mlox" will be
  created containing all the files.

- The rule-base is released as a separate archive (mlox-data_DATE.7z),
  unpack this archve in the mlox directory created when you unpacked the
  application.

- A quick explanation of the included batch files for Windows (unless
  otherwise specified, run these batch files from the mlox directory):

  mlox - run mlox in GUI mode. This is the one you normally use.
  locheck - run mlox in command-line mode to check (not update).
  lofix - run mlox in command-line mode to update your load order.
  lo - (run this in "Data Files") just prints your current load order.

- On Windows, run mlox.bat. On Linux, run: mlox.py

- mlox.py always assumes that the rule-base files (mlox_base.txt and
  mlox_user.txt, if you have created one) are in the current working
  directory (the directory where you run mlox) so you should run mlox in
  the directory where those two files live.

------------------------------------------------------------
o Introduction - Why mlox?

mlox runs on a little rule-based engine that takes rules from 2 input
files: mlox_base.txt, which contains general community knowledge, and
mlox_user.txt (if you have created one), which you can edit to contain
local knowledge of your personal load order situation. You may
completely ignore mlox_user.txt if you don't want to be bothered with
it. It's main audience will be the "power user".

Why mlox? Well, because getting your load order "sorted" (also in the
sense of "working correctly") can be a tedious, error-prone job. So
why not automate it? mlox can help in a variety of situations:

- It's not rare that a user will post on a TES forum asking for load
order help, and it is readily apparent that they have not read the
Readmes for the mods they are using. For example, sometimes a Readme
will say to activate only one of a set of plugins, but the oblivious
user has activated them all. Then they ask why it's not working. The
answer is simply: "run mlox".

- There's also the situation where a power user with hundreds of mods
may want to re-install from scratch, but they have so many mods,
they've forgotten about some of the pre-reqs, incompatibilities and
orderings, so they end up making little mistakes during the
re-install. Sadly, this has happened to me :) With the mlox knowledge
base, you don't have to remember these details, you just write a rule
and the rule remembers for you. mlox will not forget.

- If you are a modder, and you are tired of hearing people having the
same installation problems over and over again with your mod, or
hearing about alleged problems with your mod that are actually known
conflicts with other mods, you might consider contributing rules to
the mlox rule-base that describe orderings, conflicts, and
dependencies for your mod. Then when people have problems, you can
tell them to run mlox, and post the output.

So mlox is potentially for everybody.

That's the theory. Of course, before mlox really starts to deliver on
its promise, significant effort will be required to add enough rules
to provide comprehensive coverage of at least popular mods. If mlox
succeeds, it will be due to the effort of many. No one person could do
it all.

mlox works by matching filenames specified in rules against the
plugins you actually have installed. If you have merged many plugins
with the Construction Set, and no longer use the original plugin
filenames, mlox will not know this and will not be able to order or
tell you dependencies for your merged plugins. Of course, if you like,
you can write rules yourself and put them in mlox_user.txt to cover
these situations.

------------------------------------------------------------
o Origins of mlox

mlox is inspired by Random007's BOSS (formerly FCOMhelper) project,
(see: http://www.bethsoft.com/bgsforums/index.php?showtopic=890589 )
BOSS (Better Oblivion Sorting Software) is truly invaluable for
Oblivion, because Oblivion is particularly susceptible to crashing if
the load order isn't correct, and some mod projects, notably FCOM,
require a very large and complicated load ordering that is difficult
to get right. After BOSS came along, when people post about Oblivion
load order problems, the answer to them simply became: "run BOSS".
Hopefully, mlox will become as useful for Morrowind.

However, I decided to take a different approach in the design than the
approach used in BOSS. BOSS uses a "total order" approach, every
plugin in the database knows its ordering relationship with every
other plugin, mlox uses a "partial order" approach, the rules specify
a minimal set of orderings. If it does not matter whether 2 plugins
are in a particular order, there is no ordering specified for them.

BOSS also sometimes requires a second step: every time you run it, all
the plugins it doesn't know about end up at the end of the order and
must be re-ordered by hand. (While BOSS knows about a vast number of
mods, you may use some it doesn't know about. Also, experienced users
often have some home-grown plugins and patches which BOSS couldn't
know about). mlox uses your current load order as a set of
"pseudo-rules", so plugin orderings that are unknown by the rule-base
are filled in by what mlox knows about your current order. If that's
too confusing, I'll put it this way, mlox normally only has one step,
you don't need to do any manual reordering afterwards. If you don't
like the order mlox produces, you can add new rules in the
mlox_user.txt, but this only has to be done once, from then on it's
all automatic.

Don't take this explanation of the differences as a negative view of
BOSS. I have used BOSS and it really has been invaluable in setting up
a working load order for Oblivion. There's a lot to be said for the
simple approach it takes. For example, the BOSS rule-base is trivial
to understand, while the mlox rule-base in comparison is quite
complicated and that can potentially lead to errors. So it's not easy
to say which approach is better. I can just say that I prefer to be
able to write rules to customize my load order, and to be able to
express dependencies and conflicts, and these are things that really
need a little rule-based engine. So that's why I wrote mlox.

------------------------------------------------------------
o On the Importance of the output warnings

[*REQ*] warnings specify missing pre-requisites, this is usually
very important, and normally you can consider these "errors" that
should be fixed. But in some case, they are warnings about patches
that are available to make two plugins work better together.

[CONFLICT] warnings specify situations where plugins conflict and
generally speaking, these are "warnings". When 2 plugins conflict, the
second one in the load order wins, because it overrides objects it has
in common with the first. In some cases, the game will still play, but
you will not see some of the content of the first plugin. In other
cases, conflicts will break your game. The comments printed by the
conflict rules will try to tell you how important the conflict is so
you can decide which plugin to load last, or which to omit, depending
on what you want to see in your game.

[NOTE] warnings print information that may be of use to you. They may
tell you that a particular plugin is known to have evil GMSTs, or
whether or not it is a good idea to include it in "Merged Objects.esp"
if you have that. They are like annotations for all your plugins. In
command-line mode, you can always turn off the printing of NOTEs with
the (-q) command line option if you don't want to see them.

------------------------------------------------------------
o Testing

Before you start testing how mlox works on your load order, I
recommend using Wrye Mash to save your current load order: In the
plugin pane under Mash's "Mods" tab: right click on a column header,
choose "Load" -> "Save List...", and enter a name for your saved load
order so that you can revert back to it later should you decide that
you do not like the results you get from mlox.

mlox only updates your load order in GUI mode if you press the
update button, or in command-line mode if you use the -u switch.

------------------------------------------------------------
o Note to Wrye Mash users

If you use the "Lock Times" feature of Wrye Mash, then you'll need to
turn it off *before* you use mlox to sort your load order, otherwise
Mash will just undo any load order changes mlox makes when it runs.
After you have changed your load order with mlox, then you can turn
"Lock Times" back on.

------------------------------------------------------------
o Usage

On Windows, run the batch file: mlox.bat
On Linux, run the python script: mlox.py

These commands will start mlox in GUI mode. If the proposed load order
looks good to you, press the "Update Load Order" button.

Here is the full usage of mlox from "mlox -h":

Usage: mlox [OPTIONS]

 OPTIONS
 -a  Print warnings for all plugins, otherwise warning messages 
     are only printed for active plugins.
 -c  check mode, do not update the load order.
 -d  turn on debug output.
 -f  file processing mode, at least one input file must follow on
     command line, each file contains a list of plugins which is 
     used instead of reading the list of plugins from the data file
     directory. File formats accepted: Morrowind.ini, load order 
     output of Wrye Mash, and Reorder Mods++.
 -h  print this help.
 -q  run more quietly (does not print out NOTEs).
 -u  update mode, updates the load order.
 -v  print version and exit.
 -w  warnings only, do not display the new load order.

when invoked with no options, mlox runs in GUI mode.

mlox is intended to be run from somewhere under your game directory.
And it should work under Windows or Linux.

mlox sorts your plugin load order using rules from input files
(mlox_base.txt and mlox_user.txt, if it exists). A copy of the
newly generated load order is saved in mlox_loadorder.out.

Note: if you use Wrye Mash's "lock times" feature and you want mlox to
update your load order, you need to run Mash first and turn it off.
Otherwise, the next time you run Mash, it will undo all the changes in
your load order made by mlox.

oo The mlox GUI

The mlox GUI displays 4 panes. The top text pane shows the rules files
that have been loaded and their counts. The middle text pane shows
messages and warnings. And the 2 lower panes that are side by side
show the original load order on the left, and the mlox sorted load
order to the right. Plugins that have moved up due to sorting are
highlighted in the mlox sorted order.

To update your load order to the new sorted order, simply press the
button labeled: "Update Load Order".

------------------------------------------------------------
o How Rules work

Multiple instances of rules are allowed.

Rules from mlox_user.txt take precedence over those in mlox_base.txt.
The user is encouraged to use mlox_user.txt to customize their load
order, while mlox_base.txt serves as a repository of community
knowledge about plugin order, conflicts, notes and such.

A rule starts with a label, like "[Order]", and ends when a new rule
starts, or at the end of file.

All filename comparisons are caseless, so you do not have to worry
about capitalization of plugin names when entering rules.

Comments begin with '#'. When mlox.py reads rules, comments are first
stripped, and then blank lines are ignored.

Message text in rules may be multi-line. All message lines must begin
with whitespace.

Note that listed plugins must not begin with whitespace.

------------------------------------------------------------
o The Rules

oo Ordering Rules

* The [Order] rule specifies the order of plugins. (In the following
example, plugin-1.esm comes before plugin-2.esp which comes before
plugin-N.esp, and so on). If two orderings conflict, the first one
encountered wins. Order conflicts are called "cycles", and an example
would be if we have one rule that puts aaa.esp before bbb.esp, and
another rule that puts bbb.esp before aaa.esp. Whenever we encounter a
rule that would cause a cycle, it is discarded.

[Order]
plugin-1.esm
plugin-2.esp
  .
  .
plugin-N.esp

This rule is read: "plugin-1.esm precedes plugin-2.esp which precedes
plugin-N.esp". It means that plugin-1.esm must precede plugin-2.esp
AND plugin-2.esp must precede plugin-N.esp in the load order. This
relationship is transitive, so plugin-1 must also precede plugin-N.


* The [NearStart] rule specifies that one or more plugins should
appear as near as possible to the Start of the load order.

[NearStart]
plugin-1.esp
plugin-2.esp
  .
  .
plugin-N.esp

Normally there will be only one [NearStart] rule, for the main master
file, (Morrowind.esm). It is not a good idea to write lots of
[NearStart] rules. If you think you have to, we should talk. Use
[Order] rules to place plugins in relationship to each other.


* The [NearEnd] rule specifies that one or more plugins should appear
as near as possible to the End of the load order.

[NearEnd]
plugin-1.esp
plugin-2.esp
  .
  .
plugin-N.esp

Normally only a few plugins will appear in [NearEnd] rules, like
"Mashed Lists.esp".


oo Warning Rules

Note: Warnings are normally only given for "active" plugins (i.e., any
plugin listed in the [Game Files] section of Morrowind.ini). The set
of active plugins is often a subset of all plugins installed in your
data directory. If you wish to see warnings for all installed plugins,
use the "mlox.py -a" command.

* The [Conflict] rule specifies that if any two of the following
plugins are found, then we print out the given message indicating a
conflict problem.

[Conflict]
 This message is printed when any 2 of the following plugins are found
 (multi-line messages are possible with continuation lines starting 
 with whitespace)
plugin-1.esp
plugin-2.esp
  .
  .
plugin-N.esp

This rule is read: "Print the conflict message when any 2 plugins from
the set of plugin-1.esp, plugin-2.esp, ... plugin-N.esp are present at
the same time."


* The [ConflictAny] rule specifies that when the first plugin and any
of the following plugins are found, we print out the given message.

[ConflictAny]
 This message is printed when the first plugin conflicts with any of
 the following plugins
plugin-X.esp
plugin-1.esp
  .
  .
plugin-N.esp

This rule is read: "Print the conflict message when plugin-X.esp
is present along with any plugin from the rest of the list".


* The [PatchXY] rule prints out the given message when it detects that
a patch for some plugins is missing, or that some of the plugins a
patch is supposed to patch are missing. patch.esp depends on
plugin-X.esp and one of plugin-Y*.esp. This rule is used to cover the
common case where a compatibility patch exists for "gluing" two mods
together.

[PatchXY]
 Message
patch.esp
plugin-X.esp
plugin-Y1.esp
  .
  .
plugin-YN.esp

This rule is read: "Print a missing pre-requisite message if patch.esp
is present and plugin-X.esp is missing or if one of plugin-Y*.esp is
missing. And print a missing patch message if plugin-X.esp is present
along with one of plugin-Y*.esp, but patch.esp is not present."

* The [MsgAny] rule prints the given message when any of the following
plugins is present in your data files directory.

[MsgAny]
 Message printed when any of the following plugins are detected.
plugin-1.esp
plugin-2.esp
  .
  .
plugin-N.esp

This rule is read: "Print the message if any plugin in the set
plugin-1.esp, plugin-2.esp, ... plugin-N.esp is present."


* The [MsgAll] rule prints the given message when all of the following
plugins are present in your data files directory.

[MsgAll]
 Message printed if all of the following plugins are detected.
plugin-1.esp
plugin-2.esp
  .
  .
plugin-N.esp

This rule is read: "Print the message if all plugins in the set
plugin-1.esp, plugin-2.esp, ... plugin-N.esp are present."


Note: the following 4 rules [ReqAll], [ReqAny], [AllReq], [AnyReq] all
describe situations where some dependent plugin(s) are missing some
required plugin(s). The format of the names is supposed to give a hint
on the structure of the arguments. The plugins are always listed with
dependent(s) followed by requirement(s). The logical qualifiers "All"
and "Any" indicate a list of things. So when these qualifiers appear
at the start of the name, that means we have a list of dependents,
followed by one requirement. And when the qualifier appears at the end
of a name it means there is a single dependent followed by a list of
requirements. Hopefully, this will become clear from the explanation
of the rules below.

* The [ReqAll] rule specifies that when the dependant plugin is
present, that ALL of the following plugins are also required.

[ReqAll]
 Optional message
dependant-plugin.esp
required-1.esp
  .
  .
required-N.esp

This rule is read: "If the one dependent plugin (dependant-plugin.esp)
is present, then all the required plugins (required-1.esp ..
required-N.esp) must be present, otherwise print an error."


* The [ReqAny] rule specifies that when the dependant plugin is
present, that ANY of the following plugins is also required. As long
as one of the required plugins is present, no warning is printed.

[ReqAny]
 Optional message
dependant-plugin.esp
required-1.esp
  .
  .
required-N.esp

This rule is read: "If the one dependent plugin (dependant-plugin.esp)
is present, then any one of the required plugins (required-1.esp ..
required-N.esp) must also be present, otherwise print an error."


* The [AllReq] rule specifies that if all the dependant plugins are
present, that the last plugin is also required. (Note that this rule
is rarely needed since [PatchXY] rule subsumes it in most cases).

[AllReq]
 Optional message
dependant-1.esp
  .
  .
dependant-N.esp
required-plugin.esp

This rule is read: "If all the dependent plugins (dependant-1.esp ..
dependant-N.esp) are present, then the one required plugin
(required-plugin.esp) must also be present, otherwise print an error."

* The [AnyReq] rule specifies that if any of the dependant plugins
are present, then the last plugin is also required. 

[AnyReq]
 Optional message
dependant-1.esp
  .
  .
dependant-N.esp
required-plugin.esp

This rule is read: "If any of the dependent plugins (dependant-1.esp
.. dependant-N.esp) are present, then the one required plugin
(required-plugin.esp) must also be present, otherwise print an error."

==================================================

o ChangeLog

Version 0.19 - 2008/12/
	* mlox now hosted on googlecode, so I put it under the liberal
	MIT License.

Version 0.13 - 2008/12/07
	* runs with a GUI when run without any command line parameters.
	* use the new switch -u to update load order, and -c to just
	check the load order in command line mode. old switch -n removed. 
	* now comes with an .exe version for Windows that does not
	require Python

Version 0.12 - 2008/12/06
	* new strategy for making pseudo-rules from current load
	order. Now if adding an edge fails during this process due to
	cycle detection, we re-try with a few of the forefather nodes.
	This should improve the result to look more like the original
	ordering in the case where the rule-base has sparse orderings. 
	* added more debug output to -d switch.
	* batch files now save all program output first before
	displaying so a complete record of the run is kept.

Version 0.11 - 2008/12/04
	* made sure .bat files use DOS line endings.

Version 0.1 -  2008/12/04
	* Alpha release.
