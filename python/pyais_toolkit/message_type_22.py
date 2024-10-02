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
from pyais.messages import MessageType22
from pyais.encode import encode_msg

class message_type_22(gr.sync_block):
    """
    Message 22: Channel management
\n
    The fields in this message will depend on whether it is addressed or not.
\n
    # TODO: Determine YAML parameter type, then clarify following documentation:
    \n
    You cannot change whether the message is addressed or broadcast during runtime:
    https://github.com/gnuradio/gnuradio/issues/6870
    \n 
    If it is changed to an int, then you can. In that case.
    If you change whether it is addressed using set_params, you should also set the message fields associated with that version of Msg22.
\n
    Any message to the latlon port will cause this to generate a message, even though the position isn't used.
    \n
    Spare 1 is 2 bits
    Spare 2 is 23 bits
    """
    def __init__(self,
            mmsi='338123456',
            addressed=0,
            channel_a=0,
            channel_b=0,
            txrx=0,
            power=False,

            # Broadcast
            ne_lat=0,
            ne_lon=0,
            sw_lat=0,
            sw_lon=0,

            # Addressed
            dest1=0,
            empty_1=0,
            dest2=0,
            empty_2=0,

            # Other
            band_a=0,
            band_b=0,
            zonesize=0,
            repeat=0,
            spare_1=b'',
            spare_2=b''
            ):
        gr.sync_block.__init__(self,
            name="message_type_22",
            in_sig=None,
            out_sig=None)

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Handle ENUM parameters
        '''
        if power == 'False':
            power = False
        elif power == 'True':
            power = True
        if band_a == 'False':
            band_a = False
        elif band_a == 'True':
            band_a = True
        if band_b == 'False':
            band_b = False
        elif band_b == 'True':
            band_b = True
            '''

        # Initialize message
        self.msg22 = MessageType22.create(mmsi=mmsi, addressed=addressed, channel_a=channel_a, channel_b=channel_b, txrx=txrx, power=power, ne_lon=ne_lon, ne_lat=ne_lat, sw_lon=sw_lon, sw_lat=sw_lat, dest1=dest1, empty_1=empty_1, dest2=dest2, empty_2=empty_2, band_a=band_a, band_b=band_b, zonesize=zonesize, repeat=repeat, spare_1=spare_1, spare_2=spare_2)

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self.msg22, key):
                setattr(self.msg22, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG1 latlon and publishes list of encoded NMEA strings.
        """
        nmea_list = pmt.to_pmt(encode_msg(self.msg22, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

