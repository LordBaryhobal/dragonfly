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
import re

class Config:
    def __init__(self, path=None):
        self._config = {}
        self._path = path

        if self._path:
            self.load(self._path)

    def parse_arg(self, arg):
        if isinstance(arg, list):
            return list(map(self.parse_arg, arg))
        
        elif "|" in arg:
            return self.parse_arg(arg.split("|"))
        
        if arg.lower() == "true":
            return True
        
        elif arg.lower() == "false":
            return False
        
        elif arg.lower() == "null":
            return None
        
        elif arg.lower().startswith("0x"):
            return int(arg[2:], 16)
        
        elif arg.lower().startswith("0o"):
            return int(arg[2:], 8)
        
        elif arg.lower().startswith("0b"):
            return int(arg[2:], 2)
        
        try:
            arg = int(arg)
        
        except:        
            try:
                arg = float(arg)
            
            except:
                pass
        
        return arg

    def load(self, path):
        self._path = path
        with open(path, "r") as f:
            lines = f.read().split("\n")
        
        config = {
            "users": []
        }
        
        state = 0
        skipping = False
        type_ = None
        elmt = None
        
        for line in lines:
            if line.lstrip().startswith("//"):
                continue
            
            elif line.lstrip().startswith("/*"):
                skipping = True
            
            elif line.rstrip().endswith("*/"):
                skipping = False
            
            if skipping:
                continue
            
            if state == 0:
                match = re.match(r"^# (.*)$", line)
                if match:
                    type_ = match.group(1).lower()
                    elmt = {}
                    state = 1
            
            elif state == 1:
                if not line.strip():
                    state = 0
                    if type_ == "general":
                        config.update(elmt)
                    
                    elif type_ == "user":
                        config["users"].append(elmt)
                    
                    type_, elmt = None, None
                    continue
                
                args = re.split(r"\s+", line)
                args[0] = args[0].lower()
                
                if len(args) == 2:
                    elmt[args[0]] = self.parse_arg(args[1])
                
                elif len(args) > 2:
                    if args[0] == "topic":
                        if not "topics" in elmt:
                            elmt["topics"] = {}
                        
                        elmt["topics"][args[1]] = self.parse_arg(args[2])
                    
                    else:
                        elmt[args[0]] = self.parse_arg(args[1:])
        
        self._config = config
    
    def get_user(self, username, password):
        if not self.users:
            return None
        
        for user in self.users:
            if str(user["username"]) == username:
                if user.get("password") is None or str(user["password"]) == password:
                    return user
        
        return None

    def __getattr__(self, __name):
        if __name in self._config:
            return self._config[__name]
        
        return None