# Modbus interface for the Omron E5_C temperature controller.
#
# Author: Ronald Kortekaas - University of Amsterdam (TC) - 2023

import struct
import enum
from enum import Enum, EnumType
from typing import Any, Type
# from pymodbus import pymodbus_apply_logging_config
from pymodbus.client import ModbusSerialClient
from pymodbus.exceptions import ParameterException
from pymodbus.framer import ModbusFramer
from pymodbus.framer.rtu_framer import ModbusRtuFramer
from pymodbus.pdu import ModbusResponse


# Enable debugging
# pymodbus_apply_logging_config('DEBUG')


class DataSize(Enum):
    BYTE = 8
    WORD = 16


class StructSizeUnsigned(Enum):
    B = 1
    H = 2
    L = 4
    Q = 8


class MappedModbusRegisters:
    __registers = {}

    @classmethod
    @property
    def registers(cls):
        return cls.__registers

    @classmethod
    def get_info(cls, name: str):
        return cls.registers[name]  # pylint: disable=unsubscriptable-object

    @classmethod
    def list_names(cls):
        return list(cls.registers.keys())

    @classmethod
    def list_holding_names(cls):
        return list(k for k, v in cls.registers.items()
                    if 'holding' in v['register_type'])

    @classmethod
    def list_commands(cls):
        return list(k for k, v in cls.registers.items()
                    if 'command' in v['register_type'])

    @classmethod
    def list_commands_actions(cls):
        command_actions = {}
        for key, val in cls.registers.items():
            if 'command' in val['register_type']:
                if isinstance(val['data'], EnumType):
                    data = []
                    for member in val['data']:
                        data.append(member.name)
                else:
                    data = 'N/A'
                command_actions |= {val['description']: {'command': key,
                                                         'data': data}}
        return command_actions


class MappedModbusClient:
    connected: bool = False

    def __init__(
            self,
            port: str,
            registers: object,
            framer: Type[ModbusFramer] = ModbusRtuFramer,
            baudrate: int = 9200,
            timeout: int = 10,
            bytesize: int = 8,
            parity: str = 'E',
            stopbits: int = 1,
            slave: int = 0,
            ) -> None:
        self.registers = registers
        self.slave = slave

        self.client = ModbusSerialClient(
                framer=framer,
                port=port,
                baudrate=baudrate,
                timeout=timeout,
                parity=parity,
                stopbits=stopbits,
                bytesize=bytesize
                )

        self.logger = MappedModbusClient.default_logger

    @staticmethod
    def default_logger(message, error=False):
        print(message)

    def connect(self) -> bool:
        self.connected = self.client.connect()
        return self.connected

    def disconnect(self):
        self.client.close()

    def _hton(self, words: list, insize: int, outsize: int) -> int:
        val = [0] * (insize - len(words)) + words
        val = struct.pack(f"<{len(val)}{StructSizeUnsigned(insize).name}",
                          *val)
        val = struct.unpack(f">{StructSizeUnsigned(outsize*2).name}", val)[0]
        return val

    def _ntoh(self, words: list, insize: int, outsize: int) -> int:
        val = [0] * (insize - len(words)) + words
        val = struct.pack(f"<{len(val)}{StructSizeUnsigned(insize).name}",
                          *val)
        val = struct.unpack(f"<{StructSizeUnsigned(outsize*2).name}", val)[0]
        return val

    def _read(self,
              register_type: str,
              addr: int,
              count: int = 1) -> ModbusResponse | None:
        if register_type == 'holding':
            return self.client.read_holding_registers(address=addr,
                                                      count=count,
                                                      slave=self.slave)
        return None

    def _read_register(self, register: dict) -> Any:
        val = None

        if 'int' in register['data_format']:
            if register['data_length'] == 1:
                val = self._read(register['register_type'],
                                 register['address'])

            if register['data_length'] == 2:
                val = self._read(register['register_type'],
                                 register['address'],
                                 register['data_length'])
                val = self._ntoh(val.registers,
                                 register['data_length'], 1)
                val = register['data'](val)
            val = val.registers[0] / register['si_adj']
        elif 'bit' in register['data_format']:
            if register['data_length'] == 1:
                val = self._read(register['register_type'],
                                 register['address'])

            val = bin(val.registers[0])
        elif 'enum' in register['data_format']:
            val = self._read(register['register_type'],
                             register['address'])
            val = register['data'](val.registers[0]).name

        elif 'flag' in register['data_format']:
            try:
                val = self._read(register['register_type'],
                                 register['address'],
                                 register['data_length'])
                val = self._ntoh(val.registers,
                                 2,
                                 register['data_length'])
                val = register['data'](val)
            except ValueError as e:
                self.logger('Invalid flag received', True)
                self.logger(str(e), True)

        return val

    def read_register(self, name: str) -> tuple:
        """Read a register from the modbus client

        Args:
            name (str): Register name

        Returns:
            tuple: (description, value, data_unit)
        """
        register = self.registers.get_info(name)

        value = self._read_register(register)

        if 'data_unit' not in register:
            return (register['description'], value, "")

        return (register['description'], value, register['data_unit'])

    def read_all_registers(self) -> list:
        """Read all registers from the modbus client."""
        value_list = []

        for item in self.registers.list_holding_names():
            value_list.append(self.read_register(item))
        return value_list

    def write_register(self, name: str, value: Any) -> None:
        """Writes a register to the modbus client.

        Args:
            name (str): Register name
            value (Any): Register value
        """
        register = self.registers.get_info(name)
        if isinstance(value, float) or isinstance(value, int):
            val = int(value * register['si_adj'])
        elif isinstance(value, str):
            val = register['data'][value].value

        self.client.write_registers(address=register['address'],
                                    values=val,
                                    slave=self.slave)

    def write_command(self, command: str, mode: str = '') -> None:
        """Writes a command to the modbus client.

        Args:
            command (str): Command to write
            mode (str): Command mode
        """
        register = self.registers.get_info(command)
        if 'action' in register['register_type']:
            if not mode:
                val = self._hton([register['command_code'],
                                  register['data']],
                                 1, 1)
            else:
                raise ParameterException(mode)
        else:
            if mode in register['data'].__members__:
                val = self._hton([register['command_code'],
                                  register['data'][mode].value],
                                 1, 1)
            else:
                raise ParameterException(mode)
        res = self.client.write_register(address=0x0000,
                                         value=val,
                                         slave=self.slave)
        if res.isError():
            self.logger('Error: '+str(register)+str(command)+str(mode), error=True)
            self.logger(str(res), error=True)
            if hasattr(res, 'registers'):
                self.logger(str(res.registers), error=True)
            if hasattr(res, 'bits'):
                self.logger(str(res.bits), error=True)
