import sys
from pathlib import Path
from cx_Freeze import setup, Executable, build_exe

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(  name = 'puper_programmator2',
        version = '0.0.9',
        description = 'Programmator!',
        options = {
            'build_exe': {
                # put everything into library.zip
                'zip_include_packages': '*',
                'zip_exclude_packages': [],
            },
            'bdist_msi': {
                # this is supposed to make the msi installer replace the previous installed version correctly
                # but it doesn't (there are two copies in "add/remove programs"). Such is life.
                'upgrade_code': '3CC8864C-B90B-4E1E-AD52-C05C4A61E8A8',
            },
        },
        executables = [
            Executable(
                'programmator/main.py',
                base=base,
                targetName='programmator',
                shortcutName='puper_programmator2',
                shortcutDir='DesktopFolder'),
            Executable(
                'programmator/hexterminal.py',
                base=base,
                targetName='hexterminal'),
            Executable(
                'programmator/intelhex.py',
                # use default base for console application
                targetName='intelhex'),
        ])
