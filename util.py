import re


irc_re = r'^(:(?P<prefix>\S+) )?(?P<command>\S+)( (?!:)(?P<params>.+?))?( :(?P<trailing>.+))?$'


class IRCMessage(object):

    @classmethod
    def parse(cls, line):
        match_obj = re.match(irc_re, line.strip())
        match_dict = match_obj.groupdict()
        match_dict["raw"] = line
        return match_dict


    @classmethod
    def create(cls, command, prefix="", params="", trailing=""):
        string = ""
        if prefix:
            string += ":{0} ".format(prefix)
        string += "{0} {1}".format(command, params)
        if trailing:
            string += ":{0}".format(trailing)
        return string
