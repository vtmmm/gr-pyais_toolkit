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

class get_params(gr.sync_block):
    """
    - Accepts nmea_list messages
    - Decodes to a pyais message
    - Gets the values of the items passed as 'params' by block properties
    - Outputs a PDU containing a dictionary of only those items

    Note: Output matches the set_params message format used by other blocks
    """
    def __init__(self, params=['mmsi','lat','lon']):
        gr.sync_block.__init__(self,
            name="get_params",
            in_sig=None,
            out_sig=None)

        # Variables needed in MSG handling functions
        self.params = params

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_out(pmt.intern('set_params'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)

    def handle_nmea_list(self, msg):

        # Convert to python and enforce list
        nmea_list = pmt.to_python(msg)
        if type(nmea_list) != list:
            return

        matching_params = {}
        try:
            decoded_msg = decode(*nmea_list)
            for param in self.params:
                if hasattr(decoded_msg, param):
                    value = getattr(decoded_msg, param)
                    matching_params[param] = value
        except Exception as e:
            print(e)
            return

        if len(matching_params) == 0:
            return

        # Need to convert any bytes to hex
        matching_params_nobytes = {k: (v.hex() if isinstance(v, bytes) else v) for k, v in matching_params.items()}

        output_msg = pmt.cons(pmt.to_pmt(matching_params_nobytes), pmt.PMT_NIL)
        self.message_port_pub(pmt.intern('set_params'), output_msg)

