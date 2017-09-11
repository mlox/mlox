# tes3cmd

**tes3cmd is a command-line tool for examining and modifying TES3 plugins in various ways. It can also do things like make a patch for various problems and merge leveled lists, and so on. It is written in Perl and runs natively on Windows or Linux.**

# Introduction

tes3cmd combines a few small tools for various things with TES3 plugins into one program. Since this command can be used to modify your plugins, it is expected you will exercise due caution and always keep backups of your plugins and check the results (in the CS, for example) in case tes3cmd turns it into guar poop. That said, tes3cmd does try to operate safely.

# Get tes3cmd

  * [Get the latest version from the mlox project download page](https://sourceforge.net/projects/mlox/files/tes3cmd/). (The very latest, possibly unstable, script version is [available from git](https://github.com/mlox/mlox/blob/master/util/tes3cmd)). You may also find experimental versions on the download page. The experimental versions may have more bugs, so be careful.
  * As of version 0.37, tes3cmd comes in standalone executable (.exe) form. But you can also use the plain script form, which requires you to install Perl. If you wish to run the script version on Windows I recommend: [strawberry Perl](http://strawberryperl.com/). Make sure the perl program "perl.exe" is in your execution path (%PATH%) (strawberry Perl should automatically add itself to your path when it installs). (If you are unfamiliar with Perl or get stuck on this step, please read the [InstallPerl](InstallPerl) wiki page).

# Installing and Running tes3cmd

The easiest way to install tes3cmd is just to put tes3cmd.exe into your "Data Files". The recommended way to install tes3cmd is to put it someplace where you have command line tools installed (e.g.: "C:\bin", or wherever you like), and then put C:\bin in your %PATH% environment variable: ("My Computer" -&gt; "Properties" -&gt; Advanced -&gt; "Environment Variables" -&gt; Select "Path" -&gt; Edit).

## Hey what is this thing? I click on the tes3cmd icon and it pops up a window that disappears?

tes3cmd is currently a command line program. To run it, you need to start up the windows command line (Start -&gt; Run -&gt; "cmd"). This will give you a command prompt. You can then use "cd" to change directory to your "Data Files" (or wherever you want to work on your plugins), and then use tes3cmd there.

# Support

tes3cmd support is provided at the Bethsoft forums. You can always find the latest tes3cmd release thread by Search or via john.moonsugar's profile (look for the latest tes3cmd topic). (Note: you do have to be a registered member of the Bethsoft forums to use those links).

You may also send mail to john.moonsugar's gmail.com account.

# Features

The examples shown below should work on Windows (let us know if they don't). If you wish to use tes3cmd on Linux, it is assumed you can figure out how to convert quoting conventions to work on Linux.

## active - _Add/Remove/List Plugins in your load order_

    Usage: tes3cmd active OPTIONS plugin1.esp [plugin2.esp...]

    OPTIONS:
     --debug
    	turn on debug messages

     --off
    	deactivate given plugins

     --on
    	activate given plugins

    DESCRIPTION:

    Activates/Deactivates the specified plugins. When no options are specified,
    just prints current active load order.



## clean - _Clean plugins of Evil GMSTs, junk cells, and more_

    Usage: tes3cmd clean OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --backup-dir
    	where backup files get stored. The default is:
    	"Data Files/tes3cmd/backups"

     --cell-params
    	clean cell subrecords AMBI,WHGT duped from masters

     --dups
    	clean other complete records duped from masters

     --gmsts
    	clean Evil GMSTs

     --hide-backups
    	any created backup files will get stashed in the backup directory
    	(--backup-dir)

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --instances
    	clean object instances from cells when duped from masters

     --junk-cells
    	clean junk cells (no new info from definition in masters)

     --no-cache
    	do not create cache files (used for speedier cleaning)

     --output-dir <dir>
    	set output directory to <dir> (default is where input plugin is)

     --overwrite
    	overwrite original plugin with clean version (original is backed up)

    DESCRIPTION:

    Cleans plugins of various junk. If no cleaning options are selected, the
    default is to assume the options:

      --instances --cell-params --dups --gmsts --junk-cells

    The goal of the "clean" command is that it should always be safe to use it
    with no options to get the default cleaning behavior. The different cleaning
    operations are explained below:

    Object Instances (--instances)

      The clean command will clean objects in the plugin that match objects in any
      of its masters. Object instances in cells (some people call these
      "references", but "object instance" is a more accurate descriptive term) are
      defined as byte sequences starting in the subrecord following a FRMR
      subrecord, and match only if this is the same byte sequence as in the
      master, along with the same Object-Index from the FRMR. NAM0 subrecords are
      not part of object instances, and if instances are deleted from a cell, the
      NAM0 subrecord for the cell is updated to reflect any changing instance
      count.

    Cell Params (--cell-params)

      The subrecords for AMBI (ambient lighting) and WHGT (water height) for
      interior cells are often duplicated from the master of a plugin when the
      plugin is saved in the Construction Set.

    Duplicate Records (--dups)

      Object definitions for various record types defined in a master are
      sometimes unnecessarily duplicated in dependent plugins, and this option
      will safely clean them. Only objects that have identical flags and byte
      sequences will be cleaned.

    Evil GMSTs (--gmsts)

      An Evil GMST is defined as a GMST from the list of 11 Tribunal GMSTs or 61
      Bloodmoon GMSTs that are inadvertently introduced to a plugin by the
      Construction Set with specific values. Other GMSTs or GMSTs from those lists
      that do not have the specific Evil Values are NOT cleaned by this function.

      To clean GMSTs that are not Evil, you can use the command:
        "tes3cmd delete --type gmst"

    Junk Cells (--junk-cells)

      Junk cells are bogus external CELL records that crop up in many plugins due
      to a Construction Set bug. They contain only NAME, DATA and sometimes RGNN
      subrecords with data identical to the master. (In addition, interior cells
      will also be removed if they do not introduce any new information).

    Cache Files Feature

      tes3cmd will normally create cached data files for your masters in the
      subdirectory: "Data Files/tes3cmd". If you do not wish tes3cmd to create
      cache files, you can use the --no-cache option. (But it is recommended you
      do use them for speedier cleaning).

    EXAMPLES:

    # clean my plugin of only Evil GMSTs:
    tes3cmd clean --gmsts "my plugin.esp"

    # clean 2 plugins and put the cleaned versions in a subdirectory "Clean":
    tes3cmd clean --output-dir Clean "my plugin1.esp" "my plugin2.esp"

    # clean all plugins in the current directory, replacing the originals with
    # the cleaned versions and save the diagnostic output to a file (clean.txt):
    tes3cmd clean --overwrite *.esm *.esp > clean.txt


## common - _Find record IDs common between two plugins_

    Usage: tes3cmd common OPTIONS plugin1 plugin2

    OPTIONS:
     --debug
    	turn on debug messages

    DESCRIPTION:

    Prints the IDs of records that the 2 given plugins have in common.

    EXAMPLES:

    # Show the records in common between my plugin and Morrowind.esm:
    tes3cmd common "my plugin.esp" "Morrowind.esm"


## delete - _Delete records/subrecords/object instances from plugin_

    Usage: tes3cmd delete OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --backup-dir
    	where backup files get stored. The default is:
    	"Data Files/tes3cmd/backups"

     --exact-id* <id-string>
    	only delete records whose ids exactly match given <id-string>

     --exterior
    	only delete if record is an Exterior CELL

     --flag* <flag>
    	only delete records with given flag. Flags may be given symbolically
    	as: (deleted, persistent, ignored, blocked), or via their numeric
    	values (i.e. persistent is 0x400).

     --hide-backups
    	any created backup files will get stashed in the backup directory
    	(--backup-dir)

     --id* <id-regex>
    	only delete records whose ids match regular expression pattern
    	<id-regex>

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --instance-match <regex>
    	Only delete the object instances that match <regex> in the matching cell

     --instance-no-match <regex>
    	Only delete object instances in the cell that do not match <regex>

     --interior
    	only delete if record is an Interior CELL

     --match <regex>
    	only delete records that match given regular expression <regex>

     --no-match <regex>
    	only delete records that do not match given regular expression
    	<regex>

     --sub-match <regex>
    	only delete the subrecords that match <regex>

     --sub-no-match <regex>
    	only delete the subrecords that do not match <regex>

     --type* <record-type>
    	only delete records with the given <record-type>

     Note: starred (*) options can be repeated, and matching of strings is not
     case-sensitive.

    DESCRIPTION:

    Deletes entire records, or subrecords from records, or object instances from
    cell records. You can really damage things with this command, so be careful!

    One thing you should be extra careful with is deleting objects from cells.
    When objects from a master are "moved" by a plugin, a MVRF group appears
    before the object instance that starts with a FRMR sub-record. If you really
    want to delete that object, you probably want to delete both the FRMR object
    instance and the preceeding MVRF group. A future version of tes3cmd may handle
    this situation more elegantly.

    Note: documentation for regular expressions:
      http://www.perl.com/doc/manual/html/pod/perlre.html

    EXAMPLES:

    # Delete all records with IDs matching the pattern: "foo":
    # (Note that this doesn't also delete records that may depend on "foo").
    tes3cmd delete --id foo "my plugin.esp"

    # Delete all GMST records from a plugin:
    tes3cmd delete --type gmst plugin.esp

    # Delete all records flagged as "ignored":
    tes3cmd delete --flag ignored plugin.esp

    # Delete the poisonbloom spell subrecords from all current "_mca_" NPCs in quicksave.ess:
    tes3cmd delete --type npc_ --match _mca_ --sub-match spell:poisonbloom quicksave.ess


## diff - _Report differences between two plugins_

    Usage: tes3cmd diff OPTIONS plugin1 plugin2

    OPTIONS:
     --debug
    	turn on debug messages

     --ignore-type* <record-type>
    	ignore given type(s)

     --1-not-2|--e1
    	report records in plugin1 that do not exist in plugin2

     --2-not-1|--e2
    	report records in plugin2 that do not exist in plugin1

     --equal|--eq
    	report records in plugin1 that are equal in plugin2

     --not-equal|--ne
    	report records in plugin1 that are different in plugin2

     Note: starred (*) options can be repeated, and matching of strings is not
     case-sensitive.

    DESCRIPTION:

    Prints a report on the differences between the two TES3 files.
    A summary report with up to four sections is printed to standard output
    that gives an overview of differences, as lists of record IDs.
    (Report sections that would have no items are not printed).

    When records in plugin1 are different in plugin2, each of these records is
    printed in detail to a file "plugin1-diff.txt" and "plugin2-diff.txt", which
    can then be compared textually using a tool such as WinMerge or the ediff
    function of Emacs. Note that the output records will be sorted alphabetically
    by record type to make the comparison using these tools easier.

    To reduce a great deal of "uninteresting" differences when diffing savegames,
    the the ModIndex field of CELL.FRMR records are automatically ignored. (Note
    that in this case, the ObjIndex appears to only be incremented by one).

    EXAMPLES:

    # Print report on differences between 2 savegames (output to diff.out):
    tes3cmd diff "save1000.ess" "save2000.ess" > diff.out

    # You can also use the --ignore-type switch to ignore further subfields in
    # order to help reduce the amount of differences as in the following example.
    # Report on differences, but ignore the subfields CREA.AIDT and CELL.ND3D:
    tes3cmd diff --ignore-type crea.aidt --ignore-type cell.nd3d testa0000.ess testb0000.ess > diff.out

    # Just print the records that differ
    tes3cmd diff --not-equal "my plugin1.esp" plugin2.esp


## dump - _Dump records as text for easy study_

    Usage: tes3cmd dump OPTIONS plugin...

    OPTIONS:
     --debug
    	 turn on debug messages

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --instance-match <regex>
    	 when printing cells, only print the matching object instances in the
    	 cell

     --instance-no-match <regex>
    	 when printing cells, only print the non-matching object instances in
    	 the cell

     --exact-id* <id-string>
    	 only dump records whose ids exactly match given <id-string>

     --exterior
    	 only match if record is an Exterior CELL

     --flag* <flag>
    	 only dump records with given flag. Flags may be given symbolically
    	 as: (deleted, persistent, ignored, blocked), or via their numeric
    	 values (i.e. persistent is 0x400).

     --id* <id-regex>
    	 only process records whose ids match regular expression pattern
    	 <id-regex>

     --interior
    	 only match if record is an Interior CELL

     --list
    	 only list the ids of the records to be dumped, instead of the entire record

     --match <regex>
    	 only process records that match given regular expression <regex>

     --no-banner
    	 do not print banner identifying the current plugin

     --no-match <regex>
    	 only process records that do not match given regular expression
    	 <regex>

     --wrap
    	 Wrap some long fields for more nicely formatted output.

     --raw <file>
    	 dump raw records to <file>, instead of as text

     --raw-with-header <file>
    	 dump raw records with an initial TES3 header record to <file>

     --separator <string>
    	 separate subrecords with given <string>. Normally subrecords are
    	 separated by line-breaks. You can use this option to change that so
    	 they are all printed on one line.

     --type* <record-type>
    	 only dump records with the given <record-type>

     Note: starred (*) options can be repeated, and matching of strings is not
     case-sensitive.

    DESCRIPTION:

    Dumps the plugin to stdout in text form for easy perusal or in raw form for
    extracting a subset of records to create a new plugin. For large plugins, the
    text output can be voluminous. In the text output, a starred subrecord
    indicates it is related to following subrecords.

    Note: documentation for regular expressions:
      http://www.perl.com/doc/manual/html/pod/perlre.html

    EXAMPLES:

    # List all the records in the plugin, just one per line, by type and ID:
    tes3cmd dump --list "Drug Realism.esp"

    # Dump all records from a plugin. we redirect the output to a file as there
    # can be a lot of output:
    tes3cmd dump "DwemerClock.esp" > "DwemerClock-dump.txt"

    # Dump all records with IDs exactly matching "2247227652827822061":
    tes3cmd dump --exact-id 2247227652827822061 LGNPC_AldVelothi_v1_20.esp

    # Dump all the DIAL and INFO records from a plugin:
    tes3cmd dump --type dial --type info "abotWhereAreAllBirdsGoing.esp"

    # Dump all records flagged as persistent (by name) OR blocked (by value)
    tes3cmd dump --flag persistent --flag 0x2000 "Suran_Underworld_2.5.esp"

    # Dump all object instances in cells that match "galbedir":
    # (this will just show you the cell header, and subrecords just for Galbedir
    # and her chest in the cell: "Balmora, Guild of Mages"):
    tes3cmd dump --type cell --instance-match galbedir Morrowind.esm


## esm - _Convert plugin (esp) to master (esm)_

    Usage: tes3cmd esm OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --overwrite
    	overwrite output if it exists

    DESCRIPTION:

    Copies input plugin (.esp) to a master (.esm). If the output file already
    exists, you must add the --overwrite option to overwrite it.

    EXAMPLES:

    # output is: "my plugin.esm"
    tes3cmd esm "my plugin.esp"


## esp - _Convert master (esm) to plugin (esp)_

    Usage: tes3cmd esp OPTIONS master...

    OPTIONS:
     --debug
    	turn on debug messages

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --overwrite
    	overwrite output if it exists

    DESCRIPTION:

    Copies input master (.esm) to a plugin (.esp). If the output file already
    exists, you must add the --overwrite option to overwrite it.

    EXAMPLES:

    # output is: "my plugin.esp"
    tes3cmd esp "my plugin.esm"


## fixit - _tes3cmd fixes everything it knows how to fix_

    Usage: tes3cmd fixit

    OPTIONS:
     --debug
    	turn on debug messages

     --backup-dir
    	where backup files get stored. The default is:
    	"Data Files/tes3cmd/backups"

     --hide-backups
    	any created backup files will get stashed in the backup directory
    	(--backup-dir)

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

    DESCRIPTION:

    The fixit command does the following operations:
    - Cleans all your plugins ("tes3cmd clean")
    - Synchronizes plugin headers to your masters ("tes3cmd header --synchronize")
    - Generates a patch for merged leveled lists and more ("tes3cmd multipatch")
    - Resets Dates on Bethesda data files ("tes3cmd resetdates")


## header - _Read/Write plugin Author/Description, sync to masters..._

    Usage: tes3cmd header OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --author <author>
    	set the Author field to <author>

     --backup-dir
    	where backup files get stored. The default is:
    	"Data Files/tes3cmd/backups"

     --description <desc>
    	set the Description field to <desc>

     --hide-backups
    	any created backup files will get stashed in the backup directory
    	(--backup-dir)

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --multiline
    	multi-line output for listing field contents

     --synchronize
    	same as: --update-masters --update-record-count

     --update-masters
    	updates master list to reflect new versions

     --update-record-count
    	update record count in header

    DESCRIPTION:

    When no options are given, the author and description are printed.

    Author and Description field values are normally replaced by the given string.
    But if the string begins with a "+", the existing value is appended with the
    new given value.

    If a given value contains the string "\n", it will be replaced by a CRLF.

    Note:
     - the Author value should fit in 32 bytes.
     - the Description value should fit in 256 bytes.

    If the value supplied will not fit into the plugin header field, you will be
    warned.

    The --update-masters (or --synchronize) option will clear any warnings
    Morrowind gives when it starts up that say: "One or more plugins could not
    find the correct versions of the master files they depend on..."

    EXAMPLES:

    # Show the Author/Description fields for a plugin:
    tes3cmd header "my plugin.esp"

    # Set the Author field to "john.moonsugar":
    tes3cmd header --author john.moonsugar "plugin.esp"

    # Append " and friends" to the Author field:
    tes3cmd header --author "+ and friends" "plugin.esp"

    # Append a Version number to a plugin Description field:
    tes3cmd header --description "+\nVersion: 1.0" "plugin.esp"

    # update header field for the number of records in the plugin (if incorrect)
    # and sync the list of masters to the masters installed in "Data Files"
    tes3cmd header --synchronize "my plugin.esp"


## modify - _Powerful batch record modification via user code extensions_

    Usage: tes3cmd modify OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --backup-dir
    	where backup files get stored. The default is:
    	"Data Files/tes3cmd/backups"

     --exact-id* <id-string>
    	only modify records whose ids exactly match given <id-string>

     --exterior
    	only match if record is an Exterior CELL

     --flag* <flag>
    	only modify records with given flag. Flags may be given symbolically
    	as: (deleted, persistent, ignored, blocked), or via their numeric
    	values (i.e. persistent is 0x400).

     --hide-backups
    	any created backup files will get stashed in the backup directory
    	(--backup-dir)

     --id* <id-regex>
    	only modify records whose ids match regular expression pattern
    	<id-regex>

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --interior
    	only match if record is an Interior CELL

     --match <regex>
    	only modify records that match given regular expression <regex>

     --no-match <regex>
    	only modify records that do not match given regular expression
    	<regex>

     --program-file <file>
    	load Perl code to run on each matched record from file named: <file>

     --replace "/a/b/"
    	replace regular expression pattern "a" with value "b" for every field
    	value in every matching record. you can use any character instead of
    	the slash as long as it does not occur in "a" or "b". This is a very
    	powerful alternative to the --run option, as it only requires
    	understanding of regular expressions, no perl coding is necessary.

     --run "<code>"
    	specify a string of Perl <code> to run on each matched record

     --sub-match <regex>
    	only modify the subrecords that match <regex>. When this option (or
    	--sub-no-match) are used, mofification only applies to matching
    	subrecords. Without either of these options modifications are
    	performed on whole records.

     --sub-no-match <regex> only modify the subrecords that do not match <regex>.
    	(see also --sub-match above).

     --type* <record-type>
    	only modify records with the given <record-type>

     Note: starred (*) options can be repeated, and matching of strings is not
     case-sensitive.

    This command allows you to do complex batch modifications of plugin records.
    You can really damage things with this command, so be careful!

    Note: documentation for regular expressions:
      http://www.perl.com/doc/manual/html/pod/perlre.html

    Example(s):

    # Just print the the cell "Ashmelech" from Morrowind.esm. (no modification).
    tes3cmd modify --type cell --id ashmelech --run "$R->dump" Morrowind.esm

    # Add the prefix "PC_" to the ID of all the statics in a plugin:
    tes3cmd modify --type stat --sub-match "id:" --replace "/^/PC_/" pc_data.esp

    # Problem: Aleanne's clothing mods do not have restocking inventory
    # Solution: create a small patch to change the counts for inventory containers
    #   to negative numbers so they will be restocking.
    # Step 0: confirm the problem, showing the non-negative counts:
    tes3cmd dump --type cont ale_clothing_v?.esp
    # Step 1: Create the patch file ale_patch.esp containing just the container records:
    tes3cmd dump --type cont --raw-with-header ale_patch.esp ale_clothing_v?.esp
    # Step 2: Change all the count fields for the containers in Aleanne's Clothing to -3 (for restocking wares)
    tes3cmd modify --type cont --run "$R->set({f=>'count'}, -3)" ale_patch.esp
    # Note: on Linux, the quoting would be a little different:
    tes3cmd modify --type cont --run '$R->set({f=>"count"}, -3)' ale_patch.esp

    # You can also specify a list of indices to restrict which subrecords are modified.
    # First, show the subrecord indices for container "_aleanne_chest" from: ale_clothing_v0.esp:
    tes3cmd modify --type cont --run "$R->dump" ale_clothing_v0.esp
    # Then only modify the last 3 items:
    tes3cmd modify --type cont --run "$R->set({i=>[-3..-1],f=>'count'}, 4)" ale_clothing_v0.esp


## multipatch - _Patches problems, merges leveled lists, etc._

    Usage: tes3cmd multipatch

    OPTIONS:
     --debug
    	turn on debug messages

     --cellnames
    	resolve conflicts with renamed external cells

     --fogbug
    	fix interior cells with the fog bug

     --merge-lists
    	merges leveled lists used in your active plugins

     --no-activate
    	do not automatically activate multipatch.esp

     --no-cache
    	do not create cache files (used for speedier operation)

     --summons-persist
    	fixes summoned creatures crash by making them persistent

    DESCRIPTION:

    The multipatch produces a patch file based on your current load order to solve
    various problems. You should regenerate your multipatch whenever you change
    your load order. The goal of the "multipatch" command is that it should always
    be safe to use it with no options to get the default patching behavior (if you
    do find any problems, please report them and they will be fixed ASAP). When no
    options are specified, the following options are assumed:

      --cellnames --fogbug --merge-lists --summons-persist

    The different patching operations are explained below:

    Cell Name Patch (--cellnames)

      Creates a patch to ensure renamed cells are not accidentally reverted to
      their original name.

      This solves the following plugin conflict that causes bugs:
      * Master A names external CELL (1, 1) as: "".
      * Plugin B renames CELL (1, 1) to: "My City".
      * Plugin C modifies CELL (1, 1), using the original name "", reverting
        renaming done by plugin B.
      * References in plugin B (such as in scripts) that refer to "My City" break.

      This option works by scanning your currently active plugin load order for
      cell name reversions like those in the above example, and ensures whenever
      possible that cell renaming is properly maintained.

    Fog Bug Patch (--fogbug)

      Some video cards are affected by how Morrowind handles a fog density setting
      of zero in interior cells with the result that the interior is pitch black,
      except for some light sources, and no amount of light, night-eye, or gamma
      setting will make the interior visible. This is known as the "fog bug".

      This option creates a patch that fixes all fogbugged cells in your active
      plugins by setting the fog density of those cells to a non-zero value.

    Summoned creatures persists (--summons-persist)

      There is a bug in Morrowind that can cause the game to crash if you leave a
      cell where an NPC has summoned a creature. The simple workaround is to flag
      summoned creatures as persistent. The Morrowind Patch Project implements
      this fix, however other mods coming later in the load order often revert it.
      This option to the multipatch ensures that known summoned creatures are
      flagged as persistent.

    EXAMPLES:

    # Create the patch plugin "multipatch.esp"
    tes3cmd multipatch


## overdial - _Identify overlapping dialog (a source of missing topic bugs)_

    Usage: tes3cmd overdial OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

     --single
    	only test to see if dialog in the first plugin is overlapped. (by
    	default all plugins are checked against all other plugins, which is an
    	n-squared operation, meaning "possibly very slow").

    DESCRIPTION:

    Prints the IDs of dialog records that overlap from the set of given plugins.

    An overlap is defined as a dialog (DIAL) Topic from one plugin that entirely
    contains a dialog Topic from another plugin as a substring. For example, the
    mod "White Wolf of Lokken" has a dialog topic "to rescue me" which overlaps
    with the dialog topic "rescue me" from "Suran Underworld", which causes the
    "Special Guest" quest from SU to get stuck because Ylarra will not offer the
    topic "rescue me" when you find her in her cell.

    Note that overlap is only a potential problem if the plugins are loaded in the
    order they are listed in the output.

    Example(s):

    # Show dialog overlaps between Lokken and SU:
    tes3cmd overdial "BT_Whitewolf_2_0.esm" "Suran_Underworld_2.5.esp"


## recover - _Recover usable records from plugin with 'bad form' errors_

    Usage: tes3cmd recover OPTIONS plugin...

    OPTIONS:
     --debug
    	turn on debug messages

     --backup-dir
    	where backup files get stored. The default is:
    	"Data Files/tes3cmd/backups"

     --hide-backups
    	any created backup files will get stashed in the backup directory
    	(--backup-dir)

     --ignore-plugin* <plugin-name>
            skips specified plugin if it appears on command line. plugin name is
            matched by exact, but caseless, string comparison.

    DESCRIPTION:

    Attempts to recover readable records from a damaged plugin. You should only
    use this when Morrowind gives the following type of error on your plugin:

      "Trying to load a bad form in TES3File::NextForm"

    The main reason you would get this error is if the file has been physically
    corrupted, where records have been overwritten with random binary junk, or
    if the file has been truncated, or otherwise damaged.

    This is not for fixing what is commonly referred to as "savegame corruption",
    which is not actually corruption but bad data.

    In any case, you will get detailed output on what tes3cmd finds damaged.

    EXAMPLE(S):

    # fix my damaged plugin:
    tes3cmd recover "my plugin.esp"


## resetdates - _Reset dates of Bethesda Data Files to original settings_

    Usage: tes3cmd resetdates

    OPTIONS:
     --debug
    	turn on debug messages

    DESCRIPTION:

    Resets the dates of the Bethesda masters (.esm) and archives (.bsa) to their
    original settings. This may help those people who have problems with textures
    and meshes being overridden by the vanilla resources (e.g. as can happen with
    the Steam version of Morrowind).

    Example(s):

    # fix the date settings of Bethesda data files:
    tes3cmd resetdates

