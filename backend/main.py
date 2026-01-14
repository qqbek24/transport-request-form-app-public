import sys

from bot_framework import Bot


class ConfigModel:
    """Config model for the bot - for intelisense of congig.yaml params"""
    max_run_time: int
    # add your config entries here

class Task(Bot): # Process
    """Your bot class"""

    __version__ = '0.0.0.1'

    def __init__(self, sysargs):

        self.config = ConfigModel  # Use if you want

        super().__init__(sysargs)


if __name__ == '__main__':      


    with Task(sysargs=sys.argv) as bot:
        print('inside with')