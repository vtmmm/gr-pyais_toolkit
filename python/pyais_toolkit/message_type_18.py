#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import pmt
from gnuradio import gr

from pyais.messages import MessageType18
from pyais.encode import encode_msg


class message_type_18(gr.sync_block):
    """
    Standard Class B Equipment Position Report
\n
    Sample input on latlon to generate message:
    latlon: (((lat . 30)(lon . -100)))
\n
    Sample input on mmsi to generate message:
    ((mmsi . 338123456))
\n
    Sample input on set_params to set message parameters (does not generate NMEA message):
    $(TODO....)
\n
    Sample Output:
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    
    """
    def __init__(self, 
            mmsi='338123456',
            course=0,
            heading=0,
            lat=0,
            lon=0,
            speed=0):
            # Others...

        gr.sync_block.__init__(self,
                name="AIS Generator: Message Type 18",
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
        self.msg18 = MessageType18.create(mmsi=mmsi, course=course, heading=heading, lat=lat, lon=lon, speed=speed) 

    def handle_mmsi(self, msg):
        """
        Generates message based on current latlon. TODO: Make it set the mmsi as well.
        """
        # TODO: determine message format and actually set MMSI. Then copy to all relevant blocks

        nmea_list = pmt.to_pmt(encode_msg(self.msg18, talker_id='AIVDM'))
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
            if hasattr(self.msg18, key):
                setattr(self.msg18, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG1 latlon and publishes list of encoded NMEA strings.
        """
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        #print(f"lat: {lat}")
        #print(f"lon: {lon}")
        self.msg18.lat = pmt.to_float(lat)
        self.msg18.lon = pmt.to_float(lon)
        nmea_list = pmt.to_pmt(encode_msg(self.msg18, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

