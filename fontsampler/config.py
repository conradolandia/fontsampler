"""
Configuration management for FontSampler.
"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


class Config:
    """Configuration manager for FontSampler."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.

        Args:
            config_file: Path to YAML configuration file. If None, uses default location.
        """
        self.config_file = config_file or self._get_default_config_path()
        self._config = self._load_config()

    def _get_default_config_path(self) -> str:
        """Get the default configuration file path."""
        # Look for config.yaml in current directory, then in package directory
        current_dir = Path.cwd() / "config.yaml"
        if current_dir.exists():
            return str(current_dir)

        package_dir = Path(__file__).parent.parent / "config.yaml"
        if package_dir.exists():
            return str(package_dir)

        # Return current directory as fallback
        return str(Path.cwd() / "config.yaml")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file with fallback to defaults."""
        config = self._get_default_config()

        if yaml is None:
            print("Warning: PyYAML not available, using default configuration")
            return config

        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding="utf-8") as f:
                    file_config = yaml.safe_load(f)
                    if file_config:
                        config = self._merge_config(config, file_config)
            except Exception as e:
                print(
                    f"Warning: Failed to load configuration from {self.config_file}: {e}"
                )
                print("Using default configuration")
        else:
            print(f"Configuration file not found: {self.config_file}")
            print("Using default configuration")

        return config

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration values."""
        return {
            "sample_text": {
                "main": "Sphinx of black quartz, judge my vow!",
                "paragraph": (
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                    "Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. "
                    "Sed nisi. Nulla quis sem at nibh elementum imperdiet. "
                    "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~"
                ),
                "testing_scenarios": {
                    "default": {
                        "main": "Sphinx of black quartz, judge my vow!",
                        "paragraph": (
                            "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                            "Integer nec odio. Praesent libero. Sed cursus ante dapibus diam. "
                            "Sed nisi. Nulla quis sem at nibh elementum imperdiet. "
                            "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~"
                        ),
                    },
                    "typography": {
                        "main": "The quick brown fox jumps over the lazy dog",
                        "paragraph": (
                            "Typography is the art and technique of arranging type to make written language "
                            "legible, readable, and appealing when displayed. The arrangement of type involves "
                            "selecting typefaces, point sizes, line lengths, line-spacing, and letter-spacing. "
                            "ABCDEFGHIJKLMNOPQRSTUVWXYZ abcdefghijklmnopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~"
                        ),
                    },
                    "international": {
                        "main": "El veloz murciélago hindú comía feliz cardillo y kiwi",
                        "paragraph": (
                            "This pangram contains all letters of the Spanish alphabet including ñ. "
                            "It's useful for testing fonts with international character support. "
                            "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ abcdefghijklmnñopqrstuvwxyz 1234567890 !@#$%^&*()_+-=[]{}|;:,.<>?`~ áéíóúü"
                        ),
                    },
                },
            },
            "output": {"default_filename": "font_samples.pdf"},
            "fonts": {
                "extensions": [".ttf", ".otf"],
                "sample_sizes": [36, 24, 18, 14, 12],
            },
            "memory": {
                "default_batch_size": 50,
                "max_batch_size": 200,
                "min_batch_size": 10,
                "memory_threshold": 0.7,
                "estimated_memory_per_font": 5.0,
                "update_interval": 100,
                "processing_interval": 500,
            },
            "pdf": {
                "page_size": "A4",
                "page_margin": "20mm",
                "font_header_size": "24px",
                "metadata_font_size": "12px",
                "sample_text_line_height": 1.2,
                "paragraph_line_height": 1.4,
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "max_age_days": 30,
                "directory": "logs",
            },
            "ui": {
                "show_progress": True,
                "progress_update_interval": 100,
                "show_memory_usage": True,
                "show_detailed_stats": True,
                "color_output": True,
            },
        }

    def _merge_config(
        self, default: Dict[str, Any], user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Recursively merge user configuration with defaults."""
        result = default.copy()

        for key, value in user.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._merge_config(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'fonts.extensions')."""
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_sample_text(self) -> str:
        """Get the main sample text."""
        return self.get("sample_text.main")

    def get_paragraph_text(self) -> str:
        """Get the paragraph text."""
        return self.get("sample_text.paragraph")

    def get_default_output(self) -> str:
        """Get the default output filename."""
        return self.get("output.default_filename")

    def get_font_extensions(self) -> tuple:
        """Get supported font extensions."""
        return tuple(self.get("fonts.extensions", [".ttf", ".otf"]))

    def get_sample_sizes(self) -> List[int]:
        """Get font sample sizes."""
        return self.get("fonts.sample_sizes", [36, 24, 18, 14, 12])

    def get_batch_size(self) -> int:
        """Get default batch size."""
        return self.get("memory.default_batch_size", 50)

    def get_memory_threshold(self) -> float:
        """Get memory threshold."""
        return self.get("memory.memory_threshold", 0.7)

    def get_log_level(self) -> str:
        """Get log level."""
        return self.get("logging.level", "INFO")

    def get_log_directory(self) -> Path:
        """Get log directory."""
        log_dir = self.get("logging.directory", "logs")
        return Path.cwd() / log_dir

    def get_testing_scenario(self, scenario_name: str = "default") -> Dict[str, str]:
        """
        Get testing scenario content.

        Args:
            scenario_name: Name of the testing scenario (default, typography, international)

        Returns:
            Dictionary with 'main' and 'paragraph' text for the scenario
        """
        scenarios = self.get("sample_text.testing_scenarios", {})
        if scenario_name not in scenarios:
            print(
                f"Warning: Testing scenario '{scenario_name}' not found, using default"
            )
            scenario_name = "default"

        return scenarios.get(
            scenario_name,
            scenarios.get(
                "default",
                {
                    "main": "Sphinx of black quartz, judge my vow!",
                    "paragraph": "Lorem ipsum dolor sit amet...",
                },
            ),
        )

    def list_testing_scenarios(self) -> List[str]:
        """Get list of available testing scenarios."""
        scenarios = self.get("sample_text.testing_scenarios", {})
        return list(scenarios.keys())


# Global configuration instance
_config = Config()

# Backward compatibility exports
SAMPLE_TEXT = _config.get_sample_text()
PARAGRAPH = _config.get_paragraph_text()
DEFAULT_OUTPUT = _config.get_default_output()
FONT_EXTENSIONS = _config.get_font_extensions()
DEFAULT_BATCH_SIZE = _config.get_batch_size()
MEMORY_THRESHOLD = _config.get_memory_threshold()
LOG_LEVEL = _config.get_log_level()
LOG_DIR = _config.get_log_directory()
LOG_FILE = _config.get("logging.file")
LOG_MAX_AGE_DAYS = _config.get("logging.max_age_days", 30)

# Additional exports for new features
SAMPLE_SIZES = _config.get_sample_sizes()
MAX_BATCH_SIZE = _config.get("memory.max_batch_size", 200)
MIN_BATCH_SIZE = _config.get("memory.min_batch_size", 10)
UPDATE_INTERVAL = _config.get("memory.update_interval", 100)
PROCESSING_INTERVAL = _config.get("memory.processing_interval", 500)
ESTIMATED_MEMORY_PER_FONT = _config.get("memory.estimated_memory_per_font", 5.0)

# PDF settings
PDF_PAGE_SIZE = _config.get("pdf.page_size", "A4")
PDF_PAGE_MARGIN = _config.get("pdf.page_margin", "20mm")
PDF_FONT_HEADER_SIZE = _config.get("pdf.font_header_size", "24px")
PDF_METADATA_FONT_SIZE = _config.get("pdf.metadata_font_size", "12px")
PDF_SAMPLE_TEXT_LINE_HEIGHT = _config.get("pdf.sample_text_line_height", 1.2)
PDF_PARAGRAPH_LINE_HEIGHT = _config.get("pdf.paragraph_line_height", 1.4)

# UI settings
UI_SHOW_PROGRESS = _config.get("ui.show_progress", True)
UI_PROGRESS_UPDATE_INTERVAL = _config.get("ui.progress_update_interval", 100)
UI_SHOW_MEMORY_USAGE = _config.get("ui.show_memory_usage", True)
UI_SHOW_DETAILED_STATS = _config.get("ui.show_detailed_stats", True)
UI_COLOR_OUTPUT = _config.get("ui.color_output", True)
