# Controller for the light source of the solar simulator setup

Device for automatic control of HLG-480H-xx-AB power suppply. This power supply unit controls the light output of the Solar Simulator Setup, and the arduino-based control device allows the intesity to be controlled remotely and automatically from a computer via serial-thrugh-USB interface.
The device allows for direct user control via 3 buttons and a 2-lines LCD display.
The device also controls the cooling fans of the LED lights.

More detailed information is available via the documentation in the project doc folder.

# Controller connections

### Buttons
- PIN\_14 (A0) <- button 'less'
- PIN\_15 (A1) <- button 'more'
- PIN\_16 (A2) <- button 'on/off'

### LCD screen
- PIN\_8 -> LCD RS pin
- PIN\_9 -> LCD Enable pin
- PIN\_10-13 -> LCD data pins (DB4-DB7)

### Custom board
- PIN\_3 -> Custom board input #1 (light intensity control)
- PIN\_4 -> Custom board input #2 (lights circuit breaker)
- PIN\_5 -> Custom board input #3 (12v fans control)

# Serial Communication

The device is controlled via serial-through-USB using human readable commands with the following syntax:

- `Sx=y`<br>
Set variable x to value y. Variable numbers are integer, values type depends on the variable.<br>
- `Rx`<br>
Read variable x and print its value to serial.<br>

If y is a string, commands must be terminated with a newline character, if not, another commands can follow directly.
Unrecognized characters are silently ignored.


Variables:

 |Number | Acccess    | Type   	   | Description                          |
 |-------|------------|-------------|--------------------------------------|
 | 0     | RESERVED	 | NONE	      | Serial.parseInt returns 0 on error.  |
 | 1     | READ/WRITE | STRING [20] | Device identifier.                   |
 | 2     | READ/WRITE | INT [0-1] 	| Lights On/\_Off state.               |
 | 3     | READ/WRITE | INT [0-1] 	| Fans On/\_Off state.                 |
 | 4     | READ/WRITE | INT [0-1] 	| Manual interface lock On/\_Off state.|
 | 5     | READ/WRITE | INT [0-100] | Light intensity.                     |

# Dependencies

- LiquidCrystal (by Adafruit)<br>
Control of the LCD display.

Author: Simone Pilon \<s.pilon at uva.nl\>, Noël Research Group, 2023
