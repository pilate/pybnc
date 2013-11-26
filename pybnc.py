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


"""
    Class responsible for maintaining an IRC connection
"""
class IRCExchanger(asyncore.dispatcher):

    def __init__(self, settings):
        asyncore.dispatcher.__init__(self)
        self.settings = settings
        self.buffer = ""
        self.do_connect()

    def buffer_string(self, string):
        self.buffer += string + "\r\n"

    # Establish connection to server
    def do_connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.settings["server"], self.settings["port"]))

    # Register user with server
    def handle_connect(self):
        if "pass" in self.settings:
            pass_cmd = "PASS {0}".format(self.settings["pass"])
            self.buffer_string(pass_cmd)
        nick_cmd = "NICK {0}".format(self.settings["nick"])
        self.buffer_string(nick_cmd)
        user_cmd = "USER {0} 8 * :{1}".format(self.settings["user"], self.settings["real_name"])
        self.buffer_string(user_cmd)

    def handle_close(self):
        self.close()

    def handle_line(self, line):
        if line[:4] == "PING":
            pong_cmd = line.replace("PING", "PONG")
            print pong_cmd
            self.buffer_string(pong_cmd)

    def handle_read(self):
        data = self.recv(10240)
        for line in data.split("\r\n"):
            self.handle_line(line)

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

settings = {
    "test1": {
        "server": "irc.servercentral.net",
        "port": 6667,
        "nick": "testbot12",
        "user": "testuser",
        "real_name": "testy mctesterson"
    }
}
clients = []
for user, settings in settings.iteritems():
    clients.append(IRCExchanger(settings))
asyncore.loop()

"""
class EchoHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        data = self.recv(8192)
        if data:
            self.send(data)

class EchoServer(asyncore.dispatcher):

    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            handler = EchoHandler(sock)

server = EchoServer('localhost', 9550)
asyncore.loop()
"""