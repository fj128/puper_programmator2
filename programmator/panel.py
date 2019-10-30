import tkinter as tk
from tkinter import ttk

from programmator.utils import VerticalScrolledFrame, tk_set_list_maxwidth
from programmator.device_memory import (finish_initialization, MMC_Checkbutton, MMC_FixedBit, MMC_Choice,
    MMC_Int, MMC_FixedByte, MMC_String, MMC_IP_Port, MMC_BCD)


def next_grid_row(parent, column):
    return parent.grid_size()[1] - (1 if column > 1 else 0)


def grid_label_and_control(parent, label_text: str, control, column=0, **kwargs):
    row = next_grid_row(parent, column)
    label = tk.Label(parent, text=label_text)
    label.grid(row=row, column=1 + column, padx=5, **kwargs)
    control.grid(row=row, column=2 + column, sticky='nsew', padx=5, **kwargs)


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

    MMC_FixedByte(2)

    ctrl = MMC_Choice(page, 'Тип контрольной панели', 3, [2, 1, 0], {
        0: 'Коммуникатор',
        1: 'DALLAS',
        2: 'RING/TIP',
        3: 'MAGELAN',
        4: 'SECOLINK',
        5: 'ESPRIT',
        })
    grid_label_and_control_mmc(ctrl)


    ctrl = MMC_Int(page, 'Период тестовой посылки (мин)', [4, 5])
    ctrl.mmc.var.set(30) # todo - saner default
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_BCD(page, 'Тестовая посылка', 6, 7) # TODO: 7 can't be right
    ctrl.mmc.var.set('16A2AAAAA')
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_Choice(page, 'Раппорт на IP адреса', 3, [5, 4, 3], {
        0b100: 'IP 1',
        0b010: 'IP 2',
        0b110: 'IP1 основной/IP2 резервный',
        0b111: 'IP 1 + IP 2'})
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_Checkbutton(page, 'СМС на резервный номер 1', 3, 6)
    grid_control(ctrl)

    ctrl = MMC_Checkbutton(page, 'СМС на резервный номер 2', 3, 7)
    grid_control(ctrl)

    grid_separator(page)

    ctrl = MMC_IP_Port(page, 'ip:port 1', 142)
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_String(page, 'APN 1', 163, 20)
    grid_label_and_control_mmc(ctrl)

    grid_separator(page)

    ctrl = MMC_IP_Port(page, 'ip:port 2', 183)
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_String(page, 'APN 2', 204, 20)
    grid_label_and_control_mmc(ctrl)


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

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Вход задействован')
        grid_control(ctrl, sticky='w')

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Антидребезг', ctrl, column=2) # 500 ms

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Задержка срабатывания', ctrl) # 0

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Задержка восстановления', ctrl, column=2) # 0

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='SMS рассылка') # off
        grid_control(ctrl, sticky='w')

        # Тип зоны - Только под охраной, 24х часовая
        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='24х часовой')
        grid_control(ctrl, column=2, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='управление PGM1') # off
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='управление PGM2') # off
        grid_control(ctrl, column=2, sticky='w')

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Команда срабатывания', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Команда восстановления', ctrl, column=2)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Район', ctrl) # 00-99, default 00

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Пользователь', ctrl, column=2) # 000-999, 000

        grid_separator(frame, False)


    page = add_tab('PGM', 'Конфигурация программируемых выходных сигналов (PGM)')

    container = page

    for i in range(2):
        frame = tk.LabelFrame(container, text=f'PGM{i + 1}')
        grid_control(frame, pady=5)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='PGM задействован')
        grid_control(ctrl, sticky='w')

        # Режим работы: Потенциальный Импульсный
        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Импульсный')
        grid_control(ctrl, sticky='w')

        # Тип выхода: Нормально разомкнут, Нормально замкнут
        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Нормально разомкнут')
        grid_control(ctrl, column=2, sticky='w')

        # только в импульсный режим
        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Длительность при срабатывании', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Длительность при восстановлении', ctrl, column=2)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Длительность при постановке/снятии', ctrl)

        # ctrl = tk.Entry(frame)
        # grid_label_and_control(frame, 'При снятии (импульсный)', ctrl, column=2)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Программируемый через СМС')
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Зависимый от входов')
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
