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
        self.clients = []
        self.topics = {}
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

    def new_conn(self, sock):
        """Accepts a new connection

        Arguments:
            sock {socket.socket} -- incoming socket connection
        """

        conn, addr = sock.accept()
        client = self.new_client(conn)
        Logger.debug(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", step=0, length=0, id=client.id)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(conn, events, data=data)

    def close_conn(self, id_):
        """Closes a previously established connection

        Arguments:
            id_ {int} -- Client id
        """

        client = self.clients[id_]
        Logger.debug(f"Closing connection {client.socket.getpeername()}")
        self.selector.unregister(client.socket)
        client.socket.close()
        self.remove_client(id_)

    def handle_msg(self, key, mask):
        """Handles an event

        Arguments:
            key {selectors.SelectorKey} -- The event's key
            mask {selectors._EventMask} -- The event's mask
        """

        sock = key.fileobj
        data = key.data

        # Ready to read
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(data.length if data.step == 1 else 7)
            
            if recv_data:
                data.outb += recv_data
                data.step += 1
                
                if data.step == 1:
                    data.length = struct.unpack(">I", data.outb[-4:])[0]

                elif data.step == 2:
                    msg = Message()
                    try:
                        msg.from_bytes(data.outb)
                    
                    except:
                        Logger.warn(f"Malformed packet from {data.addr}")
                    
                    else:
                        Logger.debug(f"Received {msg} from {data.addr}")
                    
                    finally:
                        data.step = 0
                        data.outb = b""
            
            else:
                self.close_conn(data.id)
        
        # Ready to write
        if mask & selectors.EVENT_WRITE:
            pass
    
    def new_client(self, sock):
        """Registers new client

        Arguments:
            sock {socket.socket} -- Client socket

        Returns:
            Client -- The new client instance
        """

        if not None in self.clients:
            self.clients.append(None)
        
        id_ = self.clients.index(None)
        client = Client(sock, id_)
        self.clients[id_] = client

        return client

    def remove_client(self, id_):
        """Unregisters a client

        Arguments:
            id_ {int} -- The client's id
        """

        client = self.clients[id_]
        for topic in client.topics:
            self.topics[topic].remove(id_)
        
        self.clients[id_] = None
    
class Client:
    """Represents a client"""

    def __init__(self, sock, id_):
        """Initializes a Client instance

        Arguments:
            sock {socket.socket} -- The client socket
            id_ {int} -- The client's id (see Server#new_client)
        """

        self.socket = sock
        self.username = None
        self.password = None
        self.topics = []
        self.id = id_
    
    def __repr__(self):
        return f"<Client {self.id} topics={self.topics}>"
    
    def send(self, msg):
        """Sends a message through the socket

        Arguments:
            msg {Message} -- Message to send
        """

        self.socket.sendall(msg.to_bytes())
    
    def check_auth(self, scope, *args):
        """Checks user rights in `scope`

        Arguments:
            scope {int} -- Message type

        Returns:
            bool -- True if the client is authorized in this scope
        
        Todo:
            * Write the function
        """
        
        return True

if __name__ == "__main__":
    Logger.setup(LogType.ALL)

    import threading
    server = Server()
    
    t = threading.Thread(target=server.start, daemon=True)
    t.start()

    input()
    server.stop()