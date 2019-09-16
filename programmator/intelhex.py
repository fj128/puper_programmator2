from comms import Message

class ParseError(Exception):
    def __init__(message, line, column, column_end):
        ''


def loquacious_hexlify(s: str):
    'Would throw an exception with the exact location of failure'
    res = bytearray()
    for i in range(0, len(s), 2):
        ss = s[i : i + 2]
        assert len(ss) == 2
        res.append(int(ss, 16))
    return res


def parse_line(s: str):
    s = s.strip()
    if not s or s.startswith(';'):
        return
    assert s[0] == ':'

    data = loquacious_hexlify(s[1:])
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
    for line in s.split('\n'):
        msg = parse_line(line)
        if msg:
            res.append(msg)
    return res

