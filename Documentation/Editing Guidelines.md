# Guidelines for Editors of the mlox rule-base

## Introduction

Editors should do their best to keep the rule-base clean and well-documented.

Mlox is managed using version control software called `git`.  If you are unfamiliar with git, please see [here](https://www.atlassian.com/git/tutorials/what-is-git/) for help.

## Citing sources using (Ref:)

Whenever possible, rules should have a "(Ref: xxx)" comment, were xxx is the source of the information the rule is based on. This is necessary so that people will know how to research a rule if they find that it is incorrect, or if they need more information. The citation can be the name of the Readme for the mod, a URL to a web page or forum posting, or anything else that is useful like that. Example:

(Ref: "Luthors Compass 1.0.zip/ReadMe.txt")

In this case, I put the name of the original mod distribution archive in front of the name of the readme file, since the name is very generic, but in most cases, I would leave off the name of the archive, as it should be understood.


### URL whitespace requirements

Please make sure URLs are surrounded with whitespace:

Good:

(Ref: http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists )

Bad:

(Ref: http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists)

Sometimes rules are quoted on web pages (like forum posts) that automatically link URLs, but don't understand that the parenthesis is not part of the link, so they make a bad link. To prevent this, it helps to have the URLs surrounded with whitespace.

## Rules Sections

Most rules are grouped into "sections", which begin with "@" followed by the section name, and each section corresponds more or less to one "Mod".

This is a convention to help keep order in the file, it also makes the job of finding already existing mod rules a lot easier.

The convention for assembling the titles of rules sections is:

~~~
;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
;; @<Mod Name> <Version> [<Author>]
~~~

**Mod Name** - Note the leading @ character, a huge boon when searching the rule-set for a mod, particularly if the full name of that mod isn't known or the mod is referred to in a number of areas of user-displayed text (Note rules and the like).

Sometimes (particularly with mods uploaded to Morrowind Modding History) a mod could be listed under a number of different names. The mod's download page may have one name, the mod's readme another and the mod plugin itself may well be named something else entirely.

If there are differences then the **Mod Name** should be that listed in the mod's readme.

For certain, very popular mods the mod's common abbreviation can be used. Luckily Morrowind never descended to the abbreviation hell which is Oblivion or Skyrim modding where every mod needed to have an abbreviation, prefereably an acronym and double bonus points for a recursive acronym.

In mlox very popular mods have their common abbreviation first in **Mod Name**. Such as LGNPC (Less Generic NPC project), MCA (Morrowind Comes Alive), MWSE (Morrowind Script Extender) and TR (Tamriel Rebuilt).

**Version** - Not necessary for most mods, which only ever reach an initial release version. For mods which go through multiple iterations it is very useful to capture the version number to which the current mlox rules apply. It makes updating the rule set much easier when one can instantly see if a mod's rule section needs updating.

**Author** - Note the square brackets, these are useful for searching the entire rule-set for a particular author's work. Perhps there's a mod which you are unsure of the name of but you know the author. Or perhaps just the frst few characters of their name. Adding an opening square bracket to the search string really helps here.

## Highlighting

When a comment message on a rule begins with exclamation points, that comment will be highlighted in the GUI Messages pane.


`! - blue, for low priority.`

Use low priority for stuff that should be "noticed", but probably have low to nil impact on playing. These would often be things that the user might want to know, depending on their preferences.

`!! - yellow, for medium priority.`

Use medium priority for stuff that could possibly impact the game but is probably not too serious. These things probably should be attended to.

`!!! - red, for most urgent priority.`

Use urgent priority for stuff that could break the mod or game. These things should be fixed.

the `[Requires]` rule will automatically highlight in red.

the `[Patch]` rule will automatically highlight in yellow.

## An editing workflow

I've been writing mlox rules for, *ulp*, about nine years now. Would've thought I'd have finished by now...

In that time I've created a rules editing workflow which works well. I'll outline it here and whilst I don't recommend anyone follows it slavishly they can at least see how I work and why I work in this way.

###Tools used

I work on Windows. Those who don't should look for equivalent tools on BeOS or what have you.

All of these are freeware. As in beer.

The Python version of mlox. I've compiled this to optimised bytecode (making a mlox.pyo file) using this command:
`C:\Python27\python.exe -OO C:\Python27\Lib\py_compile.py mlox.py`
Adjust as needed for your Python path.

[Metapad](http://liquidninja.com/metapad/) - A text editor which is infinitely quicker than Windows' own Notepad. You *really* don't want to be running the search and replace I talk about later using Notepad.
I've used Metapad for years and only relatively recently installed Notepad++. I found it screwed up with the formatting of the rules in mlox, I'm sure I could fix it by messing with some tab settings, but...

[WinMerge](http://winmerge.org/) - A diff tool. Doesn't seem to be actively developed anymore but I struggle to think of the last time I had a problem with it or thought of something it didn't do which I wanted.

[TES Plugin Conflict Detector](http://www.uesp.net/wiki/Tes3Mod:TES_Plugin_Conflict_Detector) - Or TESPCD. I've linked to the UESP page which has a bit of background. It's not the most user-friendly way of presenting conflicting records in plugins but it's the only one out there for Morrowind and invaluable in working out some Order and Conflict rules.

[Enchanted Editor](http://www.uesp.net/wiki/Tes3Mod:Enchanted_Editor) - UESP again. Do yourself a favour and also grab the .CHM help file. Whilst there are other third party editors out there (TESAME, MWEdit) I use EE for my mlox needs. It's a bit slow in parsing records but it's got a nice UI and, critically, I can unzip plugin files to a temporary directory and open them from there with EE, no messing around with its required Masters or my test Data Files folder.

**Optional**
These are two more of john.moonsugar's tools which I use for checking a mod for possible SignRotate Contamination and evil GMSTs, deprecated levelled list functions and undeclared expansion dependencies.
[tes3cmd](https://sourceforge.net/projects/mlox/files/tes3cmd/) - There's a new preview release, 0.40, up on [Github](https://github.com/john-moonsugar/tes3cmd). I haven't tried it at the time of writing, it's "an unstable, lightly tested release" but that may have changed by the time you read this.
[tes3lint](https://sourceforge.net/projects/mlox/files/tes3lint/) - This requires Perl. I've installed [Strawberry Perl](http://strawberryperl.com/) on my machine.

###Writing the new rules
I'm not going into the details here but this primarily involves reading a mod's readme and turning those requirements, conflicts and ordering rules written by the mod author into mlox rules.

*mlox_rules_guide.txt* in your mlox install directory is your bible here.

Enchanted Editor and TESPCD are pretty essential to this work.

I write rules in a separate text file. When I feel I've got enough to warrant going through the process of testing and updating those new rules for inclusion into the mlox rule-set I... test those new rules.

####Some notes on rule idiosyncrasies
Sure there's a better place for these notes...

#####ORDER rules
***Don't write monolithic ORDER rules!***
Let's say we're writing some Order rules for Varg 'Euthanasiologist' Axeno's [Weapon Fix 1.77](http://mw.modhistory.com/download-87-2709):
>Weapon Fix is a plugin designed to increase realism and interest of gameplay in Morrowind by replacing unrealistic and non-balanced original weaponry stats with realistic ones based on specifications of real-world prototypes of weapons used in Morrowind.

This mod, according to its readme:
>Major mods processed:
  Assassin Armory
  Adul's Arsenal (www.adul.net)
  Dwemer Ice Weapons and Armor
  Leia's Double Wield Mod
  Marksman Mod
  Morrowind Additions Revamped
  Recoloured Ebony and Dwarven
  The Arsenal 0.9 (www.olek.ilovehost.com/Daduke/)
  The Sword of Perithia
  The Swords of Morrowind (maxedwin@hotmail.com)
  Weapon Compilation Mod V1.0
  Underwater Ruins

And in the readme's Known Issues section:
>--> Some weapons have old stats (or like them) while others of same type don't
This probably means WeaponFix is loaded before some other plugin that changes
weapon stats.

So... all we have to do is a single, monolithic Order rule like this, right?
~~~
[Order]
Aduls_Arsenal.esp
FW_Sabre.esp
Leias_Dual_Wield_03.esp
newarrows.esp
newarrowsLITE.esp
Additions_Revamped__clean_.esp
Re-coloured Ebony and Dwarven.esp
The Arsenal.esp
SOPBeta1.4.esp
SOP1.4Patch1.34.esp
The_Swords_of_Morrowind.esp
weaponFix177.esp
~~~

Well, yes, we could do that but the trouble is we're also setting in stone the load order for all those other mods. Does Adul's Arsenal *really* need to load before Morrowind Additions Revamped? What If Additions makes insignificant landscape changes to a Cell where Adul's mod places its shop?

There's also the added wrinkle of the way mlox processes Order rules (see *mlox_guts.txt* and marvel at the complexities of topological sorts).

It's a pain but the above is in mlox as:
~~~
[Order]
Aduls_Arsenal.esp
weaponFix177.esp

[Order]
FW_Sabre.esp
weaponFix177.esp

[Order]
Leias_Dual_Wield_03.esp
weaponFix177.esp

[Order]
newarrows.esp
weaponFix177.esp
etc.
~~~

***ORDER rules don't accept the ANY predicate***
So, in the above you couldn't write:
~~~
[Order]
[ANY Leias_Dual_Wield_03.esp
    newarrows.esp]
weaponFix177.esp
~~~

It doesn't work, you have to do them separately.

#####PATCH rules
***PATCH rules don't accept the NOT predicate***
This one's rather annoying.

Sensei's [The Lighting Mod](http://mw.modhistory.com/download-26-2251) has a patch plugin for the official Siege at Firemoth plugin. If you're running the Complete version of The Lighting Mod then you don't need to run it, the patch's changes to cell ambient light are already included.

So... something like this would be nice:
~~~
[PATCH]
 "[TLM - AdjMod - Siege At Firemoth.esp] contain the relevant light settings for [...] Siege At Firemoth by the Official Morrowind Team"
 (Ref: "TLM - ~Readme.htm")
TLM - AdjMod - Siege At Firemoth.esp
[ALL TLM - Ambient Light + Fog Update.esp
     [ANY Siege at Firemoth.esp
          SiegeAtFiremoth.esp
          [Official]Siege at Firemoth.esp
          OfficialMods_v5.esp
          Clean Official Plugins v1.1.esp
          Official_2002_Mods.esp
          super_adventurers302.esp
          silgrad_tower_internal_release_1-4_6.6.esp
          silgrad_tower_1-4_6.6.esp]
     [NOT TLM - Complete.esp]]
~~~
So it should display the Patch message only when needed. Trouble is it doesn't work. As the PATCH rule doesn't accept the NOT.

What we have to do is a REQUIRE rule (loading this patch plugin *needs* these records) for when people don't have the patch plugin but have the plugins it patches.

*And* we have to do a CONFLICT rule for when people have the patch plugin loaded but not all the plugins it patches.

###Testing the new rules

The idea is to check the newly written rules againt a decent set of real world mod lists and see if the rules we've written actually return the messages we want. This isn't perfect, we can't check rules relying on the SIZE or DESC predicates. We're simply seeing if the various messages are displaying as they should do, and there aren't any typos or anything like that.

**Make sure there are no entries in your mlox_user.txt before continuing**
That will mess things up, and why I do my rule writing in a separate text file.

####Preparing the ground
We need a baseline to check our rules against. For this we use the userfiles uploaded into the mlox repository (these are people's load orders in test/userfiles/).

I save those text files containing people's mod lists into a subfolder of my mlox directory:
`Games\Bethesda Softworks\Morrowind\mlox\test\userfiles`

I then run this as a batch file (called *test_rules.bat*) from my mlox directory:
~~~
IF EXIST "Original.txt" GOTO SecondRun

FOR %%f in ("C:\Games\Bethesda Softworks\Morrowind\mlox\test\userfiles\*.txt") DO mlox.pyo -wf -n "%%f" >>Original.txt

EXIT

:SecondRun
FOR %%f in ("C:\Games\Bethesda Softworks\Morrowind\mlox\test\userfiles\*.txt") DO mlox.pyo -wf -n "%%f" >>TestOutput.txt
~~~
That creates a text file called "Original.txt" and is the consolidated output of running mlox against all the various users' mod lists.

####Syntax check
I then copy and paste the candidate rules I've been writing from my working text file into mlox_user.txt

I want to make sure I haven't made any silly errors (e.g. not using the right number of closing square brackets, not starting a line of text which'll be displayed to the user with a space etc. etc.)

Rather than checking against all those user mod lists we just check against one. mlox will parse the contents of mlox_user.txt and throw errors.

I use this as a batch file (called *parse_plugins.bat*):
~~~
mlox.pyo -wf -n "C:\Games\Bethesda Softworks\Morrowind\mlox\test\userfiles\5h4rp.txt" >parse_plugins.txt

START parse_plugins.txt
~~~
I then do a Find in Notepad (or whichever program you've associated with TXT files) for the strings "parse" and "cycle". The former is an indicator of a syntax failure, the latter is a mistake in the Order rules (have a read of *mlox_guts.txt*) and the Order rule creating the cycle has been thrown out. Time to re-write it. In all cases I've had that's been avoided by not creating monolithic Order rules. See **Don't write monolithic ORDER rules!**, up there.

Once all those typos are fixed it's time to move onto the main check.

####Check against userfiles
Run *test_rules.bat* again.

This time a new text file, TestOutput.txt, is created. We need to compare that against our original Original.txt.

Before we fire up WinMerge we need to minimise the differences between the two txt files. In our first run of the *test_rules.bat* batch file we had no rules in mlox_user.txt, in our second run we did.

Open up TestOutput.txt in Metapad and look for the line like this:
`Read rules from: "mlox_user.txt"                   ( 75 rules)`

Search and replace that value (the number of rules will be different each time) with:
`Read rules from: "mlox_user.txt"                   (  0 rules)`

If you're doing that in Notepad.exe then go and watch a film whilst its working. A long film. Like the extended version of Return of the King.

Save the changed TestOutput.txt and load it and the Original.txt into WinMerge. Step through the differences and make sure that the user displayed messages are what you want them to be. Make changes as needed in mlox_user.txt.

Optionally, delete TestOutput.txt and re-run *test_rules.bat*  depending on the significance of the re-writes needed to the rules.

####Add the rules to mlox_base.txt
Not much to say here, cut and paste each rule section into mlox_base.txt, making sure you're getting each rule section in the right place alphabetically. See *Rules Sections*, above.

###Bonus round: Using tes3cmd and tes3lint
This is how I check a mod for for possible [SignRotate Contamination](http://wryemusings.com/GMST%20Vaccine.html), [evil GMSTs](http://www.mwmythicmods.com/argent/tech/gmst.html), [deprecated levelled list functions](http://www.uesp.net/wiki/Tes3Mod:Leveled_Lists) and undeclared expansion dependencies. The last one is where a plugin uses Tribunal or Bloodmoon script functions but doesn't have one of those Bethesda masters in its plugin header.

I've this batch file, *mlox_check.bat*, in the root of Data Files (along with tes3cmd and tes3lint installed):
~~~
@echo off
SET MOD="%~nx1"
SET MODPATH="%~f1"
SET CLEANPATH="%~dp1tes3cmd_%~nx1"
SET BACKUPPATH="%~dp1Clean_tes3cmd_%~nx1"
SET LOG="%~dp1mlox_check.txt"

COPY %MODPATH% %CLEANPATH%

tes3cmd clean %CLEANPATH% > %LOG%

@ECHO: >> %LOG%
@ECHO: >> %LOG%
ECHO: Checking tes3cmd_%~nx1 for possible SignRotate Contamination: >> %LOG%
perl.exe "C:\Games\Bethesda Softworks\Morrowind.testing\tes3lint\tes3lint" -f DUP-REC %CLEANPATH% > "%~dp1tes3lint.log"

DEL %CLEANPATH%

FINDSTR /C:"SCPT    DagothUrCreature1" "%~dp1tes3lint.log" >> %LOG% 2>&1
FINDSTR /C:"SCPT    EndGame" "%~dp1tes3lint.log" >> %LOG% 2>&1
FINDSTR /C:"SCPT    LorkhanHeart" "%~dp1tes3lint.log" >> %LOG% 2>&1
FINDSTR /C:"SCPT    Float" "%~dp1tes3lint.log" >> %LOG% 2>&1
FINDSTR /C:"SCPT    SignRotate" "%~dp1tes3lint.log" >> %LOG% 2>&1
@ECHO: >> %LOG%
@ECHO: >> %LOG%

DEL %BACKUPPATH%
DEL "%~dp1tes3lint.log"

ECHO: Checking %MOD% for evil GMSTs, levelled list functions and expansion dependencies: >> %LOG%
perl.exe "C:\Games\Bethesda Softworks\Morrowind.testing\tes3lint\tes3lint" -f BM-DEP,EXP-DEP,EVLGMST,DEP-LST %1 >> %LOG% 2>&1
@ECHO: >> %LOG%

ECHO.
DIR %1 /-C >> %LOG%

CLS

TYPE %LOG%
ECHO.
ECHO "(Output saved in %LOG%)"

PAUSE
~~~
I create a shortcut to that batch file on my desktop and then just drag and drop the plugin from the temporary directory its installed in (as I use Enchanted Editor FTW) onto that shortcut. Have a look at the MS-DOS window that's spawned and if needs be add an appropriate rule such as:
~~~
[Note]
 !! This plugin suffers from "SignRotate Contamination". It includes three "dirty" scripts (DagothUrCreature1, EndGame and LorkhanHeart). The ESP needs cleaning to remove these "dirty" scripts.
 !! Ref: http://wryemusings.com/GMST%20Vaccine.html
[SIZE 2048163 BS_1.0.1.esp]

[Note]
 !! This plugin contains evil GMSTs.
 !! (What the hell is a GMST? http://www.mwmythicmods.com/argent/tech/gmst.html )
[SIZE 54813 BalconyhouseV2.esp.esp]

;;expdep
[Requires]
 This plugin uses the Tribunal function setdelete and the Bloodmoon function placeatme
Deadly Dagoths.esp
Bloodmoon.esm
~~~
Those using the deprecated levelled list functions (AddToLev\* /RemoveFromLev\*) get added to this rules section:
*@Plugins using Deprecated Leveled List Functions on Bethsoft lists*
