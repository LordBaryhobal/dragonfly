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
import selectors
import socket
import struct
import types

from logger import Logger, LogType
from message import *

class State(IntEnum):
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    CRASHED = auto()

class Server:
    """Dragonfly server"""

    def __init__(self, host="localhost", port=1869):
        """Initializes a Server instance

        Keyword Arguments:
            host {str} -- Socket host (default: {"localhost"})
            port {int} -- Socket port (default: {1869})
        """

        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.state = State.STOPPED
    
    def start(self):
        """Starts this server"""

        self.state = State.STARTING
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.socket.setblocking(False)
        self.selector.register(self.socket, selectors.EVENT_READ, data=None)
        Logger.info(f"Dragonfly server listening on {(self.host, self.port)}")
        self.state = State.RUNNING

        self.mainloop()
    
    def stop(self):
        """Closes this server's socket"""

        self.state = State.STOPPING
        self.socket.close()
        self.state = State.STOPPED
    
    def mainloop(self):
        """Main event loop"""

        while self.state == State.RUNNING:
            events = self.selector.select(timeout=None)

            for key, mask in events:
                # Listening socket
                if key.data is None:
                    self.new_conn(key.fileobj)
                
                # Data
                else:
                    self.handle_msg(key, mask)

    def new_conn(self, socket):
        """Accepts a new connection

        Arguments:
            socket {socket.socket} -- incoming socket connection
        """
        conn, addr = socket.accept()
        Logger.debug(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", step=0, length=0)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(conn, events, data=data)

    def close_conn(self, socket):
        """Closes a previously established connection

        Arguments:
            socket {socket.socket} -- Socket to close
        """

        Logger.debug(f"Closing connection {socket.getpeername()}")
        self.selector.unregister(socket)
        socket.close()

    def handle_msg(self, key, mask):
        """Handles an event

        Arguments:
            key {selectors.SelectorKey} -- The event's key
            mask {selectors._EventMask} -- The event's mask
        """

        socket = key.fileobj
        data = key.data

        # Ready to read
        if mask & selectors.EVENT_READ:
            recv_data = socket.recv(data.length if data.step == 1 else 7)
            
            if recv_data:
                data.outb += recv_data
                data.step += 1
                
                if data.step == 1:
                    data.length = struct.unpack(">I", data.outb[-4:])[0]

                elif data.step == 2:
                    msg = Message()
                    msg.from_bytes(data.outb)
                    Logger.debug(f"Received {msg} from {data.addr}")
                    data.step = 0
                    data.outb = b""
            
            else:
                self.close_conn(socket)
        
        # Ready to write
        if mask & selectors.EVENT_WRITE:
            pass

if __name__ == "__main__":
    Logger.setup(LogType.ALL)

    import threading
    server = Server()
    
    t = threading.Thread(target=server.start, daemon=True)
    t.start()

    input()
    server.stop()