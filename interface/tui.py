import asyncio
import time
from typing import List, Dict, Any

from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.console import Console, Group
from rich.text import Text
from rich import box

from interface.state import EntropyState

class MaritimentroTUI:
    """
    Non-blocking TUI for Maritimentro using Rich.
    Displays harvester telemetry and the 'Matrix Fade' entropy pool.
    """
    
    def __init__(self, state: EntropyState):
        self.state = state
        self.console = Console()
        self.layout = Layout()
        self._setup_layout()

    def _setup_layout(self):
        """Initializes the multi-panel layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        self.layout["body"].split_row(
            Layout(name="stats", ratio=1),
            Layout(name="matrix", ratio=1)
        )

    async def _make_header(self) -> Panel:
        """Generates the system status header."""
        stats = await self.state.get_global_stats()
        header_text = Text.assemble(
            (" STATUS: ", "bold white on green" if stats['total_hits'] > 0 else "bold white on red"),
            f" [SYSTEM RUNNING]  |  UPTIME: {stats['uptime']:.1f}s  |  ",
            ("SEED: ", "bold cyan"),
            (f"{stats['seed_hex']}", "bold yellow")
        )
        return Panel(header_text, style="white on black")

    async def _make_stats_table(self) -> Panel:
        """Generates the table of harvester statistics."""
        table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("Harvester", style="cyan")
        table.add_column("Hits", justify="right", style="green")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Latency", justify="right", style="magenta")
        table.add_column("Status", justify="center")

        harvesters = await self.state.get_harvester_stats()
        for h in sorted(harvesters, key=lambda x: x.name):
            status = "✅" if not h.error_message else "❌"
            table.add_row(
                h.name,
                str(h.hits),
                str(h.errors),
                f"{h.last_latency:.3f}s",
                status
            )
        
        return Panel(table, title="[bold white]Telemetry[/bold white]", border_style="blue")

    async def _make_matrix_fade(self) -> Panel:
        """Generates the 'Matrix Fade' visual for entropy beans."""
        beans = await self.state.get_bean_pool()
        now = time.time()
        
        # Matrix display: Decaying color trail of raw beans
        # We'll use a wrap-around grid for the display
        matrix_text = Text()
        
        for bean in reversed(beans):
            age = now - bean['ts']
            # Decay factor: 0.0 (fresh) to 1.0 (old) over 10 seconds
            decay = min(1.0, age / 10.0)
            
            # Map decay to a color (green fade)
            # Fresh beans are bold white/green, old beans are dark green
            if decay < 0.1:
                color = "bold white on green"
            elif decay < 0.3:
                color = "bold green"
            elif decay < 0.6:
                color = "green"
            else:
                color = "dim green"
            
            # Represent the bean as its truncated hex value or name initial
            val_hex = f"{bean['value'] & 0xFFFF:04x}"
            matrix_text.append(f" {val_hex} ", style=color)
            
        return Panel(
            matrix_text, 
            title="[bold green]Matrix Fade (Entropy Pool)[/bold green]", 
            border_style="green"
        )

    async def update(self):
        """Updates all components of the layout."""
        self.layout["header"].update(await self._make_header())
        self.layout["stats"].update(await self._make_stats_table())
        self.layout["matrix"].update(await self._make_matrix_fade())

    async def run(self, refresh_rate: float = 0.2):
        """Main TUI loop."""
        with Live(self.layout, console=self.console, refresh_per_second=1/refresh_rate, screen=True):
            while True:
                await self.update()
                await asyncio.sleep(refresh_rate)

async def start_tui(state: EntropyState):
    """Entry point for the TUI task."""
    tui = MaritimentroTUI(state)
    await tui.run()
