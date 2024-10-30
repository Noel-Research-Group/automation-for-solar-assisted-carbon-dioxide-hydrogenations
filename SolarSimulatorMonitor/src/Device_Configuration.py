"""
File: Device_Configuration.py
Author: Simone Pilon - Noël Research Group - 2023
GitHub: https://github.com/simone16
Description: Load and store different hardware configurations for the Solar Simulator Setup.
"""

import copy
import os.path
from os import getcwd
import json
import Serial_devices


class DeviceConfiguration:
    """Holds information about different hardware configurations for the solar simulator setup. Different experiments
    may call for different devices to be connected and monitored: coupled with the KnownDevices class, this class
    allows to store information about each experimental setup and easily select one when starting the solar simulator
    monitor."""

    DEVICE_TYPE = {'Light': 0, 'Pressure': 1, 'Temperature': 2, 'Flow': 3}

    def __init__(self):
        self.path_to_config = os.path.join(getcwd(), 'config', 'device_config.json')
        self._configurations = None
        self._known_devices = Serial_devices.KnownDevices()

    def load(self):
        """Retrieves configurations list from file and stores it in this object."""
        if os.path.isfile(self.path_to_config):
            with open(self.path_to_config, 'r') as configurations_file:
                try:
                    self._configurations = json.load(configurations_file)
                except json.JSONDecodeError as e:
                    print(e)
                    print(f'Unable to open {self.path_to_config}.')
                    self._configurations = None
        else:
            self._configurations = None

    def save(self):
        """Overwrites the configuration list with data from this object."""
        if self._configurations:
            with open(self.path_to_config, 'w') as configurations_file:
                json.dump(self._configurations, configurations_file, indent=4)

    def add(self, configuration_name: str, device_name: str, device_type: str):
        """Add a device to an existing configuration, or creates a new one if the name does not match any existing
        configurations.

        :param configuration_name: str
            Name of the existing or new configuration.
        :param device_name: str
            Name of the device to add to the configuration (must match the name found in 'known_devices.json').
        :param device_type: str
            Type of device, must match one in 'self.DEVICE_TYPE'.
        :raise KeyError:
            Raises an exception if the device type or name is not known."""
        if not device_type in self.DEVICE_TYPE.keys():
            raise KeyError(f"'{device_type}' is not a valid device type.")
        if not device_name in self._known_devices.keys():
            raise KeyError(f"Device '{device_name}' is not known.")
        if not self._configurations:
            self.load()
            if not self._configurations:
                self._configurations = {}
        if configuration_name not in self._configurations.keys():
            self._configurations[configuration_name] = []
        self._configurations[configuration_name].append({'name': device_name, 'type': device_type})

    def __getitem__(self, configuration_name: str):
        """Returns a list of dictionaries holding information about each device in the selected configuration.

        :param configuration_name: str
            The name used to identify the configuration.
        :return: list
            Each item in the list corresponds to a device and defines:
                name: str.
                    the name of the device as found in 'known_devices.json'
                type: str
                    the type of device (enumerated in self.DEVICE_TYPE)
                comport: str
                    name of the comport the device is connected to, or None if it was not found.
        :raise KeyError:
            Raises an exception if the name is not in the configurations list."""
        if not self._configurations:
            self.load()
            if not self._configurations:
                raise KeyError('The list of known devices is empty.')
        if configuration_name in self._configurations.keys():
            configuration = copy.deepcopy(self._configurations[configuration_name])
            for device in configuration:
                device['comport'] = self._known_devices[device['name']]
            return configuration
        else:
            raise KeyError(f"The name '{configuration_name}' is not associated with any configuration.")

    def keys(self):
        """Returns the names of all configurations.

        :return: dict_keys
            Configurations names"""
        if not self._configurations:
            self.load()
        return self._configurations.keys()
