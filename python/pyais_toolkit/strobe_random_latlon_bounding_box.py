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

class strobe_random_latlon_bounding_box(gr.sync_block):
    """
    Emit a latlon message with random values within the bounds provided.

    Emits the message every *interval* seconds.
    """
    def __init__(self, interval=1.0, initial_delay=0.0, lat_min=0,lat_max=0,lon_min=0,lon_max=0):
        gr.sync_block.__init__(self,
            name="strobe_random_latlon_bounding_box",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.interval = interval
        self.initial_delay = initial_delay
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.lon_min = lon_min
        self.lon_max = lon_max

        # Message ports
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern("latlon"))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Thread for strobing
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()

    def _strobe(self):
        # Sleep for initial delay
        sleep(self.initial_delay)

        while True:
            sleep(self.interval)
            lat, lon = uniform(self.lat_min, self.lat_max), uniform(self.lon_min, self.lon_max) 
            lat_dict = pmt.dict_add( pmt.make_dict(), pmt.intern("lat"), pmt.from_float(lat))
            latlon_dict = pmt.dict_add(lat_dict, pmt.intern("lon"), pmt.from_float(lon))
            self.message_port_pub(pmt.intern('latlon'), pmt.cons(latlon_dict, pmt.PMT_NIL))

    def start(self):
        return super().start()

    def stop(self):
        return super().stop()

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



