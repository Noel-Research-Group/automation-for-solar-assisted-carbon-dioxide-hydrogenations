# Automation schedule storage and handling.
#
# Author: Simone Pilon - Noël Research Group - 2023

import threading
import pause

import Common_Device
import Default_Logger


class ScheduleParameter:
    """Contains information relative to a single parameter in the automation schedule."""

    def __init__(self):
        self.name = ''
        self.units = ''
        self.off_during_equilibration = False
        self.numeric = True
        self.read_only = False

        self._device = None

    @property
    def device(self) -> Common_Device.MonitorDevice:
        return self._device

    @device.setter
    def device(self, device: Common_Device.MonitorDevice):
        self.units = device.units
        self.name = f"{device.pv_name} {device.specific_name}"

        self._device = device

    @property
    def description(self):
        """Returns a complete description of the parameter.

        :return: str
            Parameter description."""
        description = self.name
        if not self.units == '':
            description += f" [{self.units}]"
        return description


class ScheduleRow:
    """Represents data from a single row (conditions) for the schedule."""

    def __init__(self, schedule):
        self._schedule = schedule
        self._parameter_values = {parameter: None for parameter in schedule.parameters}

    def __getitem__(self, parameter: ScheduleParameter | str) -> float | str:
        """Return the parameter value for this row.

        :param parameter: ScheduleParameter | str
            The parameter of which the value is needed, either as a reference or by name.
        :return:
            The value of the parameter.
        :raise: KeyError
            If the parameter does not match any in the schedule."""
        if isinstance(parameter, str):
            for parameter_key in self._parameter_values.keys():
                if parameter_key.name == parameter:
                    parameter = parameter_key
                    break
        if isinstance(parameter, str):
            raise KeyError(f"'{parameter}' does not match any parameter name!")
        return self._parameter_values[parameter]

    def __setitem__(self, parameter: ScheduleParameter | str, value: float | str):
        """Set a parameter value for this row.

        :param parameter: ScheduleParameter | str
            The parameter whose value should be changed, either as a reference or by name.
        :param value: float | str
            The value to assign"""
        if isinstance(parameter, str):
            for parameter_key in self._parameter_values.keys():
                if parameter_key.name == parameter:
                    parameter = parameter_key
                    break
        if isinstance(parameter, str):
            raise KeyError(f"'{parameter}' does not match any parameter name!")
        self._parameter_values[parameter] = value
        # if self._schedule.automation_window:
        #     if parameter.name == 'Status':
        #         self._schedule.automation_window.get_row(self._index).label_status.configure(text=value)
        #     elif not parameter.read_only:
        #         field = self._schedule.automation_window.get_row(self._index).fields[parameter]
        #         field.delete(0, tk.END)
        #         field.insert(0, value)

    def apply(self, equilibration: bool):
        """Applies the parameter values to the physical devices.

        :param equilibration: bool
            If True, some devices will be kept off (as specified by parameter.off_during_equilibration)."""
        for parameter in self._parameter_values.keys():
            if parameter.device:
                if not parameter.device.is_open():
                    self._schedule.logger(f"Cannot set parameter '{parameter.name}', device is not connected!",
                                          error=True)
                    continue
                if parameter.off_during_equilibration and equilibration:
                    if parameter.device.has_enable:
                        parameter.device.write_onoff(False)
                        self._schedule._monitor_window.change_device_onoff_display_value(parameter.device, False)
                    else:
                        parameter.device.write_sp(0.0)
                        self._schedule._monitor_window.change_device_sp_display_value(parameter.device,
                                                                                      0.0)
                else:
                    if parameter.device.has_enable and not parameter.device.read_onoff():
                        parameter.device.write_onoff(True)
                        self._schedule._monitor_window.change_device_onoff_display_value(parameter.device, True)
                    parameter.device.write_sp(self._parameter_values[parameter])
                    self._schedule._monitor_window.change_device_sp_display_value(parameter.device,
                                                                                  self._parameter_values[parameter])

    def keys(self):
        """Returns a list of keys (parameters) for this row."""
        return self._parameter_values.keys()


class Schedule:
    """Stores and keeps track of an ordered sequence of reaction conditions to run on the Solar Simulator Setup."""

    def __init__(self, monitor_window, devices):
        """Creates a schedule based on the given device configuration.

        :param monitor_window: Monitor_Window.MonitorWindow
            The main monitor window.
        :param devices: list of MonitorDevice objects
            List of devices which should be controlled by the schedule."""

        self._monitor_window = monitor_window

        self.parameter_status = ScheduleParameter()
        self.parameter_status.name = 'Status'
        self.parameter_status.numeric = False
        self.parameter_status.read_only = True
        self.parameter_title = ScheduleParameter()
        self.parameter_title.name = 'Title'
        self.parameter_title.numeric = False
        self.parameter_equilibration = ScheduleParameter()
        self.parameter_equilibration.name = 'Equilibration time'
        self.parameter_equilibration.units = 'min'
        self.parameter_duration = ScheduleParameter()
        self.parameter_duration.name = 'Duration'
        self.parameter_duration.units = 'min'

        self.parameters = [self.parameter_status,
                           self.parameter_title,
                           self.parameter_equilibration,
                           self.parameter_duration]

        for device in devices:
            device_parameter = ScheduleParameter()
            device_parameter.device = device
            if device.pv_name == "Light intensity":
                device_parameter.off_during_equilibration = True
            self.parameters.append(device_parameter)

        self._conditions = []

        self._iteration_index = 0
        self._running = False
        self._run_index = 0
        self._thread_run = None

        self.automation_window = None
        self.logger = Default_Logger.print_message

    @property
    def running(self):
        """Lets you know whether the automation schedule is running."""
        return self._running

    def start(self):
        """Starts the automation schedule thread."""
        self._thread_run = threading.Thread(target=self._update_conditions)
        self._thread_run.name = 'Automation Schedule Thread'
        self._thread_run.daemon = True
        self._thread_run.start()

    def stop(self):
        """Stops the automation schedule thread at the first opportunity."""
        self._running = False
        self._thread_run.join(2)
        self._thread_run = None
        self.safestate()

    def safestate(self):
        for parameter in self.parameters:
            if parameter.device is not None:
                if not parameter.device.is_open():
                    continue
                if parameter.device.has_enable:
                    parameter.device.write_onoff(False)
                    self._monitor_window.change_device_onoff_display_value(parameter.device, False)
                else:
                    parameter.device.write_sp(0.0)
                    self._monitor_window.change_device_sp_display_value(parameter.device, 0.0)

    def __iter__(self):
        """Start iterating.

        :return: self"""
        self._iteration_index = 0
        return self

    def __next__(self) -> ScheduleRow:
        """For each iteration, consecutive run conditions are returned.

        :return: ScheduleRow
            object with parameter -> value pairs."""
        if self._iteration_index >= len(self):
            raise StopIteration
        values = self[self._iteration_index]
        self._iteration_index += 1
        return values

    def __len__(self):
        """Number of conditions stored.

        :return: int
            The total number of conditions."""
        return len(self._conditions)

    def __getitem__(self, index: int) -> ScheduleRow:
        """Conditions for a determined run.

        :param index: int
            The index of the run.
        :return: ScheduleRow
            A list of parameter, values pairs as a ScheduleRow object."""
        return self._conditions[index]

    def pop(self, index: int = -1):
        """Remove reaction conditions from the schedule."""
        self._conditions.pop(index)

    def append(self) -> ScheduleRow:
        """Append an empty row of conditions to the schedule.

        :return: ScheduleRow
            The newly created conditions."""
        new_row = ScheduleRow(self)
        self._conditions.append(new_row)
        return new_row

    def _update_conditions(self):
        """This function is run as a separate thread to update the reaction conditions according to the schedule.
        self._running is checked when changing conditions and setting it to false will stop the thread. Keep in mind
        that this can take a long time to be checked."""
        self._run_index = 0
        self._running = True
        while self._run_index < len(self):
            self.logger('Running '+self._conditions[self._run_index][self.parameter_title])
            self._set_run_status(self._run_index, 'equilibrating')
            self._conditions[self._run_index].apply(equilibration=True)
            pause.minutes(self._conditions[self._run_index][self.parameter_equilibration])
            if not self.running:
                break
            self._set_run_status(self._run_index, 'running')
            self._conditions[self._run_index].apply(equilibration=False)
            pause.minutes(self._conditions[self._run_index][self.parameter_duration])
            self._set_run_status(self._run_index, 'done')
            self._run_index += 1
            if not self._running:
                break
        self.safestate()
        if self.automation_window:
            self.automation_window.enable_start(True)

    def _set_run_status(self, index: int, status: str):
        """Changes the status of a specific run condition and how it appears on the window.

        :param index: int
            The index of the run conditions.
        :param status: str
            The status to set the run to."""
        self._conditions[index][self.parameter_status] = status
        if self.automation_window:
            self.automation_window.get_row(index).label_status.configure(text=status)
