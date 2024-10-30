/*
	File: StepperDriver.h
	Author: Simone Pilon <s.pilon at uva.nl> - Noël Research Group - 2023
	GitHub: https://github.com/simone16
	Comment: Controls a stepper motor with STEP & DIR interface.
 */

#ifndef STEPPERDRIVER_h
#define STEPPERDRIVER_h

class StepperDriver {
	public:
		StepperDriver(int pin_enable, int pin_direction, int pin_step);

		void init();	// Set up pins, this needs to be called once in setup.

		void enable(bool enable);	// Enable or disable motor

		void setSpeed(float speed);	// Set the speed in steps/Second

		void move(int steps);	// Moves the motor. The function does not return until the movement is complete!

	protected:
		int pin_enable;
		int pin_direction;
		int pin_step;

		void (*delayfunc)(int);	// Pointer to delay function to be used
		int step_delay;
};

// Position is checked every this many steps
#define STEPPER_CHECK_CTR 100

class ServoStepperDriver : public StepperDriver {
  public:
    ServoStepperDriver(int pin_enable, int pin_direction, int pin_step, int pin_pot);

    void init();	// Set up pins, this needs to be called once in setup.

	 int position();	// Returns current position.
    int set_max();	// Sets current position as maximum. Returns position
    int set_min();	// Sets current position as minimum. Returns position
    void set_limits(int min, int max);  // Sets given values as maximum and minimum positions.
		
	 void move(int steps);	// Moves the motor by a number of steps. The function does not return until the movement is complete!
	 int move_to(int position);	// Moves the motor until the desired position is reached. This is not necessarily 100% accurate, the actual position reached is returned.

    int error();    // Returns an error code for the last error occurred, or 0 for no error. Calling resets the error flag.

  protected:
    int pin_pot;

    int pos_max;
    int pos_min;

    int _error;
};

#endif // STEPPERDRIVER_h
