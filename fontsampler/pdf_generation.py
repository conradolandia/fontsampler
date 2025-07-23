"""
PDF generation functionality for FontSampler.
"""

import gc
import os
import sys
from io import StringIO

from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)
from weasyprint import CSS, HTML
from weasyprint.text.fonts import FontConfiguration

from .config import LEGACY_BATCH_SIZE, PARAGRAPH, SAMPLE_TEXT
from .font_discovery import extract_font_info
from .font_validation import register_font_for_weasyprint, validate_font_with_weasyprint
from .warning_capture import (
    capture_warnings_context,
    console,
    display_captured_warnings,
    stderr_capture_handler,
)


def create_css_for_fonts(font_infos):
    """Create CSS with @font-face declarations for all fonts."""
    css_rules = []

    for info in font_infos:
        font_family = info.get("_registered_name")
        if font_family:
            # Determine format based on file extension
            font_format = (
                "truetype" if info["path"].lower().endswith(".ttf") else "opentype"
            )

            # Use file:// protocol for local files
            font_url = f"file://{info['path']}"

            css_rules.append(f"""
@font-face {{
    font-family: "{font_family}";
    src: url("{font_url}") format("{font_format}");
    font-display: block;
}}
""")

    return "\n".join(css_rules)


def create_html_content(font_infos):
    """Create HTML content for all font samples."""
    toc_entries = []
    font_pages = []

    for i, info in enumerate(font_infos):
        font_family = info.get("_registered_name")
        if not font_family:
            continue

        # Create a safe anchor ID from the filename
        anchor_id = f"font_{i}_{info['file'].replace('.', '_').replace(' ', '_')}"
        toc_entries.append((info["name"] or info["file"], anchor_id))

        # Create font sample page with anchor
        page_html = f"""
        <div class="font-page" id="{anchor_id}">
            <h1 class="font-header">{info["file"]}</h1>

            <div class="font-metadata">
                <p><strong>Font Name:</strong> {info["name"]}</p>
                <p><strong>Family:</strong> {info["family"]}</p>
                <p><strong>Version:</strong> {info["version"]}</p>
                <p><strong>Copyright:</strong> {info["copyright"]}</p>
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

    # Create table of contents with clickable links
    toc_html = """
    <div class="toc-page">
        <h1>Table of Contents</h1>
        <div class="toc-entries">
    """

    for name, anchor_id in toc_entries:
        toc_html += f'<div class="toc-entry"><a href="#{anchor_id}" class="toc-name">{name}</a></div>'

    toc_html += """
        </div>
    </div>
    """

    # Combine everything
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Font Samples</title>
        <style>
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

            .toc-name {{
                text-decoration: none;
                color: #0066cc;
            }}

            .toc-name:hover {{
                text-decoration: underline;
            }}

            .toc-name::after {{
                content: leader('.') target-counter(attr(href), page);
            }}
        </style>
    </head>
    <body>
        {toc_html}
        {"".join(font_pages)}
    </body>
    </html>
    """

    return html_content


def generate_pdf_with_toc(font_paths, output="font_samples.pdf"):
    """Generate PDF using WeasyPrint"""
    console.print(
        f"[bold blue]🔍[/bold blue] Total fonts found: [cyan]{len(font_paths)}[/cyan]"
    )
    console.print("[bold yellow]⚙️[/bold yellow] Extracting font information...")

    # Extract font information with progress bar and memory management
    raw_infos = []

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Extracting font info...", total=len(font_paths))

        for i, path in enumerate(font_paths):
            progress.update(
                task, description=f"[cyan]Extracting {os.path.basename(path)}..."
            )

            try:
                info = extract_font_info(path)
                if info:
                    raw_infos.append(info)
            except Exception as e:
                console.print(
                    f"  [bold red]❌[/bold red] Error processing [red]{os.path.basename(path)}[/red]: {e}"
                )

            # Force garbage collection every batch_size fonts to prevent memory buildup
            if (i + 1) % LEGACY_BATCH_SIZE == 0:
                gc.collect()

            progress.advance(task)

    console.print("[bold yellow]⚙️[/bold yellow] Processing fonts...")

    valid_infos = []
    rejected = []
    validation_errors = {}

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Processing fonts...", total=len(raw_infos))

        for i, info in enumerate(raw_infos):
            progress.update(task, description=f"[cyan]Processing {info['file']}...")

            try:
                # Register font and get family name
                font_family = register_font_for_weasyprint(info["path"])
                if not font_family:
                    rejected.append(info["file"])
                    validation_errors[info["file"]] = "Failed to register font"
                    progress.advance(task)
                    continue

                # Validate font with WeasyPrint test
                validation_result = validate_font_with_weasyprint(
                    info["path"], font_family
                )
                if validation_result is True:
                    info["_registered_name"] = font_family
                    valid_infos.append(info)
                else:
                    rejected.append(info["file"])
                    error_msg = (
                        validation_result[1]
                        if isinstance(validation_result, tuple)
                        else str(validation_result)
                    )
                    validation_errors[info["file"]] = error_msg
                    console.print(
                        f"  [bold red]❌[/bold red] [red]{info['file']}[/red]: {error_msg}"
                    )
            except Exception as e:
                rejected.append(info["file"])
                validation_errors[info["file"]] = f"Unexpected error: {e}"
                console.print(
                    f"  [bold red]❌[/bold red] [red]{info['file']}[/red]: Unexpected error: {e}"
                )

            # Force garbage collection every batch_size fonts to prevent memory buildup
            if (i + 1) % LEGACY_BATCH_SIZE == 0:
                gc.collect()

            progress.advance(task)

    # Sort fonts alphabetically
    valid_infos.sort(key=lambda x: x["file"].lower())

    if not valid_infos:
        console.print(
            "[bold red]❌[/bold red] No compatible fonts found to generate PDF."
        )

        # Display any captured warnings
        display_captured_warnings()

        if rejected:
            console.print(
                "\n[bold yellow]📋[/bold yellow] Problematic fonts and their issues:"
            )
            for font_file in sorted(rejected):
                error = validation_errors.get(font_file, "Unknown error")
                console.print(f"  [red]❌[/red] [red]{font_file}[/red]: {error}")
        return

    console.print(
        f"[bold green]📄[/bold green] Creating PDF with [cyan]{len(valid_infos)}[/cyan] fonts..."
    )

    # Create HTML content
    html_content = create_html_content(valid_infos)

    # Create CSS with font declarations
    css_content = create_css_for_fonts(valid_infos)

    # Configure font handling
    font_config = FontConfiguration()

    # Generate PDF
    try:
        html = HTML(string=html_content)
        css = CSS(string=css_content, font_config=font_config)

        # Start progress for PDF generation
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
                    html.write_pdf(output, stylesheets=[css], font_config=font_config)
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
            f"\n[bold green]✅[/bold green] PDF generated: [cyan]{output}[/cyan]"
        )
        console.print(
            f"[bold blue]📊[/bold blue] Fonts included: [cyan]{len(valid_infos)}[/cyan]"
        )
        console.print(
            f"[bold yellow]⚠️[/bold yellow] Incompatible fonts: [cyan]{len(rejected)}[/cyan]"
        )

        # Display any captured warnings
        display_captured_warnings()

        if rejected:
            console.print(
                "\n[bold yellow]📋[/bold yellow] Problematic fonts and their issues:"
            )
            for font_file in sorted(rejected):
                error = validation_errors.get(font_file, "Unknown error")
                console.print(f"  [red]❌[/red] [red]{font_file}[/red]: {error}")

    except Exception as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = f"Unknown error (type: {type(e).__name__})"
        console.print(
            f"\n[bold red]❌[/bold red] Error generating PDF: [red]{error_msg}[/red]"
        )
        console.print(
            "[yellow]💡[/yellow] This is unexpected since all fonts were validated. Check the error above."
        )
