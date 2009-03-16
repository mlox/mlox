@echo off
REM runs mlox in command line mode to check AND UPDATE your load order
c:\python25\python mlox.py -u > mlox_output.out
more mlox_output.out
