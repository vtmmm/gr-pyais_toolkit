#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

from array import array
import pmt
from pyais.decode import decode
from pyais.encode import encode_msg

class nmea_bytes_to_strings(gr.sync_block):
    """
    Convert an array of NMEA bytes (from gr-ais) to the strings used in this OOT module.
    \n
    This accepts messages from the PDU to NMEA block in gr-ais.
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="nmea_bytes_to_strings",
            in_sig=None,
            out_sig=None)

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_bytes'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_bytes'), self.handle_nmea_bytes)

    def handle_nmea_bytes(self, msg):
        if msg is not None:
            PMT_msg = pmt.to_python(msg)
            byte_array_msg = array('B', PMT_msg[1])
            byte_msg = bytes(byte_array_msg)
            msg = decode(byte_msg)

            nmea_list = pmt.to_pmt(encode_msg(msg, talker_id='AIVDM'))
            self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
            return
