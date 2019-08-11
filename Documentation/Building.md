# Building mlox as an exe

Many Windows users do not have python installed, and do not want to install python just to use mlox.
Therefore, we use utilities to convert mlox into a portable executable (.exe) file that can be used on almost any windows system.

## Using PyInstaller:

Building an executable on Windows with PyInstaller is pretty easy, with one possible gotcha.
Before installation, please follow the "Running mlox from source" instructions to make sure you can run `mlox.py` directly.

The only thing that should need to be done is installing PyInstaller `pip install pyinstaller` and building the executable `pyinstaller mlox.spec`.
However, there seems to be some bugs, so the following things may have to be done instead:
* `cp mlox.py mlox_works.py`
* In "mlox.spec", change 'mlox.py' to 'mlox_works.py'
