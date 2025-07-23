"""
Memory management utilities for FontSampler.
"""

import gc

import psutil

from .config import (
    DEFAULT_BATCH_SIZE,
    ESTIMATED_MEMORY_PER_FONT,
    MAX_BATCH_SIZE,
    MIN_BATCH_SIZE,
)


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def get_available_memory() -> float:
    """Get available system memory in MB."""
    return psutil.virtual_memory().available / 1024 / 1024


def get_memory_percentage() -> float:
    """Get current memory usage as percentage of total system memory."""
    return psutil.virtual_memory().percent


def adaptive_batch_size(
    current_memory: float,
    base_batch_size: int = DEFAULT_BATCH_SIZE,
    memory_threshold: float = 0.7,
) -> int:
    """
    Adjust batch size based on available memory.

    Args:
        current_memory: Current memory usage in MB
        base_batch_size: Base batch size to start with
        memory_threshold: Memory usage threshold (0.0-1.0) above which to reduce batch size

    Returns:
        Adjusted batch size
    """
    total_memory = psutil.virtual_memory().total / 1024 / 1024

    # Calculate memory usage percentage
    memory_usage_pct = current_memory / total_memory

    if memory_usage_pct > memory_threshold:
        # Reduce batch size if memory usage is high
        reduction_factor = 1 - (memory_usage_pct - memory_threshold)
        new_batch_size = max(MIN_BATCH_SIZE, int(base_batch_size * reduction_factor))
    else:
        # Increase batch size if memory usage is low
        increase_factor = 1 + (memory_threshold - memory_usage_pct)
        new_batch_size = min(MAX_BATCH_SIZE, int(base_batch_size * increase_factor))

    return new_batch_size


def force_garbage_collection():
    """Force garbage collection and return freed memory."""
    memory_before = get_memory_usage()
    gc.collect()
    memory_after = get_memory_usage()
    return memory_before - memory_after


def check_memory_safety(
    font_count: int, estimated_memory_per_font: float = ESTIMATED_MEMORY_PER_FONT
) -> tuple[bool, str]:
    """
    Check if processing a given number of fonts is safe for memory.

    Args:
        font_count: Number of fonts to process
        estimated_memory_per_font: Estimated memory usage per font in MB

    Returns:
        Tuple of (is_safe, warning_message)
    """
    available_memory = get_available_memory()
    estimated_total_memory = font_count * estimated_memory_per_font

    if estimated_total_memory > available_memory * 0.8:
        return (
            False,
            f"Estimated memory usage ({estimated_total_memory:.1f}MB) exceeds 80% of available memory ({available_memory:.1f}MB)",
        )

    return True, ""


class MemoryMonitor:
    """Context manager for monitoring memory usage during operations."""

    def __init__(self, operation_name: str = "Operation"):
        self.operation_name = operation_name
        self.start_memory = 0.0
        self.peak_memory = 0.0

    def __enter__(self):
        self.start_memory = get_memory_usage()
        self.peak_memory = self.start_memory
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # Don't suppress exceptions

    def update_peak(self):
        """Update peak memory usage."""
        current_memory = get_memory_usage()
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory

    def get_stats(self) -> dict:
        """Get memory statistics."""
        current_memory = get_memory_usage()
        return {
            "start_memory": self.start_memory,
            "current_memory": current_memory,
            "peak_memory": self.peak_memory,
            "total_increase": current_memory - self.start_memory,
            "peak_increase": self.peak_memory - self.start_memory,
        }
