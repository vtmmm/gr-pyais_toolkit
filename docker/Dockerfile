# gr-pyais_toolkit in a clean, self-contained environment.
#
# Ubuntu 26.04 (resolute) ships GNU Radio 3.10.12.0, which satisfies the
# 3.10.11.0+ requirement for the Burst to Stream block, so GNU Radio is
# installed straight from the distro with no source build.
#
# This image includes:
#   - GNU Radio + build toolchain
#   - pyais (pinned to 2.x) and geopy
#   - gr-ais_simulator (patched, needed to modulate AIS bursts to IQ)
#   - gr-pyais_toolkit (this module), built and installed
#
# It does NOT include the receive/demod side (gr-ais, gr-pyais_json) or
# any SDR hardware drivers; the intended use is headless IQ synthesis.
FROM ubuntu:26.04

ENV DEBIAN_FRONTEND=noninteractive

# GNU Radio, the OOT build toolchain, and Boost (for ais_simulator's
# Boost.Beast websocket block).
RUN apt-get update && apt-get install -y --no-install-recommends \
        gnuradio \
        gnuradio-dev \
        cmake \
        g++ \
        git \
        make \
        pkg-config \
        pybind11-dev \
        python3-dev \
        python3-numpy \
        python3-pip \
        libboost-dev \
    && rm -rf /var/lib/apt/lists/*

# pyais (pinned to the 2.x series; 2.20.0+ is required for Message Type 28)
# and geopy. Ubuntu 26.04 enforces PEP 668, so --break-system-packages is
# used deliberately inside this throwaway container.
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt

# Build and install the patched gr-ais_simulator.
#   - issue9:  output-length fix (Mictronics/ais-simulator#9)
#   - resolver: build against Boost >= 1.87 (Ubuntu 26.04)
COPY docker/patches/ais-simulator-issue9.patch docker/patches/ais-simulator-boost-resolver.patch /tmp/
RUN git clone --depth 1 https://github.com/Mictronics/ais-simulator /tmp/ais-simulator \
    && cd /tmp/ais-simulator \
    && git apply /tmp/ais-simulator-issue9.patch \
    && git apply /tmp/ais-simulator-boost-resolver.patch \
    && cmake -S gr-ais_simulator -B gr-ais_simulator/build \
    && cmake --build gr-ais_simulator/build -j"$(nproc)" \
    && cmake --install gr-ais_simulator/build \
    && ldconfig \
    && rm -rf /tmp/ais-simulator

# Build and install gr-pyais_toolkit itself. The repo is copied in last so
# edits to the module do not invalidate the (slow) layers above.
COPY . /src/gr-pyais_toolkit
RUN cmake -S /src/gr-pyais_toolkit -B /src/gr-pyais_toolkit/build \
    && cmake --build /src/gr-pyais_toolkit/build -j"$(nproc)" \
    && cmake --install /src/gr-pyais_toolkit/build \
    && ldconfig

# Render example flowgraphs to IQ. The entrypoint runs a flowgraph and
# leaves its output in /out (mount a host directory there to keep it).
WORKDIR /out
ENV NO_AT_BRIDGE=1
COPY docker/run-example.sh /usr/local/bin/run-example
RUN chmod +x /usr/local/bin/run-example
ENTRYPOINT ["/usr/local/bin/run-example"]
CMD ["msg28_to_continuous_file"]
