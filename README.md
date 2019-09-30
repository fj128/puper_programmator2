# What is this?

A work in progress.


## Prerequisites for running or building executables

Install Python3.7 or later from python.org, check "add to path", "add scripts to path" for convenience. Then:

    pip install -r requirements.txt


## Running in developer mode

You can run things like

    python -m programmator.main

from the top level source directory.

When running from VSCode, the important parts of launch.json are

                "program": "${file}",
                "cwd": "${workspaceFolder}",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}"
                }


## Building executables

    python setup.py build bdist_msi

Will build all the stuff and also a default installer.

All the stuff will be located in build/exe.win32-3.7 and can be test-launched from there.

    python setup.py build bdist --format=zip

Will build an installer-less zip-file.


## Why cx_Freeze? The state of deploying standalone Python programs on Windows in 2019

It sucks. py2exe is abandoned, Nuitka needs a C compiler, pyInstaller creates a directory with
lots of DLLs and other trash in it (and also has a very stupid alternative mode where it unpacks stuff
into a temporary directory) and also has had broken multi-entrypoint mode for two years.

cx_Freeze is much more alive because it's used by a lot of \*NIX people, and it does pretty much
exactly what I want out of the box.
