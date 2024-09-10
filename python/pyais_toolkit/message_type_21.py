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

from pyais.messages import MessageType21
from pyais.encode import encode_msg

class message_type_21(gr.sync_block):
    """
    Aids-to-navigation report
    \n
    Sample Input:
    (((lat . 30)(lon . -100)))
    or
    ((mmsi . 338123456))
    TODO: VERIFY/implement
    
    Sample Output:
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    TODO: Use an actual MSG5 NMEA string
    
    Input may be:
     - from LatLon Strobe block to the latlon message port
     - from MMSI Strobe block to the mmsi mesage port

    Latitude and longitude is not used by this block, but it
    accepts a latlon message to trigger a NMEA message for
    sake of convenience.
    """
    def __init__(self,
            # Important/Unique to message type
            mmsi='338123456',
            aid_type=0,
            virtual_aid=0,
            name='',
            name_ext='',
            lat=0.0,
            lon=0.0,
            to_bow=0,
            to_stern=0,
            to_port=0,
            to_starboard=0,
            epfd=0, # position fix type?
            off_position=0,
            # Others
            raim=0,
            accuracy=0,
            repeat=0,
            reserved_1=0,
            second=0,
            assigned=0,
            spare_1=b'',
            ):

        gr.sync_block.__init__(self,
                name="AIS Generator: Message Type 21",
            in_sig=None,
            out_sig=None)

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('mmsi'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('mmsi'), self.handle_mmsi)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Initialize message
        self.msg21 = MessageType21.create(mmsi=mmsi,aid_type=aid_type,name=name,lat=lat,lon=lon,to_bow=to_bow,to_stern=to_stern,to_port=to_port,to_starboard=to_starboard,epfd=epfd,off_position=off_position,virtual_aid=virtual_aid,assigned=assigned,spare_1=spare_1,name_ext=name_ext)

    def handle_mmsi(self, msg):
        """
        Set the MMSI and generate the message
        """
        # TODO: Determine this format and implement setting the MMSI
        nmea_list = pmt.to_pmt(encode_msg(self.msg21, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self.msg21, key):
                setattr(self.msg21, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG21 latlon and publishes list of encoded NMEA strings
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.msg21.lat = pmt.to_float(lat)
        self.msg21.lon = pmt.to_float(lon)

        # Create and publish NMEA message
        nmea_list = pmt.to_pmt(encode_msg(self.msg21, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

