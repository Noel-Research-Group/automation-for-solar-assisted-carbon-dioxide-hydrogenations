# Interface for controlling arduino-based light source system of the solar simulator setup.
#
# Author: Simone Pilon - Noël Research Group - 2023

from Serial_Arduino import Arduino


class SolarLightSource(Arduino):
    """Handles communication with the light source of the solar simulator setup.
    The device is documented in detail at https://github.com/Noel-Research-Group/solar_simulator_controller ."""

    def __init__(self):
        Arduino.__init__(self)

        self.generic_name = 'Solar Light Source'
        self.specific_name = ''
        self.units = '%'
        self.units_prefix = ''
        self.pv_name = 'Light intensity'

        self.pv_deviation_allowed = 0.1
        self.pv_set_max = 100.0
        self.pv_set_min = 0.0

        self.has_pv = False
        self.has_enable = True

        self.add_variable('light_on',
                          2,
                          'rw',
                          'int',
                          'Lights On/_Off state')
        self.add_variable('fan_on',
                          3,
                          'rw',
                          'int',
                          'Fans On/_Off state')
        self.add_variable('lock_on',
                          4,
                          'rw',
                          'int',
                          'Manual interface lock On/_Off state')
        self.add_variable('intensity',
                          5,
                          'rw',
                          'int',
                          'Light intensity [%]')

    def write_sp(self, intensity) -> None:
        """Sends a command to change the light intensity. Intensity is expressed as integer percentage.
            According to the power supply datasheet intensity should not be set lower than 10%.

        :param intensity: float
            desired light intensity as percentage."""
        self.write_variable('intensity', intensity)

    def read_sp(self) -> float:
        """Sends a command to request the set light intensity (regardless of the light on/off state). Intensity is
        returned as a percentage.

        :return: float
            percentage light intensity."""
        return self.read_variable('intensity')

    def write_onoff(self, on: bool) -> None:
        """Write a command to the device to turn the lights on or off. The cooling fans will stay on until explicitly
        turned off when the lights are off.

        :param on: bool
            If True, the device is turned on, if False it is turned off."""
        self.write_variable('light_on', 1 if on else 0)

    def read_onoff(self) -> bool:
        """Read the lights on/off state.

        :return: bool
            Returns true if the lights are on."""
        return self.read_variable('light_on') == 1

    def fan_onoff(self, on: bool) -> None:
        """Sends a command to turn the cooling fans of the light source on or off.

        :param on: bool
            If set to true, the fans will be turned on, otherwise they will be turned off."""
        self.write_variable('fan_on', 1 if on else 0)

    def lock_interface(self, enable: bool) -> None:
        """Sends a command to lock the physical interface of the device. In the locked state, changing the state of the
        device is only allowed via serial interface, not the physical buttons.

        :param enable: bool
            If true the locking mode is enabled, if false it will be possible to change settings with the buttons."""
        self.write_variable('lock_on', 1 if enable else 0)
