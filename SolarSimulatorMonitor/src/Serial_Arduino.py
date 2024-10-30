"""
File: Serial_Arduino.py
Author: Simone Pilon - Noël Research Group - 2023
GitHub: https://github.com/simone16
Description: Interface for controlling arduino-based serial devices.
"""

import serial
from threading import Lock
from time import sleep
from Common_Device import MonitorDevice


class Arduino(MonitorDevice):
    """Handles communication with an arduino-based device via serial port.
    To be able to fully take advantage of this class, the arduino device must comply with the following protocol:

        Support the following commands:
            `Sx=y`  Where x is an integer identifier for a variable/command and y a value of type integer,
                    floating point or string. In case y is of type string, a newline character must terminate the
                    command, in the other cases a newline can terminate the command, but it does not have to.
                    No response is expected after this command is sent.
            `Rx`    Where x is an integer identifier for a variable. The arduino device must respond with the value of x
                    or provide some other response. The response must terminate with a newline character.
                    Any trailing whitespace is removed from the response.
        All device functionalities should be accessible by reading or writing one of the variables (identified by the
        integer x). The user can extend the class with additional methods to handle communications outside of this
        protocol.

        General variables:
            Some variables are expected to be the same across all devices:
                Name    Number 	Acccess 	Type 	        Description
                -       0 	    RESERVED 	NONE 	        Do not use x=0.
                ID      1 	    READ/WRITE 	STRING [20] 	Device identifier.

        Usage:
            It is recommended to create a child class for every Arduino device which inherits from this.
            In the constructor, call 'add_variable' for each variable you wish to implement (note: numer 1 is
            implemented by default and 0 should not be used).

    Thread-safe: multiple threads can access this class and write at the same time, to keep track of which response is
    meant for which thread, a lock prevents concurrent access (the thread will pause until the previous thread receives
    a response)."""

    def __init__(self):
        MonitorDevice.__init__(self)

        self.generic_name = 'Arduino'

        self._serial_iface = serial.Serial()
        self._serial_iface.baudrate = 9600
        self._serial_iface.timeout = 1
        self._serial_iface.write_timeout = 1

        self._thread_lock = Lock()  # Threading lock required to access the serial interface.

        self._variables = {}
        self._access_R = ('r', 'R')
        self._access_W = ('w', 'W')
        self._access_RW = ('rw', 'RW')
        self.add_variable('ID', 1, 'rw', 'str', 'Device identifier')

    def __del__(self):
        if self.is_open():
            self.close()

    def add_variable(self, name: str, variable_number: int, access: str, variable_type: str, description: str = '')\
            -> None:
        """Adds a variable to the serial communication protocol for this device.

        :param name: str
            This name will be used to identify the variable.
        :param variable_number: int
            The number identifying the variable in the Arduino device.
        :param access: str
            Access type of the variable, accepted values are:
                'r', 'R' for READ_ONLY
                'w', 'W' for WRITE_ONLY (or COMMAND)
                'rw', 'RW' for READ/WRITE
        :param variable_type: str
            Expected type returned by reading the variable and used for writing, accepted values are:
                'int' integer number
                'float' floating point number
                'str' string
                'none' nothing is returned or set
        :param description: str
            An optional description."""
        if name in self._variables.keys():
            self.logger(f"{self.complete_name}: overriding variable '{name}'.")
        if variable_number <= 0:
            self.logger(f"{self.complete_name}: attempting to add invalid variable number: '{variable_number}'",
                        error=True)
            return
        for variable in self._variables.values():
            if variable_number == variable['number']:
                self.logger(f"{self.complete_name}: attempting to add duplicate variable number: '{variable_number}'",
                            error=True)
                return

        _access = ''
        if access in self._access_R:
            _access = 'r'
        elif access in self._access_W:
            _access = 'w'
        elif access in self._access_RW:
            _access = 'rw'
        else:
            self.logger(f"{self.complete_name}: attempting to add variable with invalid access: '{access}'",
                        error=True)
            return
        if variable_type not in ('int', 'float', 'str', 'none'):
            self.logger(f"{self.complete_name}: attempting to add variable with invalid type: '{variable_type}'",
                        error=True)
            return
        self._variables[name] = {'number': variable_number,
                                 'access': _access,
                                 'type': variable_type,
                                 'description': description}

    @property
    def variables(self) -> list:
        """A list of supported variable names complete with description.

        :return: list
            A list of (name, access, type, description) tuples listing the supported variable names."""
        return [(name,
                 self._variables[name]['access'],
                 self._variables[name]['type'],
                 self._variables[name]['description']) for name in self._variables.keys()]

    def flush_buffer_in(self) -> str:
        """Read everything from the incoming buffer and return it as a string.

        :return: str
            The contents of the incoming data buffer."""
        bytes_to_read = self._serial_iface.in_waiting
        if bytes_to_read > 0:
            return self._serial_iface.read(bytes_to_read).decode('ascii')
        return ''

    def read_variable(self, name: str) -> int | float | str:
        """Sends a command to the device, returns the response.

        :param name: str
            The name of the variable to be written.
            For a list of variables see self.variables.
        :return: int | float | str
            The value of the variable."""
        if name not in self._variables.keys():
            self.logger(f"{self.complete_name}: unknown variable name: '{name}'", error=True)
            return 0
        return_value = 0
        if self._variables[name]['type'] == 'float':
            return_value = 0.0
        elif self._variables[name]['type'] == 'str':
            return_value = ''
        if self._variables[name]['access'] in self._access_W:
            self.logger(f"{self.complete_name}: variable '{name}' is write-only.", error=True)
            return return_value
        with self._thread_lock:
            try:
                buf = self.flush_buffer_in()
                if buf:
                    self.logger(f"{self.complete_name} received unexpected data: '{buf}'", error=True)
                command = f"R{self._variables[name]['number']}\n"
                self._serial_iface.write(command.encode('ascii'))
                read_value = self._serial_iface.readline().decode('ascii')
                if read_value == '':
                    return return_value
                return_value = read_value
                if self._variables[name]['type'] == 'float':
                    return float(return_value)
                elif self._variables[name]['type'] == 'int':
                    return int(return_value)
                elif self._variables[name]['type'] == 'str':
                    return return_value.rstrip()
                else:
                    return return_value
            except (serial.SerialException, ValueError) as e:
                self.logger(str(e))
                self.logger(f"{self.complete_name} failed to read variable '{name}'", error=True)
        return return_value

    def write_variable(self, name: str, value: int | float | str | None) -> None:
        """Writes the desired value to a variable within the device.

        :param name: str
            The name of the variable to be written.
            For a list of variables see self.variables.
        :param value: int | float | str | None
            The value of the variable."""
        if name not in self._variables.keys():
            self.logger(f"{self.complete_name}: unknown variable name: '{name}'", error=True)
            return
        if self._variables[name]['access'] in self._access_R:
            self.logger(f"{self.complete_name}: attempt to write read-only variable '{name}'.", error=True)
            return
        with self._thread_lock:
            try:
                buf = self.flush_buffer_in()
                if buf:
                    self.logger(f"{self.complete_name} received unexpected data: '{buf}'", error=True)
                if value is None or self._variables[name]['type'] == 'none':
                    value = ''
                command = f"S{self._variables[name]['number']}={value}\n"
                self._serial_iface.write(command.encode('ascii'))
            except (serial.SerialException, ValueError) as e:
                self.logger(str(e))
                self.logger(f"{self.complete_name}: failed to write variable '{name}'", error=True)

    def open(self, comport: str) -> None:
        """Connects to the device. The connection must open before data can be sent or received.

        :param comport: str
            Identifier of the serial port to which the device is connected."""
        self.close()
        with self._thread_lock:
            self._serial_iface.port = comport
            try:
                self._serial_iface.open()
                # Opening the serial communication with Arduino causes a reset of the arduino board.
                # As a result, immediately trying to read/write locks up everything. This is a known issue
                # which seems to have no other solution than waiting for the reset to complete (or preventing the
                # reset line from activating, but this prevents writing to program memory).
                sleep(2)
                self.logger(f"Connected to {self.complete_name} on {self._serial_iface.port}.")
            except (serial.SerialException, ValueError) as e:
                self.logger(str(e))
                self.logger(f"Failed to connect to {self.complete_name} on {self._serial_iface.port}.", error=True)

    def is_open(self) -> bool:
        """Check whether the connection is open.

        :return: bool
            True if the connection is open."""
        return self._serial_iface.is_open

    def close(self) -> None:
        """Disconnects the device."""
        try:
            if self._serial_iface.is_open:
                with self._thread_lock:
                    self._serial_iface.close()
        except (serial.SerialException, ValueError) as e:
            self.logger(f"Failed to close connection to {self.complete_name} on {self._serial_iface.port}.", error=True)
            self.logger(str(e), error=True)
