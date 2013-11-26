import asyncore
import socket


"""
    Responsible for client interaction
"""
class ClientHandler(asyncore.dispatcher_with_send):

    def handle_read(self):
        data = self.recv(8192)
        if data:
            for line in data.split("\n"):
                print "Client: {0}".format(line)
                if line[:4] == "USER":
                    print "001 sent"
                    self.send("001 {nick} :Hey!\n".format(nick="testbot12"))
            # Proxy data to exchanger... somehow

"""
    Async server that delegates to ClientHandler
"""
class BNCServer(asyncore.dispatcher):

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
            handler = ClientHandler(sock)