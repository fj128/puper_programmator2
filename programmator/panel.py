import tkinter as tk
from tkinter import ttk
from programmator.utils import VerticalScrolledFrame, tk_set_list_maxwidth


def next_grid_row(parent, column):
    return parent.grid_size()[1] - (1 if column > 1 else 0)


def grid_label_and_control(parent, label_text, control, column=0, **kwargs):
    row = next_grid_row(parent, column)
    label = tk.Label(parent, text=label_text)
    label.grid(row=row, column=1 + column, padx=5, **kwargs)
    control.grid(row=row, column=2 + column, sticky='nsew', padx=5, **kwargs)


def grid_control(parent, control, column=0, **kwargs):
    row = next_grid_row(parent, column)
    control.grid(row=row, column=1 + column, columnspan=2, padx=5, **kwargs)


def grid_separator(parent, visible=True, columnspan=2):
    row = next_grid_row(parent, 0)
    separator = tk.Frame(parent, height=2, bd=visible, relief=tk.SUNKEN)
    separator.grid(row=row, column=1, columnspan=columnspan, pady=5, padx=0, sticky='nsew')


def create_widgets(tabs):
    def add_tab(name, header=None):
        page = ttk.Frame(tabs)

        tabs.add(page, text=name)
        page.columnconfigure(0, weight=1)
        page.columnconfigure(3, weight=1)

        if header:
            ctrl = tk.Label(page, text=header)
            grid_control(page, ctrl, pady=7)
            grid_separator(page)
        return page

    page = add_tab('Параметры', 'Основные параметры')

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'Номер устройства', ctrl)

    var = tk.StringVar(ctrl)
    options = ['Коммуникатор', 'DALLAS', 'ADEMCO', 'MAGELAN']
    ctrl = tk.OptionMenu(page, var, *options)
    tk_set_list_maxwidth(ctrl, options)
    var.set(options[0])
    grid_label_and_control(page, 'Тип панели', ctrl)

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'Период тестовой посылки', ctrl)

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'Тестовая посылка', ctrl)

    var = tk.StringVar(ctrl)
    options = ['IP 1', 'IP 2', 'Основной/резервный', 'Оба']
    ctrl = tk.OptionMenu(page, var, *options)
    tk_set_list_maxwidth(ctrl, options)
    var.set(options[0])
    grid_label_and_control(page, 'Рассылка на IP адреса', ctrl)

    var = tk.IntVar(ctrl)
    ctrl = tk.Checkbutton(page, variable=var, text='СМС на резервный номер 1')
    grid_control(page, ctrl)

    var = tk.IntVar(ctrl)
    ctrl = tk.Checkbutton(page, variable=var, text='СМС на резервный номер 2')
    grid_control(page, ctrl)

    grid_separator(page)

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'IP 1', ctrl)

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'хост 1', ctrl)

    grid_separator(page)

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'IP 2', ctrl)

    ctrl = tk.Entry(page)
    grid_label_and_control(page, 'хост 2', ctrl)

    ########

    page = add_tab('Входы', 'Конфигурация входных сигналов') #

    container = VerticalScrolledFrame(page)
    grid_control(page, container, sticky='nwse')
    # rowconfigure adds a row lol so do this after grid_control
    page.rowconfigure(2, weight=1)
    container = container.interior

    for i in range(10):
        frame = tk.LabelFrame(container, text=f'Вход №{i + 1}')
        grid_control(container, frame, pady=5)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Вход задействован')
        grid_control(page, ctrl, sticky='w')

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Антидребезг', ctrl, column=2)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Время срабатывания', ctrl)

        ctrl = tk.Entry(frame)
        grid_label_and_control(frame, 'Время восстановления', ctrl, column=2)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='SMS рассылка')
        grid_control(frame, ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='24х часовой')
        grid_control(frame, ctrl, column=2, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Выход 1 управляется')
        grid_control(frame, ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Выход 2 управляется')
        grid_control(frame, ctrl, column=2, sticky='w')

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
        grid_control(container, frame, pady=5)

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Выход задействован')
        grid_control(page, ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Импульсный')
        grid_control(frame, ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Нормально разомкнут')
        grid_control(frame, ctrl, column=2, sticky='w')

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
        grid_control(frame, ctrl, sticky='w')

        var = tk.IntVar(ctrl)
        ctrl = tk.Checkbutton(frame, variable=var, text='Зависимый от входов')
        grid_control(frame, ctrl, column=2, sticky='w')

        grid_separator(frame, False)

    page = add_tab('СМС', 'Список телефонов для рассылки СМС')
    for i in range(10):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Телефон №{i + 1}', ctrl, pady=5)

    page = add_tab('Телефоны', 'Белый список телефонов пользователей и права')
    container = tk.Frame(page)
    grid_control(page, container)

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
        grid_control(frame, ctrl)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='PGM2')
        grid_control(frame, ctrl, column=2)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='Arm/disarm')
        grid_control(frame, ctrl, column=4)

        var = tk.IntVar(frame)
        ctrl = tk.Checkbutton(frame, variable=var, text='Смена PIN')
        grid_control(frame, ctrl, column=6)

        grid_separator(container, columnspan=4)

    page = add_tab('Коды доступа', 'Коды доступа DALLAS/карточки')
    for i in range(16):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Код доступа №{i + 1}', ctrl, pady=5)

    page = add_tab('Сообщения', 'Текстовые сообщения пользователя')
    for i in range(16):
        ctrl = tk.Entry(page)
        grid_label_and_control(page, f'Сообщение №{i + 1}', ctrl, pady=5)

    page = add_tab('X-Ссылки?')


if __name__ == '__main__':
    from programmator.main import main
    main()
