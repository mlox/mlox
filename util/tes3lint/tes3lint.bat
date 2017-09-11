@echo off
rem run tes3lint with default "recommended" arguments
rem assumes perl.exe is in your %PATH%
rem (by default strawberry Perl puts itself in your %PATH%)

perl.exe tes3lint -r %1 > tes3lint.log
type tes3lint.log
echo "(Output saved in tes3lint.log)"
pause
