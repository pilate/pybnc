from settings import users, server
from client import BNCServer
from exchanger import IRCExchanger

import asyncore
import re
import socket

"""
    1) Iterate users in settings
        a) Connect to server
    2) Listen for connections
        a) Validate user/pass
        b) Proxy input to correct IRCExchanger
"""

exchangers = {}

for user, settings in users.iteritems():
    exchangers[user] = IRCExchanger(settings)

server = BNCServer(users, server, exchangers)

asyncore.loop()

