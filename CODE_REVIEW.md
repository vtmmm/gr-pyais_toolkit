# Code Review: uncommitted changes (2026-07-15)

Scope: working-tree diff on `main`. New Strobe Text File block (`strobe_text_file.py` plus GRC yml and build registration), the `sleep(0.005)` added to `message_type_1.py`, and the try/except added to `nmea_to_nmea_bits.py`.

## High severity

### 1. One bad or multipart line silently kills the strobe thread
`python/pyais_toolkit/strobe_text_file.py:82` and `:90` call `decode(message)` with no exception handling, inside a daemon thread. Any malformed line, or any single fragment of a multipart sentence (verified: pyais raises `MissingMultipartMessageException` for each fragment of a two-part type 5 message), raises in the thread and ends it. All remaining messages are never sent and nothing is reported to the user. Wrap the decode in try/except (log and skip the line), and either assemble multipart fragments or document that the file must contain single-part sentences.

### 2. Strobe thread starts in `__init__`, before the flowgraph is running
`python/pyais_toolkit/strobe_text_file.py:54-56` starts the worker at construction time. With `initial_delay=0` the first messages are published before GRC has connected the message ports and started the top block, so they are dropped. Start the thread from `start()` instead of `__init__`.

### 3. `repeat_all` thread can never be stopped
`python/pyais_toolkit/strobe_text_file.py:88` is `while True:` with no exit condition, and `stop()` at line 97 neither signals nor joins the thread. Stopping and restarting a flowgraph in the same process leaves the old thread publishing. Use a `threading.Event`, wait on it instead of `sleep()`, set it in `stop()`, and join the thread.

## Medium severity

### 4. Multipart AIS messages dropped on the `nmea_bytes` path
`python/pyais_toolkit/nmea_strings_to_bytes.py:43` publishes each sentence of a multipart message as a separate PDU, and `python/pyais_toolkit/nmea_to_nmea_bits.py:90` decodes each PDU independently. Each fragment raises `MissingMultipartMessageException`, which the newly added except block swallows, so multipart messages (type 5 and others) never produce bits. The handler carries a `TODO: Not working` comment, so this is known, but the fix is to buffer fragments and decode once complete. Note the `nmea_list` path already handles this correctly via `decode(*nmea_list)` at `nmea_to_nmea_bits.py:67`.

### 5. Empty file plus `repeat_all=True` busy-spins a CPU core
If `self.messages` is empty, the loop at `strobe_text_file.py:88` contains no sleep at all. Reject empty files at load time or sleep outside the inner for loop.

### 6. `repeat_each` only applies to the first pass, and defaults disagree
The initial pass (`strobe_text_file.py:83`) publishes each message `repeat_each` times, but the `repeat_all` loop (`strobe_text_file.py:89-92`) publishes each once. Factor the publish-one-cycle logic into a helper used by both. Also, the Python default is `repeat_each=5` while the GRC yml default is `1`; make them match.

### 7. `sleep(0.005)` blocks the message handler in message_type_1
`python/pyais_toolkit/message_type_1.py:154` sleeps 5 ms per contact inside `handle_latlon_vec`. A 1000-contact vector holds the handler for 5 seconds, delaying every queued message. If pacing is needed downstream, make it configurable and move it out of the callback.

## Low severity / cleanups

- `handle_set_params` (`strobe_text_file.py:109-111`) sets any existing attribute, including `messages`, `strobe_thread`, and `filename`. Restrict to an explicit whitelist of tunable parameters.
- Unused imports in `strobe_text_file.py`: `numpy`, `shuffle`. The `start()`/`stop()` overrides that only call `super()` are dead code (until finding 2/3 fixes give them a body).
- Hex detection `'0x' in line[:2]` does not accept an uppercase `0X` prefix; use `line.lower().startswith('0x')`.
- The load-time estimate at `strobe_text_file.py:76` ignores `repeat_each` and `initial_delay`.
- `print()` is used for errors and status throughout; prefer the GNU Radio logger (`self.logger`).
- No input validation for `filename`, `interval`, or `repeat_each` (negative or zero values are accepted silently).
- No tests exist for the new block (start timing, shutdown, empty file, repeat counts, hex input, multipart handling).

## Build / registration
CMake and `__init__.py` registration of the new block is complete and consistent (grc/CMakeLists.txt, python/pyais_toolkit/CMakeLists.txt, `__init__.py`).
