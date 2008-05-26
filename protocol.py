#!/usr/bin/env python
# Copyright 2008 Dmitri Bachtin, Frank Breitinger, 
#                Konstantin Kramer, Sergej Jakimcuk,


#    This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re

class ProtocolMessage:
    OP_HELLO = 105 # Handshake client introduction command
    OP_BYE   = 106 # Connection drop command
    OP_DIRECTION = 110 # Direction specification
    OP_OK = 200 # Message signalling acceptance of the request
    OP_BADREQ = 400 # Bad request error
    OP_NOTAUTH = 401 # Not authorized error
    OP_INCOMPAT = 417 # Incompatible version error
    OP_TIMEOUT = 408 # Authorization timeout error
    OP_VIDEO_FRAME = 111 # A video frame

    PROTO_VERSION = 1.0 # Current protocol version
    MAX_PACKET_SIZE = 64*1024

    FIELD_X_AXIS = "X-X-Axis"
    FIELD_Y_AXIS = "X-Y-Axis"
    FIELD_ACCEPT_VIDEO = "X-Accept-Video"
    def __init__(self, code, msgcode, fields = {}, version=PROTO_VERSION):
        self.code = code
        self.msgcode = msgcode
        self.fields = fields
        self.version = version

    def __str__(self):
        f_v_pairs = [ (f, self.fields[f]) for f in self.fields ]
        f_v_pairs_str = map(lambda(x): "%s: %s" % (x[0], str(x[1])), f_v_pairs)
        return "PIONEER/" + str(ProtocolMessage.PROTO_VERSION) + \
            " " + str(self.code) + " " + self.msgcode +"\r\n" + \
            "\r\n".join(f_v_pairs_str)+"\r\n" \
            "\r\n"

    def __getitem__(self, k):
        if k == "code":
            return self.code
        elif k == "msgcode":
            return self.msgcode
        elif k == "version":
            return self.version
        else:
            return self.fields[k]

    def __contains__(self, k):
        if k in [ "code", "msgcode", "version" ]:
            return True
        else:
            return k in self.fields

    def __setitem__(self, k, v):
        if k == "code":
            self.code = v
        elif k == "msgcode":
            self.msgcode = v
        elif k == "version":
            self.version = v
        else:
            self.fields[k] = v

    def __delitem__(self, k):
        if k in ["code", "msgcode", "version"]:
            raise KeyError("Cannot delete obligatory keys")
        else:
            del self.fields[k]

    def __eq__(self, o):
        if not isinstance(o, ProtocolMessage):
            return False
        return self.code == o.code and \
            self.msgcode == o.msgcode and \
            self.version == o.version and \
            self.fields  == o.fields

    def keys(self):
        kk = self.fields.keys()
        kk.append("code")
        kk.append("msgcode")
        kk.append("version")
        return kk

    def has_key(self, k):
        return k in self

    def items(self):
        return [(k, self[k]) for k in self.keys()]

class ProtocolMessageParser(ProtocolMessage):
    """ Creates a ProtocolMessage from a string """
    full_regex = re.compile("^PIONEER/\d+\.\d+ \d\d\d .*\r\n" \
                                "(.+: ?.+\r\n)*" \
                                "\r\n")
    def __init__(self, msg):
        if not ProtocolMessageParser.full_regex.match(msg):
            raise ValueError("Invalid packet")
        parts = msg.split("\r\n")
        header = parts[0]
        header_parts = header.split(" ")
        version = float(header_parts[0][8:])
        code = int(header_parts[1])
        msgcode = header_parts[2]
        fields = {}
        for field in parts[1:]:
            field_parts = field.split(":")
            if len(field_parts) != 2: # hit single \r\n
                continue
            fields[field_parts[0]]=field_parts[1].lstrip()
        ProtocolMessage.__init__(self, code, msgcode, fields, version)

if __name__ == "__main__":
    print "This module is non-executable"
