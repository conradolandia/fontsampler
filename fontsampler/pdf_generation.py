"""
PDF generation functionality for FontSampler.
"""

from .config import PARAGRAPH, SAMPLE_TEXT


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
