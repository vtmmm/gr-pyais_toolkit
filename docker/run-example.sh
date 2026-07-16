#!/usr/bin/env bash
#
# Render one of the repo's example flowgraphs to an IQ file.
#
# Usage (inside the container):
#   run-example [EXAMPLE_NAME]
#
# EXAMPLE_NAME is the basename of a .grc in examples/ (default:
# msg28_to_continuous_file). The flowgraph's file sink is redirected to
# /out/<name>.fc32, so mount a host directory at /out to keep the result:
#
#   docker run --rm -v "$PWD/out:/out" gr-pyais-toolkit
#
# The continuous-IQ example runs forever, so it is stopped after
# DURATION seconds (default 10). Override with -e DURATION=30.
set -euo pipefail

EXAMPLE="${1:-msg28_to_continuous_file}"
DURATION="${DURATION:-10}"
EXAMPLES_DIR=/src/gr-pyais_toolkit/examples
SRC="${EXAMPLES_DIR}/${EXAMPLE}.grc"
WORK="$(mktemp -d)"
OUT="/out/${EXAMPLE}.fc32"

if [[ ! -f "$SRC" ]]; then
    echo "No such example: ${EXAMPLE}" >&2
    echo "Available examples:" >&2
    for f in "${EXAMPLES_DIR}"/*.grc; do
        echo "  - $(basename "${f%.grc}")" >&2
    done
    exit 1
fi

if grep -q "generate_options: qt_gui" "$SRC"; then
    echo "'${EXAMPLE}' is a GUI flowgraph and cannot run headless in this container." >&2
    echo "Use a no_gui example such as msg28_to_continuous_file." >&2
    exit 1
fi

# Redirect the file sink to /out so the result survives the container.
sed "s#file: /tmp/[^[:space:]]*#file: ${OUT}#" "$SRC" > "${WORK}/${EXAMPLE}.grc"

echo "Compiling ${EXAMPLE}.grc ..."
grcc "${WORK}/${EXAMPLE}.grc" -o "${WORK}"

echo "Running for ${DURATION}s (writing ${OUT}) ..."
# The flowgraph runs until stopped; a clean SIGINT lets the file sink flush.
timeout --signal=INT "${DURATION}" python3 "${WORK}/${EXAMPLE}.py" || true

if [[ -f "$OUT" ]]; then
    printf 'Done. Wrote %s (%s bytes, complex float32 @ 1 Msps).\n' \
        "$OUT" "$(stat -c %s "$OUT")"
else
    echo "Flowgraph finished but no IQ file was produced at ${OUT}." >&2
    exit 1
fi
