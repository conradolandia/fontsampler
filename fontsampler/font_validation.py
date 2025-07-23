"""
Font validation and registration functionality for FontSampler.
"""

import os
import sys
import uuid
from io import BytesIO, StringIO

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from .warning_capture import capture_warnings_context, console


def validate_font_with_weasyprint(font_path, font_family):
    """Test if a font can be loaded and used by WeasyPrint for PDF generation."""
    try:
        # Create a minimal HTML with the font
        test_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                @font-face {{
                    font-family: "{font_family}";
                    src: url("file://{font_path}") format("truetype");
                }}
                .test {{
                    font-family: "{font_family}", sans-serif;
                    font-size: 12px;
                }}
            </style>
        </head>
        <body>
            <div class="test">Test text</div>
        </body>
        </html>
        """

        # Try to actually generate a PDF with this font
        html = HTML(string=test_html)
        font_config = FontConfiguration()

        # Capture warnings during PDF generation test
        with capture_warnings_context():
            # Also suppress stdout temporarily
            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output

            try:
                html.write_pdf(
                    target=BytesIO(), stylesheets=[], font_config=font_config
                )
            finally:
                sys.stdout = old_stdout

        # If we get here, the font works with PDF generation
        return True

    except Exception as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = f"PDF generation failed (type: {type(e).__name__})"
        return False, error_msg


def register_font_for_weasyprint(font_path):
    """Register font for WeasyPrint, return font family name."""
    try:
        # Validate the font file exists and is readable
        if not os.path.exists(font_path) or not os.access(font_path, os.R_OK):
            console.print(
                f"  [bold yellow]⚠️[/bold yellow] Font file not accessible: [yellow]{os.path.basename(font_path)}[/yellow]"
            )
            return None

        # WeasyPrint can handle fonts directly via CSS @font-face
        # We'll use a unique identifier as the font family name
        font_family = f"font_{uuid.uuid4().hex[:8]}"
        return font_family
    except Exception as e:
        console.print(
            f"  [bold red]❌[/bold red] Error registering font [red]{os.path.basename(font_path)}[/red]: {e}"
        )
        return None
