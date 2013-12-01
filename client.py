import asyncore
import re
import socket

from functools import wraps


def logged_in(f):
    @wraps(f)
    def wrapped(self, *args, **kwargs):
        r = f(self, *args, **kwargs)
        return r
    return wrapped

"""
    Responsible for client interaction
"""
class ClientHandler(asyncore.dispatcher_with_send):

    irc_re = r'^(:(?P<prefix>\S+) )?(?P<cmd>\S+)( (?!:)(?P<args>.+?))?( :(?P<trail>.+))?$'

    def __init__(self, users, exchangers, sock=None):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.registered = False
        self.users = users
        self.exchangers = exchangers

    def login(self, user, password):
        if user in self.users:
            if password == self.users[user]["bnc"]["password"]:
                self.exchanger = self.exchangers[user]
                self.user = user
                self.registered = True
                self.exchanger.register_client(self)

    def send_line(self, data):
        self.out_buffer += data + "\n"
        self.initiate_send()

    def handle_line(self, line):
        match_obj = re.match(self.irc_re, line)
        match_dict = match_obj.groupdict()
        match_dict["raw"] = line
        
        print "From client: {line}".format(line=line)
        if self.registered:
            self.exchanger.send_line(line)
        else:
            if match_dict["cmd"] == "PASS":
                pass_split = match_dict["args"].split(":", 2)
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
