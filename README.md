**mlox, a tool for analyzing and sorting your Morrowind plugin load order**

# Introduction
mlox is a mini "expert system" for advising you on your set of plugins. Use mlox to check for plugin dependencies and conflicts, and to sort your plugins into an optimal load order.

**Note**: If you use mlox to sort your load order, it is highly recommended that you use Hrnchamd's [Morrowind Code Patch](http://www.nexusmods.com/morrowind/mods/19510), which makes it much safer to change your load order for an existing savegame.
# Download mlox
As well as on [SourceForge](https://sourceforge.net/projects/mlox/files/mlox/) you can download mlox from these locations:

[Morrowind Nexus](http://www.nexusmods.com/morrowind/mods/43001/)

[Great House Fliggerty](http://download.fliggerty.com/download-58-999)

You only need to download the mlox application from those links. There are two options, you only need one of these:

  * **mlox-exe-VER.7z** if you have Windows and do not want to install Python (this is a substantially larger download).
  * **mlox-VER.7z** if you have Windows with Python26 and wxPython installed, or if you want to run on Linux.
   * Just in case you'd like to install the Windows pre-requisites for this version, here they are:
    * https://www.python.org/ftp/python/2.6.5/python-2.6.5.msi
    install this version or newer as earlier versions only support US version of Windows and code page 437.
    * http://downloads.sourceforge.net/wxpython/wxPython2.8-win32-ansi-2.8.7.1-py25.exe
    there are later versions of wxPython but mlox needs this specific ANSI version.

Unpack the mlox application archive in your Morrowind directory. You should see an mlox directory in the same directory as Morrowind.exe.

Versions of mlox previous to 0.59 required you to manually download and install the mlox rule-base. Version 0.59 of mlox added an automatic checking and downloading of the mlox rule-base.

**Note**: On Windows 7 (and maybe Vista), if you installed Morrowind in the default location "C:\Program Files\\...", you may need to turn off UAC to get mlox to recognize your activated plugins in Morrowind.ini.
# Features
  * optimally reorders your load order
  * warns about missing pre-requisites
  * warns about plugin conflicts
  * prints notes for things you might want to know about a mod, but were too lazy to read the Readme, or even find the info in some post somewhere in the Internets :)
  * user customizable via a rules file. Just create an mlox_user.txt in your mlox directory, and start adding your own rules.
  * runs on Windows or Linux :)
  * can also check someone else's load list from a file:

        mlox.py -wf Morrowind.ini
        mlox.py -wf someones_load_order_posting.txt

or just paste the list of plugins into the Active plugins pane of the GUI. (mlox understands output of Wrye Mash and Reorder Mods++)

(Note that mlox does not tell you if you have missing Meshes or Textures, it is only a load order tool, and does not report problems with resources).

# Customizing your Load Order

mlox allows you to customize your load order by adding your own sorting rules to a file called "mlox_user.txt", which you put in your mlox directory. Then, all you need to do to get your load order re-sorted correctly is press the update button in mlox. It can't get easier than that.

You can add any of mlox's rules to "mlox_user.txt", but for people that want to customize their load order, the **`[Order]`** rule is probably all that is needed. Here is a simple example:

Let's say you want to make sure that mlox always puts plugin "Foo.esp" before "Bar.esp". Just create a simple text file called "mlox_user.txt" in your mlox directory (using Notepad or whatever) containing the following:

    [Order]
    Foo.esp
    Bar.esp

From now on, when you press the mlox update button, mlox will make sure that this is the order for those two plugins. Note that the **`[Order]`** rules in mlox_user.txt (your personal rules) take precedence over the rules in mlox_base.txt.

You should also be aware that the **`[Order]`** rule only specifies relative order, so in the example above, it does not mean that Foo.esp must come _immediately_ before Bar.esp, only that Foo.esp must load _somewhere_ before Bar.esp.

# Documentation
The complete documentation for mlox comes as simple text files included in the mlox download, you can browse them on-line directly from the svn repository:

  * [mlox_readme.txt](http://code.google.com/p/mlox/source/browse/trunk/mlox/mlox_readme.txt) provides a guide to getting started and introduction to usage. **Important Reading!**
  * [mlox_rules_guide.txt](http://code.google.com/p/mlox/source/browse/trunk/mlox/mlox_rules_guide.txt) explains the syntax of the mlox rules, and how to write them yourself if you want to customize mlox.
  * [mlox_guts.txt](http://code.google.com/p/mlox/source/browse/trunk/mlox/mlox_guts.txt) describes mlox's inner workings and how it does its job.

# Contribute to the mlox rule-base

mlox can only succeed if you share your knowledge about plugin load order, conflicts, and pre-requisites! Your contributions will help other players that follow in your footsteps.

## Submission Guidelines

The mlox project welcomes all submissions of information for inclusion in the mlox rule-base, but the more information you can give when you make the submission, the more likely your submission will be used. Information that lacks detail or is of low quality will be given the lowest priority. Which means it may only get investigate for inclusion if time permits.

So, please try to include:

  * the Full name of the mod(s), the version number, and the author.
    * Good: '"Herbalism" 1.3 by Balor'
    * Bad: 'herbalism mod' (which one? there are a number of them!)
  * a link to the mod, if you have one.
  * the best explanation you can give
    * If it's a conflict, please explain what the actual conflict is.
    * If it's a load order, it would be great to say what the order affects.

And if you really want a gold star, try writing your submission in the [mlox rule language](http://code.google.com/p/mlox/source/browse/trunk/mlox/mlox_rules_guide.txt).

Really, I do appreciate all submissions of information of any sort for mlox, since I cannot physically learn everything about mods myself. But remember that the higher quality submissions will be given highest priority.

Thanks!

# Become a rule-base Editor

If you have solid knowledge of load order issues, and you'd like to be able to contribute to the rule-base by editing it directly, please let me know and I'll make you an editor. Editors of the rule-base should read the [Editing Guidelines](EditingGuidelines), which explain how the editing process works.

Glory awaits you my friend.

# Obligatory Screen Shot

![mlox interface](https://sourceforge.net/p/mlox/screenshot/mlox_screen.png)

# Reporting Problems

If mlox fails or gives an error, please report it. Here is some information you can provide that will help in the error analysis:

  * Usually when mlox fails it will pop up a window describing the error, please report the contents of this window when reporting a problem.
  * If the mlox GUI disappears upon startup, the usual cause for this kind of failure would be using an incompatible version of wxPython. Please install the recommended version mentioned in the [Download mlox](Mlox#Download_mlox) section of this page. If it still fails, please report the contents of "mlox.err" as mentioned in the previous item.
  * If mlox runs but gives unexpected results, please use the GUI bugdump feature and report the output. You do this by running mlox in GUI mode, right-click in the "Active Plugins" pane on the left side, choose "Debug" from the popup menu, and attach the contents of the popup window to an email to john.moonsugar's gmail.com account.

# Support

mlox support is provided at the Bethsoft forums. You can always find the latest mlox release thread by [Search](http://forums.bethsoft.com/index.php?app=core&module=search&search_in=forums) or via the [Morrowind Mods forum](http://forums.bethsoft.com/forum/12-morrowind-mods/) (look for the latest mlox topic). (Note: you do have to be a registered member of the Bethsoft forums to post there).

You _can_ post on the SourceForge Issues page here or on mlox's thread on Morrowind Nexus but those pages aren't checked as frequently as the Bethsoft forum thread.
