import asyncore
import logging
import re
import socket
import time

from util import IRCMessage

replay_commands = [
    # Connection replies
    "001", "002", "003", "004", "005",
    # Server info
    "251", "252", "253", "254", "255",

    "JOIN"
]


logger = logging.getLogger()
logger.setLevel(10)
logging.basicConfig(format="[%(asctime)s] [%(levelname)s] %(message)s")

server_handlers = {}

def server_watch(command):
    def wrap(new_class):
        if command not in server_handlers:
            server_handlers[command] = []
        server_handlers[command].append(new_class())
    return wrap


@server_watch(command="PING")
class PING(object):
    def handle(self, exchanger, line):
        pong = line["raw"].replace("PING", "PONG")
        exchanger.send_line(pong)


"""
    Class responsible for maintaining an IRC connection
"""
class IRCExchanger(asyncore.dispatcher):

    def __init__(self, settings):
        asyncore.dispatcher.__init__(self)
        self.settings = settings
        self.recv_buffer = ""
        self.send_buffer = ""
        self.all_replay = []
        self.clients = []
        self.server_connect()


    def send_line(self, line):
        logging.debug("(TO SERVER) \"{0}\"".format(line))

        # if line[:4] == "QUIT":
        #     return
        self.send_buffer += line + "\n"
        self.handle_write()


    # Establish connection to IRC server
    def server_connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.settings["server"], self.settings["port"]))


    # Register user with server after connecting
    def handle_connect(self):
        print "handle_connect"
        # if "pass" in self.settings:
        #     pass_cmd = "PASS {0}".format(self.settings["pass"])
        #     self.send_line(pass_cmd)
        user_cmd = "USER {user} * * :{real_name}".format(**self.settings)
        self.send_line(user_cmd)
        nick_cmd = "NICK {0}".format(self.settings["nick"])
        self.send_line(nick_cmd)


    def handle_close(self):
        print "handle_close"
        self.close()
        time.sleep(10)
        self.server_connect()


    # Deals with individual lines from the IRC server
    def handle_line(self, line):
        match_dict = IRCMessage.parse(line)

        logging.debug("(FROM SERVER) Prefix: \"{prefix}\", Command: \"{command}\", Params: \"{params}\", Trailing: \"{trailing}\"".format(**match_dict))

        if match_dict["command"] in replay_commands:
            self.all_replay.append(match_dict)

        if match_dict["command"] in server_handlers:
            for handler in server_handlers[match_dict["command"]]:
                handler.handle(self, match_dict)
                self.send_line("JOIN #bbeggs")
        else:
            self.client_send(line)


    # Receives data from the IRC connection and breaks it into lines
    def handle_read(self):
        self.recv_buffer += self.recv(5120)
        lines = self.recv_buffer.split("\n")
        for line in lines[:]:
            if not line:
                continue
            if line[-1] == "\r":
                lines.remove(line)
                self.handle_line(line)
        self.recv_buffer = "\n".join(lines)


    # Sends text to the IRC server
    def handle_write(self):
        sent = self.send(self.send_buffer)
        self.send_buffer = self.send_buffer[sent:]


    # Sends text to registered clients
    def client_send(self, line):
        for client in self.clients:
            client.send_line(line)
    

    def register_client(self, client):
        self.clients.append(client)
        for command in self.all_replay:
            client.send_line(command["raw"])


    def writable(self):
        return (len(self.send_buffer) > 0)


