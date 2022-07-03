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

from dragonfly.config import Config

CONFIG = """
// This is a comment

/* This is
multiline
comment */

# General
bool_t true
bool_t2 TRUE
bool_f false
bool_f2 FALSE
null null
null2 NULL
hex 0xff
oct 0o77
bin 0b11
int 1234
float 12.34
multi a b|c|d
multi2 a b c d
topic top rights
topic top2 rights2

# User
username user
password pwd
foo bar
topic top3 rights3
topic top4 rights4
"""

class TestConfig(unittest.TestCase):
    def setUpClass():
        with patch("builtins.open", mock_open(read_data=CONFIG)):
            TestConfig.config = Config("/dev/null")

    def test_types(self):
        self.assertIs(self.config.bool_t, True)
        self.assertIs(self.config.bool_t2, True)
        self.assertIs(self.config.bool_f, False)
        self.assertIs(self.config.bool_f2, False)
        self.assertIs(self.config.null, None)
        self.assertIs(self.config.null2, None)
        self.assertIs(self.config.hex, 0xff)
        self.assertIs(self.config.oct, 0o77)
        self.assertIs(self.config.bin, 0b11)
        self.assertEqual(self.config.int, 1234)
        self.assertIsInstance(self.config.int, int)
        self.assertAlmostEqual(self.config.float, 12.34, 7)
        self.assertIsInstance(self.config.float, float)
        self.assertListEqual(self.config.multi, ["a", ["b", "c", "d"]])
        self.assertListEqual(self.config.multi2, ["a", "b", "c", "d"])
        self.assertIs(self.config.not_set, None)
    
    def test_comments(self):
        with self.assertRaises(KeyError):
            self.config._config["//"]
        
        with self.assertRaises(KeyError):
            self.config._config["/*"]
    
    def test_get_user(self):
        c = Config()
        self.assertIs(c.get_user("user", "pwd"), None)

        self.assertIs(self.config.get_user("wrong", "wrong"), None)
        self.assertIs(self.config.get_user("user", "wrong"), None)
        self.assertDictEqual(self.config.get_user("user", "pwd"), {
            "username": "user",
            "password": "pwd",
            "foo": "bar",
            "topics": {
                "top3": "rights3",
                "top4": "rights4"
            }
        })
