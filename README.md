# [![FontSampler](logo.png)](https://github.com/conradolandia/fontsampler)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Pixi](https://img.shields.io/badge/Pixi-Enabled-green.svg)](https://pixi.sh/)

A Python tool that generates PDF samples of fonts found in a directory. Produces font catalogs with metadata, sample text at multiple sizes, and table of contents using streaming architecture for memory management.

## Features

- **Font Discovery**: Locates `.ttf` and `.otf` fonts in directories
- **Font Metadata**: Extracts and displays font name, family, version, and copyright information
- **Sample Text**: Renders fonts at multiple sizes (36, 24, 18, 14pt) with configurable text
- **Character Set**: Displays alphabet, numbers, and special characters
- **Text Wrapping**: Handles text wrapping within page boundaries
- **Table of Contents**: Generates table of contents with page references
- **Font Support**: Uses WeasyPrint with Pango for TrueType, OpenType and PostScript fonts
- **Terminal UI**: Progress bars, status messages, and process feedback
- **Streaming Architecture**: Memory management for processing large font collections
- **Memory Monitoring**: Adaptive batch processing with garbage collection
- **Large Collection Support**: Tested with collections of 3000+ fonts

## Requirements

- [Pixi](https://pixi.sh/) for dependency management
- Python 3.8+
- **System Libraries**: Cairo graphics library, Pango text layout, GLib core library, and FontConfig (required by WeasyPrint for PDF generation)

### Python Dependencies

The project uses the following key Python packages:
- **fonttools**: Font metadata extraction and manipulation
- **weasyprint**: PDF generation with advanced font support
- **rich**: Enhanced terminal UI with progress bars and colored output
- **psutil**: System resource monitoring and memory management

### System Dependencies

Pixi automatically handles most system dependencies through conda-forge. The following libraries are included automatically:
- **Cairo**: Graphics library for PDF generation
- **Pango**: Text layout and font rendering
- **GLib**: Core system library
- **FontConfig**: Font discovery and configuration
- **PyGObject**: Python bindings for GObject introspection (provides access to Pango, Cairo, GLib)

**Additional System Dependencies for Testing:**
- **FontForge**: Required for some tests that generate real test fonts (automatically integrated via PYTHONPATH)

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

The tool can be executed in multiple ways:

```bash
# Method 1: Direct command (recommended)
pixi run fontsampler <directory_path> [options]

# Method 2: As a Python module
pixi run python -m fontsampler <directory_path> [options]

# Method 3: Direct script execution
pixi run python main.py <directory_path> [options]
```

### Examples

Basic usage:
```bash
pixi run fontsampler /usr/share/fonts
# or
pixi run python -m fontsampler /usr/share/fonts
```

Custom output filename:
```bash
pixi run fontsampler ~/fonts -o my_samples.pdf
# or
pixi run python -m fontsampler ~/fonts -o my_samples.pdf
```

Limit fonts for testing:
```bash
pixi run fontsampler . -l 10
# or
pixi run python -m fontsampler . -l 10
```

Verbose output:
```bash
pixi run fontsampler /usr/share/fonts -v
# or
pixi run python -m fontsampler /usr/share/fonts -v
```

### Command Line Options

- `directory`: Directory containing font files (.ttf, .otf) **[required]**
- `-o, --output`: Output PDF filename (default: `font_samples.pdf`)
- `-v, --verbose`: Show detailed information about font processing
- `-l, --limit`: Limit the number of fonts to process (useful for testing)
- `-h, --help`: Show help message

### As a Library

The package can also be used as a library in other Python projects:

```python
from fontsampler import extract_font_info

# Extract font information
font_info = extract_font_info("/path/to/font.ttf")
print(f"Font: {font_info['name']}")
print(f"Family: {font_info['family']}")
```

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

Default configuration includes the pangram "Sphinx of black quartz, judge my vow!" for font samples, plus a character set including:
- Uppercase and lowercase letters
- Numbers 0-9
- Special characters and symbols

## Font Support

Uses WeasyPrint with Cairo and Pango for font rendering:
- **OpenType support**: Handles `.otf` files
- **PostScript font support**: Processes CFF and CFF2 outlines
- **TrueType support**: Supports `.ttf` files
- **Font feature support**: Detects bold, italic, and other variants
- **PDF generation**: PDF output using Cairo graphics library

## Configuration

The tool uses a `config.yaml` file for customization:
- **Header**: Application banner displayed at startup
- **Sample Text**: Text scenarios for font testing (default, typography, international)
- **Output Settings**: PDF generation parameters and formatting options
- **Memory Management**: Batch processing and memory threshold settings

## Architecture

The project uses a streaming architecture for memory management:

- **Streaming Font Discovery**: Fonts are discovered and processed sequentially
- **Adaptive Memory Management**: Garbage collection and memory monitoring
- **Batch Processing**: Configurable batch sizes based on available memory

## Project Structure

The project follows modern Python package structure best practices:

```
fontsampler/
├── fontsampler/            # Main package directory
│   ├── __init__.py         # Package initialization
│   ├── __main__.py         # Module execution entry point
│   ├── cli.py              # Command-line interface
│   ├── config.py           # Configuration constants
│   ├── warning_capture.py  # Warning capture and display
│   ├── font_discovery.py   # Font finding and metadata
│   ├── font_validation.py  # Font validation and registration
│   ├── template_manager.py # Jinja template management
│   ├── incremental_pdf.py  # Incremental PDF generation
│   ├── streaming_processor.py # Streaming font processing
│   ├── memory_utils.py     # Memory management utilities
│   └── logging_config.py   # Logging configuration
├── docs/                   # Detailed documentation
├── dist/                   # Build output
├── build/                  # Build artifacts
├── pyproject.toml          # Dependency and task management
├── fontsampler.spec        # PyInstaller configuration
├── .pre-commit-config.yaml # Pre-commit hooks
└── README.md               # Main documentation
```

## Development

This project uses [Pixi](https://pixi.sh/) for dependency management and environment setup.

### Setup

1. Install Pixi: https://pixi.sh/install
2. Clone the repository
3. Run `pixi install`

### Testing

The project includes tests for large font collections and performance benchmarks. Some tests require FontForge for generating test fonts.

#### Test Dependencies

FontForge is a system dependency that provides Python extensions for font manipulation. It's required for some tests that generate real test fonts.

**Install FontForge:**

```bash
# Ubuntu/Debian
sudo apt-get install fontforge

# Arch Linux
sudo pacman -S fontforge

# macOS
brew install fontforge
```

**Install Python test dependencies:**

```bash
# Using pixi (recommended)
pixi install

# Using pip
pip install -e .
```

**Note:** The pixi environment is configured to use Python 3.13 and automatically includes the system FontForge Python bindings when running tests.

#### Running Tests

```bash
# Run all tests
pixi run test

# Run tests with verbose output
pixi run test-verbose

# Run specific test file
pixi run pytest tests/test_large_collections.py

# Run tests with coverage
pixi run pytest --cov=fontsampler
```

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

## Troubleshooting

### Common Issues

**No fonts found**: Ensure the directory contains `.ttf` or `.otf` files and you have read permissions.

**Memory issues**: The streaming architecture handles large font collections. The tool has been tested with 3000+ fonts and uses adaptive memory management and batch processing. See [benchmarks](docs/benchmarks.md) for performance results. If you encounter memory issues, use the `-l` option to limit the number of fonts processed.

**Font rendering issues**: Some fonts may not render correctly due to format incompatibilities. The tool will skip problematic fonts and report them in the output.

### Getting Help

If you encounter issues not covered here:
1. Check the verbose output with `-v` flag
2. Review the logs in the `logs/` directory
3. Open an issue on the project repository

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome. Submit a Pull Request for changes. For major changes, open an issue first to discuss the proposed modifications.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the pre-commit hooks: `pixi run pre-commit run --all-files`
5. Submit a pull request

## Citation

If you use this tool in your research or projects, please cite it as:

```
FontSampler: A Python tool for generating PDF font catalogs
Version 0.1.0
https://github.com/your-repo/fontsampler
```
