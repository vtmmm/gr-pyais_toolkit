#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2024 michael morrison.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


from gnuradio import gr

import pmt
import threading
from pyais.decode import decode
from pyais.encode import encode_msg
from pyais.stream import TCPConnection

class pyais_tcp_connection_stream(gr.sync_block):
    """
    - Uses pyais.stream's TCPConnection
    - See the pyais 'live_stream.py' example

    """
    def __init__(self, ip='localhost',port=5631):
        gr.sync_block.__init__(self,
            name="pyais_tcp_connection_stream",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.ip = ip
        self.port = port

        # Message ports
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Start message receiving in a separate thread
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self.receive_messages)
        self._thread.start()

        self.receive_messages()

    def receive_messages(self):
        msg_count = 0
        try:
            for msg in TCPConnection(self.ip, port=self.port):
                if self._stop_event.is_set():
                    break
                msg_count += 1
                nmea_list = pmt.to_pmt(encode_msg(msg.decode(), talker_id='AIVDM'))
                self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
        except Exception as e:
            print(f"Error receiving messages: {e}")

    def stop(self):
        self._stop_event.set()
        self._thread.join()

    def __del__(self):
        self.stop()

