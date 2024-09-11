#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

import numpy as np
import pmt
from array import array
from pyais.decode import decode
from pyais.encode import encode_msg

class nmea_to_nmea_bits(gr.sync_block):
    """
    Takes nmea_list or nmea_bytes and outputs a bitarray
    that is compatible with the required input for
    gr-ais_simulator's flowgraph.
    \n
    For example, the following will generate IQ bursts that
    could be sent to a radio:
    \n
    NMEA to AIS Simulator > PDU to Tagged Stream >
    Bit String to Frame > GMSK Mod > Fast Multiply > radio or IQ
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="nmea_to_nmea_bits",
            in_sig=None,
            out_sig=None)

        # Message ports
        self.message_port_register_in(pmt.intern('nmea_list'))
        self.message_port_register_in(pmt.intern('nmea_bytes'))
        self.message_port_register_out(pmt.intern('nmea_bits'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('nmea_list'), self.handle_nmea_list)
        self.set_msg_handler(pmt.intern('nmea_bytes'), self.handle_nmea_bytes)


    def pyais_msg_to_bitarray(self, pyais_msg):
        bits_bitarray = pyais_msg.to_bitarray()
        binary_list = [int(bit) + 48 for bit in bits_bitarray.tolist()]
        binary_array = np.array(binary_list, dtype=np.int32)

        return binary_array

    def handle_nmea_list(self, msg):
        # Decode to msg
        nmea_list = pmt.to_python(msg)
        if type(nmea_list) != list:
            return

        try:
            decoded_msg = decode(*nmea_list)
        except Exception as e:
            print(e)
            return

        # Encode as bit array
        msg_np = self.pyais_msg_to_bitarray(decoded_msg)

        # Build message and publish
        metadata = pmt.dict_add(pmt.make_dict(), pmt.intern("length"), pmt.from_long(len(msg_np)))
        msg_pdu = pmt.cons(metadata, pmt.init_u8vector(len(msg_np), msg_np.tolist()))
        self.message_port_pub(pmt.intern('nmea_bits'), msg_pdu)

    def handle_nmea_bytes(self, msg):
        # Decode to msg (from gr-pyais_json)
        PMT_msg = pmt.to_python(msg)
        byte_array_msg = array('B', PMT_msg[1])
        byte_msg = bytes(byte_array_msg)
        decoded_msg = decode(byte_msg)

        # Encode as bit array
        msg_np = self.pyais_msg_to_bitarray(decoded_msg)

        # Build message and publish
        metadata = pmt.dict_add(pmt.make_dict(), pmt.intern("length"), pmt.from_long(len(msg_np)))
        msg_pdu = pmt.cons(metadata, pmt.init_u8vector(len(msg_np), msg_np.tolist()))
        self.message_port_pub(pmt.intern('nmea_bits'), msg_pdu)

