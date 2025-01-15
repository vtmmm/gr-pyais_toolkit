#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
from gnuradio import gr

import pmt
from geopy.distance import distance
from time import sleep
from threading import Thread

class strobe_latlon_list_line(gr.sync_block):
    """
    Emit a message containing a vector of latlons.

    If latlon source is set to Message, this will not emit anything until the lat_ref and lat_ref are set via the latlon input.

:   """
    def __init__(self,interval=1,initial_delay=0.0,latlon_source='Manual Entry',lat_ref=0.0,lon_ref=0.0,spacing_m=1000,num_points=32, orientation=0, offset_bearing=0, offset_distance_m=0):
        gr.sync_block.__init__(self,
            name="strobe_latlon_list_line",
            in_sig=None,
            out_sig=None)

        # Store user variables
        self.interval = interval
        self.initial_delay = initial_delay
        self.latlon_source = latlon_source
        self.lat_ref = lat_ref
        self.lon_ref = lon_ref
        self.spacing_m = spacing_m # meters
        self.num_points = num_points
        self.orientation = orientation
        self.offset_bearing = offset_bearing
        self.offset_distance_m = offset_distance_m

        # Internal
        self.latlon_initialized = False
        self.pmt_vector = None

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('latlon_vec'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Set up points in a line
        self.define_points()

        # Thread for strobing
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()

    def define_points(self):
        self.points = []

        angle = self.orientation % 360
        mid_index = (self.num_points-1)/2

        # Create geopy Points
        for i in range(self.num_points):
            offset = i - mid_index

            distance_m = abs(offset)*self.spacing_m

            if offset < 0:
                angle = (self.orientation + 180) % 360
            else:
                angle = self.orientation % 360

            origin = (self.lat_ref, self.lon_ref)
            new_point = distance(meters=distance_m).destination(origin, angle)

            # If line is shifted, apply another distance offset
            if self.offset_bearing != 0 and self.offset_distance_m != 0:
                new_point = distance(meters=self.offset_distance_m).destination(
                        (new_point.latitude, new_point.longitude), self.offset_bearing%360)

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
        # Sleep for initial delay
        sleep(self.initial_delay)

        while True:
            if not self.pmt_vector:
                sleep(0.05)
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

