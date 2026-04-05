import asyncio
import importlib
import os
import sys
import aiohttp
from typing import List

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from interface.state import EntropyState
from interface.constants import HARVESTER_INTERVAL, TIMEOUT_SECONDS
from interface.tui import start_tui
from utils.recorder import EntropyRecorder

async def harvester_loop(state: EntropyState, session: aiohttp.ClientSession, harvester_names: List[str], recorder: EntropyRecorder):
    """
    Continuous loop for staggered entropy harvesting.
    """
    while True:
        for name in sorted(harvester_names):
            try:
                # Dynamically import the module
                module = importlib.import_module(f"harvesters.{name}")
                
                # Check if harvest function exists
                if not hasattr(module, 'harvest'):
                    continue
                
                # Prepare arguments (pass session only if harvester accepts it)
                harvest_func = module.harvest
                args = {}
                if 'session' in harvest_func.__code__.co_varnames:
                    args['session'] = session
                
                # Execute with global timeout
                result = await asyncio.wait_for(
                    harvest_func(**args), 
                    timeout=TIMEOUT_SECONDS
                )
                
                # Report to centralized state
                await state.report_harvester(
                    name=name,
                    value=result.get("value"),
                    latency=result.get("latency", 0.0),
                    error=result.get("error")
                )

                # Record entropy stream
                if result.get("value"):
                    await recorder.record(name, result["value"], state.seed)
                    
            except asyncio.TimeoutError:
                await state.report_harvester(name, error="Global Timeout")
            except Exception as e:
                await state.report_harvester(name, error=f"{type(e).__name__}: {str(e)}")
            
            # Staggered execution
            await asyncio.sleep(HARVESTER_INTERVAL)

async def run_monster():
    """
    Main Async Orchestrator for Maritimentro.
    Launches the harvester loop, TUI, and recorder concurrently.
    """
    state = EntropyState()
    recorder = EntropyRecorder()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    h_dir = os.path.join(base_dir, 'harvesters')
    
    # Identify available harvester modules
    harvester_names = [
        f[:-3] for f in os.listdir(h_dir) 
        if f.endswith('.py') and f != '__init__.py'
    ]

    async with aiohttp.ClientSession() as session:
        # Launch harvester loop, TUI, and the recorder's flush loop
        try:
            await asyncio.gather(
                harvester_loop(state, session, harvester_names, recorder),
                start_tui(state),
                recorder.flush_loop()
            )
        except asyncio.CancelledError:
            # Force flush on exit
            await recorder.force_flush()

if __name__ == "__main__":
    try:
        asyncio.run(run_monster())
    except KeyboardInterrupt:
        # TUI will handle terminal cleanup on exit via Rich.live screen mode
        pass
