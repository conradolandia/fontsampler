"""
Configuration constants for FontSampler.
"""

from pathlib import Path

# Sample text for font display
SAMPLE_TEXT = "Sphinx of black quartz, judge my vow!"

# Paragraph text with full character set
PARAGRAPH = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
    "Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. "
    "Sed nisi. Nulla quis sem at nibh elementum imperdiet. "
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~"
)

# Default output filename
DEFAULT_OUTPUT = "font_samples.pdf"

# Supported font extensions
FONT_EXTENSIONS = (".ttf", ".otf")

# Streaming and memory management settings
DEFAULT_BATCH_SIZE = 50
MAX_BATCH_SIZE = 200
MIN_BATCH_SIZE = 10
UPDATE_INTERVAL = 100  # Update peak memory every 100 fonts
PROCESSING_INTERVAL = 500  # Process fonts every 500 fonts
MEMORY_THRESHOLD = 0.7  # 70% memory usage threshold
ESTIMATED_MEMORY_PER_FONT = 5.0  # MB per font

# PDF generation settings

# Logging settings
LOG_LEVEL = "INFO"
LOG_FILE = None  # None for default location
LOG_MAX_AGE_DAYS = 30  # Keep logs for 30 days
LOG_DIR = Path.cwd() / "logs"
