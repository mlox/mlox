@echo off
REM RUN THIS FILE IN THE DATA FILES DIRECTORY
REM This will show your current load order and save it to: load_order.out
REM (Based on a posting by promethean on the Bethsoft forums)
dir *.esm /o:d /b > load_order.out
dir *.esp /o:d /b >> load_order.out
more load_order.out
echo ""
echo "Saved current load order in: load_order.out"
