import sys
from pathlib import Path
from cx_Freeze import setup, Executable, build_exe

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"


# I want to include my sources as an easily editable .py files
# To that end I manually include them in setup(... 'build_exe': ) option below,
# and also hook after the build_exe command and delete '*.pyc' files here
class my_build_exe(build_exe):
    def run(self):
        super().run()
        for f in (Path(self.build_exe)/'lib'/'programmator').glob('*.pyc'):
            f.unlink()


# sys.argv.extend('build bdist --format=zip'.split())

setup(  name = 'puper_programmator2',
        version = '0.0.7',
        description = 'Programmator!',
        cmdclass = {
            'build_exe': my_build_exe,
        },
        options = {
            'build_exe': {
                # put everything except our package into library.zip
                'zip_include_packages': '*',
                'zip_exclude_packages': ['programmator'],
                'include_files': [('programmator', 'lib/programmator')], # add source files
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
