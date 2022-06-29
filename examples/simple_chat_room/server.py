from dragonfly.server import Server
from dragonfly.logger import Logger, LogType
import threading

Logger.setup(LogType.INFO|LogType.WARN|LogType.ERROR)

server = Server()

t = threading.Thread(target=server.start, daemon=True)
t.start()

input()
server.stop()