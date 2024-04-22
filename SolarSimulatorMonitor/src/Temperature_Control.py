# Wrapper for the Omron E5_C temperature control unit.
# Provides an interface with a similar feel to the other devices of Solar Simulator.
#
# Author: Simone Pilon - Noël Research Group - 2023
import pymodbus.exceptions

import e5_cregister
from mapped_modbus_client import MappedModbusClient
from e5_cregister import E5CRegisters
from threading import Lock
from Common_Device import MonitorDevice


class TemperatureControl(MonitorDevice):
    """Handles communication with the reactor temperature control of the solar simulator setup."""

    def __init__(self):
        self._modbus_client = None
        MonitorDevice.__init__(self)

        self.generic_name = 'Reactor Temperature'
        self.specific_name = ''
        self.units = '°C'
        self.units_prefix = ''
        self.pv_name = 'Temperature'

        self.pv_deviation_allowed = 0.5
        self.pv_set_max = 200.0
        self.pv_set_min = 0.0

        self.has_pv = True
        self.has_enable = True

        self._thread_lock = Lock()  # Threading lock required to access the serial interface.

    def __del__(self):
        self.close()

    @property
    def logger(self):
        return self._logger

    @logger.setter
    def logger(self, logger):
        self._logger = logger
        if self._modbus_client:
            self._modbus_client.logger = logger

    def open(self, comport: str):
        """Connects to the device. The connection must open before data can be sent or received.

        :param comport: str
            Identifier of the serial port to which the device is connected."""
        with self._thread_lock:
            try:
                self._modbus_client = MappedModbusClient(port=comport, registers=E5CRegisters, slave=1)
                if not self._modbus_client.connect():
                    self.logger(f"Could not connect to {self.complete_name} on {comport}.", error=True)
                else:
                    self._modbus_client.logger = self.logger
                    self._modbus_client.write_command('comm_write', 'ON')
                    self._modbus_client.write_command('write_mode', 'RAM_WM')
                    self._modbus_client.write_command('software_reset')
                    self._modbus_client.write_register('input_type', 'K_1')
                    # If another input type is used, make sure to check the decimal point position.
                    # print(self._modbus_client.read_register('decimal point monitor')[1])
                    self._modbus_client.write_register('pid_on_off', 'PID_CONTROL')
                    self.logger(f"Connected to {self.complete_name} on {comport}.")
            except pymodbus.exceptions.ModbusIOException as e:
                self.logger(f"Could not connect to {self.complete_name} on {comport} due to an error (continues).",
                            error=True)
                self.logger(str(e), error=True)
                self._modbus_client.disconnect()

    def is_open(self) -> bool:
        """Check whether the connection is open.

        :return: bool
            True if the connection is open."""
        if self._modbus_client:
            return self._modbus_client.connected
        else:
            return False

    def close(self):
        """Disconnects the device."""
        with self._thread_lock:
            if self._modbus_client:
                self._modbus_client.write_command('save_ram_data')
                self._modbus_client.disconnect()

    def read_status(self) -> e5_cregister.E5CStatus:
        """Reads the device status registers."""
        with self._thread_lock:
            return self._modbus_client.read_register('status')[1]

    def write_onoff(self, on: bool):
        """Write a command to the device to enable heating.

        :param on: bool
            If True, the device is turned on, if False it is turned off."""
        cmd = 'STOP'
        if on:
            cmd = 'RUN'
        with self._thread_lock:
            if self._modbus_client:
                self._modbus_client.write_command('run_stop', cmd)

    def read_onoff(self) -> bool:
        """Read whether heating is enabled or not.

        :return: bool
            Returns True if the device is on."""
        return e5_cregister.E5CStatus.STOP not in self.read_status()

    def write_sp(self, temperature: float):
        """Sets the temperature setpoint for the controller.

        :param temperature: float
            The desired temperature in °C."""
        with self._thread_lock:
            self._modbus_client.write_register('sp', temperature)

    def read_pv(self) -> float:
        """Reads the current reactor temperature.

        :return: float
            The temperature in °C."""
        with self._thread_lock:
            return self._modbus_client.read_register('pv')[1]

    def read_sp(self) -> float:
        """Reads the current target reactor temperature.

        :return: float
            The target temperature in °C."""
        with self._thread_lock:
            return self._modbus_client.read_register('sp')[1]

    def read_heating_power(self) -> float:
        """Reads the current applied heating.

        :return: float
            Heating power as %."""
        with self._thread_lock:
            return self._modbus_client.read_register('mvmonheat')[1]

    def start_autotune(self):
        """Starts the autotune AT100%"""
        with self._thread_lock:
            # self._modbus_client.write_command('software_reset')
            self._modbus_client.write_command('at_exec_cancel', 'AT_EXEC_100PCT')

    def is_autotune_running(self) -> bool:
        """Checks whether autotune is running.

        :return: bool
            True if autotune is still running."""
        return e5_cregister.E5CStatus.AT_EXEC_CANCEL in self.read_status()

    def read_pid(self):
        """Reads the PID values."""
        with self._thread_lock:
            pid_p = self._modbus_client.read_register('pid_p')[1]
            pid_i = self._modbus_client.read_register('pid_i')[1]
            pid_d = self._modbus_client.read_register('pid_d')[1]
            return {'P': pid_p, 'I': pid_i, 'D': pid_d}

    def save_ram_data(self):
        """Saves the current data from RAM to non-volatile device memory."""
        with self._thread_lock:
            self._modbus_client.write_command('save_ram_data')
