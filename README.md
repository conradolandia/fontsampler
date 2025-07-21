# Font Sampler

A Python script that generates PDF samples of fonts found in a directory. The script creates a font catalog with metadata, sample text at different sizes, and a table of contents.

## Features

- **Font Discovery**: Automatically finds `.ttf` and `.otf` fonts in a directory
- **Font Metadata**: Extracts and displays font name, family, version, and copyright information
- **Sample Text**: Shows fonts at multiple sizes (36, 24, 18, 14pt) with pangram text
- **Character Set**: Displays full alphabet, numbers, and special characters
- **Text Wrapping**: All text properly wraps to stay within page boundaries
- **Table of Contents**: Generated automatically with page numbers
- **Font Support**: Uses WeasyPrint with Pango for TrueType, OpenType and PostScript font support
- **Rich UI**: Enhanced visual output with progress bars, colored status messages, and real-time feedback

## Requirements

- [Pixi](https://pixi.sh/) for dependency management
- Python 3.6+
- **System Libraries**: Cairo graphics library (required by WeasyPrint for PDF generation)

### System Dependencies

On most Linux distributions, Cairo is included by default. If you encounter issues, you may need to install it:

**Ubuntu/Debian:**
```bash
sudo apt-get install libcairo2-dev
```

**Arch Linux:**
```bash
sudo pacman -S cairo
```

**Fedora/RHEL:**
```bash
sudo dnf install cairo-devel
```

## Installation

1. Clone or download this repository
2. Install Pixi if you haven't already:
   ```bash
   curl -fsSL https://pixi.sh/install.sh | bash
   ```
3. Install dependencies:
   ```bash
   pixi install
   ```

## Usage

```bash
pixi run python fontsampler.py <directory_path>
```

### Example

```bash
pixi run python fontsampler.py /usr/share/fonts
```

This will scan the specified directory for fonts and generate a `font_samples.pdf` file in the current directory.

## Building Standalone Binary

To create a standalone executable:

```bash
# Install dependencies first
pixi install

# Build the binary
pixi run build
```

This will create a `fontsampler` executable in the `dist/` directory.

### Build Options

- `pixi run build` - Standard build using spec file
- `pixi run build-debug` - Build with debug information
- `pixi run build-clean` - Clean build (removes previous build artifacts)
- `pixi run install` - Copy the built binary to `$HOME/.local/bin` (overwrites existing)
- `pixi run build-install` - Build and install the binary to `$HOME/.local/bin` (overwrites existing)

## Output

The generated PDF contains:
- **Table of Contents**: Lists all fonts with page numbers
- **Font Pages**: One page per font showing:
  - Font filename (large header)
  - Font metadata (name, family, version, copyright)
  - Sample text at multiple sizes
  - Full character set paragraph

## Sample Text

The script uses the pangram "Sphinx of black quartz, judge my vow!" for font samples, plus a comprehensive character set including:
- Uppercase and lowercase letters
- Numbers 0-9
- Special characters and symbols

## Font Support

This version uses WeasyPrint with Cairo and Pango for font rendering, providing:
- **OpenType support**: Direct handling of `.otf` files
- **PostScript font support**: Handles CFF and CFF2 outlines
- **TrueType support**: Full support for `.ttf` files
- **Font feature support**: Automatic detection of bold, italic, and other variants
- **PDF generation**: High-quality PDF output using Cairo graphics library

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details. 
