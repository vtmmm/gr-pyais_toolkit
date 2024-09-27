# Background

The goal of these blocks is to make it easier to experiment with `pyais` in a modular fashion within GNU Radio.

Warning: this is not in a 'finished' state, so some things may not work.

# Requirements

* GNU Radio `3.10.11.0` or later
* `pyais` version `2.7.0`
* `gr-ais_simulator` from https://github.com/mictronics/ais-simulator

GNU Radio `3.10.11.0` or later is required for flowgraphs that make use of the `Burst to Stream` block for generating continuous IQ files containing AIS bursts. If you only need the bursts, you can use an earlier version.

`gr-ais_simulator` is only necessary if you want to generate IQ. If you only want to experiment with NMEA messages, it is not necessary.

Other versions of `pyais` have not been tested.

# Types of Blocks

## Message Filters

These blocks ingest/output NMEA sentences, but only pass those that meet specific criteria.

## Message Generators

These blocks generate one or more NMEA sentences in a list. Messages are generated each time they receive something like a `latlon` message.

See individual block documentation for more details.

## Strobes

These blocks output messages at a regular interval, and are typically connected to a Message Generator.
 
## Utilities

These blocks perform a variety of functions, such as:
- Grabbing specific data fields from a message
- Converting message formats
- Sending data to or receiving data from outside GNU Radio

# Message formats used by blocks

This OOT Module is mostly made up of blocks that pass around PDUs. This section explains what these are and when/how they are used.

## latlon

A PDU (a pmt.cons containing metadata as the 'car' and data as the 'cdr') where the metadata is a dictonary of key/value pairs: one each for `lat` and `lon`. When it prints out, it looks like:

`(((lon . -100)(lat . 30)))`

These are generated by some Strobe blocks. Check `latlon_strobe.grc` in `apps/` to see an example of how they could be crafted within GNU Radio.

These are accepted by a variety of blocks to set the latlon of the message(s) (if applicable) and trigger generation of new NMEA messages.

## latlon_vec

This message is a vector of latlon pairs, and is used for generating many position reports at once.

At this time, support has only been added for and tested with Message Type 1.

## mmsi

A PDU where the metadata is a dictionary containing one key/value pair: a key of 'mmsi' and a value containing a nine digit string.

`(((mmsi . 336123456)))`

These are accepted by a variety of blocks to set the MMSI and trigger generation of new NMEA messages.

## set_params

A PDU where the metadata is a dictionary of key/value pairs, where the keys match relevant pyais message data fields.

`(((course . 30)(heading . 45)))`

These messages are produced by **Get Params** in case you want to set values of one message based on another.

If a Message Generator receives this message and the keys match parameters used to generate messages, the values will be used for new NMEA messages.

When a block receives this message, it only stores the values; it does not trigger new NMEA messages.

The `Hex to Bytes` block's `dict` input also supports this type of message.

## nmea_list

A Python or PMT list of NMEA encoded strings. Example PMT:

`#(!AIVDO,3,1,0,A,81mg:2000000000000000000000000000000000000000000000000000000,0*1D !AIVDO,3,2,0,A,000000000000000000000000000000000000000000000000000000000000,0*15 !AIVDO,3,3,0,A,000000000000000000000000000000000000000000000000,0*14)`

The above is equivalent to a Python list:

`['!AIVDO,3,1,0,A,81mg:2000000000000000000000000000000000000000000000000000000,0*1D',
 '!AIVDO,3,2,0,A,000000000000000000000000000000000000000000000000000000000000,0*15',
 '!AIVDO,3,3,0,A,000000000000000000000000000000000000000000000000,0*14']`

Lists are used instead of individual strings in order to support multi-part messages.

## nmea_bytes

These are used to interface with `gr-ais` and `gr-pyais_json`.

It can be used with:

- NMEA Bytes to Strings
- NMEA Strings to Bytes
- NMEA to AIS Simulator (bits)

# Thanks: 
- pyais developers/maintainers for an incredible Python module
- Nick Foster and bkerler for gr-ais and its GR 3.10 support
- Mictronics for ais-simulator and gr-ais_simulator
- muaddib1984 for gr-pyais_json
- GNU Radio community

# TODO:
- "max strobes" parameter for strobe blocks, so they stop emitting after a configurable number of messages
- Strobe KML Polygons: print length of longest polygon, and time to complete based on interval
- Improve per-block documentation and its formatting
- Add Message Generator blocks for more message types
- Add support for latlon_vec to more Message Generators
