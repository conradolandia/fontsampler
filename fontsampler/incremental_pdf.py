"""
Incremental PDF generation for FontSampler.
"""

import sys
from io import StringIO
from typing import Any, Dict, Generator

from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from .config import PARAGRAPH, SAMPLE_TEXT
from .logging_config import get_logger, log_memory_usage, log_pdf_generation
from .memory_utils import MemoryMonitor, force_garbage_collection
from .warning_capture import (
    capture_warnings_context,
    console,
    stderr_capture_handler,
)


def generate_pdf_incremental(
    font_generator: Generator[Dict[str, Any], None, None], output_path: str
) -> None:
    """
    Generate PDF with table of contents from a font generator.

    Args:
        font_generator: Generator yielding font information dictionaries
        output_path: Output PDF file path
    """
    logger = get_logger("fontsampler.pdf_generation")

    with MemoryMonitor("PDF Generation") as memory_monitor:
        # Collect all fonts first
        fonts = []
        font_count = 0

        for font_info in font_generator:
            fonts.append(font_info)
            font_count += 1

            if font_count % 100 == 0:
                console.print(f"[blue]📊[/blue] Processed {font_count} fonts...")
                memory_monitor.update_peak()

        console.print(f"[blue]📊[/blue] Total fonts processed: {font_count}")

        if not fonts:
            console.print("[red]❌[/red] No fonts found")
            logger.warning("No fonts found for PDF generation")
            return

        # Sort fonts alphabetically
        fonts.sort(key=lambda x: x["file"].lower())

        # Generate PDF with ToC
        console.print("[yellow]📄[/yellow] Generating PDF with table of contents...")
        log_pdf_generation(logger, "START", f"Output: {output_path}", font_count)

        try:
            html_content = _create_html_with_toc(fonts)
            css_content = _create_css_with_fonts(fonts)

            font_config = FontConfiguration()
            html = HTML(string=html_content)
            css = CSS(string=css_content, font_config=font_config)

            # Start progress for PDF generation with spinner
            from rich.progress import Progress, SpinnerColumn, TextColumn

            progress = Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            )
            task = progress.add_task("[cyan]Generating PDF...", total=1)

            with progress:
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
                        progress.update(task, advance=1)

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


def _create_html_with_toc(fonts: list) -> str:
    """Create HTML content with table of contents."""
    # Create table of contents
    toc_html = """
    <div class="toc-page">
        <h1>Table of Contents</h1>
        <div class="toc-entries">
    """

    for i, font_info in enumerate(fonts):
        font_name = font_info["name"] or font_info["file"]
        anchor_id = f"font_{i}"
        toc_html += (
            f'<div class="toc-entry"><a href="#{anchor_id}">{font_name}</a></div>'
        )

    toc_html += """
        </div>
    </div>
    """

    # Create font pages
    font_pages = []
    for i, font_info in enumerate(fonts):
        font_family = font_info.get("_registered_name")
        if not font_family:
            continue

        anchor_id = f"font_{i}"

        page_html = f"""
        <div class="font-page" id="{anchor_id}">
            <h1 class="font-header">{font_info["file"]}</h1>

            <div class="font-metadata">
                <p><strong>Font Name:</strong> {font_info["name"]}</p>
                <p><strong>Family:</strong> {font_info["family"]}</p>
                <p><strong>Version:</strong> {font_info["version"]}</p>
                <p><strong>Copyright:</strong> {font_info["copyright"]}</p>
            </div>

            <div class="font-samples">
                <div class="sample-text" style="font-family: '{font_family}', sans-serif; font-size: 36px;">{SAMPLE_TEXT}</div>
                <div class="sample-text" style="font-family: '{font_family}', sans-serif; font-size: 24px;">{SAMPLE_TEXT}</div>
                <div class="sample-text" style="font-family: '{font_family}', sans-serif; font-size: 18px;">{SAMPLE_TEXT}</div>
                <div class="sample-text" style="font-family: '{font_family}', sans-serif; font-size: 14px;">{SAMPLE_TEXT}</div>
            </div>

            <div class="font-paragraph" style="font-family: '{font_family}', sans-serif; font-size: 12px;">
                {PARAGRAPH}
            </div>
        </div>
        """
        font_pages.append(page_html)

    # Create final HTML document
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Font Samples</title>
    </head>
    <body>
        {toc_html}
        {"".join(font_pages)}
    </body>
    </html>
    """

    return html_content


def _create_css_with_fonts(fonts: list) -> str:
    """Create CSS with font declarations and ToC styling."""
    # Create @font-face declarations
    font_faces = []
    for font_info in fonts:
        font_family = font_info.get("_registered_name")
        if font_family:
            font_format = (
                "truetype" if font_info["path"].lower().endswith(".ttf") else "opentype"
            )
            font_url = f"file://{font_info['path']}"

            font_faces.append(f"""
@font-face {{
    font-family: "{font_family}";
    src: url("{font_url}") format("{font_format}");
    font-display: block;
}}
""")

    css_content = f"""
    @page {{
        size: A4;
        margin: 20mm;
    }}

    body {{
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 0;
        font-size: 12px;
        line-height: 1.4;
    }}

    .toc-page {{
        page-break-after: always;
    }}

    .toc-page h1 {{
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 30px;
    }}

    .toc-entries {{
        line-height: 1.2;
    }}

    .toc-entry {{
        margin-bottom: 5px;
    }}

    .toc-entry a {{
        text-decoration: none;
        color: #0066cc;
    }}

    .toc-entry a::after {{
        content: leader('.') target-counter(attr(href), page);
    }}

    .font-page {{
        page-break-after: always;
        margin-bottom: 30px;
    }}

    .font-header {{
        font-size: 24px;
        margin-bottom: 10px;
        color: #444;
    }}

    .font-metadata {{
        padding: 10px 0;
        margin: 10px 0 20px 0;
        border-top: 1px solid #444;
        border-bottom: 1px solid #444;
        line-height: 1.4;
    }}

    .font-metadata p {{
        margin: 5px 0;
    }}

    .font-samples {{
        margin-bottom: 20px;
    }}

    .sample-text {{
        margin: 10px 0;
        line-height: 1.2;
    }}

    .font-paragraph {{
        line-height: 1.4;
        text-align: left;
    }}

    {"".join(font_faces)}
    """

    return css_content
