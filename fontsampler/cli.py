"""
Command-line interface functionality for FontSampler.
"""

import argparse
import os
import sys

from rich.panel import Panel

from .config import DEFAULT_OUTPUT, MAX_FONTS
from .font_discovery import find_fonts
from .pdf_generation import display_captured_warnings, generate_pdf_with_toc
from .warning_capture import console


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="🎨 Generate PDF font catalog of fonts found in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fontsampler /usr/share/fonts          # Sample all fonts in system directory
  fontsampler ~/fonts -o my_samples.pdf # Custom output filename
  fontsampler . -l 10                   # Limit to first 10 fonts (for testing)
  fontsampler . --help                  # Show this help message
        """,
    )

    parser.add_argument(
        "directory", help="Directory containing font files (.ttf, .otf)"
    )

    parser.add_argument(
        "-o",
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output PDF filename (default: {DEFAULT_OUTPUT})",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show detailed information about font processing",
    )

    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        help="Limit the number of fonts to process (useful for testing)",
    )

    parser.add_argument(
        "-m",
        "--max-fonts",
        type=int,
        default=MAX_FONTS,
        help=f"Maximum number of fonts to process (default: {MAX_FONTS}, use 0 for unlimited)",
    )

    return parser


def validate_arguments(args):
    """Validate command line arguments."""
    if not os.path.exists(args.directory):
        console.print(
            f"[bold red]❌[/bold red] Error: Directory '[red]{args.directory}[/red]' does not exist"
        )
        return False

    if not os.path.isdir(args.directory):
        console.print(
            f"[bold red]❌[/bold red] Error: '[red]{args.directory}[/red]' is not a directory"
        )
        return False

    return True


def process_fonts(args):
    """Process fonts based on command line arguments."""
    fonts = find_fonts(args.directory)
    if not fonts:
        console.print(
            f"[bold blue]🔍[/bold blue] No font files (.ttf, .otf) found in '[cyan]{args.directory}[/cyan]'"
        )
        return False

    # Apply font limit if specified
    if args.limit and len(fonts) > args.limit:
        console.print(
            f"[bold yellow]📝[/bold yellow] Limiting to first [cyan]{args.limit}[/cyan] fonts (found [cyan]{len(fonts)}[/cyan])"
        )
        fonts = fonts[: args.limit]

    # Apply maximum font limit for safety
    if args.max_fonts > 0 and len(fonts) > args.max_fonts:
        console.print(
            f"[bold yellow]⚠️[/bold yellow] Limiting to [cyan]{args.max_fonts}[/cyan] fonts for memory safety (found [cyan]{len(fonts)}[/cyan])"
        )
        console.print(
            "[yellow]💡[/yellow] Use --max-fonts 0 to process all fonts (may cause memory issues)"
        )
        fonts = fonts[: args.max_fonts]

    console.print("\n[bold yellow]⚙️[/bold yellow] Starting font processing...")

    # Warn about memory usage for large collections
    if len(fonts) > MAX_FONTS:
        console.print(
            f"[bold yellow]⚠️[/bold yellow] Processing [cyan]{len(fonts)}[/cyan] fonts may require significant memory"
        )
        console.print(
            "[yellow]💡[/yellow] Consider using --max-fonts to limit the number of fonts processed"
        )

    generate_pdf_with_toc(fonts, args.output)

    # Display any remaining warnings at the end
    display_captured_warnings()

    return True


def main():
    """Main CLI entry point."""
    # Display program header
    console.print(
        Panel.fit(
            "[bold blue]FontSampler[/bold blue] - [cyan]Generate PDF font catalog[/cyan]",
            border_style="blue",
        )
    )

    parser = create_argument_parser()
    args = parser.parse_args()

    if not validate_arguments(args):
        sys.exit(1)

    if not process_fonts(args):
        sys.exit(1)
