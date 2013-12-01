import asyncore
import re
import socket


"""
    Class responsible for maintaining an IRC connection
"""
class IRCExchanger(asyncore.dispatcher):

    irc_re = r'^(:(?P<prefix>\S+) )?(?P<cmd>\S+)( (?!:)(?P<args>.+?))?( :(?P<trail>.+))?$'

    def __init__(self, settings):
        asyncore.dispatcher.__init__(self)
        self.settings = settings
        self.recv_buffer = ""
        self.send_buffer = ""
        self.clients = []
        self.joins = []
        self.server_connect()

    def send_line(self, string):
        if string[:4] == "QUIT":
            return
        self.send_buffer += string + "\n"
        self.handle_write()

    # Establish connection to IRC server
    def server_connect(self):
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((self.settings["server"], self.settings["port"]))

    # Register user with server after connecting
    def handle_connect(self):
        if "pass" in self.settings:
            pass_cmd = "PASS {0}".format(self.settings["pass"])
            self.send_line(pass_cmd)
        nick_cmd = "NICK {0}".format(self.settings["nick"])
        self.send_line(nick_cmd)
        user_cmd = "USER {user} 8 * :{real_name}".format(**self.settings)
        self.send_line(user_cmd)

    def handle_close(self):
        self.close()

    # Deals with individual lines from the IRC server
    def handle_line(self, line):
        match_obj = re.match(self.irc_re, line)
        match_dict = match_obj.groupdict()
        match_dict["raw"] = line

        print "From server:", match_dict
        if match_dict["cmd"] == "PING":
            pong_cmd = line.replace("PING", "PONG")
            print pong_cmd
            self.send_line(pong_cmd)
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

    def writable(self):
        return (len(self.send_buffer) > 0)


