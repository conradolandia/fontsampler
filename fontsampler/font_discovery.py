"""
Font discovery and metadata extraction functionality for FontSampler.
"""

import os
import sys
from io import StringIO

from fontTools.ttLib import TTFont
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .config import FONT_EXTENSIONS
from .warning_capture import capture_warnings_context, console


def extract_font_info(path):
    """Extract font metadata using fontTools."""
    try:
        # Capture warnings during font parsing
        with capture_warnings_context():
            # Also suppress stdout and stderr temporarily to catch fontTools messages
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_output

            try:
                # Try to open the font with more lenient parsing
                font = TTFont(path, fontNumber=0, lazy=True)
            except Exception:
                # If lazy loading fails, try without lazy loading
                try:
                    font = TTFont(path, fontNumber=0, lazy=False)
                except Exception as e:
                    # If both fail, return None
                    console.print(
                        f"  [bold red]❌[/bold red] Failed to parse font [red]{os.path.basename(path)}[/red]: {e}"
                    )
                    return None
            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        # Validate that the font has required tables
        if "name" not in font:
            console.print(
                f"  [bold yellow]⚠️[/bold yellow] Font [yellow]{os.path.basename(path)}[/yellow] missing name table"
            )
            return None

        name = ""
        version = ""
        copyright = ""
        family = ""

        try:
            for record in font["name"].names:
                if record.nameID == 1 and not family:
                    family = record.toStr()
                if record.nameID == 4 and not name:
                    name = record.toStr()
                if record.nameID == 5 and not version:
                    version = record.toStr()
                if record.nameID == 0 and not copyright:
                    copyright = record.toStr()
        except Exception as e:
            console.print(
                f"  [bold yellow]⚠️[/bold yellow] Error reading name table for [yellow]{os.path.basename(path)}[/yellow]: {e}"
            )
            # Continue with empty values rather than failing completely

        return {
            "file": os.path.basename(path),
            "path": os.path.abspath(path),  # Use absolute path
            "family": family,
            "name": name,
            "version": version,
            "copyright": copyright,
        }
    except Exception as e:
        console.print(
            f"  [bold red]❌[/bold red] Failed to parse font [red]{os.path.basename(path)}[/red]: {e}"
        )
        return None


def find_fonts(root):
    """Find all font files in directory tree."""
    fonts = []
    dir_count = 0
    font_count = 0

    console.print(f"[bold blue]🔍[/bold blue] Scanning directory: [cyan]{root}[/cyan]")

    # First pass to count total directories for progress bar
    total_dirs = sum(1 for _ in os.walk(root))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning directories...", total=total_dirs)

        for dirpath, _, filenames in os.walk(root):
            dir_count += 1
            progress.update(task, advance=1)

            for f in filenames:
                if f.lower().endswith(FONT_EXTENSIONS):
                    font_count += 1
                    fonts.append(os.path.join(dirpath, f))

    console.print(
        f"[bold green]✅[/bold green] Directory scan complete: [cyan]{dir_count}[/cyan] directories, [cyan]{font_count}[/cyan] fonts found"
    )
    return fonts
