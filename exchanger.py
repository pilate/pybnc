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
        self.do_connect()

    def buffer_string(self, string):
        if string[:4] == "QUIT":
            return
        self.send_buffer += string + "\n"
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

    def client_send(self, line):
        for client in self.clients:
            client.send(line)

    def handle_line(self, line):
        match_obj = re.match(self.irc_re, line)
        match_dict = match_obj.groupdict()
        match_dict["raw"] = line

        print "From server:", match_dict
        if match_dict["cmd"] == "PING":
            pong_cmd = line.replace("PING", "PONG")
            print pong_cmd
            self.buffer_string(pong_cmd)
        else:
            if match_dict["cmd"] == "JOIN":
                self.joins.append(match_dict)
            self.client_send(line)

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
                
    def writable(self):
        return (len(self.send_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.send_buffer)
        self.send_buffer = self.send_buffer[sent:]

    def register_client(self, client):
        self.clients.append(client)
        for join in self.joins:
            client.send(join["raw"])
            names_cmd = "NAMES {chan}".format(chan=join["trail"].strip())
            self.buffer_string(names_cmd)
