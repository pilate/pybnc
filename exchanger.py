import asyncore
import socket


"""
    Class responsible for maintaining an IRC connection
"""
class IRCExchanger(asyncore.dispatcher):

    def __init__(self, settings):
        asyncore.dispatcher.__init__(self)
        self.settings = settings
        self.buffer = ""
        self.clients = []
        self.do_connect()

    def buffer_string(self, string):
        self.buffer += string + "\n"
        self.handle_write()

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
        else:
            for client in self.clients:
                client.send(line)

    def handle_read(self):
        data = self.recv(10240)
        if not data:
            return
        for line in data.split("\n"):
            self.handle_line(line)

    def writable(self):
        return (len(self.buffer) > 0)

    def handle_write(self):
        sent = self.send(self.buffer)
        self.buffer = self.buffer[sent:]

    def register_client(self, client):
        self.clients.append(client)