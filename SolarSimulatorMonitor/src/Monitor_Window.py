# GUI to monitor and control the solar simulator setup interactively.
# This file contains classes for most of the GUI, main window, BPR calibration and device panels.
#
# Author: Simone Pilon - Noël Research Group - 2023

# GUI with tkinter
import tkinter as tk
from tkinter import ttk
import tkinter.messagebox
from tkinter import scrolledtext
from PIL import ImageTk

# Graphs with matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# Serial devices
import Device_Configuration
import Back_Pressure_Regulator
import Solar_Light_Source
import Mass_Flow_Controller
# import Temperature_Control
from Default_Logger import print_message

from os import getcwd
import os.path
import time
import threading

# Automation GUI
import Schedule
import Temperature_Control
from Automation_Window import AutomationWindow


class MonitorWindow(tk.Tk):
    """A tkinter root with specific behaviour to control the solar simulator devices and show realtime data from
    them."""

    def __init__(self, device_configuration):
        """Creates the main window of the Solar Simulator Monitor.

        :param device_configuration: list
            List of devices which should be monitored by this window, see Device_Configuration."""
        super().__init__()

        self.project_root = getcwd()
        self.iconphoto(True, MonitorWindow.get_icon())

        self.title("Solar Simulator - Interactive Control")
        self.geometry("1200x850")
        self._text_font = tk.font.nametofont('TkTextFont')
        self._text_font['size'] = 12

        self.update_interval = 1.0  # Interval between continuous updates [S].

        self._left_frame = ttk.Panedwindow(master=self, orient=tk.VERTICAL)
        self._left_frame.grid(column=0, row=0, sticky='N')
        self._right_frame = ttk.Frame(master=self)
        self._right_frame.grid(column=1, row=0)
        self._bottom_frame = ttk.Frame(master=self, height=500)
        self._bottom_frame.grid(column=0, row=1, columnspan=2, sticky='EW')
        self.columnconfigure(index=0, weight=0)
        self.columnconfigure(index=1, weight=1)
        self.rowconfigure(index=0, weight=1)
        self.rowconfigure(index=1, weight=0)

        self._menu_bar = tk.Menu(self)
        self.config(menu=self._menu_bar)
        self._menu_file = tk.Menu(self._menu_bar, tearoff=0)
        self._menu_file.add_command(label='exit', command=self.destroy)
        self._menu_bar.add_cascade(label='File', menu=self._menu_file, underline=0)
        self._menu_tools = tk.Menu(self._menu_bar, tearoff=0)
        self._menu_tools.add_command(label='Calibrate BPR', command=self._calibrate_bpr)
        self._menu_tools.add_command(label='Autotune PID (T)', command=self._autotune_t_control)
        self._menu_tools.add_command(label='Automation', command=self._open_automation_window)
        self._menu_bar.add_cascade(label='Tools', menu=self._menu_tools, underline=0)
        self._menu_info = tk.Menu(self._menu_bar, tearoff=0)
        self._menu_info.add_command(label='info', command=self.show_info)
        self._menu_bar.add_cascade(label='Info', menu=self._menu_info, underline=0)
        self._menu_tools.entryconfig('Calibrate BPR', state='disabled')
        self._menu_tools.entryconfig('Autotune PID (T)', state='disabled')

        self._add_log_pane()
        self._file_data_log = self._get_data_log_path()

        # The following are defined and used when the automation window pops up
        self._window_automation = None

        # The following are defined when the calibration window pops up.
        self._device_bpr = None
        self._window_bpr_cal = None
        self._field_calibration_1 = None
        self._field_calibration_2 = None

        # The following are defined to perform PID autotune.
        self._device_t_control = None
        self._autotune_is_running = False

        self._device_panes = []
        try:
            for device in device_configuration:
                self.add_device(device['type'], device['comport'])
        except KeyError as e:
            self.print_log(str(e), error=True)

        self._add_plot_area()

        # Automation schedule data
        self._automation_schedule = Schedule.Schedule(self, [devicepane.device for devicepane in self._device_panes])
        self._automation_schedule.logger = self.print_log

        self._time_0 = time.time()
        self._updating_status = False
        self._thread_update = threading.Thread(target=self._update_status_loop)
        self._thread_update.name = 'Continuous update thread'
        self._thread_update.daemon = True

    @staticmethod
    def get_icon():
        project_root = getcwd()
        try:
            icon = tk.PhotoImage(file=os.path.join(project_root, 'imgs', 'NRG_icon.png'))
            return icon
        except Exception as e:
            print(e)
            print("Could not open icon file.")

    def destroy(self):
        """Override parent destroy function to close all serial communications."""
        if self._thread_update.is_alive():
            self._updating_status = False
            self._thread_update.join(self.update_interval * 3)
        for device_pane in self._device_panes:
            if device_pane.device:
                if device_pane.device.is_open():
                    if device_pane.device.has_enable:
                        device_pane.device.write_onoff(False)
                    else:
                        device_pane.device.write_sp(0.0)
                    device_pane.device.close()
        super().destroy()

    def mainloop(self, **kwargs):
        """Override parent mainloop to start update thread."""
        self._updating_status = True
        self._thread_update.start()
        super().mainloop()

    def _get_data_log_path(self):
        """Initialize the log files."""
        datadir = os.path.join(self.project_root, 'data')
        if not os.path.isdir(datadir):
            os.mkdir(datadir)
        data_file_name = time.strftime('%Y-%m-%d_%H-%M_device_monitor_data_log.csv')
        data_file_path = os.path.join(datadir, data_file_name)
        if os.path.isfile(data_file_path):
            self.print_log('Cannot save data to log, file already exists!', error=True)
            self.print_log(f"Filename: {data_file_path}", error=True)
            return None
        return data_file_path

    def add_device(self, devicetype: str, comport: str):
        """Connects the window to a device.

            :param devicetype: str
                The type of device which needs to be connected (see
                Device_Configuration.DeviceConfiguration.DEVICE_TYPES for a list of available devices).
            :param comport: str
                Identifier of the serial port the device is connected to."""
        device_pane = DevicePane(master=self._left_frame, devicetype=devicetype, logger=self.print_log)
        device_pane.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        if comport:
            device_pane.connect_device(comport)
            if devicetype == 'Pressure':
                self._device_bpr = device_pane.device
                self._menu_tools.entryconfig('Calibrate BPR', state='normal')
            elif devicetype == 'Temperature':
                self._device_t_control = device_pane.device
                self._menu_tools.entryconfig('Autotune PID (T)', state='normal')
        else:
            self.print_log(f"{devicetype} device not found.", error=True)
            device_pane.enable = False
        self._device_panes.append(device_pane)

    def _add_plot_subplot(self, device_pane):
        """Set up a subplot within the plotting area showing data from the device linked to a pane.

        :param device_pane: DevicePane
            The device pane linked to the device of interest."""
        datalen = 1000
        y_data = np.zeros(datalen)
        x_data = np.arange(start=-(datalen * self.update_interval)/60, stop=0, step=self.update_interval/60)
        x_data = x_data[0:datalen]

        device_pane.plot_axes = self._plot_figure.add_subplot(DevicePane.PLOT_INDEX_MAX, 1, device_pane.plot_index + 1,
                                                              frameon=False, ymargin=0, xmargin=0)
        device_pane.plot_axes.set_ylabel(device_pane.plot_label())
        device_pane.plot_line, = device_pane.plot_axes.plot(x_data, y_data)
        device_pane.plot_line.set(color=device_pane.plot_color())

    def _add_plot_area(self):
        """Set up the plotting area of the window."""
        self._plot_figure = Figure(figsize=(20, 10), dpi=100)
        self._plot_figure.subplots_adjust(left=0.125, bottom=0.08, right=0.99, top=0.99, wspace=0, hspace=0)
        self._plots = []

        for device_pane in self._device_panes:
            if device_pane.plot_index >= 0:
                self._add_plot_subplot(device_pane)

        device_panes = []
        for device_pane in self._device_panes:
            if device_pane.plot_index >= 0:
                device_panes.append(device_pane)
        device_panes.sort(key=lambda d_pane: d_pane.plot_index)
        for i in range(1, len(device_panes)):
            device_panes[i].plot_axes.sharex(device_panes[i - 1].plot_axes)
        device_panes[-1].plot_axes.set_xlabel('Time [min]')

        self._plot_canvas = FigureCanvasTkAgg(self._plot_figure, master=self._right_frame)
        self._plot_canvas.draw()
        self._plot_canvas.get_tk_widget().pack(fill=tk.BOTH)

    def _add_plot_datapoint(self, device_pane, dp_time, dp_pressure):
        """Update each plot with an additional data-point."""
        x_data = device_pane.plot_line.get_xdata()
        y_data = device_pane.plot_line.get_ydata()
        x_data = np.append(x_data, dp_time)
        x_data = np.delete(x_data, [0])
        y_data = np.append(y_data, dp_pressure)
        y_data = np.delete(y_data, [0])
        device_pane.plot_line.set_xdata(x_data)
        device_pane.plot_line.set_ydata(y_data)
        device_pane.plot_axes.set_xlim(x_data[0], x_data[-1])
        device_pane.plot_axes.set_ylim(-0.1, max(y_data) + 0.5)
        self._plot_canvas.draw()
        self._plot_canvas.flush_events()

    def _add_log_pane(self):
        """Set up the logging area at the bottom of the window."""
        self._info_log = scrolledtext.ScrolledText(master=self._bottom_frame, font=self._text_font, height=6)
        self._info_log.tag_config('error', foreground='red')
        self._info_log.configure(state='disabled')
        self._info_log.pack(fill=tk.X)

    def print_log(self, message: str, **kwargs):
        """Print a message in the logging area at the bottom of the window. A timestamp is automatically added
        to the message.

        :param message: str
            The message to be given to the user.
        :param kwargs:
            See below.

        :Keyword Arguments:
            * error (``bool``) --
              If true the message will be highlighted as an error."""
        message = f"{time.strftime('%H:%M:%S')} {message}\n"
        self._info_log.configure(state='normal')
        if ('error' in kwargs.keys()) and kwargs['error']:
            self._info_log.insert(tk.END, message, 'error')
        else:
            self._info_log.insert(tk.END, message)
        self._info_log.configure(state='disabled')
        self._info_log.yview_moveto(1.0)
        print(message.rstrip())

    @staticmethod
    def show_info():
        """Display a popup with information about the program."""
        tk.messagebox.showinfo(title="Info", message="""Solar Simulator Monitor is a visual tool to control the 
        various devices which make up the Solar Simulator setup interactively or by setting a schedule for different 
        conditions to be applied at time intervals.

        Author: Simone Pilon - Noël Research Group - 2023.""")

    def _open_automation_window(self):
        """Opens the window to access the schedule for running different reaction conditions in sequence."""
        self._window_automation = AutomationWindow(self._automation_schedule)

    def _calibrate_bpr(self):
        """Starts a visual procedure for the calibration of the variable back pressure regulator pressure sensing.
        Pressure data is transferred within the device as an analog voltage which may need to be manually calibrated
        to ensure the same value is given by the sensor and the device."""
        self._window_bpr_cal = tk.Toplevel()
        photoimage = ImageTk.PhotoImage(file=os.path.join(self.project_root, 'imgs', 'BPR_sensor.png'))
        image = ttk.Label(master=self._window_bpr_cal, image=photoimage, text='blabla')
        image.grid(column=0, row=0, rowspan=3)
        image.image = photoimage
        explanation = ttk.Label(master=self._window_bpr_cal,
                                text='Fill in the pressure values as read from the device sensor display (see '
                                     'picture), then press enter.\nStart from a higher pressure value around 4 or 5 '
                                     'Bar and end with a lower value, such as 1.5 Bar.\nTwo points are needed for the '
                                     'calibration.')
        explanation.grid(column=1, row=0, columnspan=2, padx=10, pady=3)
        text1 = ttk.Label(master=self._window_bpr_cal, text='Pressure low [Bar]:')
        text1.grid(column=1, row=1, padx=10, pady=3)
        self._field_calibration_1 = ttk.Entry(master=self._window_bpr_cal, font=self._text_font)
        self._field_calibration_1.bind('<Return>', self._calibrate_bpr_point1)
        self._field_calibration_1.grid(column=2, row=1, padx=10, pady=6)
        text2 = ttk.Label(master=self._window_bpr_cal, text='Pressure high [Bar]:')
        text2.grid(column=1, row=2, padx=10, pady=3)
        self._field_calibration_2 = ttk.Entry(master=self._window_bpr_cal, font=self._text_font)
        self._field_calibration_2.configure(state='disabled')
        self._field_calibration_2.bind('<Return>', self._calibrate_bpr_point2)
        self._field_calibration_2.grid(column=2, row=2, padx=10, pady=6)

    def _calibrate_bpr_point1(self, event):
        """Set first point in the calibration procedure"""
        try:
            if self._field_calibration_1:
                pressure = float(self._field_calibration_1.get())
                self.print_log(self._device_bpr.set_calibration_point_1(pressure))
                self._field_calibration_1.configure(state='disabled')
                self._field_calibration_2.configure(state='normal')
        except ValueError:
            self.print_log('Error: enter a valid pressure for calibration!', error=True)

    def _calibrate_bpr_point2(self, event):
        """Set first point in the calibration procedure"""
        try:
            if self._field_calibration_2:
                pressure = float(self._field_calibration_2.get())
                self.print_log(self._device_bpr.set_calibration_point_2(pressure))
                self._window_bpr_cal.destroy()
        except ValueError:
            self.print_log('Error: enter a valid pressure for calibration!', error=True)

    def _autotune_t_control(self):
        """Starts PID autotune on temperature control device."""
        user_ok = tk.messagebox.askokcancel(title='Autotune', message="""The autotune procedure will be performed at the 
current setpoint temperature. If heating is disabled, it will be automatically enabled, make sure this is 
safe. If not, please press 'cancel'.""")
        if not user_ok:
            return
        self._device_t_control.write_onoff(True)
        self._device_t_control.start_autotune()
        self._autotune_is_running = True
        self._menu_tools.entryconfig('Autotune PID (T)', state='disabled')
        self.print_log('Started PID autotune on temperature control.')

    def _update_status_loop(self):
        """Target for a thread which constantly requests and updates the monitored values.
        It also reads the initial values which are not continuously monitored."""
        time.sleep(2.0)
        try:
            data_file = open(self._file_data_log, 'w')
        except IOError:
            data_file = None
            self.print_log('Cannot write to log file.', error=True)
        if data_file:
            data_file.write(f"\"Time [min]\"")
        if data_file:
            for device_pane in self._device_panes:
                data_file.write(f", \"{device_pane.value_label()}\"")
        if data_file:
            data_file.write('\n')
        while self._updating_status:
            current_time = round((time.time() - self._time_0)/60, 2)
            values = []
            active = False
            for device_pane in self._device_panes:
                if device_pane.plot_index >= 0 and device_pane.device.is_open():
                    current_value = device_pane.update_value()
                    values.append(current_value)
                    self._add_plot_datapoint(device_pane, current_time, current_value)
                if device_pane.device.has_enable:
                    if device_pane.value_on.get() == 1:
                        active = True
            if self._autotune_is_running:
                if not self._device_t_control.is_autotune_running():
                    self._autotune_is_running = False
                    self._menu_tools.entryconfig('Autotune PID (T)', state='normal')
                    self._device_t_control.save_ram_data()
                    self.print_log('Autotune finished.')
                    self.print_log(str(self._device_t_control.read_pid()))
            if data_file and active:
                data_file.write(str(current_time))
                for value in values:
                    data_file.write(f", {value}")
                data_file.write('\n')
            time.sleep(self.update_interval)
        if data_file:
            data_file.close()

    def change_device_sp_display_value(self, device, sp_value):
        """Changes the setpoint shown for a particular device, regardless of the device actual setpoint.

        :param device: CommonDevice
            The device whose setpoint has changed.
        :param sp_value: float
            The new setpoint to show."""
        for device_pane in self._device_panes:
            if device == device_pane.device:
                if device_pane.label_setpoint:
                    device_pane.label_setpoint['text'] = device_pane.value_with_units(sp_value)
                    device_pane._target_value = sp_value
                break

    def change_device_onoff_display_value(self, device, onoff_value):
        """Changes the onoff value shown for a particular device, regardless of the device actual state.

        :param device: CommonDevice
            The device whose onoff state has changed.
        :param onoff_value: bool
            True if the device should be shown as on."""
        for device_pane in self._device_panes:
            if device == device_pane.device:
                if device_pane.value_on:
                    value = 0
                    if onoff_value:
                        value = 1
                    device_pane.value_on.set(value)
                break


class DevicePane(ttk.Labelframe):
    """A tkinter ttk.Labelframe with specific behaviour to control and display data for a single device of the solar
    simulator setup. The type of device must be specified for the constructor via the 'devicetype' keyword argument.
    The available types are listed in Device_Configuration.DeviceConfiguration.DEVICE_TYPE ."""

    INFO = {'Light': {'class': Solar_Light_Source.SolarLightSource,
                      'on': 'Turn lights on',
                      'plot color': '#b5c306'},
            'Pressure': {'class': Back_Pressure_Regulator.BackPressureRegulator,
                         'on': 'Enable automatic vBPR',
                         'plot color': '#0343df'},
            'Temperature': {'class': Temperature_Control.TemperatureControl,
                            'on': 'Enable heating',
                            'plot color': '#fe4b03'},
            'Flow': {'class': Mass_Flow_Controller.MassFlowController,
                     'plot color': '#77ab56'}}
    PLOT_INDEX_MAX = 0  # Keeps count of how many plots needs to be created.

    def __init__(self, *args, **kwargs):
        if 'devicetype' not in kwargs:
            raise ValueError("Missing required argument 'devicetype'.")
        self._devicetype = kwargs['devicetype']
        if self._devicetype not in Device_Configuration.DeviceConfiguration.DEVICE_TYPE.keys():
            raise ValueError(f"{self._devicetype} is not a valid device type, check Device_Configuration.py and "
                             f"DevicePane.INFO.")
        if self._devicetype not in DevicePane.INFO.keys():
            raise ValueError(f"{self._devicetype} is not a valid device type, check Device_Configuration.py and "
                             f"DevicePane.INFO.")
        kwargs.pop('devicetype')

        self.logger = print_message
        if 'logger' in kwargs.keys():
            self.logger = kwargs['logger']
            kwargs.pop('logger')

        super().__init__(*args, **kwargs)

        self.device = DevicePane.INFO[self._devicetype]['class']()
        self.device.logger = self.logger

        if 'text' not in kwargs:
            self.configure(text=self.device.generic_name)

        self._entry_font = tk.font.nametofont('TkTextFont')
        self._entry_font['size'] = 10

        row_index = 0
        self.label_online = ttk.Label(master=self, text='offline')
        self.label_online.grid(column=0, row=row_index, columnspan=2, padx=10, pady=3)

        self.label_info = None
        self.label_reading = None
        if self.device.has_pv:
            row_index += 1
            self.label_info = ttk.Label(master=self, text=f"{self.device.pv_name}:")
            self.label_info.grid(column=0, row=row_index, padx=10, pady=3)

            self.label_reading = ttk.Label(master=self, text='-')
            self.label_reading.grid(column=1, row=row_index, padx=10, pady=3)

        row_index += 1
        info_text = 'Target:'
        if not self.device.has_pv:
            info_text = self.device.pv_name
        self.label_setpoint_info = ttk.Label(master=self, text=info_text)
        self.label_setpoint_info.grid(column=0, row=row_index, padx=10, pady=3)

        self.label_setpoint = ttk.Label(master=self, text='-')
        self.label_setpoint.grid(column=1, row=row_index, padx=10, pady=3)

        row_index += 1
        self.label_set_info = ttk.Label(master=self, text=f"Set target {self.device.pv_name.lower()}:")
        self.label_set_info.grid(column=0, row=row_index, padx=10, pady=3)

        self.field_set = ttk.Entry(master=self, font=self._entry_font)
        self.field_set.grid(column=1, row=row_index, padx=10, pady=3)
        self.field_set.bind('<Return>', self._handler_field_set)

        self.button_on = None
        self.value_on = None
        if self.device.has_enable:
            row_index += 1
            self.value_on = tk.IntVar()
            self.button_on = ttk.Checkbutton(master=self, text=DevicePane.INFO[self._devicetype]['on'],
                                             variable=self.value_on, command=self._handler_button_on)
            self.button_on.grid(column=0, row=row_index, columnspan=2, padx=10, pady=3)

        self.plot_index = -1
        self.plot_axes = None
        self.plot_line = None

        self._target_value = 0.0
        self._enabled = True

        if self.device.has_pv:
            self.plot_index = DevicePane.PLOT_INDEX_MAX
            DevicePane.PLOT_INDEX_MAX += 1

    @property
    def devicetype(self) -> str:
        return self._devicetype

    def connect_device(self, comport: str):
        """Connects to the physical device, this is required to send and receive data from the device.

        :param comport: str
            The serial port to on which the device is connected."""
        self.device.open(comport)
        if not self.device.is_open():
            self.logger(f"{self.device.complete_name}: Could not connect device on {comport}.", error=True)
            self.enable = False
            return
        self['text'] += ' '+self.device.specific_name
        self._target_value = self.device.read_sp()
        self.label_setpoint.configure(text=str(self._target_value) + self.device.units_prefix + self.device.units)
        if self.value_on:
            time.sleep(2)
            if self.device.read_onoff():
                self.value_on.set(1)
        self.enable = True

    @property
    def enable(self):
        return self._enabled

    @enable.setter
    def enable(self, enable):
        """Enables or disables the children widgets.

    :param enable: bool
        If true the widgets are enabled, otherwise they are disabled."""
        self._enabled = enable
        if enable:
            self.label_online.configure(text='online')
            if self.label_reading:
                self.label_info.configure(foreground='black')
                self.label_reading.configure(foreground='black')
            self.label_setpoint_info.configure(foreground='black')
            self.label_setpoint.configure(foreground='black')
            self.label_set_info.configure(foreground='black')
            self.field_set.configure(state='normal')
            if self.button_on:
                self.button_on.configure(state='normal')
        else:
            self.label_online.configure(text='offline')
            if self.label_reading:
                self.label_info.configure(foreground='grey')
                self.label_reading.configure(foreground='grey')
            self.label_setpoint_info.configure(foreground='grey')
            self.label_setpoint.configure(foreground='grey')
            self.label_set_info.configure(foreground='grey')
            self.field_set.configure(state='disabled')
            if self.button_on:
                self.button_on.configure(state='disabled')

    def plot_label(self):
        """Gives the text for the y-axis label of the plot for the linked device.

        :return: str
            A description of the y-axis values."""
        label = self.value_label()
        if len(label) > 10:
            label = label.replace(' ', '\n', 1)
        return label

    def value_label(self):
        """Gives the text for the label of the value for the linked device.

                :return: str
                    A description of the y-axis values."""
        space = ' '
        if self.device.specific_name == '':
            space = ''
        return f"{self.device.pv_name} {self.device.specific_name}{space}[{self.device.units}]"

    def plot_color(self) -> str:
        """Gives a color to use for the plot line based on devicetype.
        :return: str
            html hex stype color string."""
        return DevicePane.INFO[self._devicetype]['plot color']

    def update_value(self):
        """Reads the continuously monitored valued from the device and shows it on the pane.

        :return: float
            The value read from the device using default units (%, Bar, mln/min, °C)"""
        value = round(self.device.read_pv(), 2)
        self.label_reading.configure(text=self.value_with_units(value))
        if value >= self._target_value + self.device.pv_deviation_allowed:
            self.label_reading.configure(foreground='red')
        elif value <= self._target_value - self.device.pv_deviation_allowed:
            self.label_reading.configure(foreground='blue')
        else:
            self.label_reading.configure(foreground='black')
        return value

    def _handler_button_on(self):
        """Handler for the enable/disable button."""
        self.device.write_onoff(self.value_on.get() == 1)

    def _handler_field_set(self, event):
        """Handler for the value set field."""
        try:
            target_value = float(self.field_set.get())
        except ValueError:
            self.device.logger(f"Error: enter a valid {self.device.pv_name.lower()} value.", error=True)
            return
        if self.device.pv_set_min <= target_value <= self.device.pv_set_max:
            self.device.write_sp(target_value)
            self._target_value = target_value
            self.label_setpoint.configure(text=self.value_with_units(target_value))
            self.field_set.delete(0, tk.END)
        else:
            self.device.logger(f"Error: {self.device.pv_name} value out of range!", error=True)

    def value_with_units(self, value) -> str:
        """Returns a string with units along with the value.

        :return: str
            String of value with units."""
        return str(value) + self.device.units_prefix + self.device.units


class MultipleChoiceWindow(tk.Tk):
    """A tkinter root to select one out of a series of options."""

    def __init__(self, options):
        """Creates window for the multiple choice request.

        :param options: list
            List of available options."""
        if len(options) < 1:
            print('No available device configurations!')
            return

        super().__init__()

        self.title("Solar Simulator - Select device configuration")
        self.iconphoto(True, MonitorWindow.get_icon())
        self.choice = ''

        label_description = ttk.Label(master=self, text="""
Solar Simulator Monitor allows different experimental setups to be used. Select one from the available options.
The data regarding devices and experiment configurations is defined in the files within the 'config' sub-folder.
To avoid this message, select a device configuration from the command line (use argument -h for a list of options).""")
        label_description.pack(padx=10, pady=5)
        self._strvar_choice = tk.StringVar()
        box_choice = ttk.Combobox(master=self, values=options, textvariable=self._strvar_choice, state='readonly')
        self._strvar_choice.set(options[0])
        box_choice.pack(padx=10, pady=5)
        button_ok = ttk.Button(master=self, text='Ok', command=self._press_ok)
        button_ok.pack(padx=10, pady=5)
        self.grab_set()

    def _press_ok(self):
        self.choice = self._strvar_choice.get()
        self.destroy()
