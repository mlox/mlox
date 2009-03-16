@echo off
REM runs mlox in command line mode to ONLY CHECK your load order
c:\python25\python mlox.py -c > mlox_output.out
more mlox_output.out
