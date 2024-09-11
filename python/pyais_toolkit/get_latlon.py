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

class get_latlon(gr.sync_block):
    """
    Input NMEA messages
    \n
    Outputs a latlon message based on the message (if included)
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="get_latlon",
            in_sig=None,
            out_sig=None)
        
        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_out(pmt.intern('latlon'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)


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

            lat = decoded_msg.lat
            lon = decoded_msg.lon

            lat_dict = pmt.dict_add( pmt.make_dict(), pmt.intern("lat"), pmt.from_float(lat))
            latlon_dict = pmt.dict_add(lat_dict, pmt.intern("lon"), pmt.from_float(lon))
            self.message_port_pub(pmt.intern('latlon'), pmt.cons(latlon_dict, pmt.PMT_NIL))

        except Exception as e:
            print(e)

        return

