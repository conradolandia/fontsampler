"""
Streaming font processor for FontSampler.
"""

import os
from contextlib import contextmanager
from typing import Any, Dict, Generator, List

from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from .config import DEFAULT_BATCH_SIZE, FONT_EXTENSIONS, _config
from .font_discovery import extract_font_info
from .font_validation import register_font_for_weasyprint, validate_font_with_weasyprint
from .logging_config import get_logger, log_font_processing, log_memory_usage
from .memory_utils import (
    MemoryMonitor,
    adaptive_batch_size,
    check_memory_safety,
    force_garbage_collection,
    get_memory_usage,
)
from .warning_capture import console


def find_fonts_streaming(root: str) -> Generator[str, None, None]:
    """
    Generator that yields font paths as discovered.

    Args:
        root: Root directory to search for fonts

    Yields:
        Font file paths
    """
    console.print(f"[bold blue]🔍[/bold blue] Scanning directory: [cyan]{root}[/cyan]")

    font_count = 0
    dir_count = 0

    # First pass to count total directories for progress bar
    total_dirs = sum(1 for _ in os.walk(root))

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Scanning directories...", total=total_dirs)

        for dirpath, _, filenames in os.walk(root):
            dir_count += 1
            progress.update(task, advance=1)

            for f in filenames:
                if f.lower().endswith(FONT_EXTENSIONS):
                    font_count += 1
                    yield os.path.join(dirpath, f)

    console.print(
        f"[bold green]✅[/bold green] Directory scan complete: [cyan]{dir_count}[/cyan] directories, [cyan]{font_count}[/cyan] fonts found"
    )


@contextmanager
def font_resource_manager(font_path: str):
    """
    Context manager for font resource cleanup.

    Args:
        font_path: Path to the font file

    Yields:
        Font object or None if loading fails
    """
    from fontTools.ttLib import TTFont

    font = None
    try:
        font = TTFont(font_path, fontNumber=0, lazy=True)
        yield font
    except Exception as e:
        console.print(
            f"  [bold red]❌[/bold red] Failed to load font [red]{os.path.basename(font_path)}[/red]: {e}"
        )
        yield None
    finally:
        if font:
            font.close()
        force_garbage_collection()


class StreamingFontProcessor:
    """
    Streaming font processor with adaptive batch processing.
    """

    def __init__(
        self,
        base_batch_size: int = DEFAULT_BATCH_SIZE,
        memory_threshold: float = None,
        skip_problematic_fonts: bool = None,
    ):
        self.base_batch_size = base_batch_size
        self.memory_threshold = (
            memory_threshold
            if memory_threshold is not None
            else _config.get_memory_threshold()
        )
        self.skip_problematic_fonts = (
            skip_problematic_fonts
            if skip_problematic_fonts is not None
            else _config.get("pdf.skip_problematic_fonts", True)
        )
        self.processed_count = 0
        self.valid_fonts = []
        self.rejected_fonts = []
        self.validation_errors = {}
        self.metadata_warnings = []
        self.logger = get_logger("fontsampler.streaming_processor")

    def process_fonts_streaming(
        self, font_paths: Generator[str, None, None]
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process fonts in streaming fashion with adaptive batch sizing.

        Args:
            font_paths: Generator yielding font paths

            Yields:
                Processed font information dictionaries
        """
        current_batch = []
        batch_size = self.base_batch_size

        with MemoryMonitor("Font Processing") as memory_monitor:
            # Log initial memory usage
            initial_memory = get_memory_usage()
            log_memory_usage(
                self.logger, "Font processing started", initial_memory, initial_memory
            )

            for font_path in font_paths:
                current_batch.append(font_path)

                # Process batch when it reaches the current batch size
                if len(current_batch) >= batch_size:
                    batch_start_memory = get_memory_usage()
                    yield from self._process_batch(current_batch, memory_monitor)
                    batch_end_memory = get_memory_usage()

                    # Log memory usage after batch processing
                    log_memory_usage(
                        self.logger,
                        f"Batch processed ({len(current_batch)} fonts)",
                        batch_start_memory,
                        batch_end_memory,
                        memory_monitor.peak_memory,
                    )

                    current_batch.clear()

                    # Adjust batch size based on memory usage
                    current_memory = get_memory_usage()
                    new_batch_size = adaptive_batch_size(
                        current_memory, self.base_batch_size, self.memory_threshold
                    )

                    if new_batch_size != batch_size:
                        console.print(
                            f"[yellow]⚙️[/yellow] Adjusting batch size: [cyan]{batch_size}[/cyan] → [cyan]{new_batch_size}[/cyan] "
                            f"(memory: {current_memory:.1f}MB)"
                        )
                        batch_size = new_batch_size

                    memory_monitor.update_peak()

            # Process remaining fonts
            if current_batch:
                batch_start_memory = get_memory_usage()
                yield from self._process_batch(current_batch, memory_monitor)
                batch_end_memory = get_memory_usage()

                # Log memory usage after final batch
                log_memory_usage(
                    self.logger,
                    f"Final batch processed ({len(current_batch)} fonts)",
                    batch_start_memory,
                    batch_end_memory,
                    memory_monitor.peak_memory,
                )

    def _process_batch(
        self, font_paths: List[str], memory_monitor: MemoryMonitor
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Process a batch of font paths.

        Args:
            font_paths: List of font paths to process
            memory_monitor: Memory monitor instance

        Yields:
            Processed font information dictionaries
        """
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Processing batch of {len(font_paths)} fonts...",
                total=len(font_paths),
            )

            for font_path in font_paths:
                progress.update(
                    task,
                    description=f"[cyan]Processing {os.path.basename(font_path)}...",
                )

                try:
                    # Extract font information
                    font_info = extract_font_info(font_path)
                    if not font_info:
                        font_name = os.path.basename(font_path)
                        self.rejected_fonts.append(font_name)
                        self.validation_errors[font_name] = (
                            "Failed to extract font info"
                        )
                        log_font_processing(
                            self.logger,
                            font_path,
                            "FAILED",
                            "Failed to extract font info",
                        )
                        progress.advance(task)
                        continue

                    # Register font with WeasyPrint
                    font_family = register_font_for_weasyprint(font_path)
                    if not font_family:
                        self.rejected_fonts.append(font_info["file"])
                        self.validation_errors[font_info["file"]] = (
                            "Failed to register font"
                        )
                        log_font_processing(
                            self.logger, font_path, "FAILED", "Failed to register font"
                        )
                        progress.advance(task)
                        continue

                    # Validate font
                    validation_result = validate_font_with_weasyprint(
                        font_path, font_family
                    )
                    if validation_result is True:
                        font_info["_registered_name"] = font_family
                        self.valid_fonts.append(font_info)
                        self.processed_count += 1

                        # Track metadata warnings if present
                        if font_info.get("metadata_error"):
                            self.metadata_warnings.append(font_info["file"])

                        log_font_processing(
                            self.logger,
                            font_path,
                            "SUCCESS",
                            f"Registered as {font_family}",
                        )
                        yield font_info
                    else:
                        self.rejected_fonts.append(font_info["file"])
                        error_msg = (
                            validation_result[1]
                            if isinstance(validation_result, tuple)
                            else str(validation_result)
                        )
                        self.validation_errors[font_info["file"]] = error_msg
                        log_font_processing(
                            self.logger, font_path, "VALIDATION_FAILED", error_msg
                        )

                        if self.skip_problematic_fonts:
                            # Skip problematic fonts and continue processing
                            console.print(
                                f"  [bold yellow]⚠️[/bold yellow] [yellow]{font_info['file']}[/yellow]: {error_msg} (skipping)"
                            )
                        else:
                            # Stop processing when problematic fonts are encountered
                            console.print(
                                f"  [bold red]❌[/bold red] [red]{font_info['file']}[/red]: {error_msg}"
                            )
                            console.print(
                                "[bold red]❌[/bold red] Stopping processing due to problematic font"
                            )
                            raise RuntimeError(
                                f"Problematic font encountered: {font_info['file']} - {error_msg}"
                            )

                except Exception as e:
                    font_name = os.path.basename(font_path)
                    self.rejected_fonts.append(font_name)
                    self.validation_errors[font_name] = f"Unexpected error: {e}"
                    log_font_processing(
                        self.logger, font_path, "FAILED", f"Unexpected error: {e}", e
                    )

                    if self.skip_problematic_fonts:
                        # Skip problematic fonts and continue processing
                        console.print(
                            f"  [bold yellow]⚠️[/bold yellow] [yellow]{font_name}[/yellow]: Unexpected error: {e} (skipping)"
                        )
                    else:
                        # Stop processing when problematic fonts are encountered
                        console.print(
                            f"  [bold red]❌[/bold red] [red]{font_name}[/red]: Unexpected error: {e}"
                        )
                        console.print(
                            "[bold red]❌[/bold red] Stopping processing due to problematic font"
                        )
                        raise

                progress.advance(task)
                memory_monitor.update_peak()

    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "valid_fonts": len(self.valid_fonts),
            "rejected_fonts": len(self.rejected_fonts),
            "metadata_warnings": len(self.metadata_warnings),
            "validation_errors": self.validation_errors.copy(),
        }


def process_fonts_with_streaming(
    root_directory: str = None,
    font_paths: List[str] = None,
    base_batch_size: int = DEFAULT_BATCH_SIZE,
    skip_problematic_fonts: bool = None,
) -> Generator[Dict[str, Any], None, None]:
    """
    High-level function to process fonts using streaming architecture.

    Args:
        root_directory: Directory containing fonts (if font_paths not provided)
        font_paths: List of font file paths to process (if provided, overrides root_directory)
        base_batch_size: Base batch size for processing
        skip_problematic_fonts: Override config setting for skipping problematic fonts

    Yields:
        Processed font information dictionaries
    """
    logger = get_logger("fontsampler.streaming_processor")

    # Use provided setting or fall back to config default
    should_skip_problematic = (
        skip_problematic_fonts
        if skip_problematic_fonts is not None
        else _config.get("pdf.skip_problematic_fonts", True)
    )

    # Determine font paths
    if font_paths is not None:
        # Use provided font paths
        paths = font_paths
        font_count = len(paths)
        console.print(
            f"[bold blue]🔍[/bold blue] Total fonts to process: [cyan]{font_count}[/cyan]"
        )
    else:
        # Discover fonts from directory
        paths = list(find_fonts_streaming(root_directory))
        font_count = len(paths)

    if font_count == 0:
        if font_paths is not None:
            console.print(
                "[bold blue]🔍[/bold blue] No font files provided for processing"
            )
            logger.warning("No font files provided for processing")
        else:
            console.print(
                f"[bold blue]🔍[/bold blue] No font files (.ttf, .otf) found in '[cyan]{root_directory}[/cyan]'"
            )
            logger.warning(f"No font files found in directory: {root_directory}")
        return

    # Check memory safety
    is_safe, warning_msg = check_memory_safety(font_count)
    if not is_safe:
        console.print(f"[bold yellow]⚠️[/bold yellow] {warning_msg}")
        console.print(
            "[yellow]💡[/yellow] The processor will use adaptive batching to manage memory usage"
        )
        logger.warning(f"Memory safety check failed: {warning_msg}")

    if font_paths is None:
        console.print(
            f"[bold blue]🔍[/bold blue] Total fonts found: [cyan]{font_count}[/cyan]"
        )

    console.print("[bold yellow]⚙️[/bold yellow] Starting streaming font processing...")
    logger.info(
        f"Starting font processing - {font_count} fonts {'provided' if font_paths else 'found'}"
    )

    # Create streaming processor
    processor = StreamingFontProcessor(
        base_batch_size=base_batch_size, skip_problematic_fonts=should_skip_problematic
    )

    # Process fonts using generator
    font_generator = (path for path in paths)
    yield from processor.process_fonts_streaming(font_generator)

    # Display final statistics
    stats = processor.get_stats()
    console.print("\n[bold green]✅[/bold green] Processing complete!")
    console.print(
        f"[bold blue]📊[/bold blue] Fonts processed: [cyan]{stats['processed_count']}[/cyan]"
    )
    console.print(
        f"[bold blue]📊[/bold blue] Valid fonts: [cyan]{stats['valid_fonts']}[/cyan]"
    )
    console.print(
        f"[bold yellow]⚠️[/bold yellow] Rejected fonts: [cyan]{stats['rejected_fonts']}[/cyan]"
    )
    if stats["metadata_warnings"] > 0:
        console.print(
            f"[bold yellow]⚠️[/bold yellow] Fonts with metadata warnings: [cyan]{stats['metadata_warnings']}[/cyan]"
        )

    # Log final memory usage
    final_memory = get_memory_usage()
    log_memory_usage(logger, "Font processing completed", final_memory, final_memory)

    logger.info(
        f"Processing complete - Processed: {stats['processed_count']}, Valid: {stats['valid_fonts']}, Rejected: {stats['rejected_fonts']}"
    )
