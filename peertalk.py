#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#  peertalk.py
#
# Copyright (C) 2012    David House <davidahouse@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 or version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA
#
#
# This script depends on the usbmux python script that you can find here:
# http://code.google.com/p/iphone-dataprotection/source/browse/usbmuxd-python-client/?r=3e6e6f047d7314e41dcc143ad52c67d3ee8c0859
# Also only works with the PeerTalk iOS application that you can find here:
# https://github.com/rsms/peertalk
#
import usbmux
import SocketServer
import select
from optparse import OptionParser
import sys
import threading
import struct

class PeerTalkThread(threading.Thread):
	def __init__(self,*args):
		self._psock = args[0]
		self._running = True
		threading.Thread.__init__(self)

	def run(self):
		framestructure = struct.Struct("! I I I I")
		while self._running:
			try:
				msg = self._psock.recv(16)
				if len(msg) > 0:
					frame = framestructure.unpack(msg)
					size = frame[3]
					msgdata = self._psock.recv(size)
					print "Received: %s" % msgdata
			except:
				pass

	def stop(self):
		self._running = False

print "peertalk starting"
mux = usbmux.USBMux()

print "Waiting for devices..."
if not mux.devices:
    mux.process(1.0)
if not mux.devices:
    print "No device found"

dev = mux.devices[0]
print "connecting to device %s" % str(dev)
psock = mux.connect(dev, 2345)
psock.setblocking(0)
psock.settimeout(2)

ptthread = PeerTalkThread(psock)
ptthread.start()

print "type quit to exit!"

done = False
while not done:
	cmd = raw_input("message: ")
	if cmd == "quit":
		done = True
	else:
		r8 = cmd.encode('utf-8')
		headervalues = (1,101,0,len(r8)+4)
		framestructure = struct.Struct("! I I I I")
		packed_data = framestructure.pack(*headervalues)
		psock.send(packed_data)
		messagevalues = (len(r8),r8)
		fmtstring = "! I {0}s".format(len(r8))
		sm = struct.Struct(fmtstring)
		packed_message = sm.pack(*messagevalues)
		psock.send(packed_message)

ptthread.stop()
ptthread.join()
psock.close()

