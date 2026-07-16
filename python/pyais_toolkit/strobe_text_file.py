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
from threading import Thread, Event
import binascii
from pyais import decode
from pyais.encode import encode_msg

class strobe_text_file(gr.sync_block):
    """
    Load a text file where each line is an AIS message.

    If each line starts with '0x' it will read it as hex. Otherwise it will read it as ASCII.

    Consecutive lines that are fragments of the same multipart message
    are grouped together and decoded as one message.

    Each message is sent with interval time between them.
    """
    def __init__(self, filename,interval=1,initial_delay=0.0,repeat_each=1,repeat_all=False):
        gr.sync_block.__init__(self,
            name="strobe_text_file",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.filename = filename
        self.interval = interval
        self.initial_delay = initial_delay
        self.repeat_each = repeat_each
        self.repeat_all = repeat_all

        # Message ports
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('nmea_list'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Load txt file and build message array
        self.messages = []
        self.load_text_file()

        # Thread for strobing (started from start(), so nothing is
        # published before the flowgraph is connected and running)
        self._stop_event = Event()
        self.strobe_thread = None

    @staticmethod
    def _sentence_counts(sentence):
        """
        Returns (fragment_number, fragment_total) for an NMEA sentence.
        Falls back to (1, 1) if the fields cannot be parsed.
        """
        fields = sentence.split(',')
        try:
            return int(fields[2]), int(fields[1])
        except (IndexError, ValueError):
            return 1, 1

    def load_text_file(self):
        """
        Loads the text file
        """
        pending = []
        with open(self.filename, "r") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                if line[:2].lower() == '0x':
                    hex_str = line[2:]
                    try:
                        line = binascii.unhexlify(hex_str).decode("ascii", errors="ignore")
                    except Exception as e:
                        print(f"strobe_text_file: line {line_num}: {e}")
                        continue
                pending.append(line)
                num, total = self._sentence_counts(line)
                if num >= total:
                    self.messages.append(tuple(pending))
                    pending = []
        if pending:
            print(f"strobe_text_file: dropped {len(pending)} trailing sentence(s) of an incomplete multipart message")
        if not self.messages:
            print(f"strobe_text_file: no messages loaded from {self.filename}")
        print(f"Loaded {len(self.messages)} messages. Requires {len(self.messages)*self.interval} seconds.")

    def _strobe(self):
        if self._stop_event.wait(self.initial_delay):
            return

        while not self._stop_event.is_set():
            published = self._publish_all()
            if not self.repeat_all:
                return
            if published == 0:
                print("strobe_text_file: no messages could be sent, stopping strobe")
                return

    def _publish_all(self):
        """
        Publishes every loaded message once (repeated repeat_each times),
        waiting interval seconds between messages. Returns the number of
        messages published.
        """
        published = 0
        for sentences in self.messages:
            if self._stop_event.is_set():
                break
            try:
                nmea_list = pmt.to_pmt(encode_msg(decode(*sentences), talker_id='AIVDM'))
            except Exception as e:
                print(f"strobe_text_file: skipping message {sentences}: {e}")
                continue
            for i in range(self.repeat_each):
                self.message_port_pub(pmt.intern('nmea_list'), nmea_list)
            published += 1
            if self._stop_event.wait(self.interval):
                break
        return published

    def start(self):
        self._stop_event.clear()
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()
        return super().start()

    def stop(self):
        self._stop_event.set()
        if self.strobe_thread is not None:
            self.strobe_thread.join(timeout=2.0)
        return super().stop()

    def handle_set_params(self, msg):
        """
        Accepts a list of key value pairs, and sets the message fields accordingly.
        """
        params_dict = pmt.to_python(pmt.car(msg))

        if type(params_dict) != dict:
            return

        for key, value in params_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)

        return

