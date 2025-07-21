import os
import uuid
from fontTools.ttLib import TTFont
from weasyprint import HTML, CSS
from weasyprint.text.fonts import FontConfiguration

SAMPLE_TEXT = "Sphinx of black quartz, judge my vow!"
PARAGRAPH = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. "
    "Sed nisi. Nulla quis sem at nibh elementum imperdiet. "
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~"
)


def extract_font_info(path):
    """Extract font metadata using fontTools."""
    try:
        # Suppress fontTools warnings during initial parsing
        import warnings
        import sys
        from io import StringIO
        
        # Capture and suppress warnings during font parsing
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Also suppress stdout and stderr temporarily to catch fontTools messages
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_output
            
            try:
                # Try to open the font with more lenient parsing
                font = TTFont(path, fontNumber=0, lazy=True)
            finally:
                # Restore stdout and stderr
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        # Validate that the font has required tables
        if "name" not in font:
            print(f"  ⚠️  Font {os.path.basename(path)} missing name table")
            return None

        name = ""
        version = ""
        copyright = ""
        family = ""

        try:
            for record in font["name"].names:
                if record.nameID == 1 and not family:
                    family = record.toStr()
                if record.nameID == 4 and not name:
                    name = record.toStr()
                if record.nameID == 5 and not version:
                    version = record.toStr()
                if record.nameID == 0 and not copyright:
                    copyright = record.toStr()
        except Exception as e:
            print(f"  ⚠️  Error reading name table for {os.path.basename(path)}: {e}")
            # Continue with empty values rather than failing completely

        return {
            "file": os.path.basename(path),
            "path": os.path.abspath(path),  # Use absolute path
            "family": family,
            "name": name,
            "version": version,
            "copyright": copyright,
        }
    except Exception as e:
        print(f"  ❌ Failed to parse font {os.path.basename(path)}: {e}")
        return None


def find_fonts(root):
    """Find all font files in directory tree."""
    fonts = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith((".ttf", ".otf")):
                fonts.append(os.path.join(dirpath, f))
    return fonts


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

        from io import BytesIO
        import warnings
        import sys
        from io import StringIO
        
        # Suppress warnings during PDF generation test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Also suppress stdout and stderr temporarily
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_output
            
            try:
                html.write_pdf(target=BytesIO(), stylesheets=[], font_config=font_config)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

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
            print(f"  ⚠️  Font file not accessible: {os.path.basename(font_path)}")
            return None

        # WeasyPrint can handle fonts directly via CSS @font-face
        # We'll use a unique identifier as the font family name
        font_family = f"font_{uuid.uuid4().hex[:8]}"
        return font_family
    except Exception as e:
        print(f"  ❌ Error registering font {os.path.basename(font_path)}: {e}")
        return None


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
    raw_infos = [extract_font_info(p) for p in font_paths]
    raw_infos = [f for f in raw_infos if f]

    valid_infos = []
    rejected = []
    validation_errors = {}

    print(f"🔍 Total fonts found: {len(raw_infos)}")
    print("⚙️  Processing fonts...")

    for i, info in enumerate(raw_infos):
        if i % 50 == 0:
            print(f"  📝 Processing font {i + 1}/{len(raw_infos)}...")

        # Register font and get family name
        font_family = register_font_for_weasyprint(info["path"])
        if not font_family:
            rejected.append(info["file"])
            validation_errors[info["file"]] = "Failed to register font"
            continue

        # Validate font with WeasyPrint test
        validation_result = validate_font_with_weasyprint(info["path"], font_family)
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
            print(f"  ❌ {info['file']}: {error_msg}")

    # Sort fonts alphabetically
    valid_infos.sort(key=lambda x: x["file"].lower())

    if not valid_infos:
        print("❌ No compatible fonts found to generate PDF.")
        if rejected:
            print("\n📋 Problematic fonts and their issues:")
            for font_file in sorted(rejected):
                error = validation_errors.get(font_file, "Unknown error")
                print(f"  ❌ {font_file}: {error}")
        return

    print(f"📄 Creating PDF with {len(valid_infos)} fonts...")

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

        # Suppress warnings during final PDF generation
        import warnings
        import sys
        from io import StringIO
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            # Also suppress stdout and stderr temporarily
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            captured_output = StringIO()
            sys.stdout = captured_output
            sys.stderr = captured_output
            
            try:
                html.write_pdf(output, stylesheets=[css], font_config=font_config)
            finally:
                sys.stdout = old_stdout
                sys.stderr = old_stderr

        print(f"\n✅ PDF generated: {output}")
        print(f"📊 Fonts included: {len(valid_infos)}")
        print(f"⚠️  Incompatible fonts: {len(rejected)}")

        if rejected:
            print("\n📋 Problematic fonts and their issues:")
            for font_file in sorted(rejected):
                error = validation_errors.get(font_file, "Unknown error")
                print(f"  ❌ {font_file}: {error}")

    except Exception as e:
        error_msg = str(e)
        if not error_msg:
            error_msg = f"Unknown error (type: {type(e).__name__})"
        print(f"\n❌ Error generating PDF: {error_msg}")
        print(
            "💡 This is unexpected since all fonts were validated. Check the error above."
        )


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="🎨 Generate PDF samples of fonts found in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fontsampler /usr/share/fonts          # Sample all fonts in system directory
  fontsampler ~/fonts -o my_samples.pdf # Custom output filename
  fontsampler . -l 10                   # Limit to first 10 fonts (for testing)
  fontsampler . --help                  # Show this help message
        """,
    )

    parser.add_argument(
        "directory", help="Directory containing font files (.ttf, .otf)"
    )

    parser.add_argument(
        "-o",
        "--output",
        default="font_samples.pdf",
        help="Output PDF filename (default: font_samples.pdf)",
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



    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"❌ Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    if not os.path.isdir(args.directory):
        print(f"❌ Error: '{args.directory}' is not a directory")
        sys.exit(1)

    fonts = find_fonts(args.directory)
    if not fonts:
        print(f"🔍 No font files (.ttf, .otf) found in '{args.directory}'")
        sys.exit(1)

    # Apply font limit if specified
    if args.limit and len(fonts) > args.limit:
        print(f"📝 Limiting to first {args.limit} fonts (found {len(fonts)})")
        fonts = fonts[: args.limit]

    generate_pdf_with_toc(fonts, args.output)
