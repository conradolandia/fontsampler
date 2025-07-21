import os
import io
import uuid
from shutil import copyfile
from tempfile import mkdtemp
from fontTools.ttLib import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont as RLTTFont

from PyPDF2 import PdfReader, PdfWriter

SAMPLE_TEXT = "Sphinx of black quartz, judge my vow!"
PARAGRAPH = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. "
    "Sed nisi. Nulla quis sem at nibh elementum imperdiet. "
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~"
)


def wrap_text(text, font_name, font_size, max_width):
    """Wrap text to fit within max_width using the specified font."""
    if not text:
        return [""]

    # Create a temporary canvas to measure text
    temp_canvas = canvas.Canvas(io.BytesIO())
    temp_canvas.setFont(font_name, font_size)

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + " " + word if current_line else word
        test_width = temp_canvas.stringWidth(test_line, font_name, font_size)

        if test_width <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
                current_line = word
            else:
                # Word is too long, break it
                lines.append(word)

    if current_line:
        lines.append(current_line)

    return lines if lines else [""]


def draw_wrapped_text(
    canvas, text, x, y, font_name, font_size, max_width, line_height=None
):
    """Draw text with automatic wrapping."""
    if line_height is None:
        line_height = font_size + 2

    lines = wrap_text(text, font_name, font_size, max_width)
    for line in lines:
        canvas.setFont(font_name, font_size)
        canvas.drawString(x, y, line)
        y -= line_height

    return y  # Return the new y position


def extract_font_info(path):
    try:
        font = TTFont(path, fontNumber=0)
        name = ""
        version = ""
        copyright = ""
        family = ""
        for record in font["name"].names:
            if record.nameID == 1 and not family:
                family = record.toStr()
            if record.nameID == 4 and not name:
                name = record.toStr()
            if record.nameID == 5 and not version:
                version = record.toStr()
            if record.nameID == 0 and not copyright:
                copyright = record.toStr()
        return {
            "file": os.path.basename(path),
            "path": path,
            "family": family,
            "name": name,
            "version": version,
            "copyright": copyright,
        }
    except Exception:
        return None


def find_fonts(root):
    fonts = []
    for dirpath, _, filenames in os.walk(root):
        for f in filenames:
            if f.lower().endswith((".ttf", ".otf")):
                fonts.append(os.path.join(dirpath, f))
    return fonts


def convert_otf_to_ttf(otf_path):
    """Convert OpenType font to TrueType format if possible."""
    try:
        # Load the font
        font = TTFont(otf_path)
        
        # Check if it's an OpenType font with PostScript outlines
        if 'CFF ' in font or 'CFF2' in font:
            # Create a temporary file for the converted font
            temp_dir = mkdtemp()
            ttf_path = os.path.join(temp_dir, os.path.splitext(os.path.basename(otf_path))[0] + '.ttf')
            
            # For CFF fonts, we need to convert them to TrueType
            # This is a simplified approach - we'll try to save as TTF
            # but this may not work for all CFF fonts
            try:
                # Remove OpenType flavor to make it a pure TTF
                font.flavor = None
                font.save(ttf_path)
                return ttf_path
            except Exception:
                # If direct save fails, try a different approach
                # For now, we'll return None and let ReportLab handle it
                return None
        else:
            # Font is already TrueType or doesn't need conversion
            return None
    except Exception as e:
        print(f"Error converting font {os.path.basename(otf_path)}: {e}")
        return None


def register_font_for_pdf(font_path):
    """Register a font for PDF generation, return (font_name, was_converted) or None if incompatible."""
    try:
        temp_name = "F" + uuid.uuid4().hex
        temp_copy = os.path.join(mkdtemp(), os.path.basename(font_path))
        copyfile(font_path, temp_copy)
        pdfmetrics.registerFont(RLTTFont(temp_name, temp_copy))
        return temp_name, False
    except Exception as e:
        # If direct registration fails, try converting OpenType to TrueType
        if font_path.lower().endswith('.otf'):
            print(f"Direct registration failed for {os.path.basename(font_path)}, attempting conversion...")
            converted_path = convert_otf_to_ttf(font_path)
            if converted_path:
                try:
                    temp_name = "F" + uuid.uuid4().hex
                    pdfmetrics.registerFont(RLTTFont(temp_name, converted_path))
                    print(f"Successfully converted and registered {os.path.basename(font_path)}")
                    return temp_name, True
                except Exception as conv_e:
                    print(f"Conversion failed for {os.path.basename(font_path)}: {conv_e}")
        
        # Log the original error for debugging
        print(f"Error registering font {os.path.basename(font_path)}: {e}")
        return None


def create_sample_pages(font_infos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    toc_entries = []

    for i, info in enumerate(font_infos):
        font_name = info.get("_registered_name")
        if not font_name:
            continue

        page_num = len(toc_entries) + 2
        toc_entries.append((info["name"] or info["file"], page_num))

        # Header with text wrapping
        c.setFont("Helvetica-Bold", 24)
        c.drawString(20 * mm, height - 25 * mm, f"{info['file']}")

        # Font metadata with wrapping
        y = height - 35 * mm
        max_width = width - 40 * mm  # Leave margins

        c.setFont("Helvetica", 12)
        y = draw_wrapped_text(
            c, f"Font Name: {info['name']}", 20 * mm, y, "Helvetica", 9, max_width
        )
        y = draw_wrapped_text(
            c, f"Family: {info['family']}", 20 * mm, y, "Helvetica", 9, max_width
        )
        y = draw_wrapped_text(
            c, f"Version: {info['version']}", 20 * mm, y, "Helvetica", 9, max_width
        )
        y = draw_wrapped_text(
            c, f"Copyright: {info['copyright']}", 20 * mm, y, "Helvetica", 9, max_width
        )

        # Font samples
        y -= 20 * mm  # Add some space after metadata
        for size in [36, 24, 18, 14]:
            y = draw_wrapped_text(
                c, SAMPLE_TEXT, 20 * mm, y, font_name, size, max_width, size + 8
            )

        # Paragraph with proper wrapping
        y -= 10 * mm  # Add space before paragraph
        y = draw_wrapped_text(c, PARAGRAPH, 20 * mm, y, font_name, 12, max_width, 14)

        c.showPage()

    c.save()
    buffer.seek(0)
    return buffer, toc_entries


def create_toc_page(toc_entries):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, height - 30 * mm, "Table of Contents")

    y = height - 45 * mm
    c.setFont("Helvetica", 12)
    max_name_width = width - 80 * mm  # Leave space for page number

    for name, page in toc_entries:
        if y < 20 * mm:
            c.showPage()
            y = height - 30 * mm

        # Wrap long font names
        lines = wrap_text(name, "Helvetica", 12, max_name_width)
        for line in lines:
            if y < 20 * mm:
                c.showPage()
                y = height - 30 * mm
            c.drawString(25 * mm, y, line)
            c.drawRightString(width - 25 * mm, y, f"{page}")
            y -= 8 * mm
        y -= 2 * mm  # Extra space between entries

    c.save()
    buffer.seek(0)
    return buffer


def merge_pdfs(toc_pdf, content_pdf, output):
    reader_toc = PdfReader(toc_pdf)
    reader_content = PdfReader(content_pdf)

    writer = PdfWriter()
    for page in reader_toc.pages:
        writer.add_page(page)
    for page in reader_content.pages:
        writer.add_page(page)

    with open(output, "wb") as f:
        writer.write(f)


def generate_pdf_with_toc(font_paths, output="font_samples.pdf"):
    raw_infos = [extract_font_info(p) for p in font_paths]
    raw_infos = [f for f in raw_infos if f]

    valid_infos = []
    rejected = []
    converted_count = 0

    print(f"→ Total fonts found: {len(raw_infos)}")
    print("→ Processing fonts...")
    
    for i, info in enumerate(raw_infos):
        if i % 50 == 0:  # Progress indicator every 50 fonts
            print(f"  Processing font {i+1}/{len(raw_infos)}...")
            
        result = register_font_for_pdf(info["path"])
        if result:
            font_name, was_converted = result
            info["_registered_name"] = font_name
            valid_infos.append(info)
            if was_converted:
                converted_count += 1
        else:
            rejected.append(info["file"])

    # Sort fonts alphabetically by filename
    valid_infos.sort(key=lambda x: x["file"].lower())

    if not valid_infos:
        print("⛔ No compatible fonts found to generate PDF.")
        return

    print(f"→ Creating PDF with {len(valid_infos)} fonts...")
    content_pdf, toc_entries = create_sample_pages(valid_infos)
    toc_pdf = create_toc_page(toc_entries)
    merge_pdfs(toc_pdf, content_pdf, output)

    print(f"\n✅ PDF generated: {output}")
    print(f"→ Fonts included: {len(valid_infos)}")
    print(f"→ Fonts converted from OpenType: {converted_count}")
    print(f"→ Incompatible fonts: {len(rejected)}")

    if rejected:
        print("🗒️  Rejected fonts:")
        for f in sorted(rejected):
            print(f"  - {f}")


if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate PDF samples of fonts found in a directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  fontsampler /usr/share/fonts          # Sample all fonts in system directory
  fontsampler ~/fonts -o my_samples.pdf # Custom output filename
  fontsampler . --help                   # Show this help message
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

    args = parser.parse_args()

    if not os.path.exists(args.directory):
        print(f"Error: Directory '{args.directory}' does not exist")
        sys.exit(1)

    if not os.path.isdir(args.directory):
        print(f"Error: '{args.directory}' is not a directory")
        sys.exit(1)

    fonts = find_fonts(args.directory)
    if not fonts:
        print(f"No font files (.ttf, .otf) found in '{args.directory}'")
        sys.exit(1)

    generate_pdf_with_toc(fonts, args.output)
