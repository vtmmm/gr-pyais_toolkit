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
from pyais.decode import decode

class filter_bounding_box(gr.sync_block):
    """
    - Accepts nmea_list messages
    - Decodes to a pyais message
    - Checks if 'lat' and 'lon' are within specified bounding box
    - If so, it forwards the NMEA message on
    """
    def __init__(self, lat_min=0, lat_max=0, lon_min=0, lon_max=0):
        gr.sync_block.__init__(self,
            name="filter_bounding_box",
            in_sig=None,
            out_sig=None)
        
        # Variables needed in MSG handling functions
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

    def handle_nmea_list(self, msg):

        # Convert to python and enforce list
        nmea_list = pmt.to_python(msg)
        if type(nmea_list) != list:
            return

        try:
            decoded_msg = decode(*nmea_list)
            if not hasattr(decoded_msg, 'lat'):
                return
            if not hasattr(decoded_msg, 'lon'):
                return

            if self.lat_min <= decoded_msg.lat <= self.lat_max:
                if self.lon_min <= decoded_msg.lon <= self.lon_max:
                    self.message_port_pub(pmt.intern('nmea_list'), msg)

        except Exception as e:
            print(e)
            return

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

        return
