import asyncio
import json
import time
import os
import aiofiles
from typing import Dict, Any, List

"""
NOISE SCALING & ZOOM LEVELS:
The raw entropy capture in entropy_stream.jsonl allows for multi-scale noise generation.
1. WHITE NOISE: Sample entries at their native high-resolution (one-by-one).
   The lack of temporal correlation between network packets results in pure stochastic noise.
2. COHERENT NOISE (Perlin-like): Zoom out by aggregating blocks of N entries.
   By averaging or XORing chunks of entropy before sampling, we create 'blobs' of randomness 
   that exhibit smoother transitions, suitable for terrain generation or cloud patterns.
3. FRACTAL NOISE: Overlay multiple zoom levels (different buffer sizes) 
   to simulate complexity across different orders of magnitude.
"""

class EntropyRecorder:
    """
    Non-blocking 'Black Box' for recording high-resolution entropy streams.
    Buffers entries to save eMMC life on portable devices.
    """
    
    def __init__(self, log_path: str = "logs/entropy_stream.jsonl", buffer_size: int = 50):
        self.log_path = log_path
        self.buffer_size = buffer_size
        self._queue = asyncio.Queue()
        self._buffer: List[str] = []
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

    async def record(self, harvester: str, raw_value: Any, seed: int):
        """
        Pushes a new entropy event into the recording queue.
        """
        entry = {
            "ts": time.time(),
            "harvester": harvester,
            "raw_hex": f"0x{int(raw_value):016x}" if isinstance(raw_value, (int, float)) else str(raw_value),
            "seed_hex": f"0x{seed:016x}"
        }
        await self._queue.put(json.dumps(entry))

    async def flush_loop(self):
        """
        Main loop for draining the queue and flushing to disk when buffer is full.
        """
        while True:
            # Wait for an entry
            item = await self._queue.get()
            self._buffer.append(item)
            
            # If buffer is full, perform a single write
            if len(self._buffer) >= self.buffer_size:
                await self._perform_flush()
            
            self._queue.task_done()

    async def _perform_flush(self):
        """
        Appends the current buffer to the log file using aiofiles.
        """
        if not self._buffer:
            return
            
        data_to_write = "\n".join(self._buffer) + "\n"
        try:
            async with aiofiles.open(self.log_path, mode='a') as f:
                await f.write(data_to_write)
            self._buffer = []
        except Exception as e:
            # In a real system, we'd log this to stderr or a separate health check
            pass

    async def force_flush(self):
        """
        Forces a flush of whatever is in the current buffer (e.g., on shutdown).
        """
        await self._perform_flush()
