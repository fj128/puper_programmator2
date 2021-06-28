import sys, re
from cx_Freeze import setup, Executable
from programmator.version import __version__

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"


setup(  name = 'puper_programmator2',
        version = re.sub('[^0-9.]', '', __version__),
        description = 'Programmator!',
        options = {
            'build_exe': {
                # put everything into library.zip
                'zip_include_packages': '*',
                'zip_exclude_packages': [],
                'constants': [f'version="{__version__}"'],
            },
            'bdist_msi': {
                'upgrade_code': '{3CC8864C-B90B-4E1E-AD52-C05C4A61E8A8}',
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
