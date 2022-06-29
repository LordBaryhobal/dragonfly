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
import struct

from bytes import ByteStream
from logger import Logger

CONNECT = 0
CONNECTED = 1
PUBLISH = 2
PUBLISHED = 3
SUBSCRIBE = 4
SUBSCRIBED = 5
UNSUBSCRIBE = 6
UNSUBSCRIBED = 7

class MessageType:
    def __init__(self, byte):
        self.origin = (byte & 0x80) >> 7
        self.type = (byte & 0x70) >> 4
        self.flags = byte & 0x0f
    
    def __repr__(self):
        l = ["CONNECT", "CONNECTED", "PUBLISH", "PUBLISHED", "SUBSCRIBE", "SUBSCRIBED", "UNSUBSCRIBE", "UNSUBSCRIBED"]
        return f"{self.origin} {l[self.type]} {self.flags:04b}"
    
    def to_bytes(self):
        n = (self.origin << 7) | \
            (self.type << 4) | \
            self.flags
        
        return n.to_bytes(1, "big")

class Message:
    def __init__(self, version=0, type_=None):
        self.version = version
        self.type = type_
    
    def __repr__(self):
        #return f"<v{self.version} Message of type {self.type}>"
        return str(self.__dict__)
    
    def from_bytes(self, bytes_):
        stream = ByteStream(bytes_)
        self.version = struct.unpack(">H", stream.read(2))[0]
        self.type = MessageType(stream.read(1)[0])
        self.body_length = struct.unpack(">I", stream.read(4))[0]

        if self.type.type == CONNECT:
            self.username, self.password = None, None

            if self.type.flags & 2:
                self.username = self.read_string(stream)
            
            if self.type.flags & 1:
                self.password = self.read_string(stream)
        

    def to_bytes(self):
        bytes_ = b""

        body = b""

        if self.type.type == CONNECT:
            if self.username:
                self.type.flags |= 2
                body += self.write_string(self.username)
            
            if self.password:
                self.type.flags |= 1
                body += self.write_string(self.password)


        bytes_ += struct.pack(">H", self.version)
        bytes_ += self.type.to_bytes()
        bytes_ += struct.pack(">I", len(body))
        bytes_ += body

        return bytes_
    
    def read_string(self, stream):
        length = struct.unpack(">H", stream.read(2))[0]
        return stream.read(length).decode("utf-8")
    
    def write_string(self, string):
        bytes_ = struct.pack(">H", len(string))
        bytes_ += string.encode("utf-8")
        return bytes_