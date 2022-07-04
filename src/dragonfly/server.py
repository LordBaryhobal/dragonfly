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
from enum import IntEnum, auto
import logging
import re
import selectors
import socket
import struct
import types

from dragonfly.config import Config
from dragonfly.message import ORIGIN_SERVER, ORIGIN_CLIENT
from dragonfly.message import CONNECT, PUBLISH, SUBSCRIBE, UNSUBSCRIBE
from dragonfly.message import CONNECTED, PUBLISHED, SUBSCRIBED, UNSUBSCRIBED
from dragonfly.message import Message, type_name

class State(IntEnum):
    """Server state enum"""

    STOPPED = auto()
    STARTING = auto()
    RUNNING = auto()
    STOPPING = auto()
    CRASHED = auto()

class Server:
    """Dragonfly server"""

    def __init__(self, host="localhost", port=1869, config=None):
        """Initializes a Server instance

        Args:
            host (str, optional): Socket host. Defaults to "localhost".
            port (int, optional): Socket port. Defaults to 1869.
            config (str, optional): Path to config file. Defaults to None.
        """

        self.config_path = config
        self.config = Config(self.config_path)

        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.selector = selectors.DefaultSelector()
        self.clients = []
        self.topics = {}
        self.state = State.STOPPED
        self.logger = logging.getLogger("dragonfly")

    def start(self):
        """Starts this server"""

        self.state = State.STARTING
        self.socket.bind((self.host, self.port))
        self.socket.listen()
        self.socket.setblocking(False)
        self.selector.register(self.socket, selectors.EVENT_READ, data=None)
        self.logger.info("Dragonfly server listening on ('%s', %d)", self.host, self.port)
        self.state = State.RUNNING

        self.mainloop()

    def stop(self):
        """Closes this server's socket"""

        self.state = State.STOPPING
        self.socket.close()
        self.state = State.STOPPED

    def mainloop(self):
        """Main event loop"""

        while self.state == State.RUNNING:
            events = self.selector.select(timeout=None)

            for key, mask in events:
                # Listening socket
                if key.data is None:
                    self.new_conn(key.fileobj)

                # Data
                else:
                    self.handle_msg(key, mask)

    def new_conn(self, sock):
        """Accepts a new connection

        Args:
            sock (socket.socket): The incoming socket connection.
        """

        conn, addr = sock.accept()
        client = self.new_client(conn)
        self.logger.debug("Accepted connection from %s", (addr, ))
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", step=0, length=0, id=client.id)
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(conn, events, data=data)

    def close_conn(self, id_):
        """Closes a previously established connection

        Args:
            id_ (int): The client's id.
        """

        client = self.clients[id_]
        self.logger.debug("Closing connection %s", client.socket.getpeername())
        self.selector.unregister(client.socket)
        client.socket.close()
        self.remove_client(id_)

    def handle_msg(self, key, mask):
        """Handles an event

        Args:
            key (selectors.SelectorKey): The event's key.
            mask (selectors._EventMask): The event's mask.
        """

        sock = key.fileobj
        data = key.data

        # Ready to read
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(data.length if data.step == 1 else 7)

            if recv_data:
                data.outb += recv_data
                data.step += 1

                if data.step == 1:
                    data.length = struct.unpack(">I", data.outb[-4:])[0]
                    if data.length == 0:
                        data.step = 2

                if data.step == 2:
                    msg = Message()
                    if msg.from_bytes(data.outb):
                        self.logger.debug("Received %s from %s", msg, data.addr)
                        self.process_msg(msg, self.clients[data.id])

                    data.step = 0
                    data.outb = b""

            else:
                self.close_conn(data.id)

        # Ready to write
        if mask & selectors.EVENT_WRITE:
            pass

    def new_client(self, sock):
        """Registers new client

        Args:
            sock (socket.socket): The client socket.

        Returns:
            Client: The new client instance.
        """

        if not None in self.clients:
            self.clients.append(None)

        id_ = self.clients.index(None)
        client = Client(sock, id_)
        self.clients[id_] = client

        return client

    def remove_client(self, id_):
        """Unregisters a client

        Args:
            id_ (int): The client's id.
        """

        client = self.clients[id_]
        for topic in client.topics:
            self.topics[topic].remove(id_)

        self.clients[id_] = None

    def process_msg(self, msg, sender):
        """Processes a message

        Args:
            msg (Message): The message instance.
            sender (Client): The sender client.
        """

        type_ = msg.type
        if type_.origin == ORIGIN_CLIENT:
            if type_.type == CONNECT:
                if type_.flags & 4:
                    sender.send(Message(ORIGIN_SERVER, CONNECTED, 4, code=0x00))
                    self.close_conn(sender.id)

                else:
                    sender.username = msg.username
                    sender.password = msg.password

                    ack = Message(ORIGIN_SERVER, CONNECTED)
                    ack.code = 0x00

                    if not self.check_auth(sender, CONNECT):
                        ack.code = 0x81

                    else:
                        sender.connected = True

                    sender.send(ack)

            elif type_.type == PUBLISH:
                self.publish(msg, sender)

            elif type_.type == SUBSCRIBE:
                self.subscribe(msg, sender)

            elif type_.type == UNSUBSCRIBE:
                self.unsubscribe(msg, sender)

    def publish(self, msg, sender):
        """Processes a PUBLISH message

        Args:
            msg (Message): The PUBLISH message.
            sender (Client): The sender client.
        """

        ack = Message(ORIGIN_SERVER, PUBLISHED)
        ack.code = 0x00

        if not self.check_auth(sender, PUBLISH, msg.topic):
            ack.code = 0x81

        else:
            self.logger.debug("%s published '%s' to '%s'", sender, msg.body, msg.topic)
            for topic, ids in self.topics.items():
                if self.topic_match(topic, msg.topic):
                    for id_ in ids:
                        client = self.clients[id_]
                        msg.type.origin = ORIGIN_SERVER
                        client.send(msg)
                        self.logger.debug("Relaying to %s", (client, ))

        sender.send(ack)

    def topic_match(self, pattern, topic):
        """Returns wether `topic` matches `pattern`

        Args:
            pattern (str): Topic pattern.
            topic (str): Topic to match.

        Returns:
            bool: True if topic matches, False otherwise.
        """

        return bool(re.match(pattern, topic))

    def subscribe(self, msg, client):
        """Processes a SUBSCRIBE message

        Args:
            msg (Message): The SUBSCRIBE message.
            sender (Client): The sender client.
        """

        topic = msg.topic

        ack = Message(ORIGIN_SERVER, SUBSCRIBED)
        ack.code = 0x00

        if not self.check_auth(client, SUBSCRIBE, topic):
            ack.code = 0x81

        elif topic in client.topics:
            ack.code = 0x01

        else:
            client.topics.append(topic)
            if not topic in self.topics:
                self.topics[topic] = []

            self.topics[topic].append(client.id)

            self.logger.debug("%s subscribed to '%s'", client, topic)

        client.send(ack)

    def unsubscribe(self, msg, client):
        """Processes a UNSUBSCRIBE message

        Args:
            msg (Message): The UNSUBSCRIBE message.
            sender (Client): The sender client.
        """

        topic = msg.topic

        ack = Message(ORIGIN_SERVER, UNSUBSCRIBED)
        ack.code = 0x00

        if not self.check_auth(client, UNSUBSCRIBE, topic):
            ack.code = 0x81

        elif not topic in client.topics:
            ack.code = 0x01

        else:
            client.topics.remove(topic)

            self.topics[topic].remove(client.id)

            if len(self.topics[topic]) == 0:
                del self.topics[topic]

            self.logger.debug("%s unsubscribed from '%s'", client, topic)

        client.send(ack)

    def check_auth(self, client, scope, *args):
        """Checks user rights in `scope`

        Args:
            client (Client): The client.
            scope (int): Message type.

        Returns:
            True if the client is authorized in this scope, False otherwise.

        Raises:
            NotImplementedError: If ``scope`` is not a scope with rights or is
                not a valid scope.
        """

        user = self.config.get_user(client.username, client.password)

        if scope == CONNECT:
            if not self.config.require_auth:
                return True

            if user:
                return True

            return False

        elif scope == PUBLISH:
            pub_topic = args[0]

            if not client.connected:
                return False

            auth = True
            topics = list(self.config.topics.items())

            if user:
                topics += list(user["topics"].items())

            for topic, rights in topics:
                if self.topic_match(topic, pub_topic):
                    if "!pub" in rights:
                        auth = False

                    elif "pub" in rights:
                        auth = True

            return auth

        elif scope == SUBSCRIBE:
            sub_topic = args[0]

            if not client.connected:
                return False

            auth = True
            topics = list(self.config.topics.items())

            if user:
                topics += list(user["topics"].items())

            for topic, rights in topics:
                if self.topic_match(topic, sub_topic):
                    if "!sub" in rights:
                        auth = False

                    elif "sub" in rights:
                        auth = True

            return auth

        elif scope == UNSUBSCRIBE:
            return True

        raise NotImplementedError(f"{type_name(scope)} is not a scope")

class Client:
    """Represents a client"""

    def __init__(self, sock, id_):
        """Initializes a Client instance

        Args:
            sock (socket.socket): The client socket.
            id_ (int): The client's id (see :py:meth:`Server.new_client`).
        """

        self.socket = sock
        self.username = None
        self.password = None
        self.connected = False
        self.topics = []
        self.id = id_

    def __repr__(self):
        return f"<Client {self.id} topics={self.topics}>"

    def send(self, msg):
        """Sends a message through the socket

        Args:
            msg (Message): The message to send.
        """

        self.socket.sendall(msg.to_bytes())

if __name__ == "__main__":
    import threading
    server = Server()

    t = threading.Thread(target=server.start, daemon=True)
    t.start()

    input()
    server.stop()
