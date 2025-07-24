"""
Logging configuration for FontSampler.
"""

import logging
import logging.config
import os
from datetime import datetime
from pathlib import Path

from rich.console import Console

from .config import LOG_DIR, LOG_FILE, LOG_LEVEL, LOG_MAX_AGE_DAYS

# Initialize Rich console
console = Console()


def setup_logging(
    log_level: str = LOG_LEVEL, log_file: str = LOG_FILE
) -> logging.Logger:
    """
    Setup comprehensive logging configuration.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path. If None, uses default location

    Returns:
        Configured logger instance
    """
    if log_file is None:
        # Use configured log directory
        log_dir = LOG_DIR
        log_dir.mkdir(exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"fontsampler_{timestamp}.log"

    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "simple": {"format": "%(levelname)s - %(message)s"},
            "rich": {"format": "%(message)s", "datefmt": "[%X]"},
        },
        "handlers": {
            "console": {
                "class": "rich.logging.RichHandler",
                "level": "WARNING",  # Only show warnings and errors in console
                "formatter": "rich",
                "rich_tracebacks": True,
                "show_time": False,
                "show_path": False,
            },
            "file": {
                "class": "logging.FileHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "filename": str(log_path),
                "mode": "w",
                "encoding": "utf-8",
            },
            "error_file": {
                "class": "logging.FileHandler",
                "level": "ERROR",
                "formatter": "detailed",
                "filename": str(
                    log_path.parent / f"fontsampler_errors_{timestamp}.log"
                ),
                "mode": "w",
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "fontsampler": {
                "handlers": ["console", "file", "error_file"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "fontsampler.font_discovery": {
                "handlers": ["console", "file"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "fontsampler.font_validation": {
                "handlers": ["console", "file"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "fontsampler.pdf_generation": {
                "handlers": ["console", "file"],
                "level": log_level.upper(),
                "propagate": False,
            },
            "fontsampler.memory_utils": {
                "handlers": ["file"],  # Only file logging for memory info
                "level": "DEBUG",
                "propagate": False,
            },
            "fontsampler.streaming_processor": {
                "handlers": [
                    "file"
                ],  # Only file logging to avoid disrupting progress bars
                "level": log_level.upper(),
                "propagate": False,
            },
        },
        "root": {"handlers": ["console", "file"], "level": "ERROR"},
    }

    # Apply configuration
    logging.config.dictConfig(logging_config)

    # Get the main logger
    logger = logging.getLogger("fontsampler")

    # Log the setup
    logger.info(f"Logging initialized - Level: {log_level.upper()}")
    logger.info(f"Detailed logs: {log_path}")
    logger.info(
        f"Error logs: {log_path.parent / f'fontsampler_errors_{timestamp}.log'}"
    )

    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (e.g., 'fontsampler.pdf_generation')

    Returns:
        Logger instance
    """
    if name is None:
        return logging.getLogger("fontsampler")
    return logging.getLogger(name)


def log_font_processing(
    logger: logging.Logger,
    font_path: str,
    status: str,
    details: str = None,
    error: Exception = None,
):
    """
    Log font processing events with consistent formatting.

    Args:
        logger: Logger instance
        font_path: Path to the font file
        status: Processing status (SUCCESS, FAILED, SKIPPED, etc.)
        details: Additional details about the processing
        error: Exception if any occurred
    """
    font_name = os.path.basename(font_path)

    if status == "SUCCESS":
        logger.info(f"Font processed successfully: {font_name}")
        if details:
            logger.debug(f"Font details: {font_name} - {details}")
    elif status == "FAILED":
        logger.error(f"Font processing failed: {font_name} - {details}")
        if error:
            logger.exception(f"Exception details for {font_name}")
    elif status == "SKIPPED":
        logger.warning(f"Font skipped: {font_name} - {details}")
    elif status == "VALIDATION_FAILED":
        logger.warning(f"Font validation failed: {font_name} - {details}")
    else:
        logger.info(f"Font {status.lower()}: {font_name} - {details}")


def log_memory_usage(
    logger: logging.Logger,
    operation: str,
    memory_before: float,
    memory_after: float,
    peak_memory: float = None,
):
    """
    Log memory usage information.

    Args:
        logger: Logger instance
        operation: Name of the operation
        memory_before: Memory usage before operation (MB)
        memory_after: Memory usage after operation (MB)
        peak_memory: Peak memory usage during operation (MB)
    """
    memory_diff = memory_after - memory_before
    logger.debug(
        f"Memory usage for {operation}: "
        f"Before: {memory_before:.1f}MB, "
        f"After: {memory_after:.1f}MB, "
        f"Change: {memory_diff:+.1f}MB"
        + (f", Peak: {peak_memory:.1f}MB" if peak_memory else "")
    )


def log_pdf_generation(
    logger: logging.Logger,
    stage: str,
    details: str = None,
    font_count: int = None,
    error: Exception = None,
):
    """
    Log PDF generation events.

    Args:
        logger: Logger instance
        stage: Generation stage (START, PROGRESS, COMPLETE, ERROR)
        details: Additional details
        font_count: Number of fonts being processed
        error: Exception if any occurred
    """
    if stage == "START":
        logger.info(f"PDF generation started - {font_count} fonts")
        if details:
            logger.debug(f"PDF generation details: {details}")
    elif stage == "PROGRESS":
        logger.debug(f"PDF generation progress: {details}")
    elif stage == "COMPLETE":
        logger.info("PDF generation completed successfully")
        if details:
            logger.debug(f"PDF generation result: {details}")
    elif stage == "ERROR":
        logger.error(f"PDF generation failed: {details}")
        if error:
            logger.exception("PDF generation exception")


def log_pdf_font_issue(
    logger: logging.Logger,
    font_names: list,
    issue_type: str,
    error_message: str,
    stage: str = "PDF_GENERATION",
):
    """
    Log font-related issues during PDF generation.

    Args:
        logger: Logger instance
        font_names: List of font names causing issues
        issue_type: Type of issue (subsetting, validation, embedding, etc.)
        error_message: Detailed error message
        stage: Processing stage where the issue occurred
    """
    if not font_names:
        return

    # Log individual font issues
    for font_name in font_names:
        logger.warning(
            f"Font issue during {stage}: {font_name} - {issue_type}: {error_message}"
        )

    # Log summary if multiple fonts are affected
    if len(font_names) > 1:
        logger.warning(
            f"Multiple fonts affected during {stage}: {len(font_names)} fonts with {issue_type} issues"
        )
        logger.debug(f"Affected fonts: {', '.join(font_names)}")


def log_pdf_font_optimization_retry(
    logger: logging.Logger,
    error_message: str,
    retry_success: bool = None,
    retry_error: str = None,
):
    """
    Log font optimization retry attempts during PDF generation.

    Args:
        logger: Logger instance
        error_message: Original error message that triggered retry
        retry_success: Whether the retry was successful
        retry_error: Error message from retry attempt if it failed
    """
    logger.warning(f"Font optimization retry triggered: {error_message}")

    if retry_success is True:
        logger.info(
            "Font optimization retry successful - PDF generated without subsetting"
        )
    elif retry_success is False:
        logger.error(f"Font optimization retry failed: {retry_error}")
    else:
        logger.debug("Font optimization retry in progress")


def cleanup_old_logs(max_age_days: int = LOG_MAX_AGE_DAYS):
    """
    Clean up old log files.

    Args:
        max_age_days: Maximum age of log files to keep (days)
    """
    log_dir = LOG_DIR
    if not log_dir.exists():
        return

    cutoff_time = datetime.now().timestamp() - (max_age_days * 24 * 60 * 60)

    for log_file in log_dir.glob("fontsampler_*.log"):
        if log_file.stat().st_mtime < cutoff_time:
            try:
                log_file.unlink()
                console.print(f"[dim]Cleaned up old log file: {log_file.name}[/dim]")
            except Exception as e:
                console.print(
                    f"[yellow]Warning: Could not delete old log file {log_file.name}: {e}[/yellow]"
                )
