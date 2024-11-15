/*
	File: buttons.cpp
	Author: Simone Pilon <s.pilon at uva.nl> - Noël Research Group - 2023
	GitHub: https://github.com/simone16
	Comment: Control of push buttons with debounce.
 */

#include "buttons.h"

#include "Arduino.h"

Button::Button(int _pin) {
	last_press = 0;
	disable_ctr = BUTTON_DEBOUNCE;
	pin = _pin;
}

bool Button::isPressed() {
	long int time = millis();
	if (digitalRead(pin) == HIGH && time - last_press >= disable_ctr) {
		disable(BUTTON_DEBOUNCE);
		return true;
	}
	return false;
}

bool Button::isDown() {
	return digitalRead(pin) == HIGH;
}

void Button::disable(int time) {
	last_press = millis();
	disable_ctr = time;
}
