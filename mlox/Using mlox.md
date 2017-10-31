# mlox - the elder scrolls Mod Load Order eXpert

Version: 0.62

Copyright 2014-2017 [MIT License](https://github.com/mlox/mlox/blob/master/License.txt)
* John Moonsugar
* Dragon32
* Arthur Moore

This file gives basic information on what mlox is and how to use it.

For a full readme please see [here](https://github.com/mlox/mlox/blob/master/README.md).

# Backup Your Load Order Before Using!
Before you start testing how mlox works on your load order, I recommend using Wrye Mash to save your current load order, so that you can revert back to it later should you decide that you do not like the results you get from mlox.
* In the plugin pane under Mash's "Mods" tab:
  * right click on a column header, choose "Load" -> "Save List...", and enter a name for your saved load order


mlox only updates your load order in GUI mode if you press the update button, (or in command-line mode if you use the `-u` switch).
So you should let mlox tell you what it's going to do first, then decide whether or not you like the results before you actually let mlox update your load order.

# Note to Wrye Mash users

If you use the "Lock Times" feature of Wrye Mash, then you'll need to turn it off **before** you use mlox to sort your load order, otherwise Mash will just undo any load order changes mlox makes when it runs.
After you have changed your load order with mlox, then you can turn "Lock Times" back on.

# Usage
Windows users can run the program by clicking on `mlox.exe`.  Linux users can either click on `mlox.py` or type `python mlox.py` on a command line.

These commands will start mlox in GUI mode. If the proposed load order looks good to you, press the "Update Load Order" button.

Note: the .exe version does not support command line mode!

When invoked with no options, mlox runs in GUI mode.

mlox is intended to be run from somewhere under your game directory.
mlox runs under Windows or Linux.

mlox sorts your plugin load order using rules from input files (`mlox_base.txt` and `mlox_user.txt`, if it exists). A copy of the newly generated load order is saved in `mlox_loadorder.out`.

## The mlox GUI
The mlox GUI displays 4 text panes.
The top text pane shows the rules files that have been loaded and their stats.
The middle text pane shows messages and warnings.
And the 2 lower panes that are side by side show the original load order on the left, and the mlox sorted load order to the right.
Plugins that have moved up due to sorting are highlighted in the mlox sorted order.

To update your load order to the new sorted order, simply press the button labeled: "Update Load Order".

Right click on the original load order to get a context menu for advanced options.
These options are:

* Select All: allows you to select the text of the plugin order so you can copy and paste it somewhere.

* Paste: allows you to paste a list of plugins into mlox so you can, for example, analyze the plugin list posted by someone in a forum post.
Input formats can be: Morrowind.ini [Game Files] section format, the format from Wrye Mash's "Copy List" function, or the output of Reorder Mods++.
NOTE: when you paste in a list of plugins, mlox assumes they are all active!
Also, some of the rule functions like testing plugin size obviously won't work when you're pasting in from a list, and in these cases to be on the safe side, the rules will return a positive result, meaning that you will likely see false positives.
For example, with a rule checking if you have a plugin containing GMSTs it would normally do that by checking the size of the plugin you have installed.
But when you paste in from a list, mlox cannot check the size, so if it just sees the name of the plugin it will report that it may have GMSTs in it, whereas in reality it's possible that the user has cleaned that plugin, which would change its size.

* Open File: this option allows you to input a list of plugins from a file, instead of from pasting them.
See the Paste option above for input formats and caveats.

* Debug: this will pop up a window containing a list of debugging output (and automatically copy the contents to a file: `mlox_debug.out`).
If you run into problems with mlox, I may need you to send me this bugdump so I can figure out what happened.

## Command line usage

Mlox has many features that are not exposed via the GUI.
These are mostly advanced features, that most users will not need.
To access them, run mlox from a command line with at least one argument.

### Example usage
Obtain an explanation of why a plugin has it's position in the load order:
`mlox.py --explain=plugin.esp --base-only`

If you want to see the effect of adding in what mlox knows about your current load order, then leave off the `--base-only` switch.

Check, but *do not* update your load order from the command line:
`mlox.py -c`

Check, and update your load order from the command line:
`mlox.py -u`



# Known Issues

* There appear to be compatiblity issues with Yacoby's Wrye Mash Standalone.
If you are using Yacoby's mash.exe avoid using these options:
 * Mlox\Sort using mlox
 * Mlox\revert changes

* Instead, use:
    1. Mash\Lock times off
    2. Mlox\Launch mlox
    3. Sort mods using the mlox GUI
    4. Mash\lock times on

# On the Importance of the output warnings
`[REQUIRES]` warnings specify missing pre-requisites, this is usually very important, and normally you can consider these "errors" that should be fixed.
However, in some case, they are warnings about patches that are available to make two plugins work better together.

`[PATCH]` warnings specify mutual dependencies as in the case of a patch plugin where you'd like to know if the patch is missing or if the thing that's supposed to be patched is missing.
These are usually pretty important warnings since proper functioning of a mod sometimes means getting patches properly installed.

`[CONFLICT]` warnings specify situations where plugins conflict and generally speaking, these are "warnings".
When 2 plugins conflict, the second one in the load order wins, because it overrides objects it has in common with the first.
In some cases, the game will still play, but you will not see some of the content of the first plugin.
In other cases, conflicts will break your game.
The comments printed by the conflict rules will try to tell you how important the conflict is so you can decide which plugin to load last, or which to omit, depending on what you want to see in your game.

`[NOTE]` warnings print information that may be of use to you.
They may tell you that a particular plugin is known to have evil GMSTs, or whether or not it is a good idea to include it in "Merged Objects.esp" if you have that.
They are like annotations for all your plugins.
In command-line mode, you can always turn off the printing of NOTEs with the `-q` command line option if you don't want to see them.
