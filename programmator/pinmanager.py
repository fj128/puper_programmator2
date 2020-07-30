import enum, re
from typing import List
import tkinter as tk
from programmator.device_memory import MMC_Bytes, int_from_bytes, int_to_bytes
from programmator.utils import Dialog


class PseudoMMC_Int(MMC_Bytes):
    def __init__(self, name, addresses: List[int]):
        super().__init__(name, addresses)
        # pin itself is pin_protected too to avoid accidentally writing it back.
        self.pin_protected = True


    def from_memory_map(self):
        val = self.from_memory_map_raw()
        self.value = int_from_bytes(val)


    def to_memory_map(self):
        val = int_to_bytes(self.value, len(self.addresses))
        self.to_memory_map_raw(val)


    def set_default_value(self):
        self.value = 0


class PinStatus(enum.Enum):
    '''
    OPEN: pin = 0
        all editable, data from device
        "закрыть настройки пином" -> VALID
    VALID:
        all editable, data from device
        "поменять пин" -> VALID or OPEN
    CLOSED:
        nothing editable, no data
        "сбросить настройки и пин" -> OPEN, data reset to default
    '''
    OPEN=1
    VALID=2
    CLOSED=3


class PinDialog(Dialog):
    def __init__(self, parent, title, label):
        self.label = label
        self.pin = None
        super().__init__(parent, title)


    def body(self, parent):
        tk.Label(parent, text=self.label).pack()
        self.entry = tk.Entry(parent)
        self.entry.pack()
        return self.entry # initial focus


    def validate(self):
        pin = self.entry.get().strip()
        if not re.match(r'\d{6}$', pin):
            tk.messagebox.showerror("Ошибка!", "Пин должен состоять из 6 десятичных цифр")
            return False
        self.pin = int(pin, 16)
        return True



class PinManager:
    # convenience
    OPEN = PinStatus.OPEN
    VALID = PinStatus.VALID
    CLOSED = PinStatus.CLOSED

    def __init__(self):
        self.on_status_changed = None
        self._status = PinStatus.OPEN
        self.version = PseudoMMC_Int('Version', [1008, 1009])
        self.pin = PseudoMMC_Int('PIN', [1014, 1015, 1016])


    @property
    def status(self):
        return self._status

    def _set_status(self, value):
        self._status = value
        if self.on_status_changed:
            self.on_status_changed()


    @property
    def can_access_pin_protected(self):
        return self.status in (self.OPEN, self.VALID)


    def check_pin(self, parent):
        self.version.from_memory_map()
        self.pin.from_memory_map()
        if self.pin.value == 0:
            self._set_status(self.OPEN)
            return
        user_pin = PinDialog(parent, 'Проверка пина для открытия дополнительных настроек',
                'Введите пин для открытия дополнительных настроек или нажмите "Отмена":').pin
        if user_pin is not None:
            if user_pin == self.pin.value:
                self._set_status(self.VALID)
                return
            tk.messagebox.showerror("Ошибка!", "Неверный пин, дополнительные настройки недоступны")
        self._set_status(self.CLOSED)


    def change_pin(self, parent):
        user_pin = PinDialog(parent, 'Установка/смена пина',
                'Введите новый пин ("000000" открывает устройство):').pin
        if user_pin is not None:
            self.pin.value = user_pin
            self._set_status(self.VALID if user_pin else self.OPEN)


    def clear_pin(self):
        self.pin.value = 0
        self._set_status(self.OPEN)


    def update_status_after_loading_file(self, pin_protected):
        if pin_protected:
            self.version.from_memory_map()
            self.pin.from_memory_map()
            if self.pin.value == 0:
                self._set_status(self.OPEN)
            else:
                self._set_status(self.VALID)
        else:
            self._set_status(self.CLOSED)


# singleton
pinmanager = PinManager()
