"""
Logging and warning capture functionality for FontSampler.
"""

import os
import sys
import warnings
from io import StringIO

from rich.console import Console
from rich.traceback import install

# Install Rich traceback handler for better error display
install(show_locals=False)

# Initialize Rich console
console = Console()

# Global warning storage
captured_warnings = []
captured_stderr = []


def warning_handler(message, category, filename, lineno, file=None, line=None):
    """Custom warning handler that captures warnings for later display."""
    warning_info = {
        "message": str(message),
        "category": category.__name__,
        "filename": filename,
        "lineno": lineno,
        "line": line,
    }
    captured_warnings.append(warning_info)


def stderr_capture_handler(message):
    """Capture stderr messages for later display."""
    if message.strip():  # Only capture non-empty messages
        captured_stderr.append(message.strip())


def display_captured_warnings():
    """Display captured warnings and stderr messages in a nice Rich format."""
    has_warnings = bool(captured_warnings)
    has_stderr = bool(captured_stderr)

    if not has_warnings and not has_stderr:
        return

    console.print(
        "\n[bold yellow]⚠️[/bold yellow] [yellow]Messages encountered during processing:[/yellow]"
    )

    # Display Python warnings
    if has_warnings:
        console.print("\n[bold cyan]Python Warnings:[/bold cyan]")
        # Group warnings by type for better organization
        warning_groups = {}
        for warning in captured_warnings:
            category = warning["category"]
            if category not in warning_groups:
                warning_groups[category] = []
            warning_groups[category].append(warning)

        # Display warnings grouped by type
        for category, warnings_list in warning_groups.items():
            if len(warnings_list) == 1:
                warning = warnings_list[0]
                location = (
                    f"{os.path.basename(warning['filename'])}:{warning['lineno']}"
                )
                console.print(
                    f"  [cyan]{category}[/cyan]: [white]{warning['message']}[/white] [dim]({location})[/dim]"
                )
            else:
                console.print(
                    f"  [cyan]{category}[/cyan]: [white]{len(warnings_list)} warnings[/white]"
                )
                for warning in warnings_list[:3]:  # Show first 3 of each type
                    location = (
                        f"{os.path.basename(warning['filename'])}:{warning['lineno']}"
                    )
                    console.print(
                        f"    • [white]{warning['message'][:60]}{'...' if len(warning['message']) > 60 else ''}[/white] [dim]({location})[/dim]"
                    )
                if len(warnings_list) > 3:
                    console.print(
                        f"    [dim]... and {len(warnings_list) - 3} more[/dim]"
                    )

    # Display stderr messages
    if has_stderr:
        console.print("\n[bold magenta]System Messages:[/bold magenta]")
        # Group similar stderr messages
        stderr_groups = {}
        for message in captured_stderr:
            # Create a key based on the first part of the message
            key = message.split()[0] if message.split() else message
            if key not in stderr_groups:
                stderr_groups[key] = []
            stderr_groups[key].append(message)

        for _key, messages in stderr_groups.items():
            if len(messages) == 1:
                console.print(f"  [white]{messages[0]}[/white]")
            else:
                console.print(f"  [white]{len(messages)} similar messages:[/white]")
                for message in messages[:3]:  # Show first 3
                    console.print(
                        f"    • [white]{message[:60]}{'...' if len(message) > 60 else ''}[/white]"
                    )
                if len(messages) > 3:
                    console.print(f"    [dim]... and {len(messages) - 3} more[/dim]")

    # Clear all captured messages for next run
    captured_warnings.clear()
    captured_stderr.clear()


class WarningCaptureContext:
    """Context manager for capturing warnings with custom handler."""

    def __enter__(self):
        self.original_showwarning = warnings.showwarning
        warnings.showwarning = warning_handler
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        warnings.showwarning = self.original_showwarning


class SafeStderrCaptureContext:
    """Safer context manager for capturing stderr output that doesn't interfere with critical operations."""

    def __enter__(self):
        # Only capture stderr for non-critical operations
        self.original_stderr = sys.stderr
        self.captured_output = StringIO()
        sys.stderr = self.captured_output
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # Process captured stderr output
            captured_text = self.captured_output.getvalue()
            if captured_text.strip():
                for line in captured_text.splitlines():
                    if line.strip():
                        stderr_capture_handler(line)
        except Exception:
            # If anything goes wrong with processing, just ignore it
            pass
        finally:
            # Always restore original stderr
            sys.stderr = self.original_stderr


def capture_warnings_context():
    """Context manager for capturing warnings with custom handler."""
    return WarningCaptureContext()


def capture_weasyprint_warnings():
    """Capture WeasyPrint warnings without interfering with main operations."""
    # This is a simpler approach that doesn't redirect stderr
    # but can still capture some warnings through the warning system
    return capture_warnings_context()
