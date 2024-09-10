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

from pyais.messages import MessageType1
from pyais.encode import encode_msg
import random
import string

class message_type_1(gr.sync_block):
    """
    Position Reports

    Sample input on latlon to generate message:
    latlon: (((lat . 30)(lon . -100)))
    
    Sample input on mmsi to generate message:
    ((mmsi . 338123456))

    Sample input on set_params to set message parameters (does not generate NMEA message):
    $(TODO....)
    
    Sample Output:
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    
    Inputs to the message ports may be from:
    - LatLon Strobe block
    - MMSI Strobe block
    - Set Params GUI block
    """
    def __init__(self,
            mmsi='338123456',
            course=0,
            heading=0,
            latitude=0.0,
            longitude=0.0,
            speed=0
            ):
            #accuracy=0,
            #is_itdma=False,
            #is_sotdma=True,
            #lat=0,
            #lon=0,
            #maneuver=0,
            #msg_type=1,
            #radio=0,
            #raim=0,
            #repeat=0,
            #second=0,
            #spare_1
            #status (ENUM)
            #turn (ENUM)

        gr.sync_block.__init__(self,
                name="AIS Generator: Message Type 1",
            in_sig=None,
            out_sig=None)

        # Variables in case of latlon_vec
        self.mmsi_list = None

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('latlon_vec'))
        self.message_port_register_in(pmt.intern('mmsi'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('latlon_vec'), self.handle_latlon_vec)
        self.set_msg_handler(pmt.intern('mmsi'), self.handle_mmsi)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Initialize message
        self.msg1 = MessageType1.create(mmsi=mmsi, course=course, heading=heading, lat=latitude, lon=longitude, speed=speed) 
        self.msg1_vec = None

    def handle_mmsi(self, msg):
        """
        Generates message based on current latlon. TODO: Make it set the mmsi as well.
        """
        # TODO: determine message format and actually set MMSI. Then copy to all relevant blocks

        nmea_list = pmt.to_pmt(encode_msg(self.msg1, talker_id='AVIDM'))
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
            if hasattr(self.msg1, key):
                setattr(self.msg1, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG1 latlon and publishes list of encoded NMEA strings.
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.msg1.lat = pmt.to_float(lat)
        self.msg1.lon = pmt.to_float(lon)

        # Create and publish NMEA message
        nmea_list = pmt.to_pmt(encode_msg(self.msg1, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

    def handle_latlon_vec(self, msg):

        pmt_vector = pmt.cdr(msg)
        self.num_contacts = pmt.length(pmt_vector)

        if not self.mmsi_list:
            self.initialize_mmsi_list()

        if len(self.mmsi_list)!=self.num_contacts:
            self.initialize_mmsi_list()

        if not self.msg1_vec:
            self.msg1_vec = MessageType1.create(
                    mmsi='000000000',
                    course=self.msg1.course,
                    heading=self.msg1.heading,
                    speed=self.msg1.speed)

        for i in range(self.num_contacts):
            latlon_dict = pmt.vector_ref(pmt_vector, i)
            self.msg1_vec.lon = pmt.to_float(pmt.cdar(latlon_dict))
            self.msg1_vec.lat = pmt.to_float(pmt.cdr(pmt.cadr(latlon_dict)))
            self.msg1_vec.mmsi = self.mmsi_list[i]

            nmea_list = pmt.to_pmt(encode_msg(self.msg1_vec, talker_id='AIVDM'))
            self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

    def initialize_mmsi_list(self):
        self.mmsi_list = []
        mid_usa = ['338', '366', '367', '368', '369']
        for i in range(self.num_contacts):
            mid = random.choice(mid_usa)
            self.mmsi_list.append(mid + ''.join(random.choices(string.digits, k=6)))
        return


