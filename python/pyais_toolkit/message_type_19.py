#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


from gnuradio import gr

import random
import string
import pmt
from pyais.messages import MessageType19
from pyais.encode import encode_msg

class message_type_19(gr.sync_block):
    """
    Extended Class B Equipment Position Report
\n
    Sample input on latlon to generate message:
    latlon: (((lat . 30)(lon . -100)))
\n
    Sample input on mmsi to generate message:
    ((mmsi . 338123456))
\n
    Sample input on set_params to set message parameters (does not generate NMEA message):
    $(TODO....)
\n
    Sample Output:
    #(!AIVDO,1,1,,A,11mg=5@P00Hrl60BpOh000000000,0*43)
    
    """
    def __init__(self, mmsi='336123123',accuracy=0,assigned=0,course=0,dte=0,epfd=0,heading=0,lat=0,lon=0,raim=0,repeat=0,reserved_1=0,reserved_2=0,second=0,ship_type=0,shipname='',spare_1=b'',speed=0,to_bow=0,to_port=0,to_stern=0,to_starboard=0, max_num_transmissions=None):
        gr.sync_block.__init__(self,
            name="message_type_19",
            in_sig=None,
            out_sig=None)

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

        # Variables in case of latlon_vec
        self.mmsi_list = None
        self.msg19_vec = None

        # Variables in case of max_num_transmissions
        self.max_num_transmissions = None
        self.num_transmissions = 0

        # Initialize message
        self.msg19 = MessageType19.create(
                mmsi=mmsi,
                course=course,
                heading=heading,
                lat=lat,
                lon=lon,
                speed=speed,
                ship_type=ship_type,
                shipname=shipname,
                accuracy=accuracy,
                dte=dte,
                assigned=assigned,
                epfd=epfd,
                raim=raim,
                repeat=repeat,
                reserved_1=reserved_1,
                reserved_2=reserved_2,
                spare_1=spare_1,
                second=second,
                to_port=to_port,
                to_starboard=to_starboard,
                to_stern=to_stern,
                to_bow=to_bow
                ) 

    def handle_mmsi(self, msg):
        """
        Generates message based on current latlon. TODO: Make it set the mmsi as well.
        """
        # TODO: determine message format and actually set MMSI. Then copy to all relevant blocks

        nmea_list = pmt.to_pmt(encode_msg(self.msg19, talker_id='AIVDM'))
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
            if hasattr(self.msg19, key):
                setattr(self.msg19, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the MSG19 latlon and publishes list of encoded NMEA strings.
        """
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.msg19.lat = pmt.to_float(lat)
        self.msg19.lon = pmt.to_float(lon)
        nmea_list = pmt.to_pmt(encode_msg(self.msg19, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

    def handle_latlon_vec(self, msg):

        pmt_vector = pmt.cdr(msg)
        self.num_contacts = pmt.length(pmt_vector)

        if not self.mmsi_list:
            self.initialize_mmsi_list()

        if len(self.mmsi_list)!=self.num_contacts:
            self.initialize_mmsi_list()

        if not self.msg19_vec:
            self.msg19_vec = MessageType19.create(
                    mmsi='000000000',
                    course=self.msg19.course,
                    heading=self.msg19.heading,
                    speed=self.msg19.speed,
                    shipname=self.msg19.shipname,
                    ship_type=self.msg19.ship_type)

        for i in range(self.num_contacts):
            latlon_dict = pmt.vector_ref(pmt_vector, i)
            self.msg19_vec.lon = pmt.to_float(pmt.cdar(latlon_dict))
            self.msg19_vec.lat = pmt.to_float(pmt.cdr(pmt.cadr(latlon_dict)))
            self.msg19_vec.mmsi = self.mmsi_list[i]

            nmea_list = pmt.to_pmt(encode_msg(self.msg19_vec, talker_id='AIVDM'))
            self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return

    def initialize_mmsi_list(self):
        self.mmsi_list = []
        mid_usa = ['338', '366', '367', '368', '369']
        for i in range(self.num_contacts):
            mid = random.choice(mid_usa)
            self.mmsi_list.append(mid + ''.join(random.choices(string.digits, k=6)))
        return


