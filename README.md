# Dragonfly

Dragonfly is an mqtt-like communication protocol. This library includes a server and a client

## Installation

Clone this repository:
```bash
git clone https://github.com/LordBaryhobal/dragonfly.git
```

Copy `src/dragonfly` to a directory on your `PYTHONPATH`.
```bash
cp -r dragonfly/src/dragonfly/ ~/.local/lib/python3.8/site-packages/
```

## Usage

### config.dfcfg

```js
# General
// only registered users can connect
require_auth	true
//
/* by default, no on can subscribe or publish
   to topic 'chat' */
topic		chat	!sub|!pub

# User
username	admin
password	1234
//
// can subscribe and publish to 'chat'
topic		chat	sub|pub

# User
username	user1
//
// can subscribe to 'chat'
topic		chat	sub

# User
username	user2
//
// can publish to chat
topic		chat	pub

```

### Server

```python
from dragonfly.server import Server
from dragonfly.logger import setup
import threading

# sets up logging
setup()

# initializes a server
server = Server(config="config.dfcfg")

# runs the mainloop in another thread
t = threading.Thread(target=server.start, daemon=True)
t.start()

input("Presse RETURN to stop")

# closes the server
server.stop()
```

### Client
```python
from dragonfly.client import Client
from dragonfly.logger import setup

def on_c(self, code):
    if code & 0x80:
        print(f"Connection failed with code {code}")
    
    else:
        print("Connected")

def on_d(self, code):
    print("Disconnected")

def on_m(self, topic, msg):
    print(msg)

# sets up logging
setup()

username = input("username: ")
password = input("password: ")
if not username: username = None
if not password: password = None

# initializes a client
client = Client(username, password)

# connects to the server
client.connect()

# sets up callbacks for certain events
client.on_connected = on_c
client.on_disconnected = on_d
client.on_message = on_m

# subscribes to topic 'chat'
client.subscribe("chat")

# sends all user input to topic 'chat'
# exits if input is empty
while True:
    c = input()
    if c == "":
        break
    
    # publishes to topic 'chat'
    client.publish("chat", c)

# unsubscribes from topic 'chat'
client.unsubscribe("chat")

# disconnects from the server
client.disconnect()
```

## Documentation
The documentation is not yet hosted.
To build it, first install install `sphinx` and the redactor theme:
```bash
python3 -m pip install -U sphinx sphinx-redactor-theme
```

Then run `docs/build.sh` (currently only works on Linux/macOS)

You should now have a beautiful documentation in `docs/build/html`.

## Testing
To run unittests, just go into the root directory and run
```bash
coverage run
```

And to get an html report, run
```bash
coverage html
```

Coverage may complain of an unknown parameter 'theme'. Either comment out the corresponding line in `.coveragerc` or checkout [this version of coveragepy](https://github.com/nedbat/coveragepy/pull/1416)

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/)
