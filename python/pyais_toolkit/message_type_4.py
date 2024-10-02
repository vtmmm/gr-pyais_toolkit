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
from pyais.messages import MessageType4
from pyais.encode import encode_msg

class message_type_4(gr.sync_block):
    """
    Message 4: Base station report
    \n
    Sample input on latlon to generate message:
    latlon: (((lat . 30)(lon . -100)))

    Sample input on mmsi to generate message:
    ((mmsi . 003381234))

    Message 4 is used by AIS stations for determining if it is within 120 NM for response to Messages 20 and 23.
    """
    def __init__(self,
            mmsi='338123456',
            lat=0,
            lon=0,
            year=1970,
            month=1,
            day=1,
            hour=0,
            minute=0,
            second=0,
            accuracy=0,
            epfd=0,
            is_itdma=False,
            is_sotdma=True,
            radio=0,
            raim=0,
            repeat=0,
            spare_1=''
            ):
        gr.sync_block.__init__(self,
            name="message_type_4",
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
        self.msg4 = MessageType4.create(mmsi=mmsi, lat=lat, lon=lon, year=year, month=month, day=day, hour=hour, minute=minute, second=second, accuracy=accuracy, epfd=epfd, is_itdma=is_itdma, is_sotdma=is_sotdma, radio=radio, raim=raim, repeat=repeat, spare_1=str.encode(spare_1)) 

    def handle_mmsi(self, msg):
        """
        Generates message based on current latlon. TODO: Make it set the mmsi as well.
        """
        # TODO: determine message format and actually set MMSI. Then copy to all relevant blocks

        nmea_list = pmt.to_pmt(encode_msg(self.msg4, talker_id='AIVDM'))
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
            if hasattr(self.msg4, key):
                setattr(self.msg4, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG4 latlon and publishes message.
        """
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.msg4.lat = pmt.to_float(lat)
        self.msg4.lon = pmt.to_float(lon)
        nmea_list = pmt.to_pmt(encode_msg(self.msg4, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

