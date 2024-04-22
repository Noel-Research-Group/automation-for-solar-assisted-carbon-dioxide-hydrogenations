# Base class for all devices that the solar simulator monitor interfaces with.
#
# Author: Simone Pilon - Noël Research Group - 2023

from Default_Logger import print_message


class MonitorDevice:
    """A generic parent class which defines functions and variables that the Solar Setup Monitor expects to be
    defined for every device. To ensure that a class controlling a device can interface with the Monitor correctly,
    inherit from this and overwrite all members and functions.

    Naming convention:
        - Process value (pv): The main value monitored (and measured) by the device.
        - Setpoint (sp): The value that the device will attempt to achieve for the pv.
        - on/off: A device is considered to be in the off state when it only measures the pv without altering any
          process conditions. If the device is always on, set self.has_enable to false."""

    def __init__(self):
        self.generic_name = ''  # Human readable name for the device type e.g.: Temperature controller.
        self.specific_name = ''  # Identifier for a specific device, useful if more of the same type are connected.
        self.pv_name = ''  # Name to identify the process value e.g.: Temperature.
        self.units = ''  # Units to display for the process and set value
        self.units_prefix = ''  # Prefix between value and units (e.g. a space or no space).

        self.pv_deviation_allowed = 1.0  # The GUI can display an error if the process value differs from the
        # setpoint by this amount
        self.pv_set_max = 100.0  # The GUI will not allow setting the setvalue above this threshold
        self.pv_set_min = 0.0  # The GUI will not allow setting the setvalue below this threshold

        self.has_pv = False  # True if the device can measure the process value (by calling read_pv)
        self.has_enable = False  # True if the device can be enabled (by calling write_onoff)

        self.logger = print_message  # This is a callable function which the device uses to print messages for the user.

    def open(self, comport: str) -> None:
        """Connects to the device. The connection must open before data can be sent or received.

        :param comport: str
            Identifier of the serial port to which the device is connected."""
        pass

    def is_open(self) -> bool:
        """Check whether the connection is open.

        :return: bool
            True if the connection is open."""
        return False

    def close(self) -> None:
        """Disconnects the device."""
        pass

    def read_pv(self) -> float | int:
        """Read process value of device.

        :return: float
            Process value read by device."""
        return 0.0

    def write_sp(self, sp: float | int) -> None:
        """Write the desired setpoint to the device.

        :param sp: float
            Desired setpoint."""
        pass

    def read_sp(self) -> float | int:
        """Read setpoint of device.

        :return: float
            Setpoint of device."""
        return 0.0

    def write_onoff(self, on: bool) -> None:
        """Write a command to the device to enable the setpoint setting (heating/light/pressure).

        :param on: bool
            If True, the device is turned on, if False it is turned off."""
        pass

    def read_onoff(self) -> bool:
        """Read whether device is on or off.

        :return: bool
            Returns True if the device is on."""
        return False

    @property
    def complete_name(self) -> str:
        """Combination of generic and specific name.

        :return: str
            A long name with both device generic and specific names."""
        name = self.generic_name
        if not self.specific_name == '':
            name += f" ({self.specific_name})"
        return name
