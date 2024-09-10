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
from random import uniform
from threading import Thread
from time import sleep
from math import cos, radians

class strobe_random_latlon(gr.sync_block):
    """
    Emit a latlon message with random values within radius of a center point.

    Emits the message every *interval* seconds.

    Accepts latlon to set a new location.
    """
    def __init__(self, interval=1.0, lat_center=0, lon_center=0, offset=0):
        gr.sync_block.__init__(self,
            name="strobe_random_latlon",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.interval = interval
        self.lat_center = lat_center
        self.lon_center = lon_center
        self.offset = offset

        # Message ports
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_out(pmt.intern("latlon"))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Thread for strobing
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()

    def _strobe(self):
        while True:
            sleep(self.interval)

            # stores values in self.lat, self.lon
            self.set_random_lat_lon() 

            lat_dict = pmt.dict_add( pmt.make_dict(), pmt.intern("lat"), pmt.from_float(self.lat))
            latlon_dict = pmt.dict_add(lat_dict, pmt.intern("lon"), pmt.from_float(self.lon))
            self.message_port_pub(pmt.intern('latlon'), pmt.cons(latlon_dict, pmt.PMT_NIL))

    def start(self):
        return super().start()

    def stop(self):
        return super().stop()

    def set_random_lat_lon(self):
        # Latitude: 1 degree ≈ 111 km
        # Longitude: 1 degree ≈ 111 km * cos(latitude) (approx.)
        
        # km to degrees
        lat_offset = self.offset / 111
        lon_offset = self.offset / (111 * abs(cos(radians(self.lat_center))))

        self.lat = self.lat_center + uniform(-lat_offset, lat_offset)
        self.lon = self.lon_center + uniform(-lon_offset, lon_offset)

        return

    def handle_latlon(self, msg):
        """
        Sets the Center Lat/Lon
        """
        self.lat_center = pmt.to_float(pmt.cdr(pmt.car(pmt.cdar(msg))))
        self.lon_center = pmt.to_float(pmt.cdr(pmt.caar(msg)))

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



