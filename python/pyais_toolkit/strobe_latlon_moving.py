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
from geopy.distance import geodesic
from geopy.point import Point
from threading import Thread
from time import sleep

class strobe_latlon_moving(gr.sync_block):
    """
    Emit latlon starting at the reference point, moving as specified

    Accepts a latlon message to set the reference point and restart from there

    # TODO:
    - Provide option to wait until reference point is set via latlon message
    - Output the bearing as a dict that can be used for set_params (for course or heading)
    - Accept an offset to the heading or speed that can be applied
    """
    def __init__(self, lat_ref=0.0,lon_ref=0.0,bearing=0,speed=10,interval=1):
        gr.sync_block.__init__(self,
            name="strobe_latlon_moving",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.lat_ref = self.lat_new = lat_ref
        self.lon_ref = self.lon_new = lon_ref
        self.bearing = bearing
        self.speed = speed
        self.interval = interval
        self.latlon_received = False  # Not yet used

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('latlon'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Thread for strobing
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()

    def update_position(self, lat, lon, speed_knots, course, interval_seconds):
        # knots to kph
        speed_kmh = speed_knots * 1.852
        
        distance_km = (speed_kmh * interval_seconds) / 3600
        
        # Handle negative values
        course = course % 360

        start_point = Point(lat, lon)
        position = geodesic(kilometers=distance_km).destination(start_point, course)
        
        return position.latitude, position.longitude

    def _strobe(self):
        while True:
            # Emit immediately so first message is the reference point 
            lat_dict = pmt.dict_add( pmt.make_dict(), pmt.intern("lat"), pmt.from_float(self.lat_new))
            latlon_dict = pmt.dict_add(lat_dict, pmt.intern("lon"), pmt.from_float(self.lon_new))
            self.message_port_pub(pmt.intern('latlon'), pmt.cons(latlon_dict, pmt.PMT_NIL))

            self.lat_new, self.lon_new = self.update_position(self.lat_new, self.lon_new, self.speed, self.bearing, self.interval)

            sleep(self.interval)

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

    def handle_latlon(self, msg):
        """
        Sets the reference latlon and restarts simulated movement
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.lat_ref = self.lat_new = pmt.to_float(lat)
        self.lon_ref = self.lon_new = pmt.to_float(lon)

        return

