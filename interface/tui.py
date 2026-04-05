import asyncio
import time
import sys
import tty
import termios
import select
import os
import math
from typing import List, Dict, Any, Optional

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
    Displays harvester telemetry, entropy pool, and interactive statistical profiles.
    """
    
    def __init__(self, state: EntropyState):
        self.state = state
        self.console = Console()
        self.layout = Layout()
        self.selected_index = 0
        self.harvester_names: List[str] = []
        self.frame_count = 0
        self._setup_layout()

    def _setup_layout(self):
        """Initializes the multi-panel layout."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="body")
        )
        self.layout["body"].split_row(
            Layout(name="left", ratio=1),
            Layout(name="matrix", ratio=1)
        )
        self.layout["left"].split_column(
            Layout(name="stats", ratio=2),
            Layout(name="details", ratio=4)
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
        return Panel(header_text, style="white on black", title="[bold white]Maritimentro v0.1.0[/bold white]")

    async def _make_stats_table(self) -> Panel:
        """Generates the table of harvester statistics with selection highlighting."""
        table = Table(box=box.MINIMAL_DOUBLE_HEAD, expand=True)
        table.add_column("Harvester", style="cyan")
        table.add_column("Hits", justify="right", style="green")
        table.add_column("Errors", justify="right", style="red")
        table.add_column("Latency", justify="right", style="magenta")
        table.add_column("Status", justify="center")

        harvesters = await self.state.get_harvester_stats()
        self.harvester_names = sorted([h.name for h in harvesters])
        
        if not self.harvester_names:
            return Panel(
                Text("\n\nWaiting for harvesters to report beans...", style="dim italic", justify="center"),
                title="[bold white]Telemetry (Arrows to Select)[/bold white]",
                border_style="blue"
            )

        self.selected_index = self.selected_index % len(self.harvester_names)

        for i, h_name in enumerate(self.harvester_names):
            h = next((stat for stat in harvesters if stat.name == h_name), None)
            if not h: continue
            
            status = "✅" if not h.error_message else "❌"
            style = "bold white on blue" if i == self.selected_index else ""
            
            table.add_row(
                h.name,
                str(h.hits),
                str(h.errors),
                f"{h.last_latency:.3f}s",
                status,
                style=style
            )
        
        return Panel(table, title="[bold white]Telemetry (Arrows to Select)[/bold white]", border_style="blue")

    def _get_quality_label(self, std_dev: float, mean: float) -> Text:
        """Calculates a qualitative entropy score based on coefficient of variation."""
        if mean == 0: return Text("Unknown", style="dim")
        cv = std_dev / abs(mean) if mean != 0 else 0
        if cv > 0.5: return Text("High (Noisy)", style="bold green")
        if cv > 0.1: return Text("Stable (Mixed)", style="green")
        if cv > 0.01: return Text("Low (Coherent)", style="yellow")
        return Text("Static (Fixed)", style="bold red")

    def _make_neurowave(self, h: Any, width: int) -> Panel:
        """
        Generative NeuroWave Visualization.
        Driven by σ (Amp), γ (Skew), and β (Peak).
        Adaptive Scaling: Normalizes amplitude based on the harvester's dynamic range.
        """
        v_stats = h.val_stats
        l_stats = h.lat_stats
        
        sigma = v_stats.std_dev
        gamma = v_stats.skewness
        beta = v_stats.kurtosis
        
        # 1. ADAPTIVE AMPLITUDE SCALING
        # Calculate dynamic range (Max - Min)
        v_range = v_stats.max - v_stats.min
        
        if v_range > 0:
            # We use a mix of StdDev and Dynamic Range to determine 'energy'
            # If StdDev is a large portion of the range, it's high energy
            energy = (sigma / v_range) * 2.0
            amp = min(1.0, energy)
        else:
            amp = 0.1 # Minimum heartbeat pulse
            
        # Ensure even low-variance harvesters have a baseline 'alive' pulse
        amp = max(0.15, amp)

        # 2. INTENSITY & CHARACTER SELECTION
        # Driven by Kurtosis (β) and Latency Jitter
        total_jitter = beta + (l_stats.std_dev * 100)
        if total_jitter > 10: char = "@"
        elif total_jitter > 3: char = "#"
        elif total_jitter > 0: char = "*"
        elif total_jitter > -1: char = "~"
        else: char = "."

        wave_lines = ["", "", ""]
        # Animation speed influenced by Latency Jitter (more jitter = faster wave)
        speed = 5.0 + (l_stats.std_dev * 50)
        t = self.frame_count / max(1.0, speed)
        
        # 3. GENERATIVE RENDER
        for x in range(width - 4):
            # Skew (γ) leans the wave by shifting phase
            theta = (x / 5.0) + t + (0.5 * gamma * math.sin(x/5.0))
            
            # Kurtosis (β) sharpens the peak (Power function)
            # We clamp beta to prevent extreme math errors in pow()
            k = 1.0 + max(-0.5, min(5.0, beta)) / 10.0
            y_raw = math.sin(theta)
            
            # Apply power scaling and amplitude
            y = (math.copysign(1, y_raw) * abs(y_raw)**k) * amp
            
            # Assign to 3-line ASCII grid
            if y > 0.2:
                wave_lines[0] += char; wave_lines[1] += " "; wave_lines[2] += " "
            elif y < -0.2:
                wave_lines[0] += " "; wave_lines[1] += " "; wave_lines[2] += char
            else:
                wave_lines[0] += " "; wave_lines[1] += char; wave_lines[2] += " "

        # Color the wave based on Quality score
        cv = sigma / abs(v_stats.mean) if v_stats.mean != 0 else 0
        wave_color = "bold green" if cv > 0.1 else "green"
        if cv < 0.01: wave_color = "dim green"

        wave_group = Group(
            Text(wave_lines[0], style=wave_color),
            Text(wave_lines[1], style=wave_color),
            Text(wave_lines[2], style="dim " + wave_color),
            Text("-" * (width - 4), style="dim white"),
            Text(f" [ADAPTIVE PULSE] Energy:{amp:.2f} | Skew:{gamma:.2f} | Peak:{beta:.2f}", style="bold cyan")
        )
        
        return Panel(wave_group, title="[bold green]NeuroWave[/bold green]", border_style="green")

    async def _make_detail_pane(self) -> Panel:
        """Generates the metadata and statistical profile for the selected harvester."""
        if not self.harvester_names:
            return Panel(Text("Waiting for harvesters...", style="dim"), title="Harvester Details", border_style="cyan")

        selected_name = self.harvester_names[self.selected_index]
        harvesters = await self.state.get_harvester_stats()
        h = next((stat for stat in harvesters if stat.name == selected_name), None)
        metadata = await self.state.get_harvester_metadata(selected_name)
        
        if not h or h.hits == 0:
            return Panel(Text("\nWaiting for first bean report...", style="bold yellow", justify="center"), 
                         title=f"[bold cyan]{selected_name} Details[/bold cyan]", border_style="cyan")

        # 1. Metadata Table
        meta_table = Table(show_header=False, box=None, expand=True)
        meta_table.add_column("Key", style="cyan", ratio=1)
        meta_table.add_column("Value", style="white", ratio=2)
        if metadata:
            for key, val in metadata.items():
                meta_table.add_row(f"{key.replace('_', ' ').title()}:", str(val))
        
        # 2. Statistical Profile Table
        stats_table = Table(show_header=False, box=None, expand=True)
        stats_table.add_column("Label", style="bold magenta", ratio=1)
        stats_table.add_column("Val", style="white", ratio=1)
        stats_table.add_column("Lat", style="dim white", ratio=1)
        stats_table.add_row("[underline]Profile[/underline]", "[underline]Value[/underline]", "[underline]Latency[/underline]")
        stats_table.add_row("Avg (μ):", f"{h.val_stats.mean:.1f}", f"{h.lat_stats.mean:.3f}s")
        stats_table.add_row("Jitter (σ):", f"{h.val_stats.std_dev:.1f}", f"{h.lat_stats.std_dev:.4f}s")
        stats_table.add_row("Quality:", self._get_quality_label(h.val_stats.std_dev, h.val_stats.mean), "")

        # 3. Shape Analysis Table
        shape_table = Table(show_header=False, box=None, expand=True)
        shape_table.add_column("Label", style="bold yellow", ratio=1)
        shape_table.add_column("Val", style="white", ratio=1)
        shape_table.add_column("Lat", style="dim white", ratio=1)
        shape_table.add_row("[underline]Shape[/underline]", "[underline]Value[/underline]", "[underline]Latency[/underline]")
        shape_table.add_row("Skew (γ):", f"{h.val_stats.skewness:.2f}", f"{h.lat_stats.skewness:.2f}")
        shape_table.add_row("Kurt (β):", f"{h.val_stats.kurtosis:.2f}", f"{h.lat_stats.kurtosis:.2f}")
        
        v_q = h.val_stats.quantiles
        l_q = h.lat_stats.quantiles
        shape_table.add_row("Median:", f"{v_q['q2']:.1f}", f"{l_q['q2']:.3f}s")
        shape_table.add_row("IQR:", f"{v_q['iqr']:.1f}", f"{l_q['iqr']:.3f}s")

        # 4. NeuroWave (Dynamic ASCII)
        wave_panel = self._make_neurowave(h, width=40)

        content = Group(
            Panel(meta_table, title="[dim]Metadata[/dim]", border_style="dim"),
            Panel(stats_table, title="[dim]Statistical Profile[/dim]", border_style="dim"),
            Panel(shape_table, title="[dim]Shape Analysis[/dim]", border_style="dim"),
            wave_panel
        )

        return Panel(content, title=f"[bold cyan]{selected_name} Deep-Dive[/bold cyan]", border_style="cyan")

    async def _make_matrix_fade(self) -> Panel:
        """Generates the 'Matrix Fade' visual for entropy beans."""
        beans = await self.state.get_bean_pool()
        now = time.time()
        matrix_text = Text()
        
        if not beans:
            return Panel(
                Text("\n\nEmpty Pool...", style="dim italic", justify="center"),
                title="[bold green]Matrix Fade (Entropy Pool)[/bold green]",
                border_style="green"
            )

        for bean in reversed(beans):
            age = now - bean['ts']
            decay = min(1.0, age / 10.0)
            
            if decay < 0.1: color = "bold white on green"
            elif decay < 0.3: color = "bold green"
            elif decay < 0.6: color = "green"
            else: color = "dim green"
            
            val_hex = f"{bean['value'] & 0xFFFF:04x}"
            matrix_text.append(f" {val_hex} ", style=color)
            
        return Panel(
            matrix_text, 
            title="[bold green]Matrix Fade (Entropy Pool)[/bold green]", 
            border_style="green"
        )

    async def update(self):
        """Updates all components of the layout."""
        self.frame_count += 1
        # Pull all data concurrently for responsiveness
        header, stats, details, matrix = await asyncio.gather(
            self._make_header(),
            self._make_stats_table(),
            self._make_detail_pane(),
            self._make_matrix_fade()
        )
        self.layout["header"].update(header)
        self.layout["stats"].update(stats)
        self.layout["details"].update(details)
        self.layout["matrix"].update(matrix)

    def _handle_input(self):
        """Non-blocking check for keyboard input using select and os.read."""
        if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
            try:
                char = os.read(sys.stdin.fileno(), 3).decode(errors="ignore")
                if char == '\x1b[A': # Up
                    self.selected_index = (self.selected_index - 1) % max(1, len(self.harvester_names))
                elif char == '\x1b[B': # Down
                    self.selected_index = (self.selected_index + 1) % max(1, len(self.harvester_names))
                elif char in ('q', 'Q', '\x1b'):
                    raise KeyboardInterrupt()
            except Exception as e:
                if isinstance(e, KeyboardInterrupt): raise e

    async def run(self, refresh_rate: float = 0.1):
        """Main TUI loop with robust terminal state management."""
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            with Live(self.layout, console=self.console, screen=True, auto_refresh=True, refresh_per_second=10):
                while True:
                    self._handle_input()
                    await self.update()
                    await asyncio.sleep(refresh_rate)
        except (KeyboardInterrupt, asyncio.CancelledError):
            pass
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)

async def start_tui(state: EntropyState):
    """Entry point for the TUI task."""
    tui = MaritimentroTUI(state)
    await tui.run()
