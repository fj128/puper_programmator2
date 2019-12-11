import tkinter as tk
from tkinter import ttk, messagebox

from programmator.utils import VerticalScrolledFrame, tk_set_list_maxwidth
from programmator.device_memory import (finish_initialization, MMC_Checkbutton, MMC_FixedBit, MMC_Choice,
    MMC_Int, MMC_FixedByte, MMC_String, MMC_IP_Port, MMC_BCD, MMC_Time, MMC_LongTimeSeconds)


def next_grid_row(parent, column=0):
    return parent.grid_size()[1] - bool(column)


def grid_control_and_control(parent, control1, control2, column=0, **kwargs):
    row = next_grid_row(parent, column)
    control1.grid(row=row, column=1 + column, sticky='nsew', padx=5, **kwargs)
    control2.grid(row=row, column=2 + column, sticky='nsew', padx=5, **kwargs)
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
    control.grid(row=row, column=1 + column, columnspan=2, padx=5, **kwargs)


def grid_separator(parent, visible=True, columnspan=2):
    row = next_grid_row(parent, 0)
    separator = tk.Frame(parent, height=2, bd=visible, relief=tk.SUNKEN)
    separator.grid(row=row, column=1, columnspan=columnspan, pady=5, padx=0, sticky='nsew')


def create_widgets(tabs):
    def add_tab(name: str, header=''):
        page = ttk.Frame(tabs)

        tabs.add(page, text=name)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(3, weight=1)

        if header:
            ctrl = tk.Label(page, text=header)
            grid_control(ctrl, pady=7)
            grid_separator(page)
        return page

    page = add_tab('Настройки', 'Основные настройки')

    ctrl = MMC_BCD(page, 'Номер коммуникатора', 0, 4)
    grid_label_and_control_mmc(ctrl)

    for i in range(1, 8):
        MMC_FixedBit(2, i)

    ctrl = MMC_Choice(page, 'Тип контрольной панели', 3, [2, 1, 0], {
        0: 'Коммуникатор',
        1: 'DALLAS',
        2: 'RING/TIP',
        3: 'MAGELLAN',
        4: 'SECOLINK',
        5: 'ESPRIT',
        })
    grid_label_and_control_mmc(ctrl)


    ctrl = MMC_LongTimeSeconds(page, 'Период тестовой посылки (чч:мм:cc)', [4, 5])
    ctrl.mmc.var.set('30:00')
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_BCD(page, 'Тестовая посылка', 6, 7)
    ctrl.mmc.var.set('16A2AAAAA')
    grid_label_and_control_mmc(ctrl)

    # SIM1

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

    SIM(1, 163)
    SIM(2, 204)

    ctrl = MMC_Choice(page, 'Рапорт на IP адреса', 3, [5, 4, 3], {
        0b100: 'IP 1',
        0b010: 'IP 2',
        0b110: 'IP1 основной/IP2 резервный',
        # 0b111: 'IP 1 + IP 2',
        })
    grid_label_and_control_mmc(ctrl)

    grid_separator(page)

    cb_master_mode = None

    def master_mode_toggle():
        enabled = cb_master_mode.var.get()
        for it in master_controls:
            it.configure(state=tk.NORMAL if enabled else tk.DISABLED)

    var = tk.IntVar(page)
    ctrl = cb_master_mode = tk.Checkbutton(page, text='Режим установщика', var=var, command=master_mode_toggle)
    ctrl.var = var
    grid_control(ctrl, pady=(0, 15))

    master_controls = []

    ctrl = MMC_IP_Port(page, 'IP:port 1', 142)
    label, _ = grid_label_and_control_mmc(ctrl)
    master_controls.append(label)
    master_controls.append(ctrl)

    ctrl1 = MMC_Checkbutton(page, f'СМС на резервный телефон №1', 3, 6)
    ctrl2 = MMC_String(page, f'Резервный телефон №1', 224, 16)
    grid_control_and_control(page, ctrl1, ctrl2)
    master_controls.append(ctrl1)
    master_controls.append(ctrl2)

    # grid_separator(page)

    ctrl = MMC_IP_Port(page, 'IP:port 2', 183)
    label, _ = grid_label_and_control_mmc(ctrl)
    master_controls.append(label)
    master_controls.append(ctrl)

    ctrl1 = MMC_Checkbutton(page, f'СМС на резервный телефон №2', 3, 7)
    ctrl2 = MMC_String(page, f'Резервный телефон №2', 240, 16)
    grid_control_and_control(page, ctrl1, ctrl2)
    master_controls.append(ctrl1)
    master_controls.append(ctrl2)


    for it in master_controls:
        it.configure(state=tk.DISABLED)

    ########

    page = add_tab('Входы', 'Конфигурация входных сигналов') #

    container = VerticalScrolledFrame(page)
    grid_control(container, sticky='nwse')
    # rowconfigure adds a row lol so do this after grid_control
    page.rowconfigure(2, weight=1)
    container = container.interior

    for i in range(10):
        frame = tk.LabelFrame(container, text=f'Вход №{i + 1}')
        grid_control(frame, pady=5)

        base_addr = 12 + i * 12
        bitmap_addr = base_addr + 3

        ctrl = MMC_Checkbutton(frame, 'Вход задействован', bitmap_addr, 7)
        grid_control(ctrl, sticky='w')

        ctrl = MMC_Time(frame, 'Антидребезг', base_addr + 2)
        grid_label_and_control_mmc(ctrl, column=2)

        ctrl = MMC_Time(frame, 'Задержка срабатывания', base_addr + 0)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Задержка восстановления', base_addr + 1)
        grid_label_and_control_mmc(ctrl, column=2)

        ctrl = MMC_Checkbutton(frame, 'SMS рассылка', bitmap_addr, 6)
        grid_control(ctrl, sticky='w')

        # Тип зоны - Только под охраной, 24х часовая
        ctrl = MMC_Checkbutton(frame, '24х часовой', bitmap_addr, 2)
        grid_control(ctrl, column=2, sticky='w')

        ctrl = MMC_Checkbutton(frame, 'управление PGM1', bitmap_addr, 4)
        grid_control(ctrl, sticky='w')

        ctrl = MMC_Checkbutton(frame, 'управление PGM2', bitmap_addr, 5)
        grid_control(ctrl, column=2, sticky='w')

        MMC_FixedBit(bitmap_addr, 3)
        MMC_FixedBit(bitmap_addr, 1)
        MMC_FixedBit(bitmap_addr, 0) # NC?

        ctrl = MMC_BCD(frame, 'Команда срабатывания', base_addr + 4, 3)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_BCD(frame, 'Команда восстановления', base_addr + 6, 3)
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

        MMC_FixedBit(bitmap_addr, 6)
        MMC_FixedBit(bitmap_addr, 3)
        MMC_FixedBit(bitmap_addr, 2)

        # Режим работы: Потенциальный Импульсный
        ctrl = MMC_Checkbutton(frame, 'Импульсный', bitmap_addr, 1)
        grid_control(ctrl, sticky='w')

        # Тип выхода: Нормально разомкнут, Нормально замкнут
        ctrl = MMC_Checkbutton(frame, 'Нормально разомкнут', bitmap_addr, 0)
        grid_control(ctrl, column=2, sticky='w')

        # только в импульсный режим
        ctrl = MMC_Time(frame, 'Длительность при срабатывании', base_addr + 0)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Длительность при восстановлении', base_addr + 1)
        grid_label_and_control_mmc(ctrl)

        ctrl = MMC_Time(frame, 'Длительность при постановке/снятии', base_addr + 2)
        grid_label_and_control_mmc(ctrl)

        MMC_FixedByte(base_addr + 3)

        ctrl = MMC_Checkbutton(frame, 'Программируемый через СМС', bitmap_addr, 5)
        grid_control(ctrl, sticky='w')

        ctrl = MMC_Checkbutton(frame, 'Зависимый от входов', bitmap_addr, 4)
        grid_control(ctrl, column=2, sticky='w')

        grid_separator(frame, False)

    page = add_tab('СМС рассылка', 'Список телефонов пользователей для рассылки СМС')
    # "обязательно ввести международный код страны" (красным)
    for i in range(10):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Телефон №{i + 1}', ctrl, pady=5)

    page = add_tab('СМС управление', 'Белый список телефонов с правами управления')
    container = tk.Frame(page)
    grid_control(container)

    for i in range(10):
        row = next_grid_row(container, 0)
        ctrl = tk.Entry(container)
        grid_label_and_control(container, f'Телефон №{i + 1}', ctrl)

        ctrl = tk.Entry(container)
        grid_label_and_control(container, f'PIN', ctrl) # 0000

        frame = tk.LabelFrame(container, text='Права')
        frame.grid(row=row, column=3, rowspan=2, columnspan=2)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='PGM1')
        grid_control(ctrl)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='PGM2')
        grid_control(ctrl, column=2)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='Arm/disarm')
        grid_control(ctrl, column=4)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='Смена PIN')
        grid_control(ctrl, column=6)

        grid_separator(container, columnspan=4)

    page = add_tab('Коды доступа', 'Коды доступа DALLAS/карточки')
    for i in range(16):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Код доступа №{i + 1}', ctrl, pady=5)

    page = add_tab('Сообщения', 'Текстовые сообщения пользователя')
    for i in range(16):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Сообщение №{i + 1}', ctrl, pady=5)

    # page = add_tab('X-Ссылки?')

    finish_initialization()


if __name__ == '__main__':
    from programmator.main import main
    main()
