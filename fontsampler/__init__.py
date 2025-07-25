"""
FontSampler - Generate PDF font catalog

A Python package for generating PDF samples of fonts found in a directory.
"""

__version__ = "0.1.0"
__author__ = "conradolandia <andresconrado@gmail.com>"

from .cli import main
from .font_discovery import extract_font_info
from .streaming_processor import process_fonts_with_streaming

__all__ = [
    "main",
    "extract_font_info",
    "process_fonts_with_streaming",
]
