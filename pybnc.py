from settings import users
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


exchangers = []
server = BNCServer('0.0.0.0', 9550)

for user, settings in users.iteritems():
    exchangers.append(IRCExchanger(settings))

asyncore.loop()

