#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


from gnuradio import gr

from array import array
import pmt
from pyais.decode import decode
from pyais.encode import encode_msg

class nmea_strings_to_bytes(gr.sync_block):
    """
    Convert an array of NMEA strings (nmea_list) to nmea_bytes.

    per nmea_list input, this may generate one or more nmea_bytes messages
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="nmea_strings_to_nmea_list",
            in_sig=None,
            out_sig=None)

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_out(pmt.intern('nmea_bytes'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)

    def handle_nmea_list(self, msg):
        if msg is None:
            return

        PMT_msg = pmt.to_python(msg)
        if type(PMT_msg) is not list:
            return

        for sentence in PMT_msg:
            nmea_byte_array = array('B', sentence.encode('utf-8'))

            pmt_array = pmt.init_u8vector(len(nmea_byte_array), nmea_byte_array.tolist())

            self.message_port_pub(pmt.intern('nmea_bytes'), pmt.cons(pmt.PMT_NIL, pmt_array))

        return
