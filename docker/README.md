# Docker environment

A clean, self-contained way to try `gr-pyais_toolkit` and synthesize AIS IQ
without installing GNU Radio or its dependencies on your host. If you already
have a working GNU Radio 3.10.11.0+ setup, you can ignore this directory.

The image is based on **Ubuntu 26.04**, which ships **GNU Radio 3.10.12.0**
from the distro (new enough for the `Burst to Stream` block), so nothing is
built from source except the two out-of-tree modules. It installs:

- GNU Radio and the build toolchain
- `pyais` (pinned to the 2.x series) and `geopy`
- `gr-ais_simulator` (patched, used to modulate AIS bursts to IQ)
- `gr-pyais_toolkit` (this module)

It deliberately leaves out the receive/demod side and SDR drivers; the intended
use is headless IQ synthesis.

## Build

From the repository root (the build context must be the root, not `docker/`):

```bash
docker build -f docker/Dockerfile -t gr-pyais-toolkit .
```

## Generate IQ

The default command renders `examples/msg28_to_continuous_file.grc` to an IQ
file. Mount a host directory at `/out` to keep the result:

```bash
mkdir -p out
docker run --rm -v "$PWD/out:/out" gr-pyais-toolkit
# -> out/msg28_to_continuous_file.fc32  (complex float32 @ 1 Msps)
```

Pick a different example (any no-GUI `.grc` basename from `examples/`) and
control how long the continuous flowgraph runs before it is stopped:

```bash
docker run --rm -e DURATION=30 -v "$PWD/out:/out" gr-pyais-toolkit ais-simulator_to_continuous_file
```

Run with no arguments and an unknown name to list the available examples:

```bash
docker run --rm gr-pyais-toolkit does-not-exist
```

The output `.fc32` is interleaved complex float32 at 1 Msps; the AIS bursts are
single-slot (~26.7 ms) and sit well above the added noise floor.

## Patches

`gr-ais_simulator` is cloned from upstream and patched at build time (see
`patches/`):

- `ais-simulator-issue9.patch` fixes the burst output length
  (Mictronics/ais-simulator#9).
- `ais-simulator-boost-resolver.patch` lets it build against Boost >= 1.87,
  which removed the deprecated asio `resolver::query`.
