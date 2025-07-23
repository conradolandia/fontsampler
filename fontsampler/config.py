"""
Configuration constants for FontSampler.
"""

# Font processing limits
MAX_FONTS = 1000

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

# Batch size for memory management
BATCH_SIZE = 100
