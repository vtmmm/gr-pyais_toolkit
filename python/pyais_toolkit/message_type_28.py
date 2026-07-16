#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

import pmt
try:
    from pyais.messages import MessageType28
except ImportError as e:
    raise ImportError(
        "Message Type 28 support requires pyais >= 2.20.0 "
        "(MessageType28 was introduced in pyais v2.20.0)") from e
from pyais.encode import encode_msg

class message_type_28(gr.sync_block):
    """
    Message 28: Aid-to-Navigation Report (Single-slot message)

    Defined in ITU-R M.1371-6 (Table 84). Provides similar information
    as Message 21, but in one slot instead of two, and can report
    MAtoN direction and speed or extended information on the AtoN.

    Requires pyais v2.20.0 or later (MessageType28 implementation).
    \n
    Any message to the latlon port sets the AtoN position and triggers
    generation of a new NMEA message.
    \n
    Field notes (see Table 84 for full definitions):
    - Station Type: 0=physical floating, 1=physical fixed, 2=synthetic
      predicted, 3=synthetic monitored, 4=virtual, 5=mobile
    - Aid Type: 0=not available, 1-31 per Message 21 Table 72,
      32+ per Table 85 (e.g. 39=navigation hazard)
    - Dimension Type: defines what Dimensions A and B represent
      (e.g. 1=height/structural area, 2=swing circle, 3=mobile AtoN
      vector where A=COG and B=SOG, 4=area-polygon, ...)
    - Second: UTC second of report; 60=not available (default)
    - On-station Status: 0=on-station ... 9=unmarked navigation
      hazard, 10=unmarked obstruction
    """
    def __init__(self,
            mmsi='993381000',
            latitude=0.0,
            longitude=0.0,
            station_type=0,
            aid_type=0,
            iala_mrn=0,
            restricted=0,
            dimension=0,
            dimensions_a=0,
            dimensions_b=0,
            dimension_additional_data=0,
            charted_status=0,
            station_status=0,
            status_bits=0,
            auth=0,
            second=60,
            repeat=0
            ):
        gr.sync_block.__init__(self,
            name="message_type_28",
            in_sig=None,
            out_sig=None)

        # Message ports
        self.message_port_register_in(pmt.intern('latlon'))
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('latlon'), self.handle_latlon)
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Initialize message
        self.msg28 = MessageType28.create(
                mmsi=mmsi,
                lat=latitude,
                lon=longitude,
                station_type=station_type,
                aid_type=aid_type,
                iala_mrn=iala_mrn,
                restricted=restricted,
                dimension=dimension,
                dimensions_a=dimensions_a,
                dimensions_b=dimensions_b,
                dimension_additional_data=dimension_additional_data,
                charted_status=charted_status,
                station_status=station_status,
                status_bits=status_bits,
                auth=auth,
                second=second,
                repeat=repeat)

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self.msg28, key):
                setattr(self.msg28, key, value)

        return

    def handle_latlon(self, msg):
        """
        Sets the AtoN latlon and publishes list of encoded NMEA strings.
        """
        # Update latlon
        lat = pmt.cdr(pmt.car(pmt.cdar(msg)))
        lon = pmt.cdr(pmt.caar(msg))
        self.msg28.lat = pmt.to_float(lat)
        self.msg28.lon = pmt.to_float(lon)

        # Create and publish NMEA message
        nmea_list = pmt.to_pmt(encode_msg(self.msg28, talker_id='AIVDM'))
        self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        return
