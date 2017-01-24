**tes3lint is a command-line tool for investigating potential problems in TES3 plugins. It is written in Perl and runs natively on Windows or Linux.**

# Get tes3lint

  * [Get the latest stable version from the mlox project download page](https://sourceforge.net/projects/mlox/files/tes3lint/)
  * tes3lint requires Perl, if you run on Windows I recommend: [strawberry Perl](http://strawberryperl.com/). Make sure the perl program "perl.exe" is in your execution path (%PATH%) (strawberry Perl should automatically add itself to your path when it installs). (If you are unfamiliar with Perl or get stuck on this step, please read the [InstallPerl](InstallPerl) wiki page).

# Introduction

tes3lint was written for mod authors to check their plugins for potential problems. The end-user can still use it too, of course, but the output may be somewhat mysterious to someone who is not familiar with the Construction Set and plugin guts.

A small word of caution at this time regarding the results: the things that tes3lint flags are sometimes innocuous, and it's also quite possible that the program is incorrect. I think most modders will understand the output pretty well. For others, I'd say that just because something is flagged, does not mean you should go running to the author of a mod in a panic. tes3lint is really meant as a means of focusing one's investigation, and not jump to hasty conclusions based on what it says.

# Features

  * Find out if the plugin defines autocalc'ed spells.
  * Find out if the plugin has an _implicit_ dependency on Tribunal/Bloodmoon functions because it uses them but does not list the expansion as a Master.
  * List Evil GMSTs.
  * Find [deprecated usage of Leveled List scripting functions on standard Bethesda Lists](http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists#Scripted_Leveled_Lists).
  * Find duplicate (i.e.: "dirty/unclean") records that are unchanged from one of the masters.
  * Shows duplicate and modified INFO dialogs.
  * Find CELLs that trigger the FOGBUG.
  * Find any CELLs where fog density in DATA is different from AMBI subrecords.
  * Find [problematic usage of GetSoundPlaying](http://sites.google.com/site/johnmoonsugar/Home/morrowind-scripting-tips#getsoundplaying) for detecting events.
  * Find dirty junk cells that are apparently injected by some CS bug.
  * Find scripts that are unaware of MenuMode.
  * Show if plugin is missing Author/Description/Version from plugin header.
  * Find duplicate/modified INFOs.
  * Finds potentially buggy case where INFO dialogs have had their IDs changed.
  * Find all records in the plugin that override records in its Masters.
  * Find [problematic scripts attached to Bethesda doors](http://sites.google.com/site/johnmoonsugar/Home/morrowind-scripting-tips#cellchanged).

You can customize exactly which items are reported with the -f command-line switch:

Example:

     perl tes3lint -f exp-dep,bm-dep myplugin.esp

This would only report on implicit dependencies on the expansions and Bloodmoon in particular. You could always create a custom .bat file to run the reports you wish to see most often. There are a couple of example .bat files included in the download archive for reference.

More checks will be added based on user feedback.

# Obsoleted tools

tes3lint is a combination of older tools I wrote, and it now makes them obsolete. These obsolete tools are:

  * dianalyze - finds small class of dialog problems
  * fogbug.py - find cells that trigger fogbug
  * expdep - finds implicit dependency on Tribunal/Bloodmoon expansions.

# Installing and Running tes3lint

If you get the latest stable version, it comes in a 7-zip archive which you can unpack anywhere under your Morrowind directory. If you don't already have a place in mind, I recommend just unpacking in the Morrowind directory itself. The archive will extract to a subdirectory "tes3lint" containing all the files.

You also need to install Perl per the instructions above. tes3lint comes with some batch files to give you an idea of how to run the program. The batch files were written assuming you've installed strawberry Perl in the default location (C:\strawberry), and that it put itself in your %PATH%, which it does by default.

To run tes3lint, open a command line terminal window (Run -&gt; cmd.exe) then

    > cd ...\Morrowind\tes3lint
    > tes3lintfull.bat "..\Data Files\plugin.esp"

This will run a full check for all flags and the output will be stored in a plain text file called "tes3lint.log".

There is also a "tes3lint.bat" which only does a subset of checks, ones that might be considered more important.

If you wish to customize the output, I suggest you make a copy of one of the .bat files, and edit the command line to use the "-f" switch, specifying only those flags you wish to have checked.

tes3lint is fairly slow, depending on the contents of the plugin you are examining and which output flags have been selected. It may take up to a minute or so to do a full report on a large plugin that contains many scripts.

# Example Output

To get an idea of what tes3lint can tell you, view a sample output from tes3lint: [Tes3lintSample](Tes3lintSample)

# Usage

tes3lint Usage:

    tes3lint [OPTIONS] plugin...

    OPTIONS
     -D        debug output (vast)
     -f flags  specify which flags (in a comma delimited list) to print.
     -v        verbose (possibly more output)

    The following are shortcuts for printing recommended lists of flags:
     -a  all output flags on. (slowest, but most comprehensive option).
     -n  "normal" output flags on (performs relatively speedily):
          (EVLGMST, FOGBUG/FOGSYNC, MOD-IID, JUNKCEL, DUP-REC)
         this option omits some flags for the sake of speed and relevancy.
     -r  "recommended" output flags on (performs relatively slower):
          (CLEAN, EVLGMST, FOGBUG/FOGSYNC, MISSAUT, MISSDSC, MISSVER, MOD-IID,
          JUNKCEL, DEP-LST, DUP-REC, BM-DEP/EXP-DEP)
          This adds some checks that perform slowly due to massive regular
          expression matching. This is the default output flag option that
          selected if no others are specified.

    Examples:

    # print out selected flags (just: AUTOSPL and MENUMOD):
    tes3lint -f autospl,menumod plugin.esp

    # print out all flags for a bunch of plugins:
    tes3lint -a plugin1.esp plugin2.esp ... pluginN.esp

    # print out only the most important flags
    tes3lint -r plugin.esp

    [Note: tes3lint wants to be able to find Masters for a given plugin, so it
    needs to run somewhere under your Morrowind directory, but it does not
    necessarily have to be in your Data Files directory.]

    tes3lint normally only prints output for interesting things it finds. If it
    finds nothing for a plugin, no output is generated unless the CLEAN flag is
    given. When something interesting is found, a flag is printed after the plugin
    name. On following lines, an indented report is printed that gives more detail
    about the flagged items.

     The following flags are defined:

        AUTOSPL: The plugin defines autocalc'ed spells.

        BM-DEP:  The plugin uses Bloodmoon specific functions, so it needs version
                 1.6.1820, but the plugin does not list Bloodmoon.esm in its list
                 of Masters. This is similar to the EXP-DEP flag, but it is for
                 Bloodmoon only.

        CELL00:  This means that an apparently dirty copy of cell (0, 0) is
                 included in the plugin. This cell is often accidentally modified
                 since it is the default cell displayed in the cell view window.

        CLEAN:   If this flag is used, then a plugin that is not flagged with any of
                 the flags below will be flagged "CLEAN". It really just means:
                 "found nothing of interest".

        DEP-LST: This flag indicates that the plugin makes deprecated use of
                 scripting functions to modify standard Bethesda Leveled Lists.
                 This is bad because these lists will then be stored in the user's
                 savegame just like any other changed object. Since savegames load
                 after all plugins (including "Mashed Lists.esp" which contains
                 merged leveled lists), this means that merged leveled lists will
                 be ignored. Note that this warning only applies to changes to
                 Bethesda lists. Changes to leveled lists specific to the mod will
                 not be flagged. For more about the problem of using scripting
                 functions to modify Bethesda lists see:
                 http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists

        DUP-INF: indicates the exact INFO dialog with the same ID, text and filter
                 exists in one of the masters of this plugin. This may be a
                 problem, or maybe not. Sometimes duplicate dialog is intentional
                 in order for dialog sorting to be correct. It's only a mistake
                 if it really was unintentional.

        DUP-REC: These are records in the plugin that are exact duplicates of
                 records that occur in one of the masters. These are sometimes
                 referred to as "dirty" or "unclean" entries.

        EXP-DEP: The plugin requires either Tribunal or Bloodmoon because it uses
                 engine features not present in the original Morrowind such as
                 startup scripts or Tribunal functions, but the plugin has not
                 listed any expansions in its list of Masters. This is not
                 necessarily a problem, but it may contradict the Readme for the
                 mod sometimes.

        EVLGMST: You know this one! This means that some of the "72 Evil GMSTs" are
                 present in this plugin and that they have the same exact value as
                 the original GMST in the master .esm. Other GMSTs not in the list
                 of known Evil GMSTs or GMSTs that have been modified from their
                 original values are not flagged. Note that it is also possible to
                 have other GMSTs show up in the DUP-REC list, but those are not
                 from the list of 72 GMSTs that would get introduced by the
                 Construction Set.

        FOGBUG:  The plugin has an interior CELL with a fog density of 0.0, and the
                 cell is not marked to "behave as exterior". This circumstance can
                 trigger the "fog bug" in some graphics cards, resulting in the
                 cell being rendered as a black or featureless blank screen.

        FOGSYNC: This flag indicates that for some reason that the fog density
                 setting in the CELL.DATA subrecord is not equal to the fog
                 density setting in the CELL.AMBI subrecord. This is unusual, it's
                 probably caused by editing the plugin in Enchanted Editor, and
                 it's probably harmless, but you can resync the values by editing
                 that cell in the Construction Set.

        GETSND:  The plugin appears to use the scripting function GetSoundPlaying
                 to detect events (as opposed to managing the playing of sound
                 files). GetSoundPlaying fails consistently on a small number of
                 users' systems, so these users will encounter problems with these
                 scripts. Note that tes3lint uses regular expressions to detect the
                 purpose for using GetSoundPlaying, and it will sometimes get
                 false positives. For more about the GetSoundPlaying problem see:
                 http://sites.google.com/site/johnmoonsugar/Home/morrowind-scripting-tips

        JUNKCEL: These are bogus external CELL records that crop up in many
                 plugins, possibly due to a Construction Set bug. They contain
                 only NAME, DATA and sometimes RGNN subrecords, and the flags in
                 the DATA subrecord are unchanged from the flags in the Master.

        MENUMOD: The plugin contains scripts that do not check menumode. Each script
                 will be printed in the details section. This may or may not be
                 intentional, so the flag is optional and only included in the -a
                 switch.

        MISSAUT: The plugin header is missing the Author field. It is strongly
                 recommended that authors put their name or handle in the Author
                 field.

        MISSDSC: The plugin header is missing a description field. It is strongly
                 recommended that a short description of the plugin is entered in
                 this field.

        MISSVER: The plugin header description field is missing a "Version: X.Y"
                 string. It is strongly recommended that the version number be
                 added to the description. This version number is very helpful in
                 documenting which version of the plugin a user is using. This
                 information is used by tools such as Wrye Mash and mlox. The
                 regular expression pattern used by Wrye Mash to match the version
                 is: "^(Version:?) *([-0-9\.]*\+?) *\r?$". (mlox will match a
                 much wider variety of version number formats). It is safest to
                 use a string of the format: "Version: X.Y", on a line by itself.

        MOD-INF: indicates that an INFO dialog with the same ID exists in the
    	     master, but this plugin has modified the text or the filter. This
    	     is quite common when a plugin intentionally modifies a master's
    	     dialog, but it often a problem when due to unintentional changes.
    	     A MOD-INF flag may have an associated MOD-IID flag. The modified
    	     Info record is dumped in a very cursory fashion (the binary bits
    	     are just trimmed out) in order to give a quick identification.

        MOD-IID: indicates that the exact same INFO dialog text exists in this
    	     plugin as in a master, but under a different ID. When associated
    	     with a MOD-INF, this situation may be due to creating new dialog
    	     by copying the original, and then accidentally editing the
    	     original instead of the copy which may cause bad dialog problems
    	     and should probably be investigated further.

        OVR-REC: The plugin contains record(s) that override the record with the
                 same ID in one of its masters.

        SCRDOOR: The plugin adds scripts to Bethesda doors, which has the potential
                 to break any script in the same cell that uses the CellChanged
                 function. CellChanged in that cell will always return 0 from now on.
                 See: http://sites.google.com/site/johnmoonsugar/Home/morrowind-scripting-tips

        !BM-FUN: Bloodmoon.esm is listed as a master, but tes3lint did not detect
                 any usage of Bloodmoon functions. (Note that there may be other
                 reasons for listing Bloodmoon as a master).

        !TB-FUN: Tribunal.esm is listed as a master, but tes3lint did not detect
                 any usage of Tribunal functions. (Note that there may be other
                 reasons for listing Tribunal as a master).

# Support

tes3lint support is provided at the Bethsoft forums. You can always find the latest tes3lint release thread by [Search](http://www.bethsoft.com/bgsforums/index.php?s=&act=Search&mode=adv&f=0) or via [john.moonsugar's profile](http://www.bethsoft.com/bgsforums/index.php?act=Search&nav=au&CODE=show&searchid=58ce6256c770eedc8fcbfa7aadfabb76&search_in=topics&result_type=topics) (look for the latest tes3lint topic). (Note: you do have to be a registered member of the Bethsoft forums to use those links).

You may also send mail to john.moonsugar's gmail.com account.
