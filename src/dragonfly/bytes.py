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

class ByteStream:
    """Stream of bytes, simulates a file object"""

    def __init__(self, bytes_=b""):
        """Initializes a ByteStream instance

        Args:
            bytes_ (bytes, optional): The bytes string. Defaults to b"".
        """

        self.bytes = bytes_
        self.pos = 0
    
    def clamp(self):
        """Clamps the cursor's position to stay within the content's boundaries"""

        self.pos = min(len(self.bytes), max(0, self.pos))
    
    def seek(self, offset, anchor=0):
        """Changes stream position

        Changes the stream position to the given byte offset. The offset is
        interpreted relative to the position indicated by ``anchor``.

        Args:
            offset (int): The byte offset.
            anchor (int, optional): The offset anchor. Defaults to 0.
                0: start / 1: current / 2: end
        """

        if anchor == 0:
            self.pos = offset
        
        elif anchor == 1:
            self.pos += offset
        
        else:
            self.pos = len(self.bytes) + offset
        
        self.clamp()
    
    def read(self, count=-1):
        """Reads a certain amount of bytes from the stream

        Args:
            count (int): The number of bytes to read.

        Returns:
            bytes: Bytes read.
        """

        if count == -1:
            bytes_ = self.bytes[self.pos:]
            self.pos = len(self.bytes)
        
        else:
            bytes_ = self.bytes[self.pos:self.pos+count]
            self.pos += count
        
        self.clamp()

        return bytes_