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

ORIGIN_SERVER = 0
ORIGIN_CLIENT = 1

FLAG_0 = 1
FLAG_1 = 2
FLAG_2 = 4
FLAG_3 = 8

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
    """Dragonfly message"""

    def __init__(self, origin=ORIGIN_SERVER, type_=CONNECT, flags=0, **kwargs):
        """Initializes a Message instance

        Keyword Arguments:
            origin {int} -- The message's origin, either ORIGIN_SERVER or ORIGIN_CLIENT (default: {ORIGIN_SERVER})
            type_ {int} -- The message's type, one of [CONNECT, CONNECTED, PUBLISH, PUBLISHED, SUBSCRIBE, SUBSCRIBED, UNSUBSCRIBE, UNSUBSCRIBED] (default: {CONNECT})
            flags {int} -- The message's flags (default: {0})
            **kwargs: additional message properties
        """

        self.bytes = b""
        self.version = 0
        self.type = MessageType(origin<<7 | type_<<4 | flags)
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def __repr__(self):
        #return f"<v{self.version} Message of type {self.type}>"
        return str(self.__dict__)
    
    def from_bytes(self, bytes_):
        """Parses a message from bytes

        Arguments:
            bytes_ {bytes} -- The message's bytes
        """

        self.bytes = bytes_
        stream = ByteStream(bytes_)
        self.version = struct.unpack(">H", stream.read(2))[0]
        self.type = MessageType(stream.read(1)[0])
        self.body_length = struct.unpack(">I", stream.read(4))[0]

        if self.type.type == CONNECT:
            self.username, self.password = None, None

            if self.type.flags & FLAG_1:
                self.username = self.read_string(stream)
            
            if self.type.flags & FLAG_0:
                self.password = self.read_string(stream)

        elif self.type.type == PUBLISH:
            self.topic = self.read_string(stream)
            self.body = self.read_string(stream)

        elif self.type.type == SUBSCRIBE:
            self.topic = self.read_string(stream)

        elif self.type.type == UNSUBSCRIBE:
            self.topic = self.read_string(stream)
        
        elif self.type.type in [PUBLISHED, SUBSCRIBED, UNSUBSCRIBED]:
            self.code = struct.unpack(">B", stream.read(1))[0]
        

    def to_bytes(self):
        """Formats the message to bytes

        Returns:
            bytes -- The message's bytes
        """

        bytes_ = b""

        body = b""

        if self.type.type == CONNECT:
            if self.username:
                self.type.flags |= FLAG_1
                body += self.write_string(self.username)
            
            if self.password:
                self.type.flags |= FLAG_0
                body += self.write_string(self.password)

        elif self.type.type == PUBLISH:
            body += self.write_string(self.topic)
            body += self.write_string(self.body)

        elif self.type.type == SUBSCRIBE:
            body += self.write_string(self.topic)

        elif self.type.type == UNSUBSCRIBE:
            body += self.write_string(self.topic)
        
        elif self.type.type in [PUBLISHED, SUBSCRIBED, UNSUBSCRIBED]:
            body += struct.pack(">B", self.code)

        bytes_ += struct.pack(">H", self.version)
        bytes_ += self.type.to_bytes()
        bytes_ += struct.pack(">I", len(body))
        bytes_ += body

        self.bytes = bytes_
        return bytes_
    
    def read_string(self, stream):
        """Reads a string from a byte stream

        A string is always preceeded by a 2 byte unsigned short indicating its
        length.
        Strings are decoded in UTF-8

        Arguments:
            stream {ByteStream} -- Input stream

        Returns:
            str -- Decoded string
        """

        length = struct.unpack(">H", stream.read(2))[0]
        return stream.read(length).decode("utf-8")
    
    def write_string(self, string):
        """Formats a string to bytes

        A string is always preceeded by a 2 byte unsigned short indicating its
        length.
        Strings are encoded in UTF-8

        Arguments:
            string {str} -- String to encode

        Returns:
            bytes -- Encoded string
        """

        bytes_ = struct.pack(">H", len(string))
        bytes_ += string.encode("utf-8")
        return bytes_