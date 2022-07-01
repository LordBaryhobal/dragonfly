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
import os
import threading

class ThreadRunner:
    def __init__(self):
        self.threads = {}
        self.results = {}
    
    def add(self, target, name, daemon=False):
        self.threads[name] = threading.Thread(target=self.run, args=[target, name], daemon=daemon)
        self.threads[name].start()

    def run(self, target, name):
        self.results[name] = ("pass", None)
        try:
            target()
        
        except Exception as e:
            self.results[name] = ("fail", e)
    
    def result(self, name, raise_=False):
        if not self.threads[name].isDaemon:
            self.threads[name].join()
        
        r, e = self.results[name]

        if e and raise_:
            raise e
        
        return self.results[name]