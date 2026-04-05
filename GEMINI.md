# MARITIMENTRO: THE BEAST ORCHESTRATION SPEC
# Goal: Build a DRY, Modular, Parallel Entropy Stream with a TUI MVP.

## 1. THE COORDINATOR (The Brain)
- **Persona**: Systems Architect & Project Lead.
- **Focus**: `maritimentro.py` & Overall Loop Logic.
- **Responsibility**:
    - Manage the `while True` loop and the **Staggered Worker** timing.
    - Ensure the high-level math (Seed XOR/Addition) remains consistent.
    - Handle the "Handshake" between Harvesters and the Display.

## 2. THE SENSOR-TECH (The Source Specialist)
- **Persona**: Network & Hardware Specialist.
- **Focus**: `harvesters/` directory.
- **Responsibility**:
    - Optimize `doggo` and `curl` calls for maximum "Raw Bean" extraction.
    - Monitor `parallel_dns` for thread health and RTT/TTL quality.
    - Ensure each harvester returns a standardized `dict` to the Bridge.

## 3. THE BRIDGE (The Interface Specialist)
- **Persona**: TUI & UX Developer.
- **Focus**: `utils/` & `interface/` (New Directory).
- **Responsibility**:
    - Implement the **MVP Dashboard** using `rich` or `blessed`.
    - Maintain `entropy_tools.py` as the **DRY** source for all math/mixing.
    - Ensure the UI is "non-blocking"—the Monster must keep feeding even if the UI lags.