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
import time

sys.path.append("src")

from dragonfly.exceptions import InvalidMessageType
from dragonfly.message import ORIGIN_SERVER, ORIGIN_CLIENT
from dragonfly.message import CONNECT, CONNECTED, PUBLISH, PUBLISHED, SUBSCRIBE, SUBSCRIBED, UNSUBSCRIBE, UNSUBSCRIBED
from dragonfly.message import Message, MessageType, type_name
from dragonfly.server import Server, State
from tests.thread_helper import ThreadRunner

class TestServer(unittest.TestCase):
    def setUp(self):
        self.thread_runner = ThreadRunner()
        self.server = Server()

    def test_server_works(self):
        self.thread_runner.add(self.server.start, "server", True)

        time.sleep(0.2)
        
        self.server.stop()

        time.sleep(0.2)
        
        r, e = self.thread_runner.result("server", True)
        self.assertEqual(e, None)
