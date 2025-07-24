"""
Template management for FontSampler.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from jinja2 import Environment, FileSystemLoader, Template
except ImportError:
    Template = None


class TemplateManager:
    """Manages HTML and CSS templates for PDF generation."""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize template manager.

        Args:
            template_dir: Directory containing template files. If None, uses default location.
        """
        self.template_dir = template_dir or self._get_default_template_dir()
        self._env = self._create_environment()

    def _get_default_template_dir(self) -> str:
        """Get the default template directory path."""
        # Look for templates directory in current directory, then in package directory
        current_dir = Path.cwd() / "templates"
        if current_dir.exists():
            return str(current_dir)

        package_dir = Path(__file__).parent.parent / "templates"
        if package_dir.exists():
            return str(package_dir)

        # Return current directory as fallback
        return str(Path.cwd() / "templates")

    def _create_environment(self) -> Optional[Environment]:
        """Create Jinja2 environment."""
        if Template is None:
            return None

        if os.path.exists(self.template_dir):
            return Environment(
                loader=FileSystemLoader(self.template_dir),
                autoescape=False,  # We're generating HTML/CSS, not web content
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return None

    def render_html(self, fonts: List[Dict[str, Any]], **kwargs) -> str:
        """
        Render HTML template with font data.

        Args:
            fonts: List of font information dictionaries
            **kwargs: Additional template variables

        Returns:
            Rendered HTML string
        """
        if self._env is None:
            return self._fallback_html(fonts, **kwargs)

        try:
            template = self._env.get_template("html_template.jinja")
            return template.render(fonts=fonts, **kwargs)
        except Exception as e:
            print(f"Warning: Failed to load HTML template: {e}")
            return self._fallback_html(fonts, **kwargs)

    def render_css(self, fonts: List[Dict[str, Any]], **kwargs) -> str:
        """
        Render CSS template with font data.

        Args:
            fonts: List of font information dictionaries
            **kwargs: Additional template variables

        Returns:
            Rendered CSS string
        """
        if self._env is None:
            return self._fallback_css(fonts, **kwargs)

        try:
            template = self._env.get_template("css_template.css")
            return template.render(fonts=fonts, **kwargs)
        except Exception as e:
            print(f"Warning: Failed to load CSS template: {e}")
            return self._fallback_css(fonts, **kwargs)

    def _fallback_html(self, fonts: List[Dict[str, Any]], **kwargs) -> str:
        """Fallback HTML generation when templates are not available."""
        from .config import PARAGRAPH, SAMPLE_SIZES, SAMPLE_TEXT

        # Create table of contents
        toc_html = """
        <div class="toc-page">
            <h1>Table of Contents</h1>
            <div class="toc-entries">
        """

        for i, font_info in enumerate(fonts):
            font_name = font_info.get("name") or font_info.get("file", "")
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

            # Generate sample text for each size
            sample_texts = []
            for size in SAMPLE_SIZES:
                sample_texts.append(
                    f'<div class="sample-text" style="font-family: \'{font_family}\', sans-serif; font-size: {size}px;">{SAMPLE_TEXT}</div>'
                )

            page_html = f"""
            <div class="font-page" id="{anchor_id}">
                <h1 class="font-header">{font_info.get("file", "")}</h1>

                <div class="font-metadata">
                    <p><strong>Font Name:</strong> {font_info.get("name", "N/A")}</p>
                    <p><strong>Family:</strong> {font_info.get("family", "N/A")}</p>
                    <p><strong>Version:</strong> {font_info.get("version", "N/A")}</p>
                    <p><strong>Copyright:</strong> {font_info.get("copyright", "N/A")}</p>
                </div>

                <div class="font-samples">
                    {"".join(sample_texts)}
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

    def _fallback_css(self, fonts: List[Dict[str, Any]], **kwargs) -> str:
        """Fallback CSS generation when templates are not available."""
        from .config import (
            PDF_FONT_HEADER_SIZE,
            PDF_METADATA_FONT_SIZE,
            PDF_PAGE_MARGIN,
            PDF_PAGE_SIZE,
            PDF_PARAGRAPH_LINE_HEIGHT,
            PDF_SAMPLE_TEXT_LINE_HEIGHT,
        )

        # Create @font-face declarations
        font_faces = []
        for font_info in fonts:
            font_family = font_info.get("_registered_name")
            if font_family:
                font_format = (
                    "truetype"
                    if font_info.get("path", "").lower().endswith(".ttf")
                    else "opentype"
                )
                font_url = f"file://{font_info.get('path', '')}"

                font_faces.append(f"""
@font-face {{
    font-family: "{font_family}";
    src: url("{font_url}") format("{font_format}");
    font-display: block;
}}
""")

        css_content = f"""
        @page {{
            size: {PDF_PAGE_SIZE};
            margin: {PDF_PAGE_MARGIN};
        }}

        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 0;
            font-size: {PDF_METADATA_FONT_SIZE};
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
            font-size: {PDF_FONT_HEADER_SIZE};
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
            line-height: {PDF_SAMPLE_TEXT_LINE_HEIGHT};
        }}

        .font-paragraph {{
            line-height: {PDF_PARAGRAPH_LINE_HEIGHT};
            text-align: left;
        }}

        {"".join(font_faces)}
        """

        return css_content
