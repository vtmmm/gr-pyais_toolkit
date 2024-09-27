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
import xml.etree.ElementTree as ET
from random import shuffle
from threading import Thread
from time import sleep

class strobe_kml_polygons(gr.sync_block):
    """
    Load a KML and emit a vector of latlons containing one point from each polygon at a time.

    Lat offset and Lon offset will be applied to the coordinates found in the KML.

    Repeat points: This causes each point in the polygon to be emitted that number of times.

    TODO:
    - The latlon input port can be used to set the offsets.

    """
    def __init__(self, filename,interval=1,initial_delay=0.0,repeat_points=5,random_order='False', lat_offset=0.0, lon_offset=0.0):
        gr.sync_block.__init__(self,
            name="strobe_kml_polygons",
            in_sig=None,
            out_sig=None)

        # Store variables
        self.filename = filename
        self.interval = interval
        self.initial_delay = initial_delay
        self.repeat_points = repeat_points
        self.random_order = random_order
        self.lat_offset = lat_offset
        self.lon_offset = lon_offset
        self.polygons = None
        self.pmt_vector = None

        # Message ports
        self.message_port_register_in(pmt.intern('set_params'))
        self.message_port_register_out(pmt.intern('latlon_vec'))

        # Message port callbacks
        self.set_msg_handler(pmt.intern('set_params'), self.handle_set_params)

        # Load KML and configure PMT messages
        self.load_kml_polygons()

        # Thread for strobing
        self.strobe_thread = Thread(target=self._strobe)
        self.strobe_thread.daemon = True
        self.strobe_thread.start()

    def load_kml_polygons(self):
        # This function will load all the polygon data, but not define the PMT messages

        try:
            tree = ET.parse(self.filename)
            root = tree.getroot()
        except Exception as e:
            print("Could not load KML file.")
            print(e)

        namespaces = {'kml': 'http://www.opengis.net/kml/2.2'}

        polygons = []

        # Iterate through all polygons in KML; store list of polygons, each with list of points
        for polygon in root.findall(".//kml:Polygon", namespaces):
            coordinates = polygon.find(".//kml:coordinates", namespaces)
            if coordinates is not None:
                coords_text = coordinates.text.strip()
                # Omitting altitude
                coord_pairs = [
                    (float(lat)+self.lat_offset, float(lon)+self.lon_offset)
                    for lon, lat, *_ in (coord.split(',')[:2] for coord in coords_text.split())
                    ]
                polygons.append(coord_pairs)
        
        if self.random_order == 'True':
            shuffle(polygons)
        self.polygons = polygons
        #print(f"polygons:")
        #print(self.polygons)
        longest_length = len(max(polygons, key=len))
        print(f"Longest polygone is {longest_length} points. Requires {self.interval*longest_length + self.initial_delay}s to complete.")

        return

    def _strobe(self):
        # Sleep for initial delay
        sleep(self.initial_delay)

        index = 0
        # Since polygons are not all the same length, we recreate the PMT vector each time
        while True:
            if self.polygons is not None:
                pmt_vector = pmt.make_vector(len(self.polygons), pmt.PMT_NIL)

                for i, polygon_coords in enumerate(self.polygons):
                    # Store coordinate as tuple
                    coord = polygon_coords[index % len(polygon_coords)]
                    # Store latlon in dictionary
                    lat_dict = pmt.dict_add( pmt.make_dict(), pmt.intern("lat"), pmt.from_float(coord[0]))
                    latlon_dict = pmt.dict_add(lat_dict, pmt.intern("lon"), pmt.from_float(coord[1]))
                    # Add latlon dictionary to vector
                    pmt.vector_set(pmt_vector, i, latlon_dict)
                index += 1
                for _ in range(self.repeat_points):
                    self.message_port_pub(pmt.intern('latlon_vec'), pmt.cons(pmt.make_dict(), pmt_vector))
            sleep(self.interval)

    def start(self):
        return super().start()

    def stop(self):
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

