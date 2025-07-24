"""
Command-line interface functionality for FontSampler.
"""

import argparse
import os
import sys

from rich.panel import Panel

from .config import DEFAULT_OUTPUT, LOG_LEVEL
from .incremental_pdf import generate_pdf_incremental
from .logging_config import cleanup_old_logs, setup_logging
from .streaming_processor import find_fonts_streaming, process_fonts_with_streaming
from .warning_capture import console, display_captured_warnings


def create_argument_parser():
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="🎨 Generate PDF font catalog of fonts found in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fontsampler /usr/share/fonts                    # Sample all fonts in system directory
  fontsampler ~/fonts -o my_samples.pdf           # Custom output filename
  fontsampler . -l 10                             # Limit to first 10 fonts (for testing)
  fontsampler . -s typography                     # Use typography testing scenario
  fontsampler . -s international -l 5             # Use international scenario with 5 fonts
  fontsampler . --help                            # Show this help message
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
        "-s",
        "--scenario",
        choices=["default", "typography", "international"],
        default="default",
        help="Testing scenario for sample text (default: default)",
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
    try:
        # Show scenario information
        if args.scenario != "default":
            console.print(
                f"[bold blue]📝[/bold blue] Using [cyan]{args.scenario}[/cyan] testing scenario"
            )

        # Apply limit if specified (for testing)
        if args.limit:
            console.print(
                f"[bold yellow]📝[/bold yellow] Limiting to first [cyan]{args.limit}[/cyan] fonts for testing"
            )
            # Limit font paths at discovery level
            font_paths = list(find_fonts_streaming(args.directory))
            limited_paths = font_paths[: args.limit]

            if not limited_paths:
                console.print("[bold red]❌[/bold red] No font files found to process.")
                return False

            # Process limited font paths
            font_generator = process_fonts_with_streaming(font_paths=limited_paths)
            generate_pdf_incremental(font_generator, args.output, args.scenario)
        else:
            # Process all fonts
            font_generator = process_fonts_with_streaming(args.directory)
            generate_pdf_incremental(font_generator, args.output, args.scenario)

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

    # Setup logging
    log_level = "DEBUG" if args.verbose else LOG_LEVEL
    logger = setup_logging(log_level=log_level)

    # Clean up old logs
    cleanup_old_logs()

    if not validate_arguments(args):
        logger.error(f"Invalid arguments: directory={args.directory}")
        sys.exit(1)

    if not process_fonts_streaming(args):
        logger.error("Font processing failed")
        sys.exit(1)
