"""
Incremental PDF generation for FontSampler.
"""

import sys
from io import StringIO
from typing import Any, Dict, Generator

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from .config import (
    PROCESSING_INTERVAL,
    SAMPLE_SIZES,
    UPDATE_INTERVAL,
)
from .logging_config import get_logger, log_memory_usage, log_pdf_generation
from .memory_utils import MemoryMonitor, force_garbage_collection
from .template_manager import TemplateManager
from .warning_capture import (
    capture_warnings_context,
    console,
    stderr_capture_handler,
)


def generate_pdf_incremental(
    font_generator: Generator[Dict[str, Any], None, None],
    output_path: str,
    scenario: str = "default",
) -> None:
    """
    Generate PDF with table of contents from a font generator.

    Args:
        font_generator: Generator yielding font information dictionaries
        output_path: Output PDF file path
        scenario: Testing scenario name (default, typography, international)
    """
    logger = get_logger("fontsampler.pdf_generation")

    with MemoryMonitor("PDF Generation") as memory_monitor:
        # Collect all fonts first
        fonts = []
        font_count = 0

        for font_info in font_generator:
            fonts.append(font_info)
            font_count += 1

            if font_count % UPDATE_INTERVAL == 0:
                memory_monitor.update_peak()

            if font_count % PROCESSING_INTERVAL == 0:
                console.print(f"[blue]📊[/blue] Processed {font_count} fonts...")

        console.print(f"[blue]📊[/blue] Total fonts processed: {font_count}")

        if not fonts:
            console.print("[red]❌[/red] No fonts found")
            logger.warning("No fonts found for PDF generation")
            return

        # Sort fonts alphabetically
        fonts.sort(key=lambda x: x["file"].lower())

        # Generate PDF with ToC
        console.print("[yellow]📄[/yellow] Starting PDF generation...")
        log_pdf_generation(logger, "START", f"Output: {output_path}", font_count)

        try:
            # Initialize template manager
            template_manager = TemplateManager()

            # Get scenario content
            from .config import _config

            scenario_content = _config.get_testing_scenario(scenario)

            # Render HTML and CSS using templates
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
                        html.write_pdf(
                            output_path, stylesheets=[css], font_config=font_config
                        )
                        log_pdf_generation(
                            logger,
                            "COMPLETE",
                            f"PDF generated successfully: {output_path}",
                        )
                    except Exception as e:
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
