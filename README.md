![nrg logo](https://github.com/Noel-Research-Group/automation-for-solar-assisted-carbon-dioxide-hydrogenations/blob/main/imgs/NRG-Logo.png)

# automated reactor system for solar-assisted carbon dioxide hydrogenations over heterogeneous catalysts

In this repository you can find all information regarding the software side of the solar simulator setup, as well as 3D files, firmware and connectivity diagrams to build the custom devices developed for this project.

The repository includes:

## SolarSimulatorMonitor

A visual interactive tool to control and monitor the different devices that are part of the solar simulator setup on the go.
Any number of setups can be configured, each with their unique combination of devices.
This is programmed in python with few external dependences, find detailed instructions with the code under `./SolarSimulatorMonitor`.

![screenshot of solar simulator monitor](https://github.com/Noel-Research-Group/automation-for-solar-assisted-carbon-dioxide-hydrogenations/blob/main/imgs/monitor.png)

## Controller for automated variable backpressure regulator

Device for automated control of backpressure in a flow setup.
This repo includes data on the construction of the physiscal device, code for the Arduino UNO controller
and documentation on controlling the device via serial-through-USB.
Find all of this under `./AduinoDevices/BackPressureRegulator` (includes documentation).

![screenshot of solar simulator monitor](https://github.com/Noel-Research-Group/automation-for-solar-assisted-carbon-dioxide-hydrogenations/blob/main/imgs/vbpr.jpeg)

## Controller for the light source of the solar simulator setup

Device for automatic control of HLG-480H-xx-AB power suppply. This power supply unit controls the light output of the Solar Simulator Setup, and the arduino-based control device allows the intesity to be controlled remotely and automatically from a computer via serial-thrugh-USB interface.
The device allows for direct user control via 3 buttons and a 2-lines LCD display.
The device also controls the cooling fans of the LED lights.
Find all of this under `./AduinoDevices/LightSource` (includes documentation).
