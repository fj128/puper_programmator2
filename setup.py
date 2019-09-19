import sys
from typing import Dict, Any
from cx_Freeze import setup, Executable

# for future customization if necessary
build_exe_options: Dict[str, Any] = {}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name = 'puper_programmator2',
        version = '0.0.3',
        description = 'Programmator!',
        options = {'build_exe': build_exe_options},
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
        ])
