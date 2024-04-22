# Interface to Bronkhorst mass flow controller device (serial-through-USB).
#
# Author: Simone Pilon - Noël Research Group - 2023

import propar
from threading import Lock
from Common_Device import MonitorDevice


class MassFlowController(MonitorDevice):
    """Handles communication with Bronkhorst mass flow controller devices.
    Uses the Bronkhorst-propar library, wrapping the instrument class to provide a similar interface to other
    components of the solar simulator setup."""

    def __init__(self):
        MonitorDevice.__init__(self)

        self.generic_name = 'Mass Flow Controller'
        self.units = 'mLn/min'
        self.units_prefix = ' '
        self.pv_name = 'Flow'

        self.pv_deviation_allowed = 0.1
        self.pv_set_max = 20.0
        self.pv_set_min = 0.0

        self.has_pv = True
        self.has_enable = False

        self._instrument = None

        self._thread_lock = Lock()  # Threading lock required to access the serial interface.

    def open(self, comport: str):
        """Connects to the device. The connection must open before data can be sent or received.

        :param comport: str
            Identifier of the serial port to which the device is connected."""
        try:
            with self._thread_lock:
                self._instrument = propar.instrument(comport)
            self.specific_name = self.fluid_name.strip()
            self.pv_set_min = self.read_capacity_0()
            self.pv_set_max = self.read_capacity_100()
            self.logger(f"Connected to {self.complete_name} on {comport}.")
        except AttributeError:
            self._instrument = None
            self.logger(f"Could not connect to {self.complete_name} on {comport}.", error=True)


    def is_open(self) -> bool:
        """Check whether the connection is open.

        :return: bool
            True if the connection is open."""
        return bool(self._instrument)

    def close(self):
        """Disconnects the device."""
        with self._thread_lock:
            self._instrument = None

    def read_parameter(self, parameter_id: int):
        """Read a parameter from the device.

        :param parameter_id: int
            The identifier of the required parameter.
        :return: The value of the requested parameter."""
        if self.is_open():
            with self._thread_lock:
                return self._instrument.readParameter(parameter_id)
        else:
            self.logger(f"{self.complete_name} cannot read parameter: device is not connected.", error=True)

    def write_parameter(self, parameter_id: int, value):
        """Write a parameter to the device.

        :param parameter_id: int
            The identifier of the required parameter.
        :param value:
            The value to be written."""
        if self.is_open():
            with self._thread_lock:
                self._instrument.writeParameter(parameter_id, value)
        else:
            self.logger(f"{self.complete_name} cannot write parameter: device is not connected.", error=True)

    def read_pv(self) -> float:
        """Read current flow from device.

        :return: float
            Flow read by device in mln/min."""
        return self.read_parameter(205)

    def write_sp(self, flow: float):
        """Write the desired flow to the device.

        :param flow: float
            Desired flow in mln/min."""
        self.write_parameter(206, flow)

    def read_sp(self) -> float:
        """Read setpoint of device.

        :return: float
            Setpoint of device in mln/min."""
        return self.read_parameter(9)*self.pv_set_max/32000.0 + self.pv_set_min

    @property
    def flow(self) -> float:
        """Mass flow in mLn/min.
        Setting this value acts on the set-point of the device.
        Reading the value reads the measured flow, not the set-point."""
        return self.read_parameter(205)

    @flow.setter
    def flow(self, flow):
        """:type flow: float"""
        self.write_parameter(206, flow)

    @property
    def flow_units(self) -> str:
        """Units for flow measurement and setpoint.
        Should always return mln/min."""
        return self.read_parameter(129)

    @property
    def setpoint(self) -> int:
        """Flow setpoint in range 0-32000 (0-100% capacity of meter)."""
        return self.read_parameter(9)

    @property
    def measure(self) -> int:
        """Measured flow in range 0-32000 (0-100% capacity of meter)."""
        return self.read_parameter(8)

    @property
    def fluid_name(self) -> str:
        """Name of fluid the meter is currently configured for."""
        return self.read_parameter(25)

    @property
    def temperature(self) -> float:
        """Fluid temperature in degrees Celsius."""
        return self.read_parameter(181)

    @property
    def tag(self) -> str:
        """A user definable string which can be set for each device."""
        return self.read_parameter(115)

    def read_capacity_100(self) -> float:
        """Reads the maximum flow capacity in flow_units.

        :return: float
            The maximum flow capacity in flow_units."""
        return self.read_parameter(21)

    def read_capacity_0(self) -> float:
        """Reads the minimum flow capacity in flow_units.

        :return: float
            The minimum flow capacity in flow_units."""
        return self.read_parameter(183)

    @tag.setter
    def tag(self, tag):
        """:type tag: str"""
        self.write_parameter(115, str(tag))

    def __str__(self):
        """Provides a detailed description of the device and its current status.

        :return: str
            device description."""
        msg = self.name + ":\n"
        msg += "\tFlow: " + str(round(self.flow, 2)) + " " + self.flow_units + "\n"
        msg += "\tSet-point: " + str(self.setpoint) + "\n"
        msg += "\tMeasure: " + str(self.measure) + "\n"
        msg += "\tT: " + str(round(self.temperature, 2)) + "'C\n"
        msg += "\tFluid: " + self.fluid_name + "\n"
        msg += "\tUser tag: " + self.tag + "\n"
        return msg
