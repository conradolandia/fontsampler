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


def draw_wrapped_text(canvas, text, x, y, font_name, font_size, max_width, line_height=None):
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


def register_font_for_pdf(font_path):
    temp_name = "F" + uuid.uuid4().hex
    temp_copy = os.path.join(mkdtemp(), os.path.basename(font_path))
    copyfile(font_path, temp_copy)
    pdfmetrics.registerFont(RLTTFont(temp_name, temp_copy))
    return temp_name


def create_sample_pages(font_infos):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    toc_entries = []

    for i, info in enumerate(font_infos):
        font_name = register_font_for_pdf(info["path"])
        page_num = i + 2  # +1 for zero-based index, +1 because TOC is on page 1

        toc_entries.append((info["name"] or info["file"], page_num))

        # Header with text wrapping
        c.setFont("Helvetica-Bold", 32)
        c.drawString(20 * mm, height - 25 * mm, f"{info['file']}")
        
        # Font metadata with wrapping
        y = height - 35 * mm
        max_width = width - 40 * mm  # Leave margins
        
        y = draw_wrapped_text(c, f"Font Name: {info['name']}", 20 * mm, y, "Helvetica", 9, max_width)
        y = draw_wrapped_text(c, f"Family: {info['family']}", 20 * mm, y, "Helvetica", 9, max_width)
        y = draw_wrapped_text(c, f"Version: {info['version']}", 20 * mm, y, "Helvetica", 9, max_width)
        y = draw_wrapped_text(c, f"Copyright: {info['copyright']}", 20 * mm, y, "Helvetica", 9, max_width)

        # Font samples
        y -= 20 * mm  # Add some space after metadata
        for size in [36, 24, 18, 14]:
            y = draw_wrapped_text(c, SAMPLE_TEXT, 20 * mm, y, font_name, size, max_width, size + 8)

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
    c.drawString(20 * mm, height - 30 * mm, "Tabla de Contenido")

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
    font_infos = [extract_font_info(p) for p in font_paths]
    font_infos = [f for f in font_infos if f]

    content_pdf, toc_entries = create_sample_pages(font_infos)
    toc_pdf = create_toc_page(toc_entries)

    merge_pdfs(toc_pdf, content_pdf, output)
    print(f"PDF generado: {output}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uso: python generate_font_samples.py <directorio>")
        exit(1)
    root_dir = sys.argv[1]
    fonts = find_fonts(root_dir)
    generate_pdf_with_toc(fonts)
