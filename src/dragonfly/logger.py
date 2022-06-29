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
from enum import IntFlag, auto
from time import strftime

class LogType(IntFlag):
    INFO = auto()
    WARN = auto()
    ERROR = auto()
    DEBUG = auto()
    ALL = 15

class Logger:
    """Static logger"""

    level = LogType.WARN|LogType.ERROR

    def setup(level=LogType.WARN|LogType.ERROR):
        """Sets up the logging configuration

        Keyword Arguments:
            level {LogType} -- Log types to log (default: {LogType.WARN | LogType.ERROR})
        """

        Logger.level = level
    
    def log(msg, level):
        """Logs a message with the given log level

        Arguments:
            msg {str} -- Message to log
            level {LogType} -- Log level
        """

        if level & Logger.level == 0:
            return
        
        print(strftime("[%Y-%m-%d %H:%M:%S] "), end="")
        print(f"[{level.name}] ", end="")
        print(msg)
    
    def info(msg):
        """Logs a message with level LogType.INFO

        Arguments:
            msg {str} -- Message to log
        """

        Logger.log(msg, LogType.INFO)
    
    def warn(msg):
        """Logs a message with level LogType.WARN

        Arguments:
            msg {str} -- Message to log
        """

        Logger.log(msg, LogType.WARN)
    
    def error(msg):
        """Logs a message with level LogType.ERROR

        Arguments:
            msg {str} -- Message to log
        """

        Logger.log(msg, LogType.ERROR)
    
    def debug(msg):
        """Logs a message with level LogType.DEBUG

        Arguments:
            msg {str} -- Message to log
        """

        Logger.log(msg, LogType.DEBUG)