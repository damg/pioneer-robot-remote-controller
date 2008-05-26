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

from protocol import *
import sys
import socket
import asyncore
import pygame
import time

class Client(asyncore.dispatcher):
    TICK_RATE=0.20 #milliseconds
    def __init__(self, address):
        self.address = address
        self.connected = False
        self.last_send_timestamp = 0
        self.current_control_state = [0, 0]
        self.queue_control_state = [0, 0]
        if not pygame.joystick.get_count():
            print "No joysticks found"
            self.joystick = None
        else:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()

        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_DGRAM)
        handshake = \
            ProtocolMessage(ProtocolMessage.OP_HELLO,\
                                "HELLO",\
                                { ProtocolMessage.FIELD_ACCEPT_VIDEO:"False" })
        self.sendto(str(handshake), self.address)
        self.handshaking = True
        self.connected = False
        self.last_send_timestamp = time.time()

    def handle_read(self):
        message, address = self.recvfrom(ProtocolMessage.MAX_PACKET_SIZE)
        if address != self.address:
            return # ignore unauthorized message

        try:
            m = ProtocolMessageParser(message)
            if self.handshaking:
                if m.code != ProtocolMessage.OP_OK:
                    print "Handshake failed:", m.code, m.msgcode
                    self.connected = False
                    self.handshaking = False
                    sys.exit(1)
                self.connected = True
                self.handshaking = False
            elif self.connected:
                if m.code != ProtocolMessage.OP_VIDEO_FRAME:
                    print "Server sent an unknown message"
                    print message
                else:
                    print "TODO: Receive a video frame and show it"
                    
        except:
            print "Server sent an unknown message"
            print message

    def handle_write(self):
        curtime = time.time()
        events = pygame.event.get()
        if [ evt for evt in events \
                 if evt.type == pygame.QUIT ]:
            sys.exit(0)

        joyaxisevents = [ evt for evt in events \
                              if evt.type == pygame.JOYAXISMOTION ]
        
        for e in joyaxisevents:
            if e.axis == 0 or e.axis == 1:
                self.queue_control_state[e.axis] = e.value
        
        keyevents = [ evt for evt in events \
                          if evt.type == pygame.KEYDOWN ]

        for e in keyevents:
            if e.key == pygame.K_UP:
                self.queue_control_state[1] = 1.0
            elif e.key == pygame.K_DOWN:
                self.queue_control_state[1] = -1.0
            elif e.key == pygame.K_LEFT:
                self.queue_control_state[0] = -1.0
            elif e.key == pygame.K_RIGHT:
                self.queue_control_state[0] = 1.0
            elif e.key == pygame.K_SPACE:
                self.queue_control_state = [0,0]
        
        if curtime - self.last_send_timestamp > Client.TICK_RATE:
            msg = ProtocolMessage(ProtocolMessage.OP_DIRECTION, \
                                      "DIRECTION")
            for i, v in enumerate(self.queue_control_state):
                msg["X-%i-Axis" % i] = str(v) 
            self.last_send_timestamp = curtime

            self.sendto(str(msg), self.address)

    def writeable(self):
        return True

def print_help():
    print "Usage: client HOST PORT"

if __name__=="__main__":
    if len(sys.argv) != 3:
        print_help()
        sys.exit(0)
    else:
        host = sys.argv[1]
        try:
            port = int(sys.argv[2])
        except:
            print "Port is not a number"
            sys.exit(1)
    if port < 1 or port > 65535 or len(host) == 0:
        print "Port is out of range"
        sys.exit(1)
    if len(host) == 0:
        print "Hostname is empty"
        sys.exit(1)

    pygame.init()
    pygame.display.init()
    pygame.joystick.init()
    pygame.display.init()
    pygame.display.set_mode((640, 480), 16)
    address = (host, port)
    cli = Client(address)
    asyncore.loop()
        
