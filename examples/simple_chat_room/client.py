from dragonfly.client import Client
from dragonfly.logger import Logger, LogType
import json

def on_c(self, code):
    if code & 0x80:
        print(f"Connection failed with code {code}")
    
    else:
        print("Connected")

def on_d(self, code):
    print("Disconnected")

def on_m(self, topic, msg):
    msg = json.loads(msg)
    print(f"\r<{msg['username']}> {msg['body']}")

Logger.setup(LogType.INFO|LogType.WARN|LogType.ERROR)

username = input("username: ")

client = Client()
client.connect()

client.on_connected = on_c
client.on_disconnected = on_d
client.on_message = on_m

client.subscribe("chat")

while True:
	c = input()
	if c == "":
		break
	
	client.publish("chat", json.dumps({
        "username": username,
        "body": c
    }))

client.disconnect()