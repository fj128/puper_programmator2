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

    page = add_tab('Параметры', 'Основные параметры')

    ctrl = MMC_BCD(page, 'Номер устройства', 0, 4)
    grid_label_and_control_mmc(ctrl)

    MMC_FixedByte(2)

    ctrl = MMC_Choice(page, 'Тип панели', 3, [2, 1, 0], {
        0: 'Коммуникатор',
        1: 'DALLAS',
        2: 'ADEMCO',
        3: 'MAGELAN'})
    grid_label_and_control_mmc(ctrl)


    ctrl = MMC_Int(page, 'Период тестовой посылки (сек)', [4, 5])
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_BCD(page, 'Тестовая посылка', 6, 7) # TODO: 7 can't be right
    grid_label_and_control_mmc(ctrl)

    ctrl = MMC_Choice(page, 'Рассылка на IP адреса', 3, [5, 4, 3], {
        0b100: 'IP 1',
        0b010: 'IP 2',
        0b110: 'Основной/резервный',
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
        grid_label_and_control(frame, 'Антидребезг', ctrl, column=2)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Время срабатывания', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Время восстановления', ctrl, column=2)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='SMS рассылка')
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='24х часовой')
        grid_control(ctrl, column=2, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Выход 1 управляется')
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Выход 2 управляется')
        grid_control(ctrl, column=2, sticky='w')

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Команда тревоги', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Команда восстановления', ctrl, column=2)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Раздел', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Пользователь', ctrl, column=2)

        grid_separator(frame, False)


    page = add_tab('Выходы', 'Конфигурация программируемых выходных сигналов (PGM)')

    container = page

    for i in range(2):
        frame = tk.LabelFrame(container, text=f'Выход №{i + 1}')
        grid_control(frame, pady=5)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Выход задействован')
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Импульсный')
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Нормально разомкнут')
        grid_control(ctrl, column=2, sticky='w')

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Длительность при постановке', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Длительность при снятии', ctrl, column=2)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'При постановке (импульсный)', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'При снятии (импульсный)', ctrl, column=2)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Программируемый через СМС')
        grid_control(ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Зависимый от входов')
        grid_control(ctrl, column=2, sticky='w')

        grid_separator(frame, False)

    page = add_tab('СМС', 'Список телефонов для рассылки СМС')
    for i in range(10):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Телефон №{i + 1}', ctrl, pady=5)

    page = add_tab('Телефоны', 'Белый список телефонов пользователей и права')
    container = tk.Frame(page)
    grid_control(container)

    for i in range(10):
        row = next_grid_row(container, 0)
        ctrl = tk.Entry(container)
        grid_label_and_control(container, f'Телефон №{i + 1}', ctrl)

        ctrl = tk.Entry(container)
        grid_label_and_control(container, f'PIN', ctrl)

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
