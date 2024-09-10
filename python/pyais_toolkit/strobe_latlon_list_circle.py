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
from time import sleep
from threading import Thread

class strobe_latlon_list_circle(gr.sync_block):
    """
    docstring for block strobe_latlon_list_circle
    """
    def __init__(self,interval=1,latlon_source='Manual Entry',lat_ref=0.0,lon_ref=0.0,radius=100,num_points=32):
        gr.sync_block.__init__(self,
            name="strobe_latlon_list_circle",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.interval = interval
        self.latlon_source = latlon_source
        self.lat_ref = lat_ref
        self.lon_ref = lon_ref
        self.radius = radius
        self.num_points = num_points
        self.latlon_initialized = False
        self.pmt_vector = None

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('latlon_vec'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Thread for strobing
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()

        # Set up circle
        self.define_points()

    def define_points(self):
        # storing the geopy Points in case we want to do anything else with them
        self.points = []
        angle_increment = 360/self.num_points

        # Create geopy Points
        for i in range(self.num_points):
            angle = i*angle_increment
            new_point = geodesic(meters=self.radius).destination((self.lat_ref,self.lon_ref),angle)
            self.points.append(new_point)

        # Create PMT vector
        self.pmt_vector = pmt.make_vector(len(self.points), pmt.PMT_NIL)

        for i, point in enumerate(self.points):
            lat, lon = point.latitude, point.longitude
        
            lat_dict = pmt.dict_add( pmt.make_dict(), pmt.intern("lat"), pmt.from_float(lat))
            latlon_dict = pmt.dict_add(lat_dict, pmt.intern("lon"), pmt.from_float(lon))
            
            pmt.vector_set(self.pmt_vector, i, latlon_dict)

        return

    def _strobe(self):
        while True:
            if not self.pmt_vector:
                print("PMT Vector not initialized...")
                sleep(0.1)
                continue
            if self.latlon_source=='latlon MSG Input' and not self.latlon_initialized:
                sleep(self.interval)
                continue

            self.message_port_pub(pmt.intern('latlon_vec'), pmt.cons(pmt.make_dict(), self.pmt_vector))
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
        Sets the reference latlon
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.lat_ref = pmt.to_float(lat)
        self.lon_ref = pmt.to_float(lon)

        self.define_points()
        self.latlon_initialized = True

        return

