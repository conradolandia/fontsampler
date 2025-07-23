"""
Command-line interface functionality for FontSampler.
"""

import argparse
import os
import sys

from rich.panel import Panel

from .config import DEFAULT_OUTPUT
from .incremental_pdf import generate_pdf_incremental
from .streaming_processor import process_fonts_with_streaming
from .warning_capture import console, display_captured_warnings


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
        "--legacy-mode",
        action="store_true",
        help="Use legacy processing mode with hard limits (for compatibility)",
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


def process_fonts_streaming(args):
    """Process fonts using streaming architecture."""
    # Import legacy processing for compatibility
    if args.legacy_mode:
        from .font_discovery import find_fonts
        from .pdf_generation import generate_pdf_with_toc

        console.print("[yellow]⚠️[/yellow] Using legacy processing mode")

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

        generate_pdf_with_toc(fonts, args.output)
        display_captured_warnings()
        return True

    # Use new streaming architecture
    console.print(
        "[bold blue]🚀[/bold blue] Using streaming architecture with adaptive memory management"
    )

    try:
        # Process fonts using streaming
        font_generator = process_fonts_with_streaming(args.directory)

        # Apply limit if specified (for testing)
        if args.limit:
            console.print(
                f"[bold yellow]📝[/bold yellow] Limiting to first [cyan]{args.limit}[/cyan] fonts for testing"
            )
            limited_generator = []
            for i, font_info in enumerate(font_generator):
                if i >= args.limit:
                    break
                limited_generator.append(font_info)

            if not limited_generator:
                console.print(
                    "[bold red]❌[/bold red] No compatible fonts found to generate PDF."
                )
                return False

            # Generate PDF from limited fonts
            generate_pdf_incremental(iter(limited_generator), args.output)
        else:
            # Generate PDF from all fonts
            generate_pdf_incremental(font_generator, args.output)

        # Display any remaining warnings at the end
        display_captured_warnings()

        return True

    except Exception as e:
        console.print(f"[bold red]❌[/bold red] Error during processing: {e}")
        return False


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

    if not process_fonts_streaming(args):
        sys.exit(1)
