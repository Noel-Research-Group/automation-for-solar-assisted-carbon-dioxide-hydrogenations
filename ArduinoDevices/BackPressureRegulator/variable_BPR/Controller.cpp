// Controller.cpp
#include "Controller.h"

#include <math.h>

Controller::Controller() {
	mode = Mode::STANDBY;
	target = 0.0;
	setCurve(1.0, 5.0, 10.0, 10.0, 20.0, false);
}

void Controller::setCurve(float permissible_e, float slow_e, float slow_r, float fast_e, float fast_r, bool invert) {
	if (permissible_e >= 0 and slow_e > permissible_e and fast_e > slow_e) {
		Kp = (fast_r - slow_r)/(fast_e - slow_e);
		Qp = slow_r - (Kp*slow_e);
		Kp2 = slow_r/slow_e;
		e_allowed = permissible_e;
		e_slow = slow_e;
		e_fast = fast_e;
		r_slow = slow_r;
		r_fast = fast_r;
		inverted = invert;
	}
}

void Controller::setTarget(float value) {
	target = value;
	mode = Mode::ADJUST;	// Force correction on call
}

float Controller::getTarget() {
	return target;
}

void Controller::output(float input, int& move, float& speed) {
	move = 0;
	speed = 0.0;
	float error = target - input;	// Calculate error
											// Internally, keep everything positive:
	int sign = +1;
	if (error < 0) {
		error = -error;
		sign = -1;
	}
	if (inverted) {
		sign = -sign;
	}
	// If in standby...
	if (mode == Mode::STANDBY) {
		// Check whether should get out of standby
		if (error <= e_allowed) {
			// no, all good
			return;
		}
		else {
			// yes, proceed as if mode != STANDBY
			mode = Mode::ADJUST;
		}
	}
	// If not in standby...
	if (error <= (e_allowed/5.0)) {
		// target reached, go to standby
		mode = Mode::STANDBY;
		return;
	}
	else if (error <= e_slow) {
		move = round(Kp2*error);
		speed = r_slow/0.25;
	}
	else if (error >= e_fast) {
		move = round(r_fast);
		speed = r_fast/0.25;
	}
	else {
		move = round(Qp + (Kp*error));
		speed = move/0.25;
	}
	// return a signed output
	move = sign*move;
}
