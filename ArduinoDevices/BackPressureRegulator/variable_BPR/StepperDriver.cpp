#include "StepperDriver.h"
#include <math.h>
#include <Arduino.h>

StepperDriver::StepperDriver(int _pin_enable, int _pin_direction, int _pin_step) {
	pin_enable = _pin_enable;
	pin_direction = _pin_direction;
	pin_step = _pin_step;
	step_delay = 500;
}

void StepperDriver::init() {
	pinMode(pin_enable, OUTPUT);
	pinMode(pin_direction, OUTPUT);
	pinMode(pin_step, OUTPUT);
	digitalWrite(pin_enable, HIGH);
	digitalWrite(pin_direction, HIGH);
	digitalWrite(pin_step, LOW);
}

void StepperDriver::enable(bool enable) {
	if (enable) {
		digitalWrite(pin_enable, LOW);
	}
	else {
		digitalWrite(pin_enable, HIGH);
	}
}

void StepperDriver::setSpeed(float speed) {
	speed = abs(speed);
	int delayus = round(500000.0/speed);
	if (delayus < 15000) {
		// Use delayMicroseconds()
		delayfunc = &delayMicroseconds;
		if (delayus < 100) {
			// cap top speed
			step_delay = 100;
		}
		else {
			step_delay = delayus;
		}
	}
	else {
		// use delay()
		delayfunc = &delay;
		step_delay = delayus/1000;
		if (step_delay > 100) {
			// cap lowest speed
			step_delay = 100;
		}
	}
}

void StepperDriver::move(int steps) {
	if (steps > 0) {
		digitalWrite(pin_direction, LOW);
	}
	else {
		digitalWrite(pin_direction, HIGH);
		steps = -steps;
	}
	for (int i=0; i<steps; i++) {
		digitalWrite(pin_step, HIGH);
		delayfunc(step_delay);
		digitalWrite(pin_step, LOW);
		delayfunc(step_delay);
	}
}

ServoStepperDriver::ServoStepperDriver(int _pin_enable, int _pin_direction, int _pin_step, int _pin_pot)
  : StepperDriver(_pin_enable, _pin_direction, _pin_step) {
  pin_pot = _pin_pot;
  pos_max = 0;
  pos_min = 0;
  _error = 0;
}

void ServoStepperDriver::init() {
	StepperDriver::init();
	pinMode(pin_pot, INPUT);
}

int ServoStepperDriver::position() {
	return analogRead(pin_pot);
}

int ServoStepperDriver::set_max() {
	int max = analogRead(pin_pot);
	if (max >= pos_min) {
		pos_max = max;
	}
	else {
		pos_max = pos_min;
		pos_min = max;
	}
	return max;
}

int ServoStepperDriver::set_min() {
	int min = analogRead(pin_pot);
	if (min <= pos_max) {
		pos_min = min;
	}
	else {
		pos_min = pos_max;
		pos_max = min;
	}
	return min;
}

void ServoStepperDriver::set_limits(int min, int max) {
	if (min <= max) {
		pos_min = min;
		pos_max = max;
	}
	else {
		pos_min = max;
		pos_max = min;
	}
}

void ServoStepperDriver::move(int steps) {
  bool dir = true;
	if (steps > 0) {
		digitalWrite(pin_direction, LOW);
	}
	else {
		digitalWrite(pin_direction, HIGH);
		steps = -steps;
    dir = false;
	}
	int position = analogRead(pin_pot);
	while (steps > 0) {
    if (dir && position >= pos_max) {
      _error = 1;
      return;
    }
    if (!dir && position <= pos_min) {
      _error = 2;
      return;
    }
		int steps_part = STEPPER_CHECK_CTR;
		if (steps < steps_part) {
			steps_part = steps;
		}
		for (int i=0; i<steps_part; i++) {
			digitalWrite(pin_step, HIGH);
			delayfunc(step_delay);
			digitalWrite(pin_step, LOW);
			delayfunc(step_delay);
		}
		steps -= steps_part;
		position = analogRead(pin_pot);
	}
}

int ServoStepperDriver::move_to(int target_position) {
	int position = analogRead(pin_pot);
	if (target_position > position) {
		digitalWrite(pin_direction, LOW);
		while (position < target_position) {
			for (int i=0; i<STEPPER_CHECK_CTR; i++) {
				digitalWrite(pin_step, HIGH);
				delayfunc(step_delay);
				digitalWrite(pin_step, LOW);
				delayfunc(step_delay);
			}
			position = analogRead(pin_pot);
		}
	}
	else if (target_position < position) {
		digitalWrite(pin_direction, HIGH);
		while (position > target_position) {
			for (int i=0; i<STEPPER_CHECK_CTR; i++) {
				digitalWrite(pin_step, HIGH);
				delayfunc(step_delay);
				digitalWrite(pin_step, LOW);
				delayfunc(step_delay);
			}
			position = analogRead(pin_pot);
		}
	}
	return position;
}

int ServoStepperDriver::error() {
  int e = _error;
  _error = 0;
  return e;
}
