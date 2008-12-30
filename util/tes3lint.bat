@echo off
rem run esplint with default "normal" arguments

c:/strawberry/perl/bin/perl.exe esplint -r %1 > esplint.log
type esplint.log
echo "(Output saved in esplint.log)"
pause
