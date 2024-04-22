/*
	Controller for automated Variable Backpressure Regulator

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
				2: READ/WRITE INT [0-1] 	Device enable On/_Off state.
				3: READ/WRITE FLOAT 			Pressure setpoint [Bar].
				4: READ_ONLY  FLOAT 			Pressure measured value [Bar].
				5: READ_ONLY  INT [0-1024] Absolute valve position.
				6: COMMAND	  FLOAT 			Begin calibration procedure using current position and pressure provided [Bar].
				7: COMMAND	  FLOAT 			End calibration procedure using current position and pressure provided [Bar].
				8: COMMAND	  NONE 			Set current valve position as minimum.
				9: COMMAND	  NONE 			Set current valve position as maximum.
			  10: COMMAND	  INT 			Move motor by requested amount of steps.

	Hardware connections (Arduino UNO board):
		Motor driver
			pin 2 -> Stepper driver ENABLE (active low)
			pin 3 -> Stepper driver DIRECTION
			pin 4 -> Stepper driver PULSE (active low)

		Analog inputs
			pin 14 (A0) <- Analog input, reads multi-turn potentiometer for absolute position of valve.
			pin 15 (A1) <- Analog input, reads pressure via the current-to-voltage conversion circuit.

	by Simone Pilon <s.pilon at uva.nl> - Noël Research Group - 2023
 */

#include "Controller.h"	// The proportional controller
#include "StepperDriver.h"	// The motor controller
#include <math.h>
#include <EEPROM.h>

// Flags
//#define PRINT_PRESSURE	// Prints pressure to serial continuously.
//#define VERBOSE	// prints diagnostic output to serial
//#define DEBUG_COMMANDS

// Defines for stepper pins
#define PIN_ENA 2 // Active LOW!  |
#define PIN_DIR 3 //              |- Stepper driver pins
#define PIN_PUL 4 //              |
#define PIN_POS 14  // A0 analog pin to pot for reading absolute position
#define PIN_PRES 15 // A1 analog pin to pressure sensor for reading pressure

// EEPROM allocation table
#define EEPROM_TARGET 5
#define EEPROM_P_CAL_M 10
#define EEPROM_P_CAL_Q 15
#define EEPROM_POT_MAX 20
#define EEPROM_POT_MIN 25

// Other
#define P_CTR_MAX 5
#define DEVICE_ID_SIZE 20

// Device id
char device_id[DEVICE_ID_SIZE] = "PRESSURE_CONTROL_0";	// A unique identifier to distinguish this from other serial devices

// Global variables:
Controller controller = Controller();	// The proportional controller
ServoStepperDriver motor = ServoStepperDriver(PIN_ENA, PIN_DIR, PIN_PUL, PIN_POS);	// The motor interface
bool enable = false;  // The device starts in stand-by mode, can be activated by sending the command 'S'
float p_cal_m = 0.02;  // m coefficient for pressure sensor calibration : Overridden by EEPROM
float p_cal_q = -4.5;  // q coefficient for pressure sensor calibration : Overridden by EEPROM
float p_bar_1 = 0.0;  // Pressure at calibration point 1       : Used in calibration only
int p_volt_1 = 0;     // Sensor output for calibration point 1 : Used in calibration only
float pressure_last = 0.0;// Last measured pressure in bars.
float pressure_now = 0.0;// Current pressure in bars.

// Returns the pressure in bars from the sensor
float readPressureBar() {
	float p_volt = (float) analogRead(PIN_PRES);
	return p_volt*p_cal_m + p_cal_q;
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

// Checks serial line for commands
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
					// Device enable On/_Off
					Serial.println(enable?'1':'0');
					break;
				case 3:
					// Pressure setpoint
					Serial.println(controller.getTarget());
					break;
				case 4:
					// Pressure value
					Serial.println(pressure_last);
					break;
				case 5:
					// Valve position
					Serial.println(motor.position());
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
					// Device enable On/_Off
					variable_value_int = Serial.parseInt();
					enable = variable_value_int==1?true:false;
					break;
				case 3:
					// Pressure setpoint
					variable_value_float = Serial.parseFloat();
					EEPROM.put(EEPROM_TARGET, variable_value_float);
					controller.setTarget(variable_value_float);
					break;
				case 6:
					// Begin pressure sensor calibration
					p_bar_1 = Serial.parseFloat();
					p_volt_1 = analogRead(PIN_PRES);
					break;
				case 7:
					// End pressure sensor calibration
					float p_bar_2 = Serial.parseFloat();
					int p_volt_2 = analogRead(PIN_PRES);

					p_cal_m = (p_bar_2 - p_bar_1)/((float) (p_volt_2 - p_volt_1));
					p_cal_q = p_bar_2 - (p_cal_m*p_volt_2);

					EEPROM.put(EEPROM_P_CAL_M, p_cal_m);
					EEPROM.put(EEPROM_P_CAL_Q, p_cal_q);
					break;
				case 8:
					// Set valve minimum
					int pot_min = motor.set_min();
					EEPROM.put(EEPROM_POT_MIN, pot_min);
					break;
				case 9:
					// Set valve maximum
					int pot_max = motor.set_max();
					EEPROM.put(EEPROM_POT_MAX, pot_max);
					break;
				case 10:
					// Move motor
					motor.enable(true);
					motor.setSpeed(300.0);
					motor.move(Serial.parseInt());
					motor.enable(false);
					break;
			}
		}
	}
}

void setup() {	
	// Initialize motor
	motor.init();

	// Load calibration from EEPROM
	EEPROM.get(EEPROM_P_CAL_M, p_cal_m);
	EEPROM.get(EEPROM_P_CAL_Q, p_cal_q);

	// Load limits from EEPROM
	int pot_max, pot_min;
	EEPROM.get(EEPROM_POT_MAX, pot_max);
	EEPROM.get(EEPROM_POT_MIN, pot_min);
	motor.set_limits(pot_min, pot_max);

	// Initialize proportional controller
	controller.setCurve(0.05, 0.6, 10.0, 2.5, 800.0, false);
	float target = 0.0;
	EEPROM.get(EEPROM_TARGET, target);
	controller.setTarget(target);

	Serial.begin(9600);

	pressure_now = readPressureBar();
	pressure_last = pressure_now + 0.1; // Make sure it is not the same.
}

void loop() {
	// Wait until pressure is stable
	do {
		// Read pressure over ~0.5 seconds (5 times), then average.
		pressure_last = pressure_now;
		pressure_now = 0.0;
		for (int i=0; i<P_CTR_MAX; i++) {
			// Check commands
			parse_serial();

			// Measure pressure     
			delay(100);
			pressure_now += readPressureBar();
		}
		pressure_now = pressure_now/P_CTR_MAX;
#ifdef PRINT_PRESSURE
		Serial.print("P:");
		Serial.println(pressure_now);
#endif // PRINT_PRESSURE
	} while ((abs(pressure_last-pressure_now) >= 0.10) &&
			pressure_now - controller.getTarget() < 0.25);

	// Move the valve based on pressure reading
	if (enable) {
		int move = 0;
		float speed = 0.0;
		controller.output(pressure_now, move, speed);
		if (move != 0) {
			// Move
			motor.setSpeed(speed);	// Set the speed.
			motor.enable(true);
			delay(25);
			motor.move(move);	// Move, this takes ca. 250mS
			delay(25);
			motor.enable(false);
		}
		else {
			// Wait
			delay(300);
		}
#ifdef VERBOSE
		Serial.print("M:");
		Serial.println(move);
		int error = motor.error();
		if (error != 0) {
			Serial.print("M:Error ");
			Serial.println(error);
		}
#endif // VERBOSE
	}
}
