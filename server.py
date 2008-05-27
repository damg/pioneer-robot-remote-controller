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

import asyncore
import AriaPy
import sys
import socket
import time
import base64
from protocol import *

class Server(asyncore.dispatcher):
    """ Accepts commands via an UDP socket """
    EXCLUSIVE_ACCESS_TIMEOUT = 30

    def __init__(self, port=45454):
        asyncore.dispatcher.__init__(self)
        
        self.robot=AriaPy.ArRobot()
        self.sonar=AriaPy.ArSonarDevice()
        self.robot.addRangeDevice(self.sonar)
        self.connector = AriaPy.ArSimpleConnector(sys.argv)
        if not self.connector.connectRobot(self.robot):
            print "FATAL: Could not connect to the robot"
            print "Exiting"
            sys.exit(1)

        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.bind(('', port))

        self.controlling_address = None
        self.last_access_time = 0
        self.message_accu = []
        self.send_video = True
        self.direction = (0, 0)
        self.send_video = False

    def writable(self):
        return False

    def handle_handshake(self, address, message):
        """ Handles a new connection """
        curtime = time.time()
        #whether the old conn is active
        if curtime - self.last_access_time < \
                    Server.EXCLUSIVE_ACCESS_TIMEOUT:
                self.sendto(str(ProtocolMessage(ProtocolMessage.OP_NOTAUTH, \
                                                    "Unauthorized")), \
                                address)
        else: # the old connection timed out, expecting a HELLO
            if message.code != ProtocolMessage.OP_HELLO:
                self.sendto(str(ProtocolMessage(ProtocolMessage.OP_BADREQ,\
                                                    "HELLO_Expected")), \
                                address)
                # check versions, server version not older than client's and
                # version difference not bigger than 1
            elif message.version > ProtocolMessage.PROTO_VERSION or \
                    abs(message.version-ProtocolMessage.PROTO_VERSION)>1:
                self.sendto(str(\
                        ProtocolMessage(ProtocolMessage.OP_INCOMPAT,\
                                            "Incompatible")), \
                                address)
            else: # checks done, exchange connections
                # accept new client
                self.sendto(str(ProtocolMessage(ProtocolMessage.OP_OK,\
                                                    "OK")), address)
                # drop old client
                if self.controlling_address:
                    self.sendto(str(ProtocolMessage(ProtocolMessage.OP_TIMEOUT,\
                                                        "Timeout")), \
                                    self.controlling_address)
                self.controlling_address = address
                self.last_access_time = curtime
                self.message_accu = []
                if ProtocolMessage.FIELD_ACCEPT_VIDEO in message and \
                        message[ProtocolMessage.FIELD_ACCEPT_VIDEO]:
                    self.send_video = True
                else:
                    self.send_video = False
                    
                print "Authorized client", address[0], address[1]

    def handle_command(self, message): #handle a non-handshake message
        if message.code == ProtocolMessage.OP_BYE:
            self.controlling_address = None
            self.last_access_time = 0
        elif message.code == ProtocolMessage.OP_DIRECTION:
            x = self.direction[0]
            y = self.direction[1]
            if ProtocolMessage.FIELD_X_AXIS in message.fields:
                try:
                    x = float(message[ProtocolMessage.FIELD_X_AXIS])
                except:
                    print "TODO: send error message", "server.py:175"
            if ProtocolMessage.FIELD_Y_AXIS in message.fields:
                try:
                    y = float(message[ProtocolMessage.FIELD_Y_AXIS])
                except:
                    print "TODO: send error message", "server.py:180"
            self.direction = (x, y)
            print self.direction

            print "TODO: process direction data", "server.py:182"
            self.last_access_time = time.time()

    def handle_read(self):
        message, address = self.recvfrom(ProtocolMessage.MAX_PACKET_SIZE)
        try:
            message = ProtocolMessageParser(message)
        except:
            self.sendto(str(ProtocolMessage(ProtocolMessage.OP_BADREQ, \
                                                "Bad request")), address)
            return
        if address != self.controlling_address:
            self.handle_handshake(address, message)
        else:
            self.handle_command(message)

if __name__=="__main__":
    svr=Server()
    AriaPy.Aria.init()
    asyncore.loop()
