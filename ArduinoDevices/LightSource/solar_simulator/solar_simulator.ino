/*
	Light controller for the Solar Simulator setup

	Serial Communication:

		Sx=y
			Set variable x to value y. Variable number are integer, values are signed floating point.
		Rx
			Read variable x and print its value to serial.

		Variable list:
		 number: acccess    type   		description
		 --------------------------------------------------------
				0: RESERVED						Serial.parseInt returns 0 on error.
				1: READ/WRITE STRING [20] 	Device identifier.
				2: READ/WRITE INT [0-1] 	Lights On/_Off state
				3: READ/WRITE INT [0-1] 	Fans On/_Off state
				4: READ/WRITE INT [0-1] 	Manual interface lock On/_Off state
				5: READ/WRITE INT [0-100] 	Light intensity

	Libraries:
		LiquidCrystal (Adafruit)

	Hardware connections (Arduino UNO board):
		Buttons
			pin 14 (A0) <- less
			pin 15 (A1) <- more
			pin 16 (A2) <- on/off

		LCD
			pin 8 -> RS
			pin 9 ->  E
			pins [10 - 13] -> [DB4 - DB7]

		Custom board
			pin 3 -> board input 1 (light intensity control)
			pin 4 -> board input 2 (lights circuit breaker)
			pin 5 -> board input 3 (12v fans)

	by Simone Pilon <s.pilon at uva.nl> - Noël Research Group - 2023
 */

#include <LiquidCrystal.h>
#include <EEPROM.h>

// Project includes
#include "buttons.h"

// Project defines
#define ADDRESS_INTENSITY 0 // EEPROM address of intensity (int)
#define DEVICE_ID_SIZE 20

// Device id
char device_id[DEVICE_ID_SIZE] = "LIGHT_CONTROL_0";	// A unique identifier to distinguish this from other serial devices

// Buttons
Button btn_less = Button(A0);
Button btn_more = Button(A1);
Button btn_on = Button(A2);

// Init LCD
LiquidCrystal lcd( 8, 9, 10, 11, 12, 13);

// System status
int light_intensity = 0;	// Light intensity 0-100 to use for pwm. To change call update_intensity(x)!
bool system_on = false;		// if true lights, fans and pwm are on, otherwise they are off.
bool system_lock = false;	// if true allows control only via serial

// Update the values shown on the lcd only.
void update_lcd() {
	String onoff = system_on ? " on" : "off";
	String inten = String(light_intensity);
	lcd.setCursor(13,0);
	lcd.print(onoff);
	lcd.setCursor(12,1);
	lcd.print("   ");
	lcd.setCursor(15-inten.length(),1);
	lcd.print(inten);
}

// Update the values shown on the lcd with full screen clear.
void clear_lcd() {
	lcd.clear();
	lcd.setCursor(0,0);
	lcd.print("Power:");
	lcd.setCursor(0,1);
	lcd.print("Intens.:");
	lcd.setCursor(15,1);
	lcd.print("%");
	update_lcd();
}

// Changes the light intensity on the pin out if needed.
void update_intensity() {
	if (system_on) {
		analogWrite(3, (light_intensity*255)/100);			// Set pwm light int.
	}
	EEPROM.put(ADDRESS_INTENSITY, light_intensity);
}

// Turns lights, fans and pwm on
void turn_on() {
	system_on = true;
	digitalWrite(5, HIGH);	// Turn fans on
	update_intensity();
	digitalWrite(4, HIGH);	// Turn lights on
}

// Turns lights, (fans) and pwm off
void turn_off() {
	system_on = false;
	digitalWrite(4, LOW);	// Turn lights off
	analogWrite(3, 0);		// Set pwm light int. to 0
									//digitalWrite(5, LOW);	// Turn fans off (keep them on for cooling)
}

// Read a C-style string from Serial
void serial_read_id() {
	uint8_t i = 0;
	char byte_in;
	while (i < DEVICE_ID_SIZE) {
		uint8_t timeout = 20;	// Max timeout in mS per char
		while (Serial.available() == 0 && timeout != 0) {
			delay(1);
			timeout--;
		}
		byte_in = Serial.read();
		if (byte_in == '\n') {
			break;
		}
		device_id[i] = byte_in;
		i++;
	}
	device_id[i] = '\0';
}

// Read commands from serial
void parse_serial() {
	while (Serial.available() > 0) {
		char command = Serial.read();
		int variable_number = 0;
		if (command == 'R') {
			// Read variable
      variable_number = Serial.parseInt();
			switch(variable_number) {
				case 1:
					// Device identifier
					Serial.println(device_id);
					break;
				case 2:
					// Lights On/_Off
					Serial.println(system_on?1:0);
					break;
				case 3:
					// Fans On/_Off
					Serial.println(digitalRead(5)==HIGH?1:0);
					break;
				case 4:
					// Interface lock On/_Off
					Serial.println(system_lock?1:0);
					break;
				case 5:
					// Light intensity
					Serial.println(light_intensity);
					break;
			}
		}
		else if (command == 'S') {
			// Write variable
      variable_number = Serial.parseInt();
			Serial.read();
			int variable_value_int = 0;
			float variable_value_float = 0;
			switch(variable_number) {
				case 1:
					// Device identifier
					serial_read_id();
				case 2:
					// Lights On/_Off
					variable_value_int = Serial.parseInt();
					if (variable_value_int == 1) {
						turn_on();
					}
					else {
						turn_off();
					}
					update_lcd();
					break;
				case 3:
					// Fans On/_Off
					variable_value_int = Serial.parseInt();
					if (variable_value_int == 1) {
						digitalWrite(5, HIGH);
					}
					else {
						if (!system_on) {
							digitalWrite(5, LOW);
						}
					}
					break;
				case 4:
					// Interface lock On/_Off
					variable_value_int = Serial.parseInt();
					if (variable_value_int == 1) {
						system_lock = true;
						lcd.setCursor(7,0);
						lcd.print("LOCK");
					}
					else {
						system_lock = false;
						clear_lcd();
					}
					break;
				case 5:
					// Light intensity
					variable_value_float = Serial.parseFloat();
					if (variable_value_float >= 0 && variable_value_float <= 100) {
						light_intensity = int(variable_value_float);
						update_intensity();
						update_lcd();
					}
					else {
						Serial.println('E');
					}
					break;
			}
		}
	}
}

void setup() {
	// Load values
	EEPROM.get(ADDRESS_INTENSITY, light_intensity);
	if (light_intensity < 0 || light_intensity > 100) {
		light_intensity = 0;
	}

	// init LCD
	lcd.begin(16, 2);
	clear_lcd();

	// Serial
	Serial.begin(9600);

	// External board
	pinMode(3, OUTPUT);
	pinMode(4, OUTPUT);
	pinMode(5, OUTPUT);
	digitalWrite(3, LOW);
	digitalWrite(4, LOW);
	digitalWrite(5, LOW);
}

void loop() {
	// Read buttons
	if (!system_lock) {
		bool update = false;
		if (btn_less.isPressed()) {
			light_intensity--;
			if (light_intensity < 0) {
				light_intensity = 0;
			}
			update_intensity();
			update = true;

		}
		if (btn_more.isPressed()) {
			light_intensity++;
			if (light_intensity > 100) {
				light_intensity = 100;
			}
			update_intensity();
			update = true;
		}
		if (btn_on.isPressed()) {
			// request confirmation by holding button
			lcd.clear();
			lcd.setCursor(3,0);
			lcd.print("hold button");
			lcd.setCursor(3,2);
			lcd.print("to confirm");
			bool confirm = true;
			for (int i=0; i<20; i++) {
				delay(100);
				if (!btn_on.isDown()) {
					confirm = false;
					break;
				}
			}
			btn_on.disable(1000);
			if (confirm) {
				if (!system_on) {
					turn_on();
				}
				else {
					turn_off();
				}
			}
			clear_lcd();
		}
		if (update) {
			update_lcd();
		}
	}
	parse_serial();
}
