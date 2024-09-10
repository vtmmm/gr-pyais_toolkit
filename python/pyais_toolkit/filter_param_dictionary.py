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
from pyais.decode import decode

class filter_param_dictionary(gr.sync_block):
    """
    - Accepts nmea_list messages
    - Decodes to a pyais message
    - Checks if all key:value pairs passed in params_dict match message contents
    - If so, it forwards the NMEA message on

    Note: keys passed must match attributes of pyais data fields.
    """
    def __init__(self, params_dict={'mmsi':'336123456', 'msg_type':1}):
        gr.sync_block.__init__(self,
            name="filter_param_dictionary",
            in_sig=None,
            out_sig=None)
        
        # Variables needed in MSG handling functions
        self.params_dict = params_dict

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)

    def handle_nmea_list(self, msg):

        # Convert to python and enforce list
        nmea_list = pmt.to_python(msg)
        if type(nmea_list) != list:
            return

        try:
            decoded_msg = decode(*nmea_list)
            for param, value in self.params_dict.items():

                # Doesn't have that data field
                if not hasattr(decoded_msg, param):
                    return

                current_value = getattr(decoded_msg, param)

                # Data value doesn't match
                try:
                    if str(current_value) != str(value):
                        return
                except Exception as e:
                    print(f"Could not cast to string: {current_value} or {value}")
                    print(e)
                    return

            print(f"MATCH: getattr(decoded_msg, param))")

            # If the parameter and value match, forward the msg
            self.message_port_pub(pmt.intern('nmea_list'), msg)

        except Exception as e:
            print(e)
            return

