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

from dragonfly.message import ORIGIN_SERVER, ORIGIN_CLIENT
from dragonfly.message import CONNECT, CONNECTED, PUBLISH, PUBLISHED, SUBSCRIBE, SUBSCRIBED, UNSUBSCRIBE, UNSUBSCRIBED
from dragonfly.message import Message, MessageType, type_name
from dragonfly.exceptions import InvalidMessageType

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
        #TODO
        with self.assertLogs("dragonfly", logging.ERROR):
            msg = Message()
            msg.from_bytes(b"")
    
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