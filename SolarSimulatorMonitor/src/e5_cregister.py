# Register map for the Omron E5_C temperature controller modbus interface.
#
# Author: Ronald Kortekaas - University of Amsterdam (TC) - 2023
# Author: Simone Pilon - Noël Research Group - 2023

from enum import Enum, Flag, CONFORM

from mapped_modbus_client import MappedModbusRegisters


class E5CStatus(Flag, boundary=CONFORM):
    """Omron E5_C Status Registers Values."""
    HEATER_OVERCURRENT_CT1 = 0x00000001
    HEATER_CURRENT_HOLD_CT1 = 0x00000002
    AD_CONVERTER_ERROR = 0x00000004
    HS_ALARM = 0x00000008
    RSP_INPUT_ERROR = 0x00000010
    INPUT_ERROR = 0x00000040
    POTENTIOMETER_INPUT_ERROR = 0x00000080
    CONTROL_OUTPUT_OPEN = 0x00000100
    CONTROL_OUTPUT_CLOSE = 0x00000200
    HB_ALARM_CT1 = 0x00000400
    HB_ALARM_CT2 = 0x00000800
    AL1 = 0x00001000
    AL2 = 0x00002000
    AL3 = 0x00004000
    PROGRAM_END_OUTPUT = 0x00008000
    EV1 = 0x00010000
    EV2 = 0x00020000
    EV3 = 0x00040000
    EV4 = 0x00080000
    WRITE_MODE = 0x00100000
    NON_VOLATILE_MEM = 0x00200000
    SETUP_AREA = 0x00400000
    AT_EXEC_CANCEL = 0x00800000
    STOP = 0x01000000
    COMM_WRITE = 0x02000000
    AUTO_MAN = 0x04000000
    PROGRAM_START = 0x08000000
    HEATER_OVERCURRENT_CT2 = 0x010000000
    HEATER_CURRENT_HOLD_CT2 = 0x020000000
    HS_ALARM_CT2 = 0x080000000

    WB1 = 0x100000000
    WB2 = 0x200000000
    WB3 = 0x400000000
    WB4 = 0x800000000
    WB5 = 0x1000000000
    WB6 = 0x2000000000
    WB7 = 0x4000000000
    WB8 = 0x8000000000

    EV5 = 0x10000000000
    EV6 = 0x20000000000

    INVERT = 0x100000000000
    SP_RAMP = 0x200000000000

    SP_MODE = 0x0800000000000
    AL4 = 0x10000000000000

    SUB1 = 0x1000000000000000


class E5CRegisters(MappedModbusRegisters):
    """Omron E5_C Register Mapping"""
    registers = {
        'pv': {
            'address': 0x2000,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 10,
            'signed': True,
            'data_unit': '°C',
            'data_length': 1,
            'description': 'Process Value'
        },
        'status': {
            'address': 0x2406,
            'register_type': 'holding',
            'data_format': 'flag',
            'data_length': 4,
            'data': E5CStatus,
            'description': 'Status'
        },
        'int_sp': {
            'address': 0x2002,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 10,
            'signed': True,
            'data_unit': '°C',
            'data_length': 1,
            'description': 'Internal Set Point'
        },
        'heatcur1vm': {
            'address': 0x2003,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 10,
            'signed': True,
            'data_unit': '°C',
            'data_length': 1,
            'description': 'Heater Current 1 Value Monitor'
        },
        'mvmonheat': {
            'address': 0x2004,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 10,
            'signed': True,
            'data_unit': '%',
            'data_length': 1,
            'description': 'Manipulated Variable Monitor (Heating)'
        },
        'sp': {
            'address': 0x2103,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 10,
            'signed': True,
            'data_unit': '°C',
            'data_length': 1,
            'description': 'Set Point'
        },
        'av1': {
            'address': 0x2104,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Alarm Value 1'
        },
        'avul1': {
            'address': 0x2105,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Alarm Value Upper Limit 1'
        },
        'avll1': {
            'address': 0x2106,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Alarm Value Lower Limit 1'
        },
        'av2': {
            'address': 0x2107,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Alarm Value 1'
        },
        'avul2': {
            'address': 0x2108,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Alarm Value Upper Limit 2'
        },
        'avll2': {
            'address': 0x2109,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Alarm Value Lower Limit 2'
        },
        'decimal point monitor': {
            'address': 0x2410,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'signed': True,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Decimal Point Monitor'
        },
        'pid_p': {
            'address': 0x2A00,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 10,
            'data_unit': 'EU',
            'data_length': 1,
            'description': 'Proportional Band'
        },
        'pid_i': {
            'address': 0x2A01,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'data_unit': 's',
            'data_length': 1,
            'description': 'Integral Time'
        },
        'pid_d': {
            'address': 0x2A02,
            'register_type': 'holding',
            'data_format': 'int16',
            'si_adj': 1,
            'data_unit': 's',
            'data_length': 1,
            'description': 'Derivative Time'
        },
        'pid_on_off': {
            'address': 0x2D14,
            'register_type': 'holding',
            'data_format': 'enum',
            'data': Enum('data', {'ON_OFF': 0x00, 'PID_CONTROL': 0x01}),
            'description': 'PID ON/OFF'
        },
        'input_type': {
            'address': 0x2C00,
            'register_type': 'holding',
            'data_format': 'enum',
            'data': Enum('parameter', {'Pt_0': 0x00,
                                       'Pt_1n': 0x01,
                                       'Pt_1p': 0x02,
                                       'JPt_0': 0x03,
                                       'JPt_1': 0x04,
                                       'K_0': 0x05,
                                       'K_1': 0x06,
                                       'J_0': 0x07,
                                       'J_1': 0x08,
                                       'T_0': 0x09,
                                       'T_1': 0x0A,
                                       'E': 0x0B,
                                       'L': 0x0C,
                                       'U_0': 0x0D,
                                       'U_1': 0x0E,
                                       'N': 0x0F,
                                       'R': 0x10,
                                       'S': 0x11,
                                       'B': 0x12,
                                       'W': 0x13,
                                       'PLII': 0x14,
                                       'IR1': 0x15,
                                       'IR2': 0x16,
                                       'IR3': 0x17,
                                       'IR4': 0x18,
                                       'EXT1': 0x19,
                                       'EXT2': 0x1A,
                                       'EXT3': 0x1B,
                                       'EXT4': 0x1C,
                                       'EXT5': 0x1D,
                                       'EXT6': 0x1E}),
            'description': 'Input Type'
        },
        'pvstsdispfun': {
            'address': 0x3011,
            'register_type': 'holding',
            'data_format': 'enum',
            'data': Enum('parameter', {'OFF': 0x00,
                                       'MAN': 0x01,
                                       'STOP': 0x02,
                                       'AL1': 0x03,
                                       'AL2': 0x04,
                                       'AL3': 0x05,
                                       'AL4': 0x06,
                                       'AL1_4': 0x07,
                                       'ALHEAT': 0x08,
                                       'STS': 0x09,
                                       }),
            'description': 'PV Status Display Function'
        },
        'i_d_timeunit': {
            'address': 0x3309,
            'register_type': 'holding',
            'data_format': 'enum',
            'data': Enum('parameter', {'1s': 0x00, '0_1s': 0x01}),
            'description': 'Integral/Derivative Time Unit'
        },
        'comm_write': {
            'command_code': 0x00,
            'register_type': 'command',
            'data': Enum('data', {'OFF': 0x00, 'ON': 0x01}),
            'description': 'Communications writing'
        },
        'run_stop': {
            'command_code': 0x01,
            'register_type': 'command',
            'data': Enum('data', {'RUN': 0x00, 'STOP': 0x01}),
            'description': 'RUN/STOP'
        },
        'multi_sp': {
            'command_code': 0x02,
            'register_type': 'command',
            'data': Enum('data', {'SP0': 0x00,
                                  'SP1': 0x01,
                                  'SP2': 0x02,
                                  'SP3': 0x03,
                                  'SP4': 0x04,
                                  'SP5': 0x05,
                                  'SP6': 0x06,
                                  'SP7': 0x07,
                                  }),
            'description': 'Multi-SP'
        },
        'at_exec_cancel': {
            'command_code': 0x03,
            'register_type': 'command',
            'data': Enum('data', {'AT_CANCEL': 0x00,
                                  'AT_EXEC_100PCT': 0x01,
                                  'AT_EXEC_40PCT': 0x02}),
            'description': 'AT execute/cancel'
        },
        'write_mode': {
            'command_code': 0x04,
            'register_type': 'command',
            'data': Enum('data', {'BACKUP': 0x00, 'RAM_WM': 0x01}),
            'description': 'Write mode'
        },
        'save_ram_data': {
            'command_code': 0x05,
            'register_type': 'command_action',
            'data': 0x00,
            'description': 'Save RAM data'
        },
        'software_reset': {
            'command_code': 0x06,
            'register_type': 'command_action',
            'data': 0x00,
            'description': 'Software reset'
        },
        'move_to_setup_area_1': {
            'command_code': 0x07,
            'register_type': 'command_action',
            'data': 0x00,
            'description': 'Move to setup area 1'
        },
        'move_to_protect_level': {
            'command_code': 0x08,
            'register_type': 'command_action',
            'data': 0x00,
            'description': 'Move to protect level'
        },
        'auto_manual': {
            'command_code': 0x09,
            'register_type': 'command',
            'data': Enum('data', {'AUTOMATIC': 0x00, 'MANUAL': 0x01}),
            'description': 'Automatic/manual switch'
        },
        'param_init': {
            'command_code': 0x0B,
            'register_type': 'command_action',
            'data': 0x00,
            'description': 'Parameter initialization'  # Warning! This command will reset the device to CompoWay
            # communication protocol, it will need to be changed to Modbus manually after.
        },
        'alarm_latch_cancel': {
            'command_code': 0x0C,
            'register_type': 'command',
            'data': Enum('data', {'AL1': 0x00,
                                  'AL2': 0x01,
                                  'AL3': 0x02,
                                  'HBAL': 0x03,
                                  'HSAL': 0x04,
                                  'AL4': 0x05,
                                  'ALL': 0x0F,
                                  }),
            'description': 'Alarm latch cancel'
        },
        'sp_mode': {
            'command_code': 0x0C,
            'register_type': 'command',
            'data': Enum('data', {'LOCAL': 0x00, 'REMOTE': 0x01}),
            'description': 'SP Mode'
        },
        'invert': {
            'command_code': 0x0D,
            'register_type': 'command',
            'data': Enum('data', {'NOT': 0x00, 'INVERT': 0x01}),
            'description': 'Invert direct/reverse operation'
        },
        'program_start': {
            'command_code': 0x11,
            'register_type': 'command',
            'data': Enum('data', {'RESET': 0x00, 'START': 0x01}),
            'description': 'Program start'
        }
    }
