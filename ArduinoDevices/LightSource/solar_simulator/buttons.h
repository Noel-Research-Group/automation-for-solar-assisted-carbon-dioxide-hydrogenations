#ifndef BUTTONS_h
#define BUTTONS_h

/*
	Control of push buttons with debounce.

	This file is part of the lights controller for the Solar Simulator setup.

	by Simone Pilon <s.pilon at uva.nl> - Noël Research Group - 2023
 */

#define BUTTON_DEBOUNCE 200	// Inhibit a second press until this many millisenconds have elapsed

class Button {
	public:
		Button(int pin);

		bool isPressed();		// Returns true if the button is pressed and enough time has past since last press.
		bool isDown();			// Returns true if the button is pressed, use only for holding down.
		
		void disable(int time);	// Disables button press for some time (in mS) starting from function call.

	private:
		long int last_press;	// Stores the moment a button is pressed (calls millis())
		int disable_ctr;		// Disables the button for milliseconds.
		int pin;	// Stores the pin number associated with the button.

};

#endif  //BUTTONS_h
