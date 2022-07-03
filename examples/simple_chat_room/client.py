from dragonfly.client import Client
from dragonfly.logger import setup
import json

def on_c(self, code):
    if code & 0x80:
        print(f"Connection failed with code {code}")
    
    else:
        print("Connected")

def on_s(self, code):
    if code & 0x80:
        print(f"Couldn't subscribe: code {code}")
    
    else:
        print("Subscribed")

def on_p(self, code):
    if code & 0x80:
        print(f"Couldn't publish: code {code}")
    
    else:
        print("Published")

def on_d(self, code):
    print("Disconnected")

def on_m(self, topic, msg):
    msg = json.loads(msg)
    print(f"\r<{msg['username']}> {msg['body']}")

setup()

username = input("username: ")
password = input("password: ")
if not username: username = None
if not password: password = None

client = Client(username, password)
client.connect()

client.on_connected = on_c
client.on_disconnected = on_d
client.on_message = on_m
client.on_subscribed = on_s
client.on_published = on_p

client.subscribe("chat")

while True:
    c = input()
    if c == "":
        break

    client.publish("chat", json.dumps({
        "username": username,
        "body": c
    }))

client.unsubscribe("chat")
client.disconnect()