from dataclasses import dataclass
import serial

import logging
log = logging.getLogger(__name__)


ERROR_CODES = {
    0x31 : 'неправильная длина посылки',
	0x32 : 'ошибка контрольной суммы',
    0x33 : 'нет 0x0D в конце посылки',
    0x34 : 'неизвестная команда',
}


@dataclass
class Message:
    command: int
    address: int
    data: bytes
    def __repr__(self):
        return f'Message({self.command}, {self.address:04X}, [{pretty_hexlify(self.data)}])'


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


class CommunicationError(Exception):
    ''

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
            log.error(str(exc))
            raise
        except ParseError as exc:
            log.error(str(exc))
            continue


def send_receive(port: serial.Serial, msg: Message) -> Message:
    retries = 10
    for i in range(retries): # retries because currently communication is hard.
        # just in case
        port.reset_input_buffer()
        port.reset_output_buffer()
        log.debug(f'cmd {msg.command} at {msg.address:04X}: {pretty_hexlify(msg.data)}')
        raw = compose(msg.command, msg.address, msg.data)
        log.debug(pretty_hexlify(raw))
        port.write(raw)
        try:
            response = None # initialize the variable
            response = receive(port)
            break
        except TimeoutError as exc:
            if not len(exc.buffer):
                log.warning(f'retrying {i + 1}/10')

    if response is None:
        return

    log.debug(f'got {response.command} {response.address:04X}: {pretty_hexlify(response.data)}')
    if response.command == 2:
        if msg.command == 0:
            if response.data == msg.data:
                return response
            raise CommunicationError('Неверные данные в контрольном считывании: хотели {}, получили {}'.format(
                pretty_hexlify(msg.data), pretty_hexlify(response.data)))
        elif msg.command == 1:
            if len(response.data) == len(msg.data):
                return response
            raise CommunicationError('Неверная длина ответа: хотели {} байт, получили {}'.format(
                len(msg.data), pretty_hexlify(response.data)))
        else:
            assert False

    if response.command == 3:
        if len(response.data) == 1:
            [code] = response.data
            if code in ERROR_CODES:
                raise CommunicationError(f'Устройство вернуло ошибку: {ERROR_CODES[code]}')
            else:
                raise CommunicationError(f'Устройство вернуло неизвестную ошибку: {code:02X}')
    raise CommunicationError(f'Устройство вернуло непонятное сообщение: {response}')

