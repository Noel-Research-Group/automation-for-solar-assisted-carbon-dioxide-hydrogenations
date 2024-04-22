# Controller for automated Variable Backpressure Regulator

Device for automated control of backpressure in a flow setup.
This repo includes data on the construction of the physiscal device, code for the Arduino UNO controller
and documentation on controlling the device via serial-through-USB.

More detailed information is available via the documentation in the doc folder.

# Controller connections

### Stepper driver
- PIN\_2 -> Stepper driver ENABLE (active low)
- PIN\_3 -> Stepper driver DIRECTION
- PIN\_4 -> Stepper driver PULSE (active low)

### Analog inputs
- PIN\_14 (A0) <- Analog input, reads multi-turn potentiometer for absolute position of valve.
- PIN\_15 (A1) <- Analog input, reads pressure via the current-to-voltage conversion circuit.

# Serial Communication

The device is controlled via serial-through-USB using human readable commands with the following syntax:

- `Sx=y`<br>
Set variable x to value y. Variable numbers are integer, values type depends on the variable.<br>
- `Rx`<br>
Read variable x and print its value to serial.<br>

If y is a string, commands must be terminated with a newline character, if not, another commands can follow directly.
Unrecognized characters are silently ignored.


Variables:

 |Number | Acccess    | Type   	    | Description                                                                     |
 |-------|------------|--------------|----------------------------------------------------------------------------------|
 | 0     | RESERVED   | NONE         | Serial.parseInt returns 0 on error.                                              |
 | 1     | READ/WRITE | STRING [20]  | Device identifier.                                                               |
 | 2     | READ/WRITE | INT [0-1] 	 | Device enable On/\_Off state.                                                     |
 | 3     | READ/WRITE | FLOAT 		 | Pressure setpoint [Bar].                                                         |
 | 4     | READ\_ONLY  | FLOAT 		 | Pressure measured value [Bar].                                                   |
 | 5     | READ\_ONLY  | INT [0-1024] | Absolute valve position.                                                         |
 | 6     | COMMAND	 | FLOAT 		 | Begin calibration procedure using current position and pressure provided [Bar].  |
 | 7     | COMMAND	 | FLOAT 		 | End calibration procedure using current position and pressure provided [Bar].    |
 | 8     | COMMAND	 | NONE\* 		 | Set current valve position as minimum.                                           |
 | 9     | COMMAND	 | NONE\* 		 | Set current valve position as maximum.                                           |
 | 10    | COMMAND	 | INT 			 | Move motor by requested amount of steps.                                         |

> [!NOTE]
> Commands are sent as 'write only' variables. If the argument type is `NONE`, the command should be issued in the form `Sx=` without any argument.

# Dependencies

This project does not have any external dependencies.

Author: Simone Pilon \<s.pilon at uva.nl\>, Noël Research Group, 2023
