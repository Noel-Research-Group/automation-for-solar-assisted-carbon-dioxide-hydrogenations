# Python GUI for controlling several serial devices
# Designed for use with the solar simulator setup.
#
# Author: Simone Pilon - Noël Research Group - 2023
import os
import Command_Line_Arguments
import Device_Configuration
import Monitor_Window

if __name__ == '__main__':
    # Project assumes running directory to be project root, refuses to run if not.
    path_to_main = os.path.dirname(os.path.realpath(__file__))
    current_directory = os.getcwd()
    if not path_to_main == current_directory:
        print(
            "Solar Simulator Monitor must run from project root (the directory with the main.py script).\nMake sure "
            "to cd or set the working directory properly and re-run.")
        exit(1)

    parser = Command_Line_Arguments.solar_simulator_monitor_argparser()
    args = parser.parse_args()
    configurations = Device_Configuration.DeviceConfiguration()
    configuration = None
    if args.configuration:
        try:
            configuration = configurations[args.configuration]
        except KeyError as e:
            print(e)
            print('Available configurations:')
            for name in configurations.keys():
                print(f"    {name}")
            exit(1)
    else:
        available_configurations = list(configurations.keys())
        device_choice_window = Monitor_Window.MultipleChoiceWindow(available_configurations)
        device_choice_window.mainloop()
        configuration = configurations[device_choice_window.choice]

    monitor_window = Monitor_Window.MonitorWindow(configuration)
    monitor_window.mainloop()
