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
import unittest
import struct
import sys

sys.path.append("src")

from dragonfly.bytes import ByteStream
from dragonfly.exceptions import InvalidMessageType
from dragonfly.message import ORIGIN_SERVER, ORIGIN_CLIENT
from dragonfly.message import CONNECT, CONNECTED, PUBLISH, PUBLISHED, SUBSCRIBE, SUBSCRIBED, UNSUBSCRIBE, UNSUBSCRIBED
from dragonfly.message import Message, MessageType, type_name

class TestMessageDefaults(unittest.TestCase):
    def setUp(self):
        self.msg = Message()
    
    def test_version(self):
        self.assertEqual(self.msg.version, 0)
    
    def test_origin(self):
        self.assertEqual(self.msg.type.origin, 0)
    
    def test_type(self):
        self.assertEqual(self.msg.type.type, 0)
    
    def test_flags(self):
        self.assertEqual(self.msg.type.flags, 0)

class TestMessageEncoding(unittest.TestCase):
    def test_non_utf8_decode(self):
        with self.assertLogs("dragonfly", logging.ERROR):
            msg = Message()
            # type: PUBLISH / length: 7 / topic: . / body: \xc0\x80 -> invalid
            msg.from_bytes(b"\x00\x00\x20\x00\x00\x00\x07\x00\x01\x2e\x00\x02\xc0\x80")
    
    def test_non_utf8_encode(self):
        with self.assertLogs("dragonfly", logging.ERROR):
            msg = Message()
            msg.username = u"\ud835"
            msg.to_bytes()

    def test_malformed(self):
        with self.assertLogs("dragonfly", logging.ERROR):
            msg = Message()
            msg.from_bytes(b"")
    
    def test_missing_property(self):
        types = [
            (PUBLISH, ["topic", "body"]),
            (SUBSCRIBE, ["topic"]),
            (UNSUBSCRIBE, ["topic"])
        ]

        for t, props in types:
            d = {p: None for p in props}
            for prop in props:
                d_ = d.copy()
                del d_[prop]
                
                with self.subTest(type=t, property=prop):
                    msg = Message(type_=t, **d_)
                    
                    with self.assertLogs("dragonfly", logging.ERROR):
                        msg.to_bytes()

    def test_encode_origin(self):
        with self.subTest(origin=ORIGIN_SERVER):
            msg = Message(origin=ORIGIN_SERVER)
            self.assertEqual(msg.to_bytes(), b"\x00\x00\x00\x00\x00\x00\x00")
        
        with self.subTest(origin=ORIGIN_CLIENT):
            msg = Message(origin=ORIGIN_CLIENT)
            self.assertEqual(msg.to_bytes(), b"\x00\x00\x80\x00\x00\x00\x00")

    def test_encode_type(self):
        types = [CONNECT, CONNECTED, PUBLISH, PUBLISHED, SUBSCRIBE, SUBSCRIBED, UNSUBSCRIBE, UNSUBSCRIBED]

        for t in types:
            with self.subTest(type=t):
                msg = Message(type_=t, topic=None, body=None)
                b = (t << 4).to_bytes(1, "big")
                length = 1
                if t == PUBLISH:
                    length = 4
                elif t == CONNECT:
                    length = 0
                elif t in [SUBSCRIBE, UNSUBSCRIBE]:
                    length = 2
                
                self.assertEqual(msg.to_bytes(), b"\x00\x00"+b+struct.pack(">I", length)+b"\x00"*length)
    
    def test_invalid_type(self):
        with self.assertLogs("dragonfly", logging.ERROR):
            msg = Message()
            msg.type.type = 7239847598
            msg.to_bytes()
    
    def test_decode_connect(self):
        bytes_ = b"\x00\x00\x00\x00\x00\x00\x00"
        msg = Message()
        msg.from_bytes(bytes_)

        self.assertEqual(msg.type.type, CONNECT)
        self.assertEqual(msg.username, None)
        self.assertEqual(msg.password, None)

    def test_decode_connect_username_password(self):
        bytes_ = b"\x00\x00\x03\x00\x00\x00\x0b\x00\x04\x55\x73\x65\x72\x00\x03\x50\x77\x64"
        msg = Message()
        msg.from_bytes(bytes_)

        self.assertEqual(msg.username, "User")
        self.assertEqual(msg.password, "Pwd")
    
    def test_decode_connect_username(self):
        bytes_ = b"\x00\x00\x02\x00\x00\x00\x06\x00\x04\x55\x73\x65\x72"
        msg = Message()
        msg.from_bytes(bytes_)

        self.assertEqual(msg.username, "User")
        self.assertEqual(msg.password, None)
    
    def test_decode_connect_password(self):
        bytes_ = b"\x00\x00\x01\x00\x00\x00\x05\x00\x03\x50\x77\x64"
        msg = Message()
        msg.from_bytes(bytes_)

        self.assertTrue(hasattr(msg, "password"))
        self.assertEqual(msg.username, None)
        self.assertEqual(msg.password, "Pwd")

    def test_decode_publish(self):
        msg = Message()
        
        # type: PUBLISH / length: 9 / topic: . / body: Body
        bytes_ = b"\x00\x00\x20\x00\x00\x00\x09\x00\x01\x2e\x00\x04\x42\x6f\x64\x79"
        msg.from_bytes(bytes_)

        self.assertEqual(msg.type.type, PUBLISH)
        self.assertEqual(msg.topic, ".")
        self.assertEqual(msg.body, "Body")

    def test_decode_subscribe(self):
        msg = Message()
        
        # type: SUBSCRIBE / length: 3 / topic: .
        bytes_ = b"\x00\x00\x40\x00\x00\x00\x03\x00\x01\x2e"
        msg.from_bytes(bytes_)

        self.assertEqual(msg.type.type, SUBSCRIBE)
        self.assertEqual(msg.topic, ".")

    def test_decode_unsubscribe(self):
        msg = Message()
        
        # type: UNSUBSCRIBE / length: 3 / topic: .
        bytes_ = b"\x00\x00\x60\x00\x00\x00\x03\x00\x01\x2e"
        msg.from_bytes(bytes_)

        self.assertEqual(msg.type.type, UNSUBSCRIBE)
        self.assertEqual(msg.topic, ".")
    
    def test_decode_ack(self):
        for t in [CONNECTED, PUBLISHED, SUBSCRIBED, UNSUBSCRIBED]:
            with self.subTest(type=t):
                msg = Message()
                
                b = (t << 4).to_bytes(1, "big")
                bytes_ = b"\x00\x00"+b+b"\x00\x00\x00\x01\x2a"
                msg.from_bytes(bytes_)

                self.assertEqual(msg.type.type, t)
                self.assertEqual(msg.code, 42)
    


    def test_encode_connect(self):
        bytes_ = b"\x00\x00\x00\x00\x00\x00\x00"
        msg = Message(type_=CONNECT)
        self.assertEqual(msg.to_bytes(), bytes_)

    def test_encode_connect_username_password(self):
        bytes_ = b"\x00\x00\x03\x00\x00\x00\x0b\x00\x04\x55\x73\x65\x72\x00\x03\x50\x77\x64"
        msg = Message(type_=CONNECT, username="User", password="Pwd")
        self.assertEqual(msg.to_bytes(), bytes_)
    
    def test_encode_connect_username(self):
        bytes_ = b"\x00\x00\x02\x00\x00\x00\x06\x00\x04\x55\x73\x65\x72"
        msg = Message(type_=CONNECT, username="User")
        self.assertEqual(msg.to_bytes(), bytes_)
    
    def test_encode_connect_password(self):
        bytes_ = b"\x00\x00\x01\x00\x00\x00\x05\x00\x03\x50\x77\x64"
        msg = Message(type_=CONNECT, password="Pwd")
        self.assertEqual(msg.to_bytes(), bytes_)

    def test_encode_publish(self):
        bytes_ = b"\x00\x00\x20\x00\x00\x00\x09\x00\x01\x2e\x00\x04\x42\x6f\x64\x79"
        msg = Message(type_=PUBLISH, topic=".", body="Body")
        self.assertEqual(msg.to_bytes(), bytes_)

    def test_encode_subscribe(self):
        bytes_ = b"\x00\x00\x40\x00\x00\x00\x03\x00\x01\x2e"
        msg = Message(type_=SUBSCRIBE, topic=".")
        self.assertEqual(msg.to_bytes(), bytes_)

    def test_encode_unsubscribe(self):
        bytes_ = b"\x00\x00\x60\x00\x00\x00\x03\x00\x01\x2e"
        msg = Message(type_=UNSUBSCRIBE, topic=".")
        self.assertEqual(msg.to_bytes(), bytes_)
    
    def test_encode_ack(self):
        for t in [CONNECTED, PUBLISHED, SUBSCRIBED, UNSUBSCRIBED]:
            with self.subTest(type=t):
                b = (t << 4).to_bytes(1, "big")
                bytes_ = b"\x00\x00"+b+b"\x00\x00\x00\x01\x2a"
                msg = Message(type_=t, code=42)
                self.assertEqual(msg.to_bytes(), bytes_)

class TestByteStream(unittest.TestCase):
    def setUp(self):
        self.bytes = b"".join([n.to_bytes(1, "big") for n in range(8)])
        self.stream = ByteStream(self.bytes)
    
    def test_seek(self):
        # pos, offset, anchor, result
        positions = [
            (0, 0, 0, 0),
            (4, 0, 0, 0),
            (0, 4, 0, 4),
            (2, 2, 0, 2),

            (0, 0, 1, 0),
            (4, 0, 1, 4),
            (0, 4, 1, 4),
            (2, 2, 1, 4),

            (0, 0, 2, 8),
            (4, 0, 2, 8),
            (0,-4, 2, 4),
            (2,-2, 2, 6),

            (0, -4, 0, 0),
            (0, 10, 0, 8),
            (0, -4, 1, 0),
            (6,  4, 1, 8),
            (0,-10, 2, 0),
            (0,  4, 2, 8)
        ]

        for p, o, a, r in positions:
            with self.subTest(pos=p, offset=o, anchor=a, result=r):
                self.stream.pos = p
                self.stream.seek(o, a)
                self.assertEqual(self.stream.pos, r)
    
    def test_read_to_end(self):
        self.stream.seek(0)
        self.assertEqual(self.stream.read(), b"\x00\x01\x02\x03\x04\x05\x06\x07")
    
    def test_read_zero(self):
        self.stream.seek(0)
        self.assertEqual(self.stream.read(0), b"")
    
    def test_read(self):
        self.stream.seek(0)
        self.assertEqual(self.stream.read(3), b"\x00\x01\x02")
    
    def test_read_eof(self):
        self.stream.seek(0)
        self.assertEqual(self.stream.read(10), b"\x00\x01\x02\x03\x04\x05\x06\x07")