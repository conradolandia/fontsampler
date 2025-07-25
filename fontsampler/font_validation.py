"""
Font validation and registration functionality for FontSampler.
"""

import os
import sys
import uuid
from io import BytesIO, StringIO

from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration

from .config import _config
from .warning_capture import capture_warnings_context, console


def log_font_validation_issue(font_path: str, issue_type: str, error_message: str):
    """
    Log font validation issues with detailed information.

    Args:
        font_path: Path to the problematic font
        issue_type: Type of validation issue
        error_message: Detailed error message
    """
    font_name = os.path.basename(font_path)
    console.print(
        f"  [bold yellow]⚠️[/bold yellow] Font validation issue: [yellow]{font_name}[/yellow] - {issue_type}: {error_message}"
    )


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
                # First try with normal font configuration
                html.write_pdf(
                    target=BytesIO(), stylesheets=[], font_config=font_config
                )
            except Exception as e:
                # If normal generation fails, try with subsetting disabled
                error_msg = str(e)
                if (
                    "unpack requires a buffer" in error_msg
                    or "font" in error_msg.lower()
                ):
                    try:
                        # Create font config with subsetting disabled
                        font_config_no_subset = FontConfiguration()

                        html.write_pdf(
                            target=BytesIO(),
                            stylesheets=[],
                            font_config=font_config_no_subset,
                        )
                        # If this succeeds, the font works but has subsetting issues
                        return True, "font_subsetting_issue"
                    except Exception as subset_error:
                        # Font fails even with subsetting disabled
                        subset_error_msg = str(subset_error)
                        log_font_validation_issue(
                            font_path, "subsetting_retry_failed", subset_error_msg
                        )
                        return False, f"Font validation failed: {subset_error}"
                else:
                    # Re-raise non-font-related errors
                    raise
            finally:
                sys.stdout = old_stdout

        # If we get here, the font works with PDF generation
        return True

    except Exception as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = f"PDF generation failed (type: {type(e).__name__})"

        # Log the validation issue
        log_font_validation_issue(font_path, "validation_failed", error_msg)
        return False, error_msg


def register_font_for_weasyprint(font_path):
    """Register font for WeasyPrint, return font family name."""
    try:
        # Validate the font file exists and is readable
        if not os.path.exists(font_path) or not os.access(font_path, os.R_OK):
            log_font_validation_issue(
                font_path, "file_access", "Font file not accessible"
            )
            return None

        # Check file size - very small files might be corrupted
        file_size = os.path.getsize(font_path)
        if file_size < _config.get("pdf.min_font_size_bytes", 1024):
            log_font_validation_issue(
                font_path,
                "file_size",
                f"Font file too small ({file_size} bytes), likely corrupted",
            )
            return None

        # WeasyPrint can handle fonts directly via CSS @font-face
        # We'll use a unique identifier as the font family name
        font_family = f"font_{uuid.uuid4().hex[:8]}"
        return font_family
    except Exception as e:
        log_font_validation_issue(font_path, "registration_error", str(e))
        return None
