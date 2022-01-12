import os, ast
from typing import Union
from pathlib import Path
from dataclasses import dataclass


def get_appdata_dir(subdir: Union[Path, str, None]=None) -> Path:
    path = Path(os.environ['APPDATA']) / 'puper_programmator2'
    if subdir:
        path /= subdir
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    return path


x = object()
def f(a=x):
    ''

help(f)


@dataclass
class Settings:
    button_reset_enabled = False

    def __init__(self):
        self.load()

    @property
    def path(self):
        return get_appdata_dir() / 'settings.py'

    def load(self):
        path = self.path
        if not path.exists():
            self.save()
        else:
            ast.literal_eval(path.read_text())


    def save(self):
        with self.path().open('w') as f:
            f.write(repr(self.as_dict()))


settings = Settings()


