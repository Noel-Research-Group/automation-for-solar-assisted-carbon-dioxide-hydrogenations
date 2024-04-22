import argparse

def solar_simulator_monitor_argparser():
    """Returns the ArgumentParser object for the solar simulator monitor."""
    parser = argparse.ArgumentParser(prog='Solar Simulator Monitor',
                                     description="""Solar Simulator Monitor is a visual tool to control the 
        various devices which make up the Solar Simulator setup interactively or by setting a schedule for different 
        conditions to be applied at time intervals.""",
                                     epilog='Author: Simone Pilon - Noël Research Group - 2023.')
    parser.add_argument('-c', '--configuration', help='Specify hardware configuration from the command line.')
    return parser