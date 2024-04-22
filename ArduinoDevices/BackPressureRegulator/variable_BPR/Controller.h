// Controller.h
#ifndef CONTROLLER_h
#define CONTROLLER_h

// This is a purely proportional controller (PID, without I and D).
// Response curve:
//
// response
//  max ^ . . . .___________
//      |       /
//      |      /.
//  min | |---/ .
//      +-------------------> error
//        ^   ^ ^
//        |   | |_fast threshold
//        |   |_slow threshold
//        |_permissible threshold
//
// Author: Simone Pilon <s.pilon@uva.nl>

class Controller {
	public:
		Controller();

		// Set the response curve (all error parameters must be positive):
		// @param permissible_e Within this error, response is 0
		// @param slow_e beyond this deviation, proportional response is calculated
		// @param slow_r This response is given below slow_e
		// @param fast_e beyond this deviation, maximuma response fast_r  is given
		// @param fast_r the maximum response given beyond fast_e
		// @param invert Set to true to invert the direction of the movement
		void setCurve(float permissible_e, float slow_e, float slow_r, float fast_e, float fast_r, bool invert);

		void setTarget(float value);	// Set the desired target
		float getTarget();				// Return the set target

		void output(float input, int& move, float& speed);	// Calculate required move and speed.

	private:
		typedef enum Mode {
			STANDBY,
			ADJUST
		};

		Controller::Mode mode;	// Defines controller behaviour. 

		float target;	// The desired measured value to obtain.

		float e_allowed;	// Maximum allowed deviation from target.
		float e_slow;	// slow threshold
		float e_fast;	// fast threshold
		float Kp;		// Proportional factor K (response = error*Kp + Qp).
		float Qp;		// Proportional factor Q (response = error*Kp + Qp).
		float r_slow;	// slow response
		float r_fast;	// fast response
		float Kp2;		// Proportional factor K (response = error*Kp) for fine_adjust.
		bool inverted;  // If true inverts response.
};

#endif // CONTROLLER_h
