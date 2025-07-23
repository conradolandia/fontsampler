"""
FontSampler - Generate PDF font catalog

A Python package for generating PDF samples of fonts found in a directory.
"""

__version__ = "0.1.0"
__author__ = "conradolandia <andresconrado@gmail.com>"

from .cli import main
from .font_discovery import extract_font_info, find_fonts
from .pdf_generation import generate_pdf_with_toc

__all__ = [
    "main",
    "generate_pdf_with_toc",
    "find_fonts",
    "extract_font_info",
]
