"""
File: Default_Logger.py
Author: Simone Pilon - Noël Research Group - 2023
GitHub: https://github.com/simone16
Description: Defines a default logger function.
"""

import time


def print_message(message: str, **kwargs):
    """Print a message to the console.
    This is a wrapper to enable classes of the solar simulator monitor to use the same parameters for printing messages
    to the console or to the Monitor_Window logging area.

    :param message: str
        The message to be given to the user.
    :param kwargs:
        See below.

    :Keyword Arguments:
        * error (``bool``) --
          If true the message will be highlighted as an error."""
    message = f"{time.strftime('%H:%M:%S')} {message}\n"
    if ('error' in kwargs.keys()) and kwargs['error']:
        message = '[ERROR] ' + message
    print(message)
