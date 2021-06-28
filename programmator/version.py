import os, sys, re, subprocess, errno

def _get_version():
    try:
        import BUILD_CONSTANTS # type: ignore
    except:
        pass
    else:
        return BUILD_CONSTANTS.version
    p = subprocess.Popen('git describe --tags --dirty --always'.split(), stdout=subprocess.PIPE)
    version = p.communicate()[0].strip()
    assert p.returncode == 0
    return version.decode()

__version__ = _get_version()
del _get_version
