# Maritimentro: Async/SoC Architecture

## 1. Core Philosophy: Separation of Concerns (SoC)
- **Math (`utils/entropy_tools.py`)**: Pure bitwise operations. Deterministic 64-bit mixing. No side effects.
- **State (`interface/state.py`)**: Thread-safe (async) centralized pool. Tracks telemetry and global seed.
- **Sensors (`harvesters/`)**: Isolated async workers. Responsibility is raw data extraction and RTT measurement.
- **Bridge (`interface/`)**: Non-blocking TUI using `Rich`. Consumes state, does not modify it.
- **Coordinator (`maritimentro.py`)**: The `asyncio` orchestrator. Manages the loop and worker staggered timing.

## 2. Async Execution Model
- **Network**: All HTTP/API calls must use `aiohttp.ClientSession`.
- **System**: External tools (`doggo`, `curl`) must use `asyncio.create_subprocess_exec`.
- **Timing**: Use `asyncio.sleep()` for staggered worker delays to prevent IO bursts.
- **Concurrency**: Harvesters run as independent `asyncio.create_task` or via a controlled worker pool.

## 3. Data Flow
1. **Harvester** triggers -> Measures latency -> Performs async IO.
2. **Harvester** returns standardized result to **Coordinator**.
3. **Coordinator** calls `state.report_harvester(name, value, latency)`.
4. **State** uses `mix_with_time` to update global seed.
5. **TUI** polls `state.get_global_stats()` for rendering.

## 4. Safety & Standards
- **64-bit Boundary**: All seed operations must apply `0xFFFFFFFFFFFFFFFF` (handled by `mix_entropy`).
- **Non-blocking**: No `requests`, no `time.sleep()`, no `subprocess.run()`.
- **Handoffs**: Standardized `dict` return from harvesters for bridge compatibility.
