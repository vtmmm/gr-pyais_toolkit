#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

import pmt
from socket import socket, AF_INET, SOCK_DGRAM

class nmea_to_opencpn(gr.sync_block):
    """
    Accepts nmea_list
    For each NMEA message, it broadcasts the string on the UDP port specified
    
    To view the data in OpenCPN:
    - Go to Settings > Connections
    - Add a new connection with type Network and UDP using the specified port
    """
    def __init__(self, ip='127.0.0.1', port=2999):
        gr.sync_block.__init__(self,
            name="nmea_to_opencpn",
            in_sig=None,
            out_sig=None)

        self.ip = ip
        self.port = port
        self.sock = socket(AF_INET, SOCK_DGRAM)

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)


    def handle_nmea_list(self, msg):

        # Convert to python and enforce list
        nmea_list = pmt.to_python(msg)
        if type(nmea_list) != list:
            return

        try: 
            nmea_bytes = [s.encode('utf-8') for s in nmea_list]
        except Exception as e:
            print("Failed to convert to bytes:")
            print(e)
            return
        for sentence in nmea_bytes:

            try:
                self.sock.sendto(sentence, (self.ip, self.port))
            except Exception as e:
                print(f"Failed to send sentence: {sentence}")
                print(e)
                continue
        return

