import asyncore
import socket


"""
    Responsible for client interaction
"""
class ClientHandler(asyncore.dispatcher_with_send):

    def __init__(self, users, exchangers, sock=None):
        asyncore.dispatcher_with_send.__init__(self, sock=sock)
        self.users = users
        self.exchangers = exchangers
        for username, exchanger in self.exchangers.iteritems():
            exchanger.register_client(self)

    def send(self, data):
        self.out_buffer += data + "\n"
        self.initiate_send()

    def handle_line(self, line):
        print "From client: {line}".format(line=line)
        if line[:4] == "USER":
            self.send("001 {nick} :Hey!\n".format(nick="testbot12"))
        for username, exchanger in self.exchangers.iteritems():
            exchanger.buffer_string(line)

    def handle_read(self):
        data = self.recv(8192)
        if data:
            for line in data.split("\n"):
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
