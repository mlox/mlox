@echo off
rem run esplint with all output turned on

c:/strawberry/perl/bin/perl.exe esplint -a %1 > esplint.log
type esplint.log
echo "(Output saved in esplint.log)"
pause
