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
import unittest
import sys

sys.path.append("src")

from dragonfly.bytes import ByteStream

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