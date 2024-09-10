#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
import pmt
from gnuradio import gr

from pyais.messages import MessageType6
from pyais.encode import encode_msg


class message_type_6(gr.sync_block):
    """
    Sample input on latlon to generate message:
    latlon: (((lat . 30)(lon . -100)))
    
    Sample input on mmsi to generate message:
    ((mmsi . 338123456))

    Sample input on set_params to set message parameters (does not generate NMEA message):
    $(TODO....)
    
    Sample Output:
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    # TODO: Use correct message type
    
    Inputs to the message ports may be from:
    - LatLon Strobe
    """
    def __init__(self, 
            mmsi='338123456',
            dest_mmsi='338654321',
            data=b'hello',
            dac=0,
            fid=0,
            retransmit=False,
            seqno=0
            ):

        gr.sync_block.__init__(self,
                name="AIS Generator: Message Type 6",
            in_sig=None,
            out_sig=None)

        # Can probably skip this since they're stored in the pyais message: self.msgX
        self.mmsi = mmsi
        self.dest_mmsi = dest_mmsi
        self.data = data
        self.dac = dac
        self.fid = fid
        self.retransmit = retransmit
        self.seqno = seqno

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Initialize message
        self.msg6 = MessageType6.create(mmsi=mmsi, dest_mmsi=dest_mmsi, data=data, dac=dac, fid=fid, retransmit=retransmit, seqno=seqno) 

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self.msg6, key):
                setattr(self.msg6, key, value)

        return

    def handle_latlon(self, msg):
        """
        Publishes list of encoded NMEA strings based on existing parameters.
        """
        nmea_list = pmt.to_pmt(encode_msg(self.msg6, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

