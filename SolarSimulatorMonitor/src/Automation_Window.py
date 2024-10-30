"""
File: Automation_Window.py
Author: Simone Pilon - Noël Research Group - 2023
GitHub: https://github.com/simone16
Description: Part of the GUI to monitor and control the solar simulator setup interactively.
"""

import tkinter as tk
from tkinter import ttk

import Schedule


class AutomationWindow(tk.Toplevel):
    """A tkinter toplevel window with specific behaviour to control the solar simulator automation schedule."""

    def __init__(self, schedule):
        """Opens the automation window. Data is retrieved from the schedule argument.

        :param schedule: Schedule.Schedule
            Schedule object holding the data for the sequence of reaction conditions."""
        super().__init__()

        self._schedule = schedule
        self._schedule.automation_window = self

        self.title("Solar Simulator - Automation Schedule")

        self._entry_font = tk.font.nametofont('TkTextFont')
        self._entry_font['size'] = 10

        self._menu_bar = tk.Menu(self)
        self.config(menu=self._menu_bar)
        self._menu_file = tk.Menu(self._menu_bar, tearoff=0)
        self._menu_file.add_command(label='Load...', command=self.destroy)
        self._menu_file.add_command(label='Save...', command=self.destroy)
        self._menu_file.add_command(label='Exit', command=self.destroy)
        self._menu_bar.add_cascade(label='File', menu=self._menu_file, underline=0)
        self._menu_file = tk.Menu(self._menu_bar, tearoff=0)
        self._menu_file.add_command(label='Start', command=self.start_schedule)
        self._menu_file.add_command(label='Stop', command=self.stop_schedule)
        self._menu_file.add_command(label='Reset', command=self.reset_schedule)
        self._menu_file.add_command(label='Add entry', command=self.add_row)
        self._menu_bar.add_cascade(label='Schedule', menu=self._menu_file, underline=0)
        if schedule.running:
            self._menu_file.entryconfig('Start', state='disabled')
        else:
            self._menu_file.entryconfig('Stop', state='disabled')

        self._main_frame = ttk.Frame(master=self)
        self._main_frame.pack()
        self._bottom_frame = ttk.Frame(master=self)
        self._bottom_frame.pack()
        self._message_to_user = ttk.Label(master=self._bottom_frame, text='')
        self._message_to_user.pack()

        column = 0
        headers = ['Action'] + [parameter.description for parameter in schedule.parameters]
        for title in headers:
            header_label = ttk.Label(master=self._main_frame, text=title)
            header_label.grid(column=column, row=0, padx=10, pady=3)
            column += 1

        self.rows = []

        self._button_addrow = ttk.Button(master=self._main_frame, text='Add', command=self.add_row)
        self._button_addrow.grid(column=0, row=1, padx=1, pady=3)

        for run_parameters in self._schedule:
            self.add_row(run_parameters)
        if len(self.rows) == 0:
            self.add_row()

    def destroy(self):
        """Override parent destroy function to update schedule."""
        try:
            self.update_fields_to_schedule()
        except (KeyError, ValueError) as e:
            self._message_to_user.configure(text=str(e))
        else:
            self._schedule.automation_window = None
            super().destroy()

    def start_schedule(self):
        """Starts the automation schedule."""
        self.update_fields_to_schedule()
        self.reset_schedule()
        self._schedule.start()
        self.enable_start(False)

    def stop_schedule(self):
        """Stops the automation schedule."""
        self._schedule.stop()
        self.enable_start(True)

    def reset_schedule(self):
        """Resets the schedule (all rows to 'ready'), so that it can be run again."""
        for run_condition in self._schedule:
            run_condition[self._schedule.parameter_status] = 'ready'
        for row in self.rows:
            row.label_status.configure(text='ready')

    def enable_start(self, enable):
        """Enables the schedule start buttons.

        :param enable: bool
            If true the schedule start button is enabled, the stop is disabled."""
        start_state = 'disabled'
        stop_state = 'normal'
        if enable:
            start_state = 'normal'
            stop_state = 'disabled'
        self._menu_file.entryconfig('Stop', state=stop_state)
        self._menu_file.entryconfig('Start', state=start_state)
        self._menu_file.entryconfig('Reset', state=start_state)

    def update_fields_to_schedule(self):
        """Reads all data from the window and updates the internal schedule object accordingly. Must be called to
        ensure data entered by the user is not lost on exiting the window or when running the schedule."""
        for row in self.rows:
            if not row._schedule_row:
                self._schedule.append()
                row._schedule_row = self._schedule[-1]
            row.update_to_schedule()
        while len(self._schedule) > WindowRow.MAX_INDEX:
            self._schedule.pop()

    def add_row(self, run_parameters: Schedule.ScheduleRow = None):
        """Adds a row of parameters.

        :param run_parameters: Schedule.ScheduleRow
            The parameters to be linked to this row.
            If none are specified, a new row is added to the Schedule."""
        if not run_parameters:
            run_parameters = self._schedule.append()
        new_row = WindowRow(parent=self, run_parameters=run_parameters)
        self.rows.append(new_row)

    def get_row(self, index: int):
        """Return the row with the requested index.

        :param index: int
            The index of the row (starting at 0)."""
        for row in self.rows:
            if row.index == index:
                return row


class WindowRow:
    """Collects all elements within a row of fields within the Automation Window."""
    MAX_INDEX = 0

    def __init__(self, parent: AutomationWindow, run_parameters: Schedule.ScheduleRow):
        """Adds a window row to the parent AutomationWindow.

        :param parent: AutomationWindow
            The Automation window that this row belongs to.
        :param run_parameters: Schedule.ScheduleRow
            The row in the schedule data this row is linked to."""
        self._row_index = WindowRow.MAX_INDEX
        WindowRow.MAX_INDEX += 1

        self._parent = parent
        self._schedule_row = run_parameters
        column = 0

        parent._button_addrow.grid(column=0, row=WindowRow.MAX_INDEX+1, padx=1, pady=3)

        self.button_remove = ttk.Button(master=parent._main_frame, text='Remove', command=self.remove)
        self.button_remove.grid(column=column, row=self._row_index+1, padx=1, pady=3)
        column += 1

        self.label_status = ttk.Label(master=parent._main_frame, text='ready')
        self.label_status.grid(column=column, row=self._row_index+1, padx=1, pady=3)
        column += 1

        self.fields = {}
        for parameter in self._schedule_row.keys():
            if not parameter.read_only:
                field = ttk.Entry(master=parent._main_frame, font=parent._entry_font)
                field.grid(column=column, row=self._row_index+1, padx=1, pady=3)
                self.fields[parameter] = field
                column += 1

        self.update_from_schedule()

    @property
    def index(self):
        return self._row_index

    def empty(self):
        """Is the row completely empty?

        :return: bool
            Returns true if the row is empty."""
        return all(field.get() == '' for field in self.fields.values())

    def update_from_schedule(self):
        """Populates this row with data from the corresponding row on the schedule."""
        for parameter in self._schedule_row.keys():
            if not parameter.read_only:
                self.fields[parameter].delete(0, tk.END)
                value = self._schedule_row[parameter]
                if value:
                    self.fields[parameter].insert(0, value)
        self.label_status.configure(text=self._schedule_row['Status'])

    def update_to_schedule(self):
        """Transfers all info in this row to the corresponding row on the schedule."""
        if self._schedule_row and not self.empty():
            for parameter in self.fields.keys():
                value = self.fields[parameter].get()
                if parameter.numeric:
                    value = float(value)
                self._schedule_row[parameter] = value

    def remove(self):
        """Remove this row from the window."""
        self.button_remove.destroy()
        self.label_status.destroy()
        for field in self.fields.values():
            field.destroy()
        WindowRow.MAX_INDEX -= 1
        self._parent._button_addrow.grid(column=0, row=WindowRow.MAX_INDEX+1, padx=1, pady=3)
