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

class ByteStream:
    def __init__(self, bytes_=b""):
        self.bytes = bytes_
        self.pos = 0
    
    def clamp(self):
        self.pos = min(len(self.bytes)-1, max(0, self.pos))
    
    def seek(self, offset, anchor=0):
        if anchor == 0:
            self.pos = offset
        
        elif anchor == 1:
            self.pos += offset
        
        elif anchor == 2:
            self.pos = len(self.bytes) + offset
        
        self.clamp()
    
    def read(self, count):
        bytes_ = self.bytes[self.pos:self.pos+count]
        self.pos += count
        self.clamp()

        return bytes_