from dragonfly.server import Server
from dragonfly.logger import setup
import threading

setup()

server = Server(config="config.dfcfg")

t = threading.Thread(target=server.start, daemon=True)
t.start()

input()
server.stop()