import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.font import Font

from programmator.utils import VerticalScrolledFrame, tk_set_list_maxwidth, enumerate_first_last
from programmator.device_memory import (finish_initialization, MMC_Checkbutton, MMC_FixedBit, MMC_Choice,
    MMC_Int, MMC_FixedByte, MMC_String, MMC_IP_Port, MMC_BCD, MMC_BCD_A, MMC_Time, MMC_LongTimeMinutes,
    MMC_Phone, make_fixed_bits)
from programmator.pinmanager import pinmanager

import logging
log = logging.getLogger(__name__)


def revupdate_kwargs(extra_kwargs: dict, **kwargs):
    'Update the dict of kwargs given explicitly with the first argument, overriding duplicate values'
    kwargs.update(extra_kwargs)
    return kwargs


def next_grid_row(parent, column=0):
    return parent.grid_size()[1] - bool(column)


def grid_control_and_control(parent, control1, control2, column=0, kwargs={}, kwargs1={}, kwargs2={}):
    row = next_grid_row(parent, column)
    kwargs1 = revupdate_kwargs(kwargs1, **kwargs)
    kwargs2 = revupdate_kwargs(kwargs2, **kwargs)
    control1.grid(revupdate_kwargs(kwargs1, row=row, column=1 + column, sticky='nsew', padx=5))
    control2.grid(revupdate_kwargs(kwargs2, row=row, column=2 + column, sticky='nsew', padx=5))
    return control1, control2


def grid_label_and_control(parent, label_text: str, control, column=0, **kwargs):
    label = tk.Label(parent, text=label_text)
    return grid_control_and_control(parent, label, control, column=column, **kwargs)


def grid_label_and_control_mmc(mmc_control, column=0, **kwargs):
    parent = mmc_control.master
    label_text = mmc_control.mmc.description
    return grid_label_and_control(parent, label_text, mmc_control, column, **kwargs)


def grid_control(control, column=0, **kwargs):
    row = next_grid_row(control.master, column)
    control.grid(revupdate_kwargs(kwargs, row=row, column=1 + column, columnspan=2, padx=5))


def grid_separator(parent, visible=True, columnspan=2):
    row = next_grid_row(parent, 0)
    separator = tk.Frame(parent, height=2, bd=visible, relief=tk.SUNKEN)
    separator.grid(row=row, column=1, columnspan=columnspan, pady=5, padx=0, sticky='nsew')


def recursively_set_state(widget, state):
    try:
        if getattr(widget, 'hack_dont_set_state', None):
            return
        widget.configure(state=state)
    except tk.TclError:
        pass
    for w in widget.winfo_children():
        recursively_set_state(w, state)


def create_widgets(tabs):
    # placeholder pseudo-controls
    # mmc_version = MMC_Int(tabs, 'version', [1008, 1009]).mmc
    # mmc_pin = MMC_BCD(tabs, 'PIN', 1014, 6).mmc # 3 bytes instead of specced 6.
    # log.info(f'version={mmc_version.var.get()}')
    # log.debug(f'pin={mmc_pin.var.get()}')

    def add_tab(name: str, header=''):
        page = ttk.Frame(tabs)

        tabs.add(page, text=name)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(3, weight=1)

        if header:
            for is_first, is_last, line in enumerate_first_last(header.split('\n')):
                ctrl = tk.Label(page, text=line)
                # increase font size somewhat
                font = Font(font=ctrl['font'])
                font.configure(size=font['size'] + 2)
                ctrl.configure(font=font)
                grid_control(ctrl, pady=(10 if is_first else 0, 10 if is_last else 0))
            grid_separator(page)
        return page

    page = add_tab('Настройки', 'Основные настройки')

    ctrl = MMC_BCD(page, 'Номер коммуникатора', 0, 4)
    grid_label_and_control_mmc(ctrl)

    make_fixed_bits(2, range(1, 8))

    ctrl = MMC_Choice(page, 'Тип контрольной панели', 3, [2, 1, 0], {
        0: 'Коммуникатор',
        1: 'DALLAS',
        2: 'RING/TIP',
        3: 'MAGELLAN',
        4: 'SECOLINK',
        5: 'ESPRIT',
        })
    grid_label_and_control_mmc(ctrl)


    ctrl = MMC_LongTimeMinutes(page, 'Период тестовой посылки (минуты)', [4, 5])
    ctrl.mmc.var.set('30')
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_BCD_A(page, 'Тестовая посылка', 6, 9)
    ctrl.mmc.var.set('16A2AAAAA')
    grid_label_and_control_mmc(ctrl)

    # ctrl = MMC_Choice(page, 'Рапорт на IP адреса', 3, [5, 4, 3], {
    #     0b100: 'IP 1',
    #     0b010: 'IP 2',
    #     0b110: 'IP1 основной/IP2 резервный',
    #     # 0b111: 'IP 1 + IP 2',
    #     })
    # grid_label_and_control_mmc(ctrl)

    grid_separator(page)

    # PIN protected controls

    pin_protected_controls = []

    def pin_status_changed():
        if pinmanager.can_access_pin_protected:
            for it in pin_protected_controls:
                recursively_set_state(it, tk.NORMAL)
        else:
            for it in pin_protected_controls:
                it.mmc.clear()
                recursively_set_state(it, tk.DISABLED)

        toggle_pin_status_button.configure(text={
            pinmanager.OPEN: 'Закрыть',
            pinmanager.VALID: 'Сменить пин',
            pinmanager.CLOSED: 'Сбросить настройки'}[pinmanager.status])

        pin_status_label.configure(text={
            pinmanager.OPEN: 'Дополнительные настройки открыты',
            pinmanager.VALID: 'Дополнительные настройки защищены',
            pinmanager.CLOSED: 'Дополнительные настройки недоступны'}[pinmanager.status])

    pinmanager.on_status_changed = pin_status_changed

    def toggle_pin_status():
        if pinmanager.can_access_pin_protected:
            # then close or change pin
            pinmanager.change_pin(page.winfo_toplevel())
        else:
            for it in pin_protected_controls:
                it.mmc.set_default_value()
            pinmanager.clear_pin()

    toggle_pin_status_button = tk.Button(page, text='---', command=toggle_pin_status)
    pin_status_label = tk.Label(page, text='---')
    grid_control_and_control(page, pin_status_label, toggle_pin_status_button)

    # SIM/APN

    def SIM(n, apn_offset):
        row = next_grid_row(page)
        frame = tk.Frame(page)

        ctrl = tk.Label(frame, text=f'APN{n}')
        ctrl.pack(side=tk.RIGHT, padx=(30, 0))

        if n == 1:
            ctrl = tk.Checkbutton(frame, text=f'SIM{n}')
            ctrl.select()
            ctrl.config(state=tk.DISABLED)
        else:
            ctrl = MMC_Checkbutton(frame, f'SIM{n}', 2, 0)
        ctrl.pack(side=tk.RIGHT)

        ctrl = MMC_String(page, f'APN{n}', apn_offset, 20)
        grid_control_and_control(page, frame, ctrl)
        pin_protected_controls.append(ctrl)

    SIM(1, 163)
    SIM(2, 204)

    name = 'Основной IP:port'
    ctrl1 = tk.Checkbutton(page, text=name)
    ctrl1.select()
    ctrl1.configure(state=tk.DISABLED)
    ctrl2 = MMC_IP_Port(page, name, 142)
    grid_control_and_control(page, ctrl1, ctrl2, kwargs1=dict(sticky='w'))
    pin_protected_controls.append(ctrl2)

    MMC_FixedBit(3, 3)
    MMC_FixedBit(3, 4, 1)
    name = 'Резервный IP:port'
    ctrl1 = MMC_Checkbutton(page, name, 3, 5)
    ctrl2 = MMC_IP_Port(page, name, 183)
    grid_control_and_control(page, ctrl1, ctrl2, kwargs1=dict(sticky='w'))
    pin_protected_controls.append(ctrl1)
    pin_protected_controls.append(ctrl2)

    name = 'Телефон резервного СМС канала SIM1'
    ctrl1 = MMC_Checkbutton(page, name, 3, 6)
    ctrl2 = MMC_Phone(page, name, 224, 16)
    grid_control_and_control(page, ctrl1, ctrl2)
    pin_protected_controls.append(ctrl1)
    pin_protected_controls.append(ctrl2)

    name = 'Телефон резервного СМС канала SIM2'
    ctrl1 = MMC_Checkbutton(page, name, 3, 7)
    ctrl2 = MMC_Phone(page, name, 240, 16)
    grid_control_and_control(page, ctrl1, ctrl2)
    pin_protected_controls.append(ctrl1)
    pin_protected_controls.append(ctrl2)

    for it in pin_protected_controls:
        it.mmc.pin_protected = True
    # hack: manually trigger it, for a default-initialized panel everything should be consistent with OPEN
    pin_status_changed()

    ########

    page = add_tab('Входы', 'Конфигурация входных сигналов') #

    container = VerticalScrolledFrame(page)
    grid_control(container, sticky='nwse')
    # rowconfigure adds a row lol so do this after grid_control
    page.rowconfigure(2, weight=1)
    container = container.interior

    for i in range(10):
        is_input_nine = (i == 8)
        is_input_ten = (i == 9)

        frame = tk.LabelFrame(container, text=(
            'Вход №9. Постановка/Снятие' if is_input_nine else
            'Разряд АКБ' if is_input_ten else
            f'Вход №{i + 1}'))
        grid_control(frame, pady=5)

        base_addr = 12 + i * 12
        bitmap_addr = base_addr + 3

        ctrl = MMC_Checkbutton(frame, 'Вход задействован' if i != 9 else 'Задействован', bitmap_addr, 7)
        grid_control(ctrl, sticky='w')

        ctrl = MMC_Time(frame, 'Антидребезг (сек)', base_addr + 2, fine_count=300)
        grid_label_and_control_mmc(ctrl, column=2)

        ctrl = MMC_Time(frame, 'Задержка срабатывания (сек)', base_addr + 0, fine_count=0, max_byte_value=127)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Задержка восстановления (сек)', base_addr + 1, fine_count=0, max_byte_value=127)
        grid_label_and_control_mmc(ctrl, column=2)

        ctrl = MMC_Checkbutton(frame, 'SMS рассылка', bitmap_addr, 6)
        grid_control(ctrl, sticky='w')

        if not is_input_nine:
            # Тип зоны - Только под охраной, 24х часовая
            ctrl = MMC_Checkbutton(frame, '24-х часовой', bitmap_addr, 2)
            grid_control(ctrl, column=2, sticky='w')
        else:
            MMC_FixedBit(bitmap_addr, 2)

        ctrl = MMC_Checkbutton(frame, 'управление PGM1', bitmap_addr, 4)
        grid_control(ctrl, sticky='w')

        ctrl = MMC_Checkbutton(frame, 'управление PGM2', bitmap_addr, 5)
        grid_control(ctrl, column=2, sticky='w')

        MMC_FixedBit(bitmap_addr, 3)
        MMC_FixedBit(bitmap_addr, 1)

        if not is_input_nine:
            ctrl = MMC_Choice(frame, 'Уровень срабатывания', bitmap_addr, [0], {
                0: 'Низкий',
                1: 'Высокий',
                })
            grid_label_and_control_mmc(ctrl)
        else:
            MMC_FixedBit(bitmap_addr, 0)

        ctrl = MMC_BCD_A(frame, 'Команда срабатывания' if not is_input_nine else 'Команда постановки', base_addr + 4, 4)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_BCD_A(frame, 'Команда восстановления' if not is_input_nine else 'Команда снятия', base_addr + 6, 4)
        grid_label_and_control_mmc(ctrl, column=2)

        ctrl = MMC_BCD(frame, 'Район', base_addr + 8, 2) # 00-99, 00
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_BCD(frame, 'Пользователь', base_addr + 9, 3) # 000-999, 000
        grid_label_and_control_mmc(ctrl, column=2)

        grid_separator(frame, False)


    page = add_tab('PGM', 'Конфигурация программируемых выходных сигналов (PGM)')

    container = page

    for i in range(2):
        frame = tk.LabelFrame(container, text=f'PGM{i + 1}')
        grid_control(frame, pady=5)

        base_addr = 137 if i else 132
        bitmap_addr = base_addr + 4

        ctrl = MMC_Checkbutton(frame, 'PGM задействован', bitmap_addr, 7)
        grid_control(ctrl, sticky='w')

        make_fixed_bits(bitmap_addr, [6, 3, 2])

        # Режим работы: Потенциальный Импульсный
        # ctrl = MMC_Checkbutton(frame, 'Импульсный', bitmap_addr, 1)
        # grid_control(ctrl, sticky='w')

        # # Тип выхода: Нормально разомкнут, Нормально замкнут
        # ctrl = MMC_Checkbutton(frame, 'Нормально разомкнут', bitmap_addr, 0)
        # grid_control(ctrl, column=2, sticky='w')

        ctrl = MMC_Choice(frame, 'Режим работы', bitmap_addr, [1], {
            0: 'Потенциальный',
            1: 'Импульсный',
            })
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Choice(frame, 'Тип выхода', bitmap_addr, [0], {
            0: 'Нормально замкнут',
            1: 'Нормально разомкнут',
            })
        grid_label_and_control_mmc(ctrl)

        # только в импульсный режим
        ctrl = MMC_Time(frame, 'Длительность при постановке (сек)', base_addr + 0)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Длительность при снятии (сек)', base_addr + 1)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Длительность при срабатывании (сек)', base_addr + 2)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Длительность при восстановлении (сек)', base_addr + 3)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Checkbutton(frame, 'Программируемый через СМС', bitmap_addr, 5)
        grid_control(ctrl, sticky='w')

        ctrl = MMC_Checkbutton(frame, 'Зависимый от входов', bitmap_addr, 4)
        grid_control(ctrl, column=1, sticky='w')

        grid_separator(frame, False)

    page = add_tab('СМС управление', 'Белый список телефонов с правами управления' +
            '\n(последние 8 цифр номера)')
    container = tk.Frame(page)
    grid_control(container)

    for i in range(10):
        row = next_grid_row(container, 0)
        base_addr = 384 + i * 8

        MMC_FixedByte(base_addr + 0) # CLS

        ctrl = MMC_BCD(container, f'Телефон №{i + 1}', base_addr + 1, 8)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_BCD(container, f'PIN', base_addr + 6, 4)
        grid_label_and_control_mmc(ctrl)

        frame = tk.LabelFrame(container, text='Права')
        frame.grid(row=row, column=3, rowspan=2, columnspan=2)

        bitmap_addr = base_addr + 5
        make_fixed_bits(bitmap_addr, [7, 6, 5, 4, 0])

        ctrl = MMC_Checkbutton(frame, 'PGM1', bitmap_addr, 2)
        grid_control(ctrl)

        ctrl = MMC_Checkbutton(frame, 'PGM2', bitmap_addr, 3)
        grid_control(ctrl, column=2)

        ctrl = MMC_Checkbutton(frame, 'Постановка/Снятие', bitmap_addr, 1)
        grid_control(ctrl, column=4)

        grid_separator(container, columnspan=4)

    page = add_tab('СМС рассылка', 'Список телефонов пользователей для рассылки СМС')
    # "обязательно ввести международный код страны" (красным)
    for i in range(10):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Телефон №{i + 1}', ctrl, kwargs=dict(pady=5))

    recursively_set_state(page, tk.DISABLED)

    # page = add_tab('Коды доступа', 'Коды доступа DALLAS/карточки')
    # for i in range(16):
    #     ctrl = tk.Entry(page)
    #     grid_label_and_control(page, f'Код доступа №{i + 1}', ctrl, kwargs=dict(pady=5))

    page = add_tab('Сообщения', 'Текстовые сообщения пользователя')
    for i in range(16):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Сообщение №{i + 1}', ctrl, kwargs=dict(pady=5))

    recursively_set_state(page, tk.DISABLED)

    # page = add_tab('X-Ссылки?')

    finish_initialization()


if __name__ == '__main__':
    from programmator.main import main
    main()
