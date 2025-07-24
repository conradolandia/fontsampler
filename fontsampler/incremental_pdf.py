"""
Incremental PDF generation for FontSampler.
"""

import sys
from io import StringIO
from typing import Any, Dict, Generator

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from .config import (
    PDF_FONT_SUBSETTING,
    PDF_RETRY_WITHOUT_SUBSETTING,
    PROCESSING_INTERVAL,
    SAMPLE_SIZES,
    UPDATE_INTERVAL,
)
from .logging_config import (
    get_logger,
    log_memory_usage,
    log_pdf_font_issue,
    log_pdf_font_optimization_retry,
    log_pdf_generation,
)
from .memory_utils import MemoryMonitor, force_garbage_collection
from .template_manager import TemplateManager
from .warning_capture import (
    capture_warnings_context,
    console,
    stderr_capture_handler,
)


def extract_font_names_from_error(error_message: str, fonts: list) -> list:
    """
    Extract font names from error messages by matching against known fonts.

    Args:
        error_message: The error message from WeasyPrint
        fonts: List of font dictionaries being processed

    Returns:
        List of font names that might be causing the issue
    """
    problematic_fonts = []

    # Common patterns in WeasyPrint font errors
    font_error_patterns = [
        "font",
        "subset",
        "glyph",
        "character",
        "unicode",
        "cmap",
        "name table",
        "post table",
        "glyf table",
        "hmtx table",
    ]

    # Check if error contains font-related keywords
    error_lower = error_message.lower()
    is_font_error = any(pattern in error_lower for pattern in font_error_patterns)

    if is_font_error:
        # For font-related errors, we can't always identify the specific font
        # So we log all fonts being processed as potentially problematic
        problematic_fonts = [font.get("file", "unknown") for font in fonts]

        # Try to extract specific font names from error message
        for font in fonts:
            font_name = font.get("file", "")
            if font_name and font_name.lower() in error_lower:
                problematic_fonts = [font_name]  # Found specific font
                break

    return problematic_fonts


def generate_pdf_incremental(
    font_generator: Generator[Dict[str, Any], None, None],
    output_path: str,
    scenario: str = "default",
    font_subsetting: str = None,
) -> None:
    """
    Generate PDF with table of contents from a font generator.

    Args:
        font_generator: Generator yielding font information dictionaries
        output_path: Output PDF file path
        scenario: Testing scenario name (default, typography, international)
        font_subsetting: Font subsetting behavior (auto, enabled, disabled). If None, uses config default.
    """
    logger = get_logger("fontsampler.pdf_generation")

    # Use provided font_subsetting or fall back to config default
    subsetting_mode = (
        font_subsetting if font_subsetting is not None else PDF_FONT_SUBSETTING
    )

    with MemoryMonitor("PDF Generation") as memory_monitor:
        # Collect all fonts first
        fonts = []
        font_count = 0

        # Collect fonts with frequent progress updates
        console.print("[cyan]📥[/cyan] Collecting fonts from generator...")
        for font_info in font_generator:
            fonts.append(font_info)
            font_count += 1

            if font_count % UPDATE_INTERVAL == 0:
                memory_monitor.update_peak()

            if font_count % PROCESSING_INTERVAL == 0:
                console.print(f"[blue]📊[/blue] Processed {font_count} fonts...")

        console.print(f"[blue]📊[/blue] Total fonts collected: {font_count}")

        if not fonts:
            console.print("[red]❌[/red] No fonts found")
            logger.warning("No fonts found for PDF generation")
            return

        # Sort fonts alphabetically
        console.print("[yellow]🔄[/yellow] Sorting fonts...")
        fonts.sort(key=lambda x: x["file"].lower())

        # Generate PDF with ToC
        console.print("[yellow]📄[/yellow] Starting PDF generation...")
        log_pdf_generation(logger, "START", f"Output: {output_path}", font_count)

        try:
            # Initialize template manager
            console.print("[cyan]🔧[/cyan] Preparing templates...")
            template_manager = TemplateManager()

            # Get scenario content
            from .config import _config

            scenario_content = _config.get_testing_scenario(scenario)

            # Render HTML and CSS using templates
            console.print("[cyan]🎨[/cyan] Rendering HTML and CSS...")
            html_content = template_manager.render_html(
                fonts,
                sample_text=scenario_content["main"],
                paragraph_text=scenario_content["paragraph"],
                sample_sizes=SAMPLE_SIZES,
                paragraph_size=12,
            )
            css_content = template_manager.render_css(fonts)

            font_config = FontConfiguration()
            html = HTML(string=html_content)
            css = CSS(string=css_content, font_config=font_config)

            with console.status("[cyan]Generating PDF..."):
                # Capture warnings and stderr for the final PDF generation
                with capture_warnings_context():
                    # Also capture stderr for WeasyPrint warnings
                    original_stderr = sys.stderr
                    stderr_capture = StringIO()
                    sys.stderr = stderr_capture

                    try:
                        # Try to generate PDF with font subsetting based on configuration
                        if subsetting_mode == "disabled":
                            console.print(
                                "[cyan]🔧[/cyan] Generating PDF with font subsetting disabled..."
                            )
                            # Note: Font subsetting control is handled via CSS properties in newer WeasyPrint versions
                        elif subsetting_mode == "enabled":
                            console.print(
                                "[cyan]🔧[/cyan] Generating PDF with font subsetting enabled..."
                            )
                        else:  # auto
                            console.print(
                                "[cyan]🔧[/cyan] Attempting PDF generation with font optimization..."
                            )

                        html.write_pdf(
                            output_path, stylesheets=[css], font_config=font_config
                        )
                        log_pdf_generation(
                            logger,
                            "COMPLETE",
                            f"PDF generated successfully: {output_path}",
                        )
                    except Exception as e:
                        error_msg = str(e)
                        if PDF_RETRY_WITHOUT_SUBSETTING and (
                            "unpack requires a buffer" in error_msg
                            or "font" in error_msg.lower()
                        ):
                            # Extract problematic font names from error
                            problematic_fonts = extract_font_names_from_error(
                                error_msg, fonts
                            )

                            # Log the font issue
                            log_pdf_font_issue(
                                logger,
                                problematic_fonts,
                                "font_optimization",
                                error_msg,
                                "PDF_GENERATION",
                            )

                            console.print(
                                "\n[yellow]⚠️[/yellow] Font optimization failed, retrying with disabled subsetting..."
                            )
                            log_pdf_font_optimization_retry(logger, error_msg)

                            try:
                                # Retry with font subsetting disabled
                                # Create a new font configuration
                                font_config_no_subset = FontConfiguration()

                                console.print(
                                    "[cyan]🔧[/cyan] Retrying PDF generation without font subsetting..."
                                )
                                html.write_pdf(
                                    output_path,
                                    stylesheets=[css],
                                    font_config=font_config_no_subset,
                                )
                                log_pdf_generation(
                                    logger,
                                    "COMPLETE",
                                    f"PDF generated successfully (no subsetting): {output_path}",
                                )
                                log_pdf_font_optimization_retry(
                                    logger, error_msg, retry_success=True
                                )
                                console.print(
                                    "[green]✅[/green] PDF generated successfully (font subsetting disabled)"
                                )
                            except Exception as retry_error:
                                retry_error_msg = str(retry_error)
                                console.print(
                                    f"[red]❌[/red] PDF generation failed even with subsetting disabled: {retry_error}"
                                )

                                # Log the retry failure with font details
                                retry_problematic_fonts = extract_font_names_from_error(
                                    retry_error_msg, fonts
                                )
                                log_pdf_font_issue(
                                    logger,
                                    retry_problematic_fonts,
                                    "font_optimization_retry_failed",
                                    retry_error_msg,
                                    "PDF_GENERATION_RETRY",
                                )

                                log_pdf_generation(
                                    logger,
                                    "ERROR",
                                    f"PDF generation failed (retry): {retry_error}",
                                    error=retry_error,
                                )
                                log_pdf_font_optimization_retry(
                                    logger,
                                    error_msg,
                                    retry_success=False,
                                    retry_error=retry_error_msg,
                                )
                                raise retry_error
                        else:
                            # Non-font-related error or retry disabled
                            log_pdf_generation(
                                logger, "ERROR", f"PDF generation failed: {e}", error=e
                            )
                            raise
                    finally:
                        # Process captured stderr
                        stderr_output = stderr_capture.getvalue()
                        if stderr_output.strip():
                            for line in stderr_output.splitlines():
                                if line.strip():
                                    stderr_capture_handler(line)

                        # Restore stderr
                        sys.stderr = original_stderr

            console.print(
                f"[green]✅[/green] PDF generated: [cyan]{output_path}[/cyan]"
            )

        except Exception as e:
            console.print(f"[red]❌[/red] Error generating PDF: {e}")

        finally:
            # Clean up
            fonts.clear()
            force_garbage_collection()

        stats = memory_monitor.get_stats()
        console.print(
            f"[blue]📊[/blue] Memory usage: {stats['peak_increase']:.1f}MB peak increase"
        )

        # Log memory usage
        log_memory_usage(
            logger,
            "PDF Generation",
            stats["start_memory"],
            stats["current_memory"],
            stats["peak_memory"],
        )
