"""
Command-line interface functionality for FontSampler.
"""

import argparse
import os
import sys

from rich.panel import Panel

from .config import DEFAULT_OUTPUT, LOG_LEVEL, _config
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

    parser.add_argument(
        "--font-subsetting",
        choices=["auto", "enabled", "disabled"],
        default="auto",
        help="Font subsetting behavior: auto (default), enabled, or disabled",
    )

    parser.add_argument(
        "--skip-problematic-fonts",
        action="store_true",
        default=None,
        help="Skip problematic fonts and continue processing (overrides config)",
    )

    parser.add_argument(
        "--no-skip-problematic-fonts",
        action="store_true",
        default=None,
        help="Stop processing when problematic fonts are encountered (overrides config)",
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

        # Show font subsetting setting if not auto
        if args.font_subsetting != "auto":
            console.print(
                f"[bold blue]🔧[/bold blue] Font subsetting: [cyan]{args.font_subsetting}[/cyan]"
            )

        # Determine skip_problematic_fonts setting
        skip_problematic_fonts = None
        if args.skip_problematic_fonts:
            skip_problematic_fonts = True
            console.print(
                "[bold blue]🔧[/bold blue] Font processing: [cyan]skip problematic fonts[/cyan]"
            )
        elif args.no_skip_problematic_fonts:
            skip_problematic_fonts = False
            console.print(
                "[bold blue]🔧[/bold blue] Font processing: [cyan]stop on problematic fonts[/cyan]"
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
            font_generator = process_fonts_with_streaming(
                font_paths=limited_paths, skip_problematic_fonts=skip_problematic_fonts
            )
            generate_pdf_incremental(
                font_generator, args.output, args.scenario, args.font_subsetting
            )
        else:
            # Process all fonts
            font_generator = process_fonts_with_streaming(
                args.directory, skip_problematic_fonts=skip_problematic_fonts
            )
            generate_pdf_incremental(
                font_generator, args.output, args.scenario, args.font_subsetting
            )

        # Display any remaining warnings at the end
        display_captured_warnings()

        return True

    except Exception as e:
        console.print(f"[bold red]❌[/bold red] Error during processing: {e}")
        return False


def main():
    """Main CLI entry point."""
    # Display ASCII art header
    header = _config.get_header()
    if header:
        console.print(
            Panel.fit(header, border_style="dark_slate_gray1"), style="wheat1"
        )
        console.print()  # Add a blank line after header
    else:
        # Fallback to Rich panel if no header in config
        console.print(
            Panel.fit(
                "[yellow2]FontSampler[/yellow2] - [wheat1]Generate PDF font catalog[/wheat1]",
                border_style="dark_slate_gray1",
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
