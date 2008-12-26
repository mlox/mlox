@echo off
rem run esplint with default arguments

c:/strawberry/perl/bin/perl.exe esplint %1 > esplint.log
type esplint.log
echo "(Output saved in esplint.log)"
pause
