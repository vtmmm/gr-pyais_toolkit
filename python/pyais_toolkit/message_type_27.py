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

from pyais.messages import MessageType27
from pyais.encode import encode_msg

class message_type_27(gr.sync_block):
    """
    Sample input on latlon to generate message:
    latlon: (((lat . 30)(lon . -100)))
    
    Sample input on mmsi to generate message:
    ((mmsi . 338123456))

    Sample input on set_params to set message parameters (does not generate NMEA message):
    $(TODO....)
    
    Sample Output (TODO: actual msg 27):
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    
    Inputs to the message ports may be from:
    - LatLon Strobe block
    - MMSI Strobe block
    - Set Params GUI block
    """
    def __init__(self,
            mmsi='338123456',
            course=0,
            heading=0,
            lat=0.0,
            lon=0.0,
            speed=0,
            accuracy=0,
            gnss=0,
            is_itdma=False,
            is_sotdma=True,
            maneuver=0,
            radio=0,
            raim=0,
            repeat=0,
            second=0,
            spare_1=''
            ):
            #status (ENUM)
            #turn (ENUM)

        gr.sync_block.__init__(self,
                name="AIS Generator: Message Type 27",
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
        self.msg27 = MessageType27.create(mmsi=mmsi, course=course, heading=heading, lat=lat, lon=lon, speed=speed, accuracy=accuracy, gnss=gnss, is_itdma=is_itdma, maneuver=maneuver, radio=radio, raim=raim, repeat=repeat, second=second, spare_1=str.encode(spare_1)) 

    def handle_mmsi(self, msg):
        """
        Generates message based on current latlon. TODO: Make it set the mmsi as well.
        """
        # TODO: determine message format and actually set MMSI. Then copy to all relevant blocks

        nmea_list = pmt.to_pmt(encode_msg(self.msg27, talker_id='AVIDM'))
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
            if hasattr(self.msg27, key):
                setattr(self.msg27, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG27 latlon and publishes list of encoded NMEA strings.
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.msg27.lat = pmt.to_float(lat)
        self.msg27.lon = pmt.to_float(lon)

        # Create and publish NMEA message
        nmea_list = pmt.to_pmt(encode_msg(self.msg27, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

