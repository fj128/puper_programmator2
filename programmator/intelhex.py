'''Implements a very relaxed and chill version of intel hex format that allows
line comments (with ';') and spaces between bytes in hex thing'''

import sys, logging, argparse
from contextlib import contextmanager
from pprint import pprint

from programmator.comms import Message, send_receive
from programmator.hexterminal import ParseError, parse_hex_input
from programmator.port_monitor import PortMonitor


def parse_line(s: str):
    # TODO: replace asserts with throws ParseError
    s = s.strip()
    if not s or s.startswith(';'):
        return
    assert s[0] == ':'

    data = parse_hex_input(s[1:], 1)
    assert len(data) >= 5

    payload_length = data[0]
    assert payload_length == len(data) - 5

    addr = (data[1] << 8) + data[2]

    op = data[3]
    assert op in (0, 1)

    crc = sum(data) & 0xFF
    assert crc == 0

    if op == 0: # write
        return Message(0, addr, data[4 : -1])
    elif op == 1: # EOF
        assert payload_length == 0
        return
    else:
        assert False


def parse_text(s: str):
    res = []
    for line_nr, line in enumerate(s.split('\n')):
        try:
            msg = parse_line(line)
        except ParseError as exc:
            # rethrow adding line number, to construct the message properly
            raise ParseError(exc.msg, exc.column, exc.column_end, line_nr) from None
        if msg:
            res.append(msg)
    return res


@contextmanager
def _outfile_or_stdout(fname: str):
    f = open(fname, 'w', encoding='utf-8') if fname else sys.stdout
    try:
        yield f
    finally:
        if fname:
            f.close()


def read(args):
    template_filename = args.template
    output_filename = args.output
    with open(template_filename) as f:
        template = parse_text(f.read())
    # pprint(template)
    pm = PortMonitor()
    pm.scan_and_connect()

    with _outfile_or_stdout(output_filename) as outfile:
        for msg in template:
            resp = send_receive(pm.port, msg)
            if resp is None:
                break
            data = msg.compose()
            intelhex = ':' + ''.join(f'{b:02X}' for b in data[1:-1]) # except start and stop
            print(intelhex, file=outfile)


def write(args):
    print(f'write {args} (not implemented lol)')


def main():
    # logging goes to stderr by default
    logging.basicConfig(level=logging.DEBUG)
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    subparsers.required = True
    subparsers.dest = 'command' # required for error message

    parser_read = subparsers.add_parser('read', help='read the data at addresses used in template file, write to output file')
    parser_read.add_argument('template', type=str, help='template file name')
    parser_read.add_argument('output', nargs='?', type=str, help='output file name (stdout if omitted)')
    parser_read.set_defaults(func=read)

    parser_write = subparsers.add_parser('write', help='write the file to the device')
    parser_write.add_argument('input', type=str, help='input file name')
    parser_write.set_defaults(func=write)

    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
