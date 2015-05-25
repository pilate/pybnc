import asyncore
import logging
import re
import socket

from functools import wraps

from util import IRCMessage


def logged_in(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        r = f(self, *args, **kwargs)
        return r
    return wrapped


logger = logging.getLogger()
logger.setLevel(10)
logging.basicConfig(format="[%(asctime)s] [%(levelname)s] %(message)s")


client_handlers = {}

def client_watch(command):
    def wrap(new_class):
        if command not in client_handlers:
            client_handlers[command] = []
        client_handlers[command].append(new_class())
    return wrap

@client_watch(command="USER")
class USER(object):
    def handle(self, exchanger, line):
        pass

@client_watch(command="USERHOST")
class USERHOST(object):
    def handle(self, exchanger, line):
        pass


"""
    Responsible for client interaction
"""
class ClientHandler(asyncore.dispatcher_with_send):

    def __init__(self, users, exchangers, sock=None):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.registered = False
        self.users = users
        self.exchangers = exchangers


    def login(self, user, password):
        if user in self.users:
            if password == self.users[user]["bnc"]["password"]:
                logging.debug("User {0} logged in".format(user))
                self.exchanger = self.exchangers[user]
                self.user = user
                self.registered = True
                self.exchanger.register_client(self)
            else:
                logging.debug("Failed login from user {0}".format(user))


    # Write line to client
    def send_line(self, data):
        self.out_buffer += data + "\n"
        self.initiate_send()


    # Handle line from client
    def handle_line(self, line):
        match_dict = IRCMessage.parse(line)
        
        logging.debug("(CLIENT) {line}".format(line=line))
        if self.registered:
            if match_dict["command"] in client_handlers:
                for handler in client_handlers[match_dict["command"]]:
                    handler.handle(self.exchanger, line)
            else:
                self.exchanger.send_line(line)
        else:
            if match_dict["command"] == "PASS":
                pass_split = match_dict["params"].split(":", 2)
                if len(pass_split) != 2:
                    return
                self.login(*pass_split)


    def handle_read(self):
        data = self.recv(8192)
        if data:
            lines = data.split("\n")
            for line in filter(bool, lines):
                self.handle_line(line)


"""
    Async server that delegates to ClientHandler
"""
class BNCServer(asyncore.dispatcher):

    def __init__(self, users, server, exchangers):
        asyncore.dispatcher.__init__(self)
        self.server_settings = server
        self.users = users
        self.exchangers = exchangers
        self.handle_bind()

    def handle_bind(self):
        server_settings = self.server_settings
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        bind_tuple = (server_settings["bind_ip"], server_settings["bind_port"])
        self.bind(bind_tuple)
        self.listen(5)

    def handle_accept(self):
        pair = self.accept()
        if pair is not None:
            sock, addr = pair
            print 'Incoming connection from %s' % repr(addr)
            handler = ClientHandler(self.users, self.exchangers, sock=sock)
            handler.send_line(":pyBNC NOTICE AUTH :*** Log in with PASS\r")
