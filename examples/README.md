`msg1_example.grc` uses `Strobe latlon (Moving)` and `Message Type 1 (Class A position report)` blocks to generate NMEA that simulates a moving vessel. These messages are converted to bits compatible with the transmit flowgraph provided by `Mictronics/ais-simulator` (except it passes messages via ZMQ instead of websocket).

`ais-simulator_to_burst_file.grc` accepts these messages via ZMQ, generates IQ data, and writes the bursts to a file.

`ais-simulator_to_continuous_file.grc` also accepts the messages via ZMQ and generates IQ, but it adds the bursts to continuous noise before writing to file. This functionality requires `Burst to Stream`, which is in GNU Radio 3.10.11.0+.

`msg28_to_continuous_file.grc` is a self-contained flowgraph (no ZMQ pair needed) that simulates three aids-to-navigation broadcasting Message 28: a virtual AtoN marking a navigation hazard, a charted physical buoy with a swing circle, and a mobile AtoN whose strobed position moves to match its reported COG/SOG vector. The bursts are GMSK modulated and added to continuous noise before being written to an IQ file. Requires `pyais` 2.20.0+, `gr-ais_simulator`, and GNU Radio 3.10.11.0+ (`Burst to Stream`).
