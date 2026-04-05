# Maritimentro Orchestration: Foundation (State & Utils)

- [x] Implement `interface/state.py` (Centralized EntropyState) <!-- id: 1 -->
- [x] Refactor `utils/entropy_tools.py` (Exclusive Bitwise Math) <!-- id: 2 -->
- [x] Implement `interface/constants.py` (Core configuration) <!-- id: 4 -->
- [x] Transition Coordinator (`maritimentro.py`) to Async Loop <!-- id: 5 -->
- [x] Refactor all Harvesters to Async/Pristine pattern <!-- id: 6 -->
- [x] Verify Foundation logic <!-- id: 3 -->

# Maritimentro The Bridge: TUI & UX

- [x] Initialize `interface/tui.py` (Rich.live dashboard) <!-- id: 7 -->
- [x] Implement non-blocking polling of `EntropyState` <!-- id: 8 -->
- [x] Implement 'Matrix Fade' visual (Entropy Pool) <!-- id: 9 -->
- [x] Refine TUI layout and responsiveness <!-- id: 10 -->
- [x] Implement Interactive Detail Pane with Keyboard Support <!-- id: 14 -->

# Maritimentro Phase 4: Recording & Noise

- [x] Implement `logs/entropy_stream.jsonl` recording <!-- id: 11 -->
- [x] Use `aiofiles` for non-blocking buffered appends <!-- id: 12 -->
- [x] Document Noise Scaling & Zoom Levels <!-- id: 13 -->

# Maritimentro Phase 5: Statistical Profiling

- [x] Implement `RunningStats` (Welford's Algorithm) <!-- id: 15 -->
- [x] Track Value & Latency distributions per harvester <!-- id: 16 -->
- [x] Implement DNS 'Table Jitter' (Standard Deviation across probes) <!-- id: 17 -->
- [x] Add 'Deep-Dive' Statistical Profile to TUI Detail Pane <!-- id: 18 -->

# Maritimentro Phase 6: Shape Analysis & Higher-Order Moments

- [x] Implement 3rd and 4th Moments (Skewness $\gamma$, Kurtosis $\beta$) <!-- id: 19 -->
- [x] Implement $Q$-Summary (Reservoir-based Median/IQR) <!-- id: 20 -->
- [x] Add 'Shape Analysis' section to TUI Detail Pane <!-- id: 21 -->

# Maritimentro Phase 7: The NeuroWave Visualization

- [x] Implement Generative NeuroWave ASCII logic <!-- id: 22 -->
- [x] Add data-driven waveform to Deep-Dive pane <!-- id: 23 -->
- [x] Add 'Bio-Readout' legend (σ, γ, β integration) <!-- id: 24 -->
