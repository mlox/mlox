# Building mlox as an exe

Many Windows users do not have python installed, and do not want to install python and wxpython just to use mlox.  Therefore, we use utilities to convert mlox into a portable executable (.exe) file that can be used on almost any windows system.

## Using Nuitka:

Thanks to [this](https://sourcecontribute.com/2015/05/02/compiling-python-to-standalone-executables-on-linux-using-nuitka/) guide for helping with the basics.  These instructions are for how to cross compile mlox for windows from Linux.  Linux users must have windows installed before following these directions.

First, install all of the dependencies to run and build mlox:

    wine msiexec /i python-2.7.13.msi /L*v log.txt
    wine wxPython3.0-win32-3.0.2.0-py27.exe
    wine mingw-w64-install.exe

Next, we're going to         run these two commands from within wine's command prompt `wine cmd`:

    pip install -U nuitka
    pip install --egg scons

This has to be run outside of wine, to fix a problem with nuitka not properly detecting scons.

    /drive_c/Python27/Lib/site-packages/nuitka/build/inline_copy$ ln -s ../../../../../Scripts/ bin

Back in wine (`wine cmd`) we run these two commands to actually build mlox:

    set PATH=C:\Program Files\mingw-w64\i686-6.4.0-posix-dwarf-rt_v5-rev0\mingw32\bin;%PATH%
    nuitka -j 3 --show-modules --recurse-all --standalone --show-scons mlox.py

This creates a directory called 'mlox.dist' which contains the EXE, and many DLL files that are also needed.

Copy the 'Resources' folder, '7za.exe' executable, and 'Readme.md' file into the 'mlox.dist', and it's ready to be packaged.

## DLL Bundling:

I've attempted multiple methods of bundling the DLL files with the executable after compilation, but none seem to work.

Methods tried:
* [gta_asi_injector](https://osdn.net/projects/pefrm-units/)
* [pefrmdllembed](https://pefrmdllembed.codeplex.com/) (`pefrmdllembed.exe -injimp test.exe python27.dll _socket.pyd out.exe`)
* ILMerge (`ILMerge.exe /target:winexe /out:test_bundled.exe test.exe *.dll`)

# Possible problems
Nuitka seems to have a problem detecting everything needed by 'update.py'.
If the compiled EXE does not run, or the updater fails, try adding these two lines to 'update.py'

    import _socket
    import _ssl
