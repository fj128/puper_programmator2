import sys, re
from importlib import resources
from typing import List, NoReturn
from types import MappingProxyType
from dataclasses import dataclass, field
import programmator
import logging as log

def load_factory_settings():
    with resources.open_text(programmator, 'ZAVOD1.ASM') as f:
        parsed = parse_asm(f)
        return compute_mapping(parsed)

######

g_file : str
g_line_num: int
g_orig_line: str

def error(why, what=None) -> NoReturn:
    raise Exception(f'Failed to parse {g_file}, error at line {g_line_num}: {why}'
        + (f': {what!r}' if what is not None else ''), g_orig_line) from None


@dataclass
class Org():
    addr: int


@dataclass
class Db():
    values: List[int]
    line_num: int = field(init=False, default_factory=lambda: g_line_num)
    orig_line: str = field(init=False, default_factory=lambda: g_orig_line)


MATCH_TOKEN_APPROXIMATELY = re.compile(r'.\w*')
MATCH_COMMA_AND_WHITESPACE = re.compile(r'\s*,\s*')
MATCH_STRING = re.compile(r"'([^']|'')*'")


def parse_number(s: str, pos: int):
    end = MATCH_TOKEN_APPROXIMATELY.match(s, pos).end() # type: ignore # it always matches
    s = s[pos : end].lower()

    if not s:
        error('Invalid number', s)

    try:
        base = {
            'h': 16,
            'd': 10,
            'o': 8,
            'q': 8,
            'b': 2,
        }.get(s[-1])

        if base is None:
            base = 10
        else:
            s = s[:-1]

        return end, [int(s, base)]
    except ValueError:
        error('Invalid number', s)


def parse_string(s: str, pos: int):
    m = MATCH_STRING.match(s, pos)
    if not m:
        error(f'Invalid string {s[pos:]!r}')
    s = s[pos + 1 : m.end() - 1]
    s = s.replace("''", "'")
    values = [ord(c) for c in s]
    for v in values:
        if not 0 <= v < 128:
            error('Invalid character value in string: {v}', s)
    return m.end(), values


def parse_args(s: str):
    pos = 0
    args: List[int] = []
    # s should not start with whitespace
    while pos < len(s):
        if s[pos] == '\'':
            f = parse_string
        elif re.match(r'[0-9A-Fa-f]', s[pos]):
            f = parse_number
        else:
            end_match = MATCH_TOKEN_APPROXIMATELY.match(s, pos)
            end = end_match.end() if end_match else -1
            error(f'Unrecognized token {s[pos:end]!r}')
        pos, values = f(s, pos)
        args.extend(values)
        end_match = MATCH_COMMA_AND_WHITESPACE.match(s, pos)
        if end_match:
            pos = end_match.end()
    return args


def parse_asm(file):
    global g_file, g_line_num, g_orig_line
    g_file = file
    for g_line_num, g_orig_line in enumerate(file):
        g_line_num += 1
        g_orig_line = g_orig_line.strip()
        line = g_orig_line.split(';', 1)[0].strip()

        if not line:
            continue

        try:
            verb, args = line.split(maxsplit=1)
        except ValueError:
            error('No arguments for directive', line)

        verb = verb.upper()
        if verb not in ['ORG', 'DB']:
            error('Unknown directive', verb)
        args = parse_args(args)

        if verb == 'ORG':
            if len(args) != 1:
                error(f'ORG expects exactly 1 argument, got {args}')
            [arg] = args
            if not isinstance(arg, int):
                error(f'ORG expects a number argument, got {arg!r}')
            yield Org(arg)
        elif verb == 'DB':
            for arg in args:
                assert 0 <= arg < 256
            yield Db(args)
        else:
            assert False


def compute_mapping(directives):
    org = 0
    m = dict()
    orig_defs = dict()
    for d in directives:
        if isinstance(d, Org):
            org = d.addr
        elif isinstance(d, Db):
            for value in d.values:
                if org in m:
                    log.warning(f'Overriding value 0x{m[org]:02x} with 0x{value:02x} at address {org}')
                    log.warning(f'First defined at line {orig_defs[org].line_num:3d}: {orig_defs[org].orig_line!r}')
                    log.warning(f'Redefined at line     {d.line_num:3d}: {d.orig_line!r}')
                m[org] = value
                orig_defs[org] = d
                org += 1
    for i in range(1024):
        if i not in m:
            log.warning(f'Undefined value at address {i}')

    return MappingProxyType(m)
