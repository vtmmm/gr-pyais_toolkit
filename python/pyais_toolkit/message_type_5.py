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

from pyais.messages import MessageType5
from pyais.encode import encode_msg

class message_type_5(gr.sync_block):
    """
    Sample Input:
    (((lat . 30)(lon . -100)))
    or
    ((mmsi . 338123456))
    TODO: VERIFY/implement
    
    Sample Output:
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    TODO: Use an actual MSG5 NMEA string
    
    Input may be:
     - from LatLon Strobe block to the latlon message port
     - from MMSI Strobe block to the mmsi mesage port

    Latitude and longitude is not used by this block, but it
    accepts a latlon message to trigger a NMEA message for
    sake of convenience.
    """
    def __init__(self,
            mmsi='338123456',
            callsign='',
            destination='',
            imo=0,
            shipname='',
            ship_type=0
            ):
            #day=0,
            #draught=0,
            #dte=0,
            #epfd=0,
            #others......

        gr.sync_block.__init__(self,
                name="AIS Generator: Message Type 5",
            in_sig=None,
            out_sig=None)
        self.mmsi = mmsi
        self.callsign = callsign
        self.destination = destination 
        self.imo = imo
        self.shipname = shipname
        self.ship_type = ship_type

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
        self.msg5 = MessageType5.create(mmsi=mmsi, callsign=callsign, destination=destination, imo=imo, shipname=shipname, ship_type=ship_type) 

    def handle_mmsi(self, msg):
        """
        Set the MMSI and generate the message
        """
        # TODO: Determine this format and implement setting the MMSI
        nmea_list = pmt.to_pmt(encode_msg(self.msg5, talker_id='AIVDM'))
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
            if hasattr(self.msg5, key):
                setattr(self.msg5, key, value)

        return

    def handle_latlon(self, msg):
        """
        Generate message even though the latlon isn't actually used
        Unsure if this should pass the latlon message through to output.
        Unsure if this should validate for properly formatted latlon.
        """
        # Not setting anything since presumably only a latlon message was sent
        nmea_list = pmt.to_pmt(encode_msg(self.msg5))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return
        
