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

class hex_to_bytes(gr.sync_block):
    """
    Accepts a PMT dictionary.
    \n
    Grabs the value associated with the specified key.
    \n
    Attempts to convert from hex to bytes.
    \n
    Publishes the resulting bytes.
    \n
    Example: 
    MSG 8 (Binary Broadcast Message) > Get Params with ['data'] > Hex to Bytes

    """
    def __init__(self, data_key='data'):
        gr.sync_block.__init__(self,
            name="hex_to_bytes",
            in_sig=None,
            out_sig=None)

        self.data_key = data_key

        # Message ports
        self.message_port_register_in(pmt.intern('dict'))
        self.message_port_register_out(pmt.intern('bytes'))


        # Message port callbacks
        self.set_msg_handler(pmt.intern('dict'), self.handle_dict)

    def handle_dict(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        try:
            my_dict = pmt.to_python(pmt.car(msg))
        except Exception as e:
            print(f"Couldn't parse: {msg}")
            print(e)
            return


        if type(my_dict) is not dict:
            print(f"Not a dictionary. Received a {type(my_dict)}: {my_dict}")
            return

        for key, value in my_dict.items():
            if key == self.data_key:
                try:
                    my_bytes = bytes.fromhex(value)
                except Exception as e:
                    print("Couldn't decode from hex:")
                    print(f"key: {key}")
                    print(f"value: {value}")
                    print(f"Key is of type {type(key)} and value is of type {type(value)}")
                    print(e)
                    continue
                try:
                    pmt_array = pmt.init_u8vector(len(my_bytes), list(my_bytes))
                except Exception as e:
                    print("FAILED TO CONVERT TO PMT ARRAY")
                    print(e)
                    continue
                try:
                    self.message_port_pub(pmt.intern('bytes'), pmt.cons(pmt.PMT_NIL, pmt_array))
                except Exception as e:
                    print("COULDNT PUBLISH")
                    print(e)
                    continue
        return



