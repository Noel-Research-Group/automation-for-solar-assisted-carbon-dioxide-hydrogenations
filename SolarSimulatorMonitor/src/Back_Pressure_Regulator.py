"""
File: Back_Pressure_Regulator.py
Author: Simone Pilon - Noël Research Group - 2023
GitHub: https://github.com/simone16
Description: Interface for controlling arduino-based adjustable back pressure regulator.
"""

from Serial_Arduino import Arduino


class BackPressureRegulator(Arduino):
    """Handles communication with an adjustable back pressure regulator device.
    This device is documented in detail at https://github.com/Noel-Research-Group/variable_BPR ."""

    def __init__(self):
        Arduino.__init__(self)

        self.generic_name = "Back Pressure Regulator"
        self.units = 'Bar'
        self.units_prefix = ' '
        self.pv_name = 'Pressure'

        self.pv_deviation_allowed = 0.2
        self.pv_set_max = 50.0
        self.pv_set_min = 0.0

        self.has_pv = True
        self.has_enable = True

        self.add_variable('enable',
                          2,
                          'rw',
                          'int',
                          'Enable automatic back pressure adjustment')
        self.add_variable('setpoint',
                          3,
                          'rw',
                          'float',
                          'Pressure setpoint [Bar, relative]')
        self.add_variable('pressure',
                          4,
                          'r',
                          'float',
                          'Pressure measured [Bar, relative]')
        self.add_variable('valve_position',
                          5,
                          'r',
                          'int',
                          'Absolute valve position [0-1024]')
        self.add_variable('calibration_1',
                          6,
                          'w',
                          'float',
                          'Begin calibration procedure [Bar, relative]')
        self.add_variable('calibration_2',
                          7,
                          'w',
                          'float',
                          'End calibration procedure [Bar, relative]')
        self.add_variable('set_minimum',
                          8,
                          'w',
                          'none',
                          'Set current valve position as minimum')
        self.add_variable('set_maximum',
                          9,
                          'w',
                          'none',
                          'Set current valve position as maximum')
        self.add_variable('move',
                          10,
                          'w',
                          'int',
                          'Move valve actuator by this many steps')

    def write_sp(self, pressure: float) -> None:
        """Sends a command to change the desired target pressure for the regulator.

        :param pressure: float
            desired relative pressure in Bar."""
        self.write_variable('setpoint', pressure)

    def read_sp(self) -> float:
        """Read the current target pressure of the device.

        :return: float
            current relative pressure setpoint in Bar."""
        return self.read_variable('setpoint')

    def read_pv(self) -> float:
        """Sends a command to request current pressure reading from the device and returns it.

        :return: float
            Relative pressure in Bar as measured by device."""
        return self.read_variable('pressure')

    def write_onoff(self, on: bool) -> None:
        """Write a command to the device to enable automatic valve adjustment.
        When enabled, the device will operate its valve to achieve the desired back-pressure.

        :param on: bool
            If True, the device is enabled, if False it is disabled."""
        self.write_variable('enable', 1 if on else 0)

    def read_onoff(self) -> bool:
        """Read whether device is enabled or not.

        :return: bool
            Returns True if the device is enabled."""
        return self.read_variable('enable') == 1

    def set_calibration_point_1(self, pressure: float) -> None:
        """Set the expected pressure reading for the current status of the sensor.
        This value can be read on the instrument display.
        Note: this will have no effect until the second calibration point is set.

        :param pressure: float
            The current pressure measured in the system in Bar."""
        self.write_variable('calibration_1', pressure)

    def set_calibration_point_2(self, pressure: float) -> None:
        """Set the expected pressure reading for the current status of the sensor.
        This value can be read on the instrument display.
        Note: this should be called after 'set_calibration_point_1' and with different pressure conditions. The larger
        the difference the more accurate the calibration is.
        Once this is called, the new calibration values are used when reading pressure.

        :param pressure: float
            The current pressure measured in the system in Bar."""
        self.write_variable('calibration_2', pressure)
