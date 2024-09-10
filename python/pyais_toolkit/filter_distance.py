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
from geopy.distance import geodesic

class filter_distance(gr.sync_block):
    """
    - Accepts nmea_list messages
    - Decodes to a pyais message
    - Checks if 'lat' and 'lon' are within specified distance to the reference point
    - If so, it forwards the NMEA message on

    latlon: input can be used to set the reference point

    # TODO
    distance: emits distance and mmsi for matching messages 
    
    """
    def __init__(self, lat_ref=0,lon_ref=0,distance_min=0,distance_max=0):
        gr.sync_block.__init__(self,
            name="filter_distance",
            in_sig=None,
            out_sig=None)

        self.lat_ref = lat_ref
        self.lon_ref = lon_ref
        self.distance_min = distance_min
        self.distance_max = distance_max

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))
        self.message_port_register_out(pmt.intern('distance'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
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

            # Distance calculation that requires geopy
            distance = geodesic( (decoded_msg.lat, decoded_msg.lon), (self.lat_ref, self.lon_ref) ).km

            if self.distance_min <= distance <= self.distance_max:
                self.message_port_pub(pmt.intern('nmea_list'), msg)
                # TODO: Also emit mmsi and distance as a dict

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

    def handle_latlon(self, msg):
        """
        Sets the Reference Lat/Lon
        """
        self.lat_ref = pmt.to_float(pmt.cdr(pmt.car(pmt.cdar(msg))))
        self.lon_ref = pmt.to_float(pmt.cdr(pmt.caar(msg)))

        return
