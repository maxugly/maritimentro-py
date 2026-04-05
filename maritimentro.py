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
    try:
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
                        error=result.get("error"),
                        metadata=result.get("metadata")
                    )

                    # Record entropy stream
                    if result.get("value"):
                        await recorder.record(name, result["value"], state.seed)
                        
                except asyncio.TimeoutError:
                    await state.report_harvester(name, error="Global Timeout")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    await state.report_harvester(name, error=f"{type(e).__name__}: {str(e)}")
                
                # Staggered execution
                await asyncio.sleep(HARVESTER_INTERVAL)
    except asyncio.CancelledError:
        pass

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
        # Create tasks for all major components
        tasks = [
            asyncio.create_task(harvester_loop(state, session, harvester_names, recorder), name="harvester"),
            asyncio.create_task(start_tui(state), name="tui"),
            asyncio.create_task(recorder.flush_loop(), name="recorder")
        ]
        
        try:
            # Wait for any task to complete (usually the TUI when 'q' is pressed)
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Check for exceptions in the tasks that finished
            for task in done:
                if not task.cancelled() and task.exception():
                    exc = task.exception()
                    print(f"\n[CRITICAL ERROR] Task '{task.get_name()}' failed:")
                    import traceback
                    traceback.print_exception(type(exc), exc, exc.__traceback__)
                    
        finally:
            # Shutdown procedure: cancel everything else
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for tasks to handle cancellation (with timeout to prevent hang)
            if tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*tasks, return_exceptions=True),
                        timeout=2.0
                    )
                except asyncio.TimeoutError:
                    pass
            
            # Final high-priority cleanup
            await recorder.force_flush()

if __name__ == "__main__":
    try:
        asyncio.run(run_monster())
    except KeyboardInterrupt:
        pass
