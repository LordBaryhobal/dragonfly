#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dragonfly is an mqtt-like communication protocol
Copyright (C) 2022  Louis HEREDERO

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from enum import IntEnum, auto
import socket

from logger import Logger, LogType
from message import *

class State(IntEnum):
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    CRASHED = auto()

class Client:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def connect(self, host="localhost", port=1869):
        self.socket.connect((host, port))

        msg = Message()
        msg.type = MessageType(1<<7 | CONNECT<<4 | 0)
        msg.username = self.username
        msg.password = self.password

        self.socket.sendall(msg.to_bytes())
        
    def disconnect(self):
        self.socket.close()

if __name__ == "__main__":
    Logger.setup(LogType.ALL)

    username = "Baryhobal"
    password = "123456789"

    client = Client(username, password)
    client.connect()
    
    """
    while True:
        c = input()
        if c:
            client.socket.sendall(c.encode("utf-8"))
        else:
            break"""

    client.disconnect()
