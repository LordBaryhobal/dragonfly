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
from unittest.mock import patch, mock_open
import sys

sys.path.append("src")

from dragonfly.message import CONNECT, CONNECTED, PUBLISH, PUBLISHED, SUBSCRIBE, SUBSCRIBED, UNSUBSCRIBE, UNSUBSCRIBED
from dragonfly.message import type_name
from dragonfly.server import Server, Client

CONFIG = """
# General
require_auth true
topic nsub !sub
topic npub !pub
topic nsp !sub|!pub

# User
username user1
password wrong

# User
username user2
password pwd2

# User
username user3
password pwd3
topic nsub sub

# User
username user4
password pwd4
topic npub pub

# User
username user5
password pwd5
topic nsp sub|pub
"""

class TestServerAuth(unittest.TestCase):
    def setUpClass():
        with patch("builtins.open", mock_open(read_data=CONFIG)):
            TestServerAuth.server = Server(config="/dev/null")

    def setUp(self):
        self.clients = []
        for i in range(6):
            c = Client(None, None)
            c.username = f"user{i}"
            c.password = f"pwd{i}"
            self.clients.append(c)
    
    def auth(self, i, *args):
        return self.server.check_auth(self.clients[i], *args)

    def test_connect(self):
        self.server.config._config["require_auth"] = False
        self.assertTrue(self.auth(0, CONNECT))
        self.assertTrue(self.auth(1, CONNECT))
        self.assertTrue(self.auth(2, CONNECT))
        
        self.server.config._config["require_auth"] = True
        self.assertFalse(self.auth(0, CONNECT))
        self.assertFalse(self.auth(1, CONNECT))
        self.assertTrue(self.auth(2, CONNECT))
    
    def test_publish(self):
        for c in self.clients[1:]:
            c.connected = True
        
        with self.subTest(i=0):
            self.assertFalse(self.auth(0, PUBLISH, "sp"))
            self.assertFalse(self.auth(0, PUBLISH, "npub"))
            self.assertFalse(self.auth(0, PUBLISH, "nsp"))
        
        with self.subTest(i=1):
            self.assertTrue(self.auth(1, PUBLISH, "sp"))
            self.assertFalse(self.auth(1, PUBLISH, "npub"))
            self.assertFalse(self.auth(1, PUBLISH, "nsp"))
        
        with self.subTest(i=4):
            self.assertTrue(self.auth(4, PUBLISH, "sp"))
            self.assertTrue(self.auth(4, PUBLISH, "npub"))
            self.assertFalse(self.auth(4, PUBLISH, "nsp"))
        
        with self.subTest(i=5):
            self.assertTrue(self.auth(5, PUBLISH, "sp"))
            self.assertFalse(self.auth(5, PUBLISH, "npub"))
            self.assertTrue(self.auth(5, PUBLISH, "nsp"))
    
    def test_subscribe(self):
        for c in self.clients[1:]:
            c.connected = True
        
        with self.subTest(i=0):
            self.assertFalse(self.auth(0, SUBSCRIBE, "sp"))
            self.assertFalse(self.auth(0, SUBSCRIBE, "nsub"))
            self.assertFalse(self.auth(0, SUBSCRIBE, "nsp"))
        
        with self.subTest(i=1):
            self.assertTrue(self.auth(1, SUBSCRIBE, "sp"))
            self.assertFalse(self.auth(1, SUBSCRIBE, "nsub"))
            self.assertFalse(self.auth(1, SUBSCRIBE, "nsp"))
        
        with self.subTest(i=3):
            self.assertTrue(self.auth(3, SUBSCRIBE, "sp"))
            self.assertTrue(self.auth(3, SUBSCRIBE, "nsub"))
            self.assertFalse(self.auth(3, SUBSCRIBE, "nsp"))
        
        with self.subTest(i=5):
            self.assertTrue(self.auth(5, SUBSCRIBE, "sp"))
            self.assertFalse(self.auth(5, SUBSCRIBE, "nsub"))
            self.assertTrue(self.auth(5, SUBSCRIBE, "nsp"))
    
    def test_unsubscribe(self):
        self.assertTrue(self.auth(0, UNSUBSCRIBE, "us"))
    
    def test_invalid_scope(self):
        for t in [CONNECTED, PUBLISHED, SUBSCRIBED, UNSUBSCRIBED]:
            with self.subTest(scope=type_name(t)):
                with self.assertRaises(NotImplementedError):
                    self.auth(0, t)