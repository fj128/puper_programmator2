from typing import Union, List, Dict, Tuple, Sequence
import functools
import tkinter as tk
import re

from programmator.utils import tk_set_list_maxwidth, pretty_hexlify
from programmator.comms import send_receive, Message

import logging
log = logging.getLogger(__name__)

# static descriptions

controls: 'List[MMC_Base]' = []

# used for sanity checking the model
bit_memory_registry: 'Dict[int, Dict[int, MMC_Base]]' = {}
byte_memory_registry: 'Dict[int, MMC_Base]' = {}

memory_spans: List[Tuple[int, int]] = []

# actual dynamic memory

memory_map: Dict[int, int] = {}


# API

def finish_initialization():
    # sanity check
    for address, bits in bit_memory_registry.items():
        if len(bits) != 8:
            print(bits)
            assert False, f'Incomplete byte at {address}'

    # compute spans
    addresses = sorted(bit_memory_registry.keys() | byte_memory_registry.keys())
    spans = []

    start = None
    prev = None
    page_mask = 0xFF80
    bytes_per_span = 4 # 16 bugs out more often than not.

    for addr in addresses:
        if start is None:
            start = prev = addr
        elif (     addr != prev + 1
                or addr - start >= bytes_per_span
                or (addr & page_mask) != (start & page_mask)):
            spans.append((start, prev + 1))
            start = prev = addr
        else:
            prev = addr
    spans.append((start, prev + 1))
    memory_spans[:] = spans


def read_into_memory_map(port, callback):
    memory_map.clear()
    for start, end in memory_spans:
        msg = Message(1, start, [0] * (end - start))
        msg = send_receive(port, msg, callback)
        if msg is None:
            memory_map.clear()
            return
        for i, b in enumerate(msg.data):
            memory_map[start + i] = b
    return True


def populate_controls_from_memory_map():
    for control in controls:
        control.from_memory_map()


def populate_memory_map_from_controls():
    memory_map.clear()
    for control in controls:
        control.to_memory_map()
    return True



def write_from_memory_map(port, callback):
    for start, end in memory_spans:
        msg = Message(0, start, [memory_map[i] for i in range(start, end)])
        msg = send_receive(port, msg, callback)
        if msg is None:
            memory_map.clear()
            return
    return True




# helpers

def register_bit(control, address: int, bit: int):
    assert control is not None
    assert 0 <= bit < 8
    other = byte_memory_registry.get(address)
    assert not other, f'{control!r} wants to use address {address}[{bit}] already used by {other!r}'
    bits = bit_memory_registry.setdefault(address, {})
    other = bits.get(bit)
    assert not other, f'{control!r} wants to use address {address}[{bit}] already used by {other!r}'
    bits[bit] = control


def register_byte(control, address: int):
    assert control is not None
    other = byte_memory_registry.get(address)
    assert not other, f'{control!r} wants to use address {address} already used by {other!r}'
    bits = bit_memory_registry.get(address, None)
    if bits:
        other = next(iter(bits.values()))
        assert False, f'{control!r} wants to use address {address} already used by {other!r}'
    byte_memory_registry[address] = control


# Base classes that deal with reading and writing memory, but not tk.

class MMC_Base:
    def __init__(self, description:str, base_address: str):
        self.base_address = base_address # for error reporting purposes
        self.description = description
        controls.append(self)


    # *_memory_map_raw functions don't know anything about the target control and get/return values directly.
    # *_memory_map functions are supposed to call the above and set the value to the control.

    def from_memory_map_raw(self) -> Union[int, bytes]:
        raise NotImplementedError()


    def to_memory_map_raw(self, value: Union[int, bytes]):
        raise NotImplementedError()


    def from_memory_map(self):
        raise NotImplementedError()


    def to_memory_map(self):
        raise NotImplementedError()


    # utility

    def __str__(self):
        return self.description + ' @' + self.base_address


    def __repr__(self):
        return f'{self.__class__}({self.base_address}, {self.description})'


class MMC_Bits(MMC_Base):
    def __init__(self, description: str, address: int, bits: List[int]):
        'bits must be a list of bit numbers, MSB first, like [2, 1, 0]'
        assert all(0 <= b < 8 for b in bits)
        bits_str = ','.join(map(str, bits))
        super().__init__(description, f'{address}[{bits_str}]')
        self.address = address
        self.bits = bits
        for b in bits:
            register_bit(self, address, b)


    def from_memory_map_raw(self) -> int:
        val = memory_map[self.address]
        acc = 0
        for b in self.bits:
            acc <<= 1
            acc |= ((val >> b) & 1)
        return acc


    def to_memory_map_raw(self, value):
        assert isinstance(value, int)
        byte = memory_map.get(self.address, 0)
        for b in reversed(self.bits):
            byte |= (value & 1) << b
            value >>= 1
        memory_map[self.address] = byte


class MMC_Bytes(MMC_Base):
    def __init__(self, description: str, addresses: Sequence[int]):
        super().__init__(description, f'{addresses[0]}')
        self.addresses = addresses
        for a in self.addresses:
            register_byte(self, a)


    def from_memory_map_raw(self) -> bytes:
        return bytes(memory_map[a] for a in self.addresses)


    def to_memory_map_raw(self, values):
        assert len(values) == len(self.addresses)
        for addr, val in zip(self.addresses, values):
            memory_map[addr] = val


# Pseudo-controls for constant values

class MMC_FixedBit(MMC_Bits):
    def __init__(self, address: int, bit: int, value=0):
        super().__init__('', address, [bit])
        self.value = value


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        if val != self.value:
            log.warning(f'{self}: фиксированный бит с неправильным значением: {val}')


    def to_memory_map(self):
        self.to_memory_map_raw(self.value)


class MMC_FixedByte(MMC_Bytes):
    def __init__(self, address: int, value=0):
        super().__init__('', [address])
        self.value = value


    def from_memory_map(self):
        [val] = self.from_memory_map_raw()
        if val != self.value:
            log.warning(f'{self}: фиксированный байт с неправильным значением: {val}')


    def to_memory_map(self):
        self.to_memory_map_raw([self.value])


# Actual controls

def return_wrapped_control(cls):
    'In 99% of the cases we want to get the resulting tk control instead of the MMC itself'
    @functools.wraps(cls.__init__)
    def wrapper(*args, **kwargs):
        mmc = cls(*args, **kwargs)
        mmc.control.mmc = mmc
        return mmc.control
    return wrapper


@return_wrapped_control
class MMC_Checkbutton(MMC_Bits):
    def __init__(self, parent, text: str, address: int, bit: int):
        super().__init__(text, address, [bit])
        self.var = tk.IntVar(parent)
        self.control = tk.Checkbutton(parent, var=self.var, text=text)


    def from_memory_map(self):
        self.var.set(self.from_memory_map_raw())


    def to_memory_map(self):
        self.to_memory_map_raw(self.var.get())


@return_wrapped_control
class MMC_Choice(MMC_Bits):
    def __init__(self, parent, text: str, address: int, bits: List[int], options: dict):
        super().__init__(text, address, bits)
        self.var = tk.StringVar(parent)
        self.options_bin_to_str = options
        # Python3.6 preserves order of insertion, so this was the first option
        self.default_value = next(iter(self.options_bin_to_str.values()))
        self.options_str_to_bin = {v: k for k, v in options.items()}
        self.control = tk.OptionMenu(parent, self.var, *self.options_str_to_bin.keys())
        tk_set_list_maxwidth(self.control, self.options_str_to_bin.keys())
        self.set_default_value()


    def set_default_value(self):
        self.var.set(self.default_value)


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        if val in self.options_bin_to_str:
            self.var.set(self.options_bin_to_str[val])
        else:
            log.warning(f'Неправильное значение для {self!r}: {val}, используем значение по умолчанию')
            self.set_default_value()


    def to_memory_map(self):
        self.to_memory_map_raw(self.options_str_to_bin[self.var.get()])


@return_wrapped_control
class MMC_Int(MMC_Bytes):
    def __init__(self, parent, text: str, addresses: List[int]):
        super().__init__(text, addresses)
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.set_default_value()


    def set_default_value(self):
        self.var.set('0')


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        acc = 0
        for v in val:
            acc <<= 8
            acc += v
        self.var.set(str(acc))


    def to_memory_map(self):
        i = int(self.var.get())
        val = i.to_bytes(len(self.addresses), 'big') # Yay Python!
        self.to_memory_map_raw(val)


def str_to_bytes(s: str, length: int):
    b = s.encode('utf-8')
    padding = length - len(b)
    assert padding >= 0
    return b + b'\0' * padding


def bytes_to_str(val: bytes):
    try:
        s = val.decode('utf-8') # why not?
    except UnicodeError:
        log.warning(f'Инвалидные unicode символы: {val!r}')
        s = val.decode('utf-8', errors='replace')
    zeropos = s.find('\0')
    if zeropos >= 0:
        s = s[:zeropos]
    return s


@return_wrapped_control
class MMC_String(MMC_Bytes):
    def __init__(self, parent, text: str, address: int, length: int):
        # TODO: check if the device considers zero terminator optional?
        super().__init__(text, range(address, address + length))
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.set_default_value()


    def set_default_value(self):
        self.var.set('')


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        self.var.set(bytes_to_str(val))


    def to_memory_map(self):
        s = self.var.get()
        b = str_to_bytes(s, len(self.addresses))
        self.to_memory_map_raw(b)


@return_wrapped_control
class MMC_IP_Port(MMC_Bytes):
    def __init__(self, parent, text: str, address: int):
        # TODO: check if the device considers zero terminator optional?
        self.ip_length = 16
        self.port_length = 5
        super().__init__(text, range(address, address + self.ip_length + self.port_length))
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.set_default_value()


    def set_default_value(self):
        self.var.set('0.0.0.0:2048')


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        ip = bytes_to_str(val[:self.ip_length])
        port = bytes_to_str(val[self.ip_length:])
        self.var.set(ip + ':' + port)


    def to_memory_map(self):
        s = self.var.get()
        m = re.match(r'^(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}):(\d{1,5})$', s.strip())
        # TODO: more thorough check
        if not m:
            raise Exception(f'{self}: неправильный формат: {s!r}')

        ip, port = m.groups()
        self.to_memory_map_raw(str_to_bytes(ip, self.ip_length) + str_to_bytes(port, self.port_length))


@return_wrapped_control
class MMC_BCD(MMC_Bytes):
    def __init__(self, parent, text: str, address: int, length: int):
        'Length is in _nibbles_'
        super().__init__(text, range(address, address + (length + 1) // 2))
        self.length = length
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.set_default_value()


    def set_default_value(self):
        self.var.set('0' * self.length)


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        def validate_digit(digit):
            if not 0 <= digit <= 9:
                raise Exception(f'{self}: недесятичная цифра в данных: {pretty_hexlify(val)}')
            return digit
        result = []
        try:
            for b in val:
                result.append(str(validate_digit(b >> 4)))
                if len(result) < self.length:
                    result.append(str(validate_digit(b & 0x0F)))
                elif b & 0x0F:
                        raise Exception(f'{self}: последний ниббл в данных должен быть нулём: {pretty_hexlify(val)}')
        except Exception as exc:
            log.error(exc)
            self.set_default_value()
            return
        assert len(result) == self.length
        self.var.set(''.join(result))


    def to_memory_map(self):
        s = self.var.get().strip()
        if len(s) != self.length:
            raise Exception(f'{self}: неправильная длина: {s!r} ({len(s)}), должна быть {self.length}')

        result = []
        for i, c in enumerate(s):
            if not i & 1:
                result.append(int(c) << 4)
            else:
                result[-1] |= int(c)
        self.to_memory_map_raw(result)


