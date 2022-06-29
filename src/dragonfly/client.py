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
from threading import Thread
import types

from logger import Logger, LogType
from message import *

class State(IntEnum):
    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    CRASHED = auto()

class Client:
    """Dragonfly client"""

    def __init__(self, username=None, password=None):
        """Initializes a Client instance

        Keyword Arguments:
            username {str} -- The client's username (default: {None})
            password {str} -- The client's password (default: {None})
        """

        self.username = username
        self.password = password
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.selector = selectors.DefaultSelector()
        self.thread = None
        self.state = State.STOPPED

        self.on_connected = lambda self, code: None
        self.on_published = lambda self, code: None
        self.on_subscribed = lambda self, code: None
        self.on_unsubscribed = lambda self, code: None
        self.on_message = lambda self, topic, msg: None
    
    def connect(self, host="localhost", port=1869):
        """Connects to a server and starts listening

        Keyword Arguments:
            host {str} -- The server's host (default: {"localhost"})
            port {int} -- The server's port (default: {1869})
        """

        self.state = State.STARTING
        self.socket.connect((host, port))
        self.socket.setblocking(False)
        data = types.SimpleNamespace(addr=(host, port), inb=b"", outb=b"", step=0, length=0)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(self.socket, events, data=data)

        msg = Message(ORIGIN_CLIENT, CONNECT)
        msg.username = self.username
        msg.password = self.password

        self.send(msg)

        self.state = State.RUNNING

        self.thread = Thread(target=self.mainloop, daemon=True)
        self.thread.start()
        
    def disconnect(self):
        """Stops this client"""

        self.state = State.STOPPING
        self.socket.close()
        self.state = State.STOPPED
    
    def mainloop(self):
        """Main event loop"""

        while self.state == State.RUNNING:
            events = self.selector.select(timeout=None)

            for key, mask in events:
                if not key.data is None:
                    self.handle_msg(key, mask)

    def send(self, msg):
        """Sends a message throught the socket

        Arguments:
            msg {Message} -- Message to send
        """
        
        self.socket.sendall(msg.to_bytes())
    
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
                    if data.length == 0:
                        data.step = 2

                if data.step == 2:
                    msg = Message()
                    try:
                        msg.from_bytes(data.outb)
                    
                    except:
                        Logger.warn(f"Malformed packet from {data.addr}")
                    
                    else:
                        Logger.debug(f"Received {msg} from {data.addr}")
                        self.process_msg(msg)
                    
                    finally:
                        data.step = 0
                        data.outb = b""
        
        # Ready to write
        if mask & selectors.EVENT_WRITE:
            pass

    def process_msg(self, msg):
        """Processes a message

        Arguments:
            msg {Message} -- The message instance
        """

        t = msg.type
        if t.origin == ORIGIN_SERVER:
            if t.type == CONNECTED:
                code = msg.code
                self.on_connected(self, code)
            
            elif t.type == PUBLISHED:
                code = msg.code
                self.on_published(self, code)
            
            elif t.type == SUBSCRIBED:
                code = msg.code
                self.on_subscribed(self, code)
            
            elif t.type == UNSUBSCRIBED:
                code = msg.code
                self.on_unsubscribed(self, code)
            
            elif t.type == PUBLISH:
                topic, body = msg.topic, msg.body
                self.on_message(self, topic, body)
    
    """
    Public api
    """

    def subscribe(self, topic):
        self.send(Message(ORIGIN_CLIENT, SUBSCRIBE, topic=topic))
    
    def unsubscribe(self, topic):
        self.send(Message(ORIGIN_CLIENT, UNSUBSCRIBE, topic=topic))
    
    def publish(self, topic, msg):
        self.send(Message(ORIGIN_CLIENT, PUBLISH, topic=topic, body=msg))


def on_c(self, code):
    Logger.info(f"Connected {code}")

def on_p(self, code):
    Logger.info(f"Published {code}")

def on_s(self, code):
    Logger.info(f"Subscribed {code}")

def on_u(self, code):
    Logger.info(f"Unsubscribed {code}")

def on_m(self, topic, msg):
    Logger.info(f"Message in {topic}: {msg}")

if __name__ == "__main__":
    #Logger.setup(LogType.ALL)
    Logger.setup(LogType.INFO|LogType.WARN|LogType.ERROR)

    username = "Baryhobal"
    password = "123456789"

    client = Client(username, password)
    client.connect()

    client.on_connected = on_c
    client.on_published = on_p
    client.on_subscribed = on_s
    client.on_unsubscribed = on_u
    client.on_message = on_m
    
    client.subscribe("test")
    input(">")

    client.subscribe("test")
    input(">")
    
    client.publish("test", "Essai")
    input(">")
    
    client.publish("essai", "Essai")
    input(">")
    
    client.unsubscribe("test")
    input(">")
    
    client.unsubscribe("test")
    input(">")

    client.publish("test", "Essai")
    input(">")

    """
    sub = Message(ORIGIN_CLIENT, SUBSCRIBE)
    sub.topic = "test"
    client.send(sub)
    input(">")
    
    client.send(sub)
    input(">")

    pub = Message(ORIGIN_CLIENT, PUBLISH)
    pub.topic = "test"
    pub.body = "Ceci est un test"
    client.send(pub)
    input(">")
    """

    """
    while True:
        c = input()
        if c:
            client.socket.sendall(c.encode("utf-8"))
        else:
            break"""

    client.disconnect()