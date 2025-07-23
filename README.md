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

### Command Line

```bash
pixi run python main.py <directory_path>
```

### Example

```bash
pixi run python main.py /usr/share/fonts
```

### As a Library

The package can also be used as a library in other Python projects:

```python
from fontsampler import find_fonts, generate_pdf_with_toc

# Find fonts in a directory
fonts = find_fonts("/path/to/fonts")

# Generate PDF catalog
generate_pdf_with_toc(fonts, "output.pdf")
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

## Project Structure

The project follows modern Python package structure best practices:

```
fontsampler/
├── main.py                 # Entry point
├── fontsampler/            # Main package directory
│   ├── __init__.py         # Package initialization
│   ├── config.py           # Configuration constants
│   ├── warning_capture.py  # Warning capture and display
│   ├── font_discovery.py   # Font finding and metadata
│   ├── font_validation.py  # Font validation and registration
│   ├── pdf_generation.py   # HTML/CSS generation and PDF creation
│   └── cli.py              # Command-line interface
├── dist/                   # Build output
├── build/                  # Build artifacts
├── pixi.toml              # Dependency management
├── fontsampler.spec       # PyInstaller configuration
└── README.md              # Documentation
```

This structure follows [Python packaging best practices](https://pythonpackaging.info/02-Package-Structure.html) and makes the codebase:
- **Professional**: Proper package structure for distribution
- **Maintainable**: Clear separation of concerns
- **Testable**: Easy to add unit tests
- **Importable**: Can be used as a library in other projects

## Development

This project uses [Pixi](https://pixi.sh/) for dependency management and environment setup.

### Setup

1. Install Pixi: https://pixi.sh/install
2. Clone the repository
3. Run `pixi install` to set up the environment
4. Run `pixi run python main.py --help` to test the installation

### Code Quality

The project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, with [pre-commit](https://pre-commit.com/) hooks for automated code quality checks.

#### Pre-commit Hooks

The following hooks run automatically on every commit:
- **Ruff linting**: Catches code quality issues and potential bugs
- **Ruff formatting**: Ensures consistent code formatting
- **Trailing whitespace**: Removes trailing whitespace
- **End of file**: Ensures files end with newline
- **YAML validation**: Validates YAML files
- **Large files**: Prevents accidentally committing large files
- **Merge conflicts**: Detects unresolved merge conflicts

#### Manual Code Quality Checks

```bash
# Run linting
pixi run ruff check .

# Run formatting
pixi run ruff format .

# Run all pre-commit hooks manually
pixi run pre-commit run --all-files
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
