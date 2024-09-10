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
from pyais.encode import encode_msg
from pyais.filter import DistanceFilter, FilterChain, GridFilter, MessageTypeFilter, NoneFilter
from pyais import IterMessages

class filter_pyais_combined(gr.sync_block):
    """

Implements 4 of the 5 filters supported by pyais:
    https://pyais.readthedocs.io/en/latest/filters.html
\n
You may choose to use however many you want.
\n
If no filters are activated, you may select whether to BLOCK ALL or PASS ALL.
\n
NoneFilter:
 - List attributes that must exist in the message and not equal None
 - Example: If you want to ensure you're only getting messages UTC time reports, enter ['year']
\n
MessageTypeFilter:
 - Enter a python list of message types you want to keep
 - Example: to only keep messages 1, 2, 3, and 18, enter [1,2,3,18]
\n
DistanceFilter:
 - Only keeps messages with a lat/lon within some distance of a reference point
 - The reference point can be set manually or via latlon message input
 - If selecting latlon message, filter will be inactive until a latlon message is received
 - If selecting Manual Entry, a latlon message will still override the manual reference point
\n
GridFilter:
 - Only keeps messages within a bounding box
\n
# TODO:
- Add AttributeFilter
- Support nmea_bytes
    """
    def __init__(self,
           use_NoneFilter=None,
           required_attributes=None,
           use_MessageTypeFilter=None,
           msg_types_kept=None,
           use_DistanceFilter=None,
           latlon_source=None,
           lat_ref=None,
           lon_ref=None,
           distance_km=None,
           use_GridFilter=None,
           lat_min=None,
           lat_max=None,
           lon_min=None,
           lon_max=None,
           no_filter_policy=None
           ):

        gr.sync_block.__init__(self,
            name="filter_pyais_combined",
            in_sig=None,
            out_sig=None)

        # Store block parameter variables 
        self.use_NoneFilter=use_NoneFilter
        self.required_attributes=required_attributes

        self.use_MessageTypeFilter=use_MessageTypeFilter
        self.msg_types_kept=msg_types_kept

        self.use_DistanceFilter=use_DistanceFilter
        self.latlon_source=latlon_source
        self.lat_ref=lat_ref
        self.lon_ref=lon_ref
        self.distance_km=distance_km

        self.use_GridFilter=use_GridFilter
        self.lat_min=lat_min
        self.lat_max=lat_max
        self.lon_min=lon_min
        self.lon_max=lon_max

        self.no_filter_policy=no_filter_policy

        # Store other variables
        self.latlon_initialized=False
 
        # Construct initial filter chain
        self.construct_filter_chain()

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))


        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

    def construct_filter_chain(self):
        """
        Initialize whatever filters were enabled in the block parameters.

        This method is called on __init__ and whenever a latlon msg is received.

        This might be inefficient if new latlons are constantly received...
        """
        filters = []
        if self.use_NoneFilter:
            filters.append(NoneFilter(*self.required_attributes))
            print('appended nonefilter')
        if self.use_MessageTypeFilter:
            filters.append(MessageTypeFilter(*self.msg_types_kept))
            print('appended msgTypeFilter')
        if self.use_DistanceFilter:
            print('using distancefilter')
            # Regardless of latlon_source, if a latlon msg is received, use it instead
            if self.latlon_initialized or (self.latlon_source=='Manual Entry'): 
                filters.append(DistanceFilter((self.lat_ref, self.lon_ref), self.distance_km))
        if self.use_GridFilter:
            filters.append(GridFilter(
                lat_min=self.lat_min,
                lat_max=self.lat_max,
                lon_min=self.lon_min,
                lon_max=self.lon_max
                ))
            print('using gridfilter')

        print(f"filters: {filters}")
        if len(filters) > 0:
            self.filter_chain = FilterChain(filters)
        else:
            self.filter_chain = None
        print(self.filter_chain)
        return

    def handle_nmea_list(self, msg):

        # All filters turned off, or using uninitialized DistanceFilter
        if not self.filter_chain:
            if self.no_filter_policy == 'PASS ALL':
                # TODO: Publish messages
                self.message_port_pub(pmt.intern('nmea_list'), msg)
                return
            else:
                return

        # Convert to python and enforce list
        try:
            nmea_list = pmt.to_python(msg)
        except Exception as e:
            print("Failed to convert received msg to python")

        if type(nmea_list) != list:
            return

        try:
            nmea_bytes = [s.encode('utf-8') for s in nmea_list]
        except Exception as e:
            print("failed to convert to nmea_bytes")
            print(e)
            return

        try:
            # FilterChain only operates on a stream or fake stream via IterMessages of bytes 
            filtered = self.filter_chain.filter(IterMessages(nmea_bytes))
        except Exception as e:
            print("Failed to filter nmea_bytes")
            print(e)
            return 

        for message in filtered:
            nmea_list = pmt.to_pmt(encode_msg(message, talker_id='AIVDM'))
            try:
                self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
            except Exception as e:
                print('failed to publish')
                print(e)
        return

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and resets the filters.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

        self.filter_chain = self.construct_filter_chain()

        return

    def handle_latlon(self, msg):
        """
        Sets the DistanceFilter latlon reference and updates the filters.
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.lat_ref = pmt.to_float(lat)
        self.lon_ref = pmt.to_float(lon)

        print(f"Updated distance reference: {lat}, {lon}")

        self.latlon_initialized = True
        self.construct_filter_chain()

        return

