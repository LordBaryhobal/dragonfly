#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Dragonfly is an mqtt-like communication protocol
# Copyright (C) 2022  Louis HEREDERO

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import logging

FORMAT = "[%(asctime)s][%(levelname)s] %(message)s"  #: Logging format
DATEFMT = "%Y-%m-%d %H:%M:%S"  #: Logging date format

class ColorFormatter(logging.Formatter):
    """Logging formatter to colorize output

    * Critical: bold red
    * Error: red
    * Warning: yellow
    * Info: grey
    * Debug: italic magenta
    """

    italic_magenta = "\x1b[95;3m"
    grey = "\x1b[37m"
    yellow = "\x1b[33m"
    red = "\x1b[31m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: italic_magenta,
        logging.INFO: grey,
        logging.WARNING: yellow,
        logging.ERROR: red,
        logging.CRITICAL: bold_red
    }

    def __init__(self, fmt=None, datefmt=None, style="%"):
        super().__init__(fmt, datefmt, style)
        self.my_fmt = fmt
        self.my_datefmt = datefmt

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt+self.my_fmt+ColorFormatter.reset, self.my_datefmt)
        return formatter.format(record)

def setup():
    """Sets up logging for the module

    Sets up a ColorFormatter for console logging using :py:const:`FORMAT` and
    :py:const:`DATEFMT`.
    """

    logger = logging.getLogger("dragonfly")
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    ch.setFormatter(ColorFormatter(FORMAT, DATEFMT))
    logger.addHandler(ch)
