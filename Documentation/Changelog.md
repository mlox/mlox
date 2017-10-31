# ChangeLog

Version 0.63 -
* Support unicode file names [EmperorArthur]
* Switch to python3 [EmperorArthur]
* Move from a wxWidgets GUI to a PyQt5 based GUI


Version 0.62 -
* Completely refactored mlox code! [EmperorArthur]
* Rewrote / Re-aranged most documentation. [EmperorArthur]
* mlox (including updater) now works on linux, and does not crash if unable to update!! [EmperorArthur]
* Now find game directories by looking for configuration files, not .exe (Allow for easily using mlox with OpenMW) [EmperorArthur]
* mlox now understands OpenMW config files format, though it does not (yet) actively find them. [EmperorArthur]
* mlox now writes new load orders to the users Morrowind.ini file.
   Note: It still uses the Data Files as the primary source for load order information.  If the .ini file has a wrong load order, but the plugin timestamps are correct it will NOT modify the .ini
   WARNING:  Mlox will automatically scrub any plugins not in the Data Files directory when updating Morrowind.ini  This is a feature to prevent the game from trying to load plugins that no onger exist.

Version 0.61 - 2015/08/01
* URI for checking and downloading new rule-base changed from Google Code to SourceForge [Dragon32]

Version 0.60 - 2014/09/07
* mlox will now skip reporting an error if it fails to make a connection when downloading the rule-base [abot]
* fixed potential compatibility issues caused by Python changing their function names between versions [abot]

Version 0.59 - 2014/07/06
* Fix conflict with tes3cmd's resetdates and only redate files if necessary [abot]
* Automatic checking for and downloading of new rule-base [abot]

Version 0.58 - 2011/02/16 [Not released]
* Fix for parsing [SIZE] predicate with plugin names that contain brackets
* Added Melchor's workaround for problem displaying different encodings in wx.

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
* Small GUI presentation tweak to ensure the labels at the bottom of the load order panes don't collide when the sash is adjusted all the way down.

Version 0.50 - 2009/01/06
* Beta release. Documentation has been edited to be current. No new application functionality from version 0.41.
