from typing import Union, List, Dict, Tuple, Sequence, Any, Iterable
import functools
import tkinter as tk
from dataclasses import dataclass
import re
import itertools

from programmator.utils import tk_set_list_maxwidth, pretty_hexlify, timeit_block
from programmator.comms import send_receive, Message, ThreadController
from programmator.asmparser import load_factory_settings


import logging
log = logging.getLogger(__name__)

# static descriptions

controls: 'List[MMC_Base]' = []

'''
We don't always read/write all memory. We have pin-protected areas that we read but not write unless
we have a valid pin. Both are stored in byte_memory_registry and are used to produce
memory_spans_all and memory_spans_unlocked.

bit_memory_registry doesn't support pin-protected memory.
'''

bit_memory_registry: 'Dict[int, Dict[int, MMC_Base]]' = {}
byte_memory_registry: 'Dict[int, MMC_Base]' = {}


@dataclass
class MemorySpans:
    spans: List[Tuple[int, int]]
    total_bytes: int

# what we are reading
memory_spans_read: MemorySpans
# what we are writing when correct pin was not entered
memory_spans_write: MemorySpans
# what we are writing with correct/unset pin (includes memory_spans_write)
memory_spans_write_pin_protected: MemorySpans
# Spans for the factory reset image, ideally cover the entire memory.
memory_spans_write_factory_reset: MemorySpans

# actual dynamic memory.
memory_map: Dict[int, int] = {}

memory_map_factory_reset: Dict[int, int] = {}

# API

def _compute_spans(addresses: Iterable[int]) -> MemorySpans:
    spans: List[Tuple[int, int]] = []
    start = None
    prev = None
    page_mask = 0xFF80
    bytes_per_span = 15

    for addr in sorted(addresses):
        if start is None:
            start = prev = addr
        elif (     addr != prev + 1
                or addr - start >= bytes_per_span
                or (addr & page_mask) != (start & page_mask)):
            spans.append((start, prev + 1))
            start = prev = addr
        else:
            prev = addr
    assert start is not None
    assert prev is not None
    spans.append((start, prev + 1))
    total_bytes = sum(end - start for start, end in spans)
    return MemorySpans(spans, total_bytes)


def finish_initialization():
    # sanity check
    for address, bits in bit_memory_registry.items():
        if len(bits) != 8:
            print(bits)
            assert False, f'Incomplete byte at {address}'

    global memory_map_factory_reset
    global memory_spans_read
    global memory_spans_write_unprotected
    global memory_spans_write_pin_protected
    global memory_spans_write_factory_reset

    memory_map_factory_reset = load_factory_settings()
    # currently memory_spans_read and memory_spans_write_pin_protected are the same, I use a
    # separate name in case I need to compute control sum or something like that again.
    memory_spans_read = _compute_spans(bit_memory_registry.keys() | byte_memory_registry.keys())
    memory_spans_write_pin_protected = _compute_spans(bit_memory_registry.keys() | byte_memory_registry.keys())
    memory_spans_write_unprotected = _compute_spans(bit_memory_registry.keys() | (
            addr for addr, mmc in byte_memory_registry.items() if not mmc.pin_protected))
    memory_spans_write_factory_reset = _compute_spans(memory_map_factory_reset)

    set_default_values()


def read_into_memory_map(port, controller: ThreadController):
    # we currently always read all, then check pin
    memory_map.clear()
    with timeit_block('Reading device memory'):
        read_bytes = 0
        for start, end in memory_spans_read.spans:
            msg = Message(1, start, [0] * (end - start))
            resp = send_receive(port, msg, controller)
            if resp is None:
                memory_map.clear()
                return False
            for i, b in enumerate(resp.data):
                memory_map[start + i] = b
            read_bytes += end - start
            controller.report_progress(read_bytes, memory_spans_read.total_bytes)
        return True


def populate_controls_from_memory_map():
    # import here to avoid import cycles
    from programmator.pinmanager import pinmanager
    for control in controls:
        if pinmanager.can_access_pin_protected or not control.pin_protected:
            if control.is_fixed_value:
                # TODO: use compare when implemented
                pass
            else:
                control.from_memory_map()


def populate_memory_map_from_controls():
    from programmator.pinmanager import pinmanager
    memory_map.clear()
    for control in controls:
        if pinmanager.can_access_pin_protected or not control.pin_protected:
            control.to_memory_map()
    return True


def set_default_values():
    global memory_map
    original_memory_map = memory_map
    try:
        memory_map = memory_map_factory_reset
        for control in controls:
            control.set_default_value()
            control.from_memory_map()
            if control.is_fixed_value:
                control.make_control_readonly()
    finally:
        memory_map = original_memory_map


def _get_appropriate_spans(pin_protected=None):
    from programmator.pinmanager import pinmanager
    if pin_protected is None:
        pin_protected = pinmanager.can_access_pin_protected
    if pin_protected:
        return memory_spans_write_pin_protected
    else:
        return memory_spans_write_unprotected


def write_from_memory_map(port, controller: ThreadController, do_factory_reset: bool):
    if do_factory_reset:
        spans = memory_spans_write_factory_reset
        l_memory_map = memory_map_factory_reset
    else:
        spans = _get_appropriate_spans()
        l_memory_map = memory_map

    memory_spans, total_bytes = spans.spans, spans.total_bytes

    write_bytes = 0
    def write(start, data):
        nonlocal write_bytes
        msg = Message(0, start, data)
        resp = send_receive(port, msg, controller)
        if resp is None:
            return False
        write_bytes += len(data)
        controller.report_progress(write_bytes, total_bytes)
        return True

    for start, end in memory_spans:
        if not write(start, [l_memory_map[i] for i in range(start, end)]):
            return False

    return True


def memory_map_to_str(pin_protected):
    memory_spans = _get_appropriate_spans(pin_protected).spans
    res = ['v0.0.19', str(int(pin_protected))]
    for start, end in memory_spans:
        s = ' '.join(f'{memory_map[i]:02X}' for i in range(start, end))
        res.append(f'{start} {end} {s}')
    return '\n'.join(res)


def memory_map_from_str(s):
    line_iter = iter(s.split('\n'))
    version = next(line_iter)
    assert version == 'v0.0.19'
    pin_protected = bool(int(next(line_iter)))

    memory_spans = _get_appropriate_spans(pin_protected).spans

    memory_map.clear()
    for start, end in memory_spans:
        fstart, fend, *hh = next(line_iter).split()
        assert int(fstart) == start
        assert int(fend) == end
        assert len(hh) == end - start
        for i, h in zip(range(start, end), hh):
            memory_map[i] = int(h, 16)

    return pin_protected


# helpers

def register_bit(control, address: int, bit: int):
    assert control is not None
    assert 0 <= bit < 8
    assert not control.is_factory_reset_only
    assert not control.pin_protected

    def assert_not_used(other):
        assert not other, f'{control!r} wants to use address {address}[{bit}] already used by {other!r}'

    assert_not_used(byte_memory_registry.get(address))
    bits = bit_memory_registry.setdefault(address, {})
    assert_not_used(bits.get(bit))
    bits[bit] = control


def register_byte(control, address: int):
    assert control is not None
    def assert_not_used(other):
        assert not other, f'{control!r} wants to use address {address} already used by {other!r}'
    assert_not_used(byte_memory_registry.get(address))
    bits = bit_memory_registry.get(address, None)
    if bits:
        assert_not_used(next(iter(bits.values())))
    if control.is_factory_reset_only:
        assert not control.pin_protected
        assert control.is_fixed_value
    else:
        byte_memory_registry[address] = control


def int_from_bytes(b : bytes):
    return int.from_bytes(b, 'big')


def int_to_bytes(i: int, length: int):
    return i.to_bytes(length, 'big')


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


# Base classes that deal with reading and writing memory, but not tk.

class MMC_Base:
    def __init__(self, description:str, base_address: str):
        self.base_address = base_address # for error reporting purposes
        self.description = description
        self.default_value = ''
        self.var: object = None
        # allow setting these these in derived classes before calling super()
        # because these are checked by register_byte()
        self.__dict__.setdefault('is_fixed_value', False)
        self.__dict__.setdefault('pin_protected', False)
        self.__dict__.setdefault('is_factory_reset_only', False)
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


    def set_default_value(self):
        assert self.var is not None
        self.var.set(self.default_value)


    def clear(self):
        # a separate method is sometimes needed for pin-protected controls
        self.set_default_value()


    def make_control_readonly(self):
        self.control.configure(state='readonly')


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


    def set_default_value(self):
        pass


def make_fixed_bits(address: int, bits: Iterable[int]):
    return [MMC_FixedBit(address, bit) for bit in bits]


class MMC_FixedByte(MMC_Bytes):
    def __init__(self, address: int, value=0xFF):
        super().__init__('', [address])
        self.value = value


    def from_memory_map(self):
        [val] = self.from_memory_map_raw()
        if val != self.value:
            log.warning(f'{self}: фиксированный байт с неправильным значением: {val}')


    def to_memory_map(self):
        self.to_memory_map_raw([self.value])


    def set_default_value(self):
        pass


class MMC_FactoryResetBytes(MMC_Bytes):
    def __init__(self, address: int, values: List[int]):
        # set these before super()
        self.is_fixed_value = True
        self.is_factory_reset_only = True
        super().__init__('FactoryResetBytes', range(address, address + len(values)))
        self.values = values


    def to_memory_map(self):
        self.to_memory_map_raw(self.values)

    # No-ops

    def from_memory_map(self):
        pass


    def set_default_value(self):
        pass


    def make_control_readonly(self):
        pass


# Actual controls

def return_wrapped_control(cls):
    '''In 99% of the cases we want to get the resulting tk control instead of the MMC itself.
    This makes mypy very confused about inheritance unfortunately, but what you gonna do'''
    @functools.wraps(cls.__init__)
    def wrapper(*args, **kwargs):
        mmc = cls(*args, **kwargs)
        mmc.control.mmc = mmc
        return mmc.control
    wrapper.cls = cls
    return wrapper


@return_wrapped_control
class MMC_Checkbutton(MMC_Bits):
    def __init__(self, parent, text: str, address: int, bit: int):
        super().__init__(text, address, [bit])
        self.var = tk.IntVar(parent)
        self.control = tk.Checkbutton(parent, var=self.var, text=text)
        self.default_value = '0'


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


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        if val in self.options_bin_to_str:
            self.var.set(self.options_bin_to_str[val])
        else:
            log.warning(f'Неправильное значение для {self!r}: {val}, используем значение по умолчанию')
            self.set_default_value()


    def to_memory_map(self):
        self.to_memory_map_raw(self.options_str_to_bin[self.var.get()])


    def make_control_readonly(self):
        self.control.configure(state='disabled')


@return_wrapped_control
class MMC_Int(MMC_Bytes):
    def __init__(self, parent, text: str, addresses: List[int]):
        super().__init__(text, addresses)
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.default_value = '0'


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        self.var.set(str(int_from_bytes(val)))


    def to_memory_map(self):
        i = int(self.var.get())
        val = int_to_bytes(i, len(self.addresses))
        self.to_memory_map_raw(val)


@return_wrapped_control
class MMC_String(MMC_Bytes):
    def __init__(self, parent, text: str, address: int, length: int):
        # TODO: check if the device considers zero terminator optional?
        super().__init__(text, range(address, address + length))
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)


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
        self.default_value = '0.0.0.0:0000'


    def clear(self):
        self.var.set('')


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
    cls : Any = None # calm down mypy

    def __init__(self, parent, text: str, address: int, length: int):
        'Length is in _nibbles_'
        super().__init__(text, range(address, address + (length + 1) // 2))
        self.length = length
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.default_value = ''.join(self.digit_to_char(0) for _ in range(self.length))


    def digit_to_char(self, d):
        if not 0 <= d <= 9:
            raise Exception(f'{self}: недесятичная цифра в данных: {pretty_hexlify(d)}')
        return str(d)


    def char_to_digit(self, c):
        return int(c)


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        result = []
        try:
            for b in val:
                result.append(self.digit_to_char(b >> 4))
                if len(result) < self.length:
                    result.append(self.digit_to_char(b & 0x0F))
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
                result.append(self.char_to_digit(c) << 4)
            else:
                result[-1] |= self.char_to_digit(c)
        self.to_memory_map_raw(result)


@return_wrapped_control
class MMC_BCD_A(MMC_BCD.cls):
    'In alert messages 0 is replaced with A'

    def digit_to_char(self, d):
        return super().digit_to_char(d) if d else 'A'


    def char_to_digit(self, c):
        if c.upper() in 'A\u0410': # accept latin and cyrillic A
            return 0
        return super().char_to_digit(c)


@return_wrapped_control
class MMC_Time(MMC_Bytes):
    def __init__(self, parent, text: str, address: int, max_byte_value=255, fine_step=0.05, fine_count=20):
        super().__init__(text, [address])
        self.max_byte_value = max_byte_value
        self.fine_step = fine_step
        self.fine_count = fine_count

        self.decimals = 0 if not fine_count else 2
        self.threshold = fine_step * fine_count
        assert self.threshold == int(self.threshold)
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        # TODO: refactor formatting from to/from_memory_map.
        self.default_value = '{:0.{decimals}f}'.format(0, decimals=self.decimals)


    def from_memory_map(self):
        [val] = self.from_memory_map_raw()
        if val <= self.fine_count:
            res_f = self.fine_step * val
        else:
            res_f = int(self.threshold + val - self.fine_count)
        res = '{:0.{decimals}f}'.format(res_f, decimals=self.decimals)
        self.var.set(res)


    def to_memory_map(self):
        # TODO: add warnings for rounding
        x = float(self.var.get())
        if x <= self.threshold:
            res = round(x / self.fine_step)
        else:
            res = round(x - self.threshold) + self.fine_count
        if res > self.max_byte_value:
            res = self.max_byte_value
        self.to_memory_map_raw([res])


@return_wrapped_control
class MMC_LongTimeMinutes(MMC_Bytes):
    '''several bytes containing a number of seconds, but presented with 1 minute accuracy'''
    def __init__(self, parent, text: str, addresses: List[int]):
        super().__init__(text, addresses)
        self.var = tk.StringVar(parent)
        self.control = tk.Entry(parent, textvariable=self.var)
        self.default_value = '0'


    def from_memory_map(self):
        val = int_from_bytes(self.from_memory_map_raw())
        mm = round(val / 60)
        self.var.set(f'{mm}')


    def to_memory_map(self):
        s = self.var.get()
        i = int(s)
        val = int_to_bytes(i * 60, len(self.addresses))
        self.to_memory_map_raw(val)


@return_wrapped_control
class MMC_Phone(MMC_Bytes):
    def __init__(self, parent, text: str, address: int, length: int):
        # TODO: check if the device considers zero terminator optional?
        super().__init__(text, range(address, address + length))

        # def validate(s):
        #     return s.startswith('+')
        # vcmd = (self.control.register(validate), '%P')
        # self.entry = tk.Entry(self.control, textvariable=self.var, validate='key', validatecommand=vcmd)

        self.control = tk.Frame(parent)

        self.varplus = tk.StringVar(parent)
        self.plus = tk.Entry(self.control, textvariable=self.varplus, width=1, relief=tk.FLAT, state=tk.DISABLED)
        self.plus.configure(disabledforeground=self.plus.cget('foreground'))
        setattr(self.plus, 'hack_dont_set_state', True) # avoid mypy complaining
        self.plus.pack(side=tk.LEFT, expand=True, fill='y')
        self.varplus.set('+')

        self.var = tk.StringVar(parent)
        self.entry = tk.Entry(self.control, textvariable=self.var)
        self.entry.pack(side=tk.LEFT, expand=True, fill='both')


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        self.var.set(bytes_to_str(val))


    def to_memory_map(self):
        s = self.var.get()
        b = str_to_bytes(s, len(self.addresses))
        self.to_memory_map_raw(b)




if __name__ == '__main__':
    from programmator.main import main
    main()
