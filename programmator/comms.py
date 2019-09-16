from dataclasses import dataclass
import serial


@dataclass
class Message:
    command: int
    address: int
    data: bytes


def pretty_hexlify(data):
    return ' '.join(f'{b:02X}' for b in data)


def compose(cmd, address, data):
    '''Compose a command in our pseudo IntelHEX format

    >>> s = compose(3, 0x1234, [0x30, 0x40, 0x50, 0xFF])
    >>> sum(s[:-1]) & 0xFF
    0
    >>> pretty_hexlify(s)
    '3A 04 12 34 33 30 40 50 FF 8A 0D'

    '''
    res = bytearray()
    res.append(ord(':'))
    res.append(len(data))
    res.append(address >> 8)
    res.append(address & 0xFF)
    res.append(cmd | 0x30) # currently required
    res.extend(data)
    res.append(-sum(res) & 0xFF)
    res.append(0x0D)
    return res


@dataclass
class ParseError(Exception):
    reason: str
    buffer: bytearray

    def __str__(self):
        return f'Parse failed: {self.reason}, after reading {pretty_hexlify(self.buffer)}'


class TimeoutError(ParseError):
    def __init__(self, buffer, waiting_for):
        super().__init__(f'timeout while waiting for {waiting_for}', buffer)


def receive_one(port):
    buffer = bytearray()
    waiting_for = 'start byte (":")'
    def read():
        r = port.read(1)
        if not r:
            raise TimeoutError(buffer, waiting_for)
        buffer.append(r[0])
        return r[0]

    while read() != ord(':'):
        pass # skip garbage quietly, only complain at the end if we really failed.

    waiting_for = 'length'
    length = read() & 0x1F # panel sends pseudo-ascii regardless of input
    if length > 16:
        raise ParseError(f'length too big: {length}', buffer)

    waiting_for = 'address'
    address = ((read() << 8) + read()) & 0x07FF

    waiting_for = 'command'
    command = read() & 0x0F

    waiting_for = 'data'
    data = [read() for _ in range(length)]

    waiting_for = 'crc'
    crc = read()

    computed_crc = sum(buffer) & 0xFF
    if computed_crc and False: # currently broken
        raise ParseError(f'nonzero computed crc: {computed_crc:02X}', buffer)

    waiting_for = 'end byte (0x0D)'
    if read() != 0x0D:
        raise ParseError(f'missing end byte', buffer)

    return Message(command, address, data)


def receive(port):
    '''Repeatedly receive until we get timeout.

    Don't attempt to reparse buffer from the next position because this will result in an unholy spam of errors'''

    while True:
        try:
            return receive_one(port)
        except TimeoutError as exc:
            print(exc)
            return
        except ParseError as exc:
            print(exc)
            continue


def send_receive(port: serial.Serial, msg: Message) -> Message:
    # just in case
    port.reset_input_buffer()
    port.reset_output_buffer()
    port.write(compose(msg.command, msg.address, msg.data))
    return receive(port)


if __name__ == '__main__':
    main()
