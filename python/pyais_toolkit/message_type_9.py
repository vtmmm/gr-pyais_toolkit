#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

class message_type_9(gr.sync_block):
    """
    SAR Aircraft Position Report
    """
    def __init__(self, mmsi):
        gr.sync_block.__init__(self,
            name="message_type_9",
            in_sig=None,
            out_sig=None)

