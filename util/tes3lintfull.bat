@echo off
rem run tes3lint with all output turned on
rem assumes perl.exe is in your %PATH%
rem (by default strawberry Perl puts itself in your %PATH%)

perl.exe tes3lint -a %1 > tes3lint.log
type tes3lint.log
echo "(Output saved in tes3lint.log)"
pause
