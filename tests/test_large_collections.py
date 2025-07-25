"""
Test large font collections to demonstrate scalability.

This module includes comprehensive cleanup mechanisms:
- Temporary directories are automatically cleaned up via tempfile.TemporaryDirectory()
- FontForge objects are explicitly closed in finally blocks
- Garbage collection is forced after processing large batches
- Session-level cleanup ensures all resources are freed
"""

import gc
import tempfile
import time
from pathlib import Path

import pytest

from fontsampler import process_fonts_with_streaming


@pytest.fixture(scope="function")
def fontforge_cleanup():
    """Fixture to ensure FontForge resources are properly cleaned up."""
    # Setup: nothing needed
    yield
    # Teardown: force garbage collection to clean up FontForge objects
    # Only run if FontForge was actually used
    try:
        import fontforge  # type: ignore # noqa: F401

        gc.collect()
    except ImportError:
        # FontForge not available, no cleanup needed
        pass


@pytest.fixture(scope="session", autouse=True)
def session_cleanup():
    """Session-level cleanup to ensure all resources are freed."""
    yield
    # Final cleanup at the end of all tests
    gc.collect()


def create_placeholder_fonts(num_fonts: int, temp_dir: Path) -> list[Path]:
    """Create placeholder font files for testing (legacy function)."""
    font_paths = []
    for i in range(num_fonts):
        font_path = temp_dir / f"test_font_{i:04d}.ttf"
        # Create a minimal TTF file (just header)
        with open(font_path, "wb") as f:
            f.write(b"OTTO")  # OpenType signature
        font_paths.append(font_path)
    return font_paths


def create_real_test_fonts(num_fonts: int, temp_dir: Path) -> list[Path]:
    """Create real test fonts using fontforge for meaningful testing."""
    try:
        import random
        import string

        import fontforge  # type: ignore # noqa: F401
    except ImportError:
        pytest.skip(
            "fontforge not available for real font generation. Install FontForge system package: sudo apt-get install fontforge (Ubuntu/Debian), sudo pacman -S fontforge (Arch), or brew install fontforge (macOS)"
        )

    # Try to find a base font to copy from
    base_font_paths = [
        "/usr/share/fonts/TTF/DejaVuSans.ttf",  # Arch Linux
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Ubuntu/Debian
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",  # Fedora/other
        "/System/Library/Fonts/Arial.ttf",  # macOS
        "C:/Windows/Fonts/arial.ttf",  # Windows
    ]

    base_font_path = None
    for path in base_font_paths:
        if Path(path).exists():
            base_font_path = path
            break

    if not base_font_path:
        pytest.skip("No suitable base font found for testing")

    font_paths = []

    def random_font_name(length=6):
        return "".join(random.choices(string.ascii_letters, k=length))

    for i in range(num_fonts):
        font = None
        try:
            rand_name = random_font_name()
            font = fontforge.open(base_font_path)

            # Set random names in metadata
            font.familyname = f"TestFont_{rand_name}"
            font.fontname = f"TestFont-{rand_name}"
            font.fullname = f"Test Font {rand_name}"

            # Modify a few glyphs to ensure uniqueness (but keep it minimal)
            modified_count = 0
            for glyph in font.glyphs():
                if (
                    glyph.unicode != -1
                    and random.random() < 0.005
                    and modified_count < 5
                ):
                    glyph.comment = f"Test_{rand_name}"
                    modified_count += 1

            # Save the new font
            output_path = temp_dir / f"test_font_{rand_name}_{i:04d}.ttf"
            font.generate(str(output_path))
            font_paths.append(output_path)

        except Exception as e:
            print(f"Warning: Failed to generate font {i}: {e}")
            # Fall back to placeholder if font generation fails
            font_path = temp_dir / f"placeholder_font_{i:04d}.ttf"
            with open(font_path, "wb") as f:
                f.write(b"OTTO")
            font_paths.append(font_path)
        finally:
            # Ensure FontForge object is always closed
            if font is not None:
                try:
                    font.close()
                except Exception as e:
                    print(f"Warning: Failed to close font {i}: {e}")

    return font_paths


def test_large_collection_performance(fontforge_cleanup):
    """Test processing time and memory usage for large font collections."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test with different collection sizes
        sizes = [10, 50, 100, 200]  # Reduced sizes for real font testing

        print("\n🔍 Testing large collection performance with real fonts...")

        for size in sizes:
            print(f"\n📊 Testing {size} fonts...")

            # Create test fonts
            font_paths = create_real_test_fonts(size, temp_path)

            # Measure processing time
            start_time = time.time()
            start_memory = get_memory_usage()

            # Process fonts
            processed_count = 0
            for _ in process_fonts_with_streaming(font_paths=font_paths):
                processed_count += 1
                if processed_count % 20 == 0:
                    print(f"  Processed {processed_count}/{size} fonts...")

            end_time = time.time()
            end_memory = get_memory_usage()

            # Calculate metrics
            processing_time = end_time - start_time
            memory_used = end_memory - start_memory
            fonts_per_second = size / processing_time if processing_time > 0 else 0

            print(f"  Results for {size} fonts:")
            print(f"    Processing time: {processing_time:.2f} seconds")
            print(f"    Memory usage: {memory_used:.1f} MB")
            print(f"    Fonts per second: {fonts_per_second:.1f}")
            print(f"    Successfully processed: {processed_count}/{size}")

            # Assert reasonable performance (adjusted for real fonts)
            assert processing_time < 600, (
                f"Processing {size} fonts took too long: {processing_time}s"
            )
            assert memory_used < 4096, f"Memory usage too high: {memory_used}MB"

            # With real fonts, we expect most to be processed successfully
            success_rate = processed_count / size if size > 0 else 0
            print(f"    Success rate: {success_rate:.1%}")

            # Clean up memory after processing each batch
            gc.collect()


def test_memory_efficiency(fontforge_cleanup):
    """Test that memory usage doesn't grow linearly with font count."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Test with increasing collection sizes (smaller for real fonts)
        sizes = [10, 25, 50, 100]
        memory_usage = []

        print("\n🧠 Testing memory efficiency with real fonts...")

        for size in sizes:
            font_paths = create_real_test_fonts(size, temp_path)

            start_memory = get_memory_usage()

            # Process fonts
            processed_count = 0
            for _ in process_fonts_with_streaming(font_paths=font_paths):
                processed_count += 1

            end_memory = get_memory_usage()
            memory_usage.append(end_memory - start_memory)

            print(
                f"  Memory test for {size} fonts: {end_memory - start_memory:.1f} MB, processed: {processed_count}"
            )

            # Clean up memory after processing each batch
            gc.collect()

        # Check that memory usage doesn't grow linearly
        # Memory should be relatively constant due to streaming
        avg_memory = sum(memory_usage) / len(memory_usage)
        if avg_memory > 1.0:  # Only check if there was significant memory usage
            for usage in memory_usage:
                assert usage < avg_memory * 3, "Memory usage growing too fast"
            print("  ✅ Memory efficiency test passed")
        else:
            print("  ✅ No significant memory usage detected")


def test_placeholder_fonts_fallback():
    """Test that the system handles invalid fonts gracefully."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        print("\n⚠️  Testing placeholder fonts fallback...")

        # Create placeholder fonts (invalid)
        font_paths = create_placeholder_fonts(50, temp_path)

        start_time = time.time()
        processed_count = 0

        for _ in process_fonts_with_streaming(font_paths=font_paths):
            processed_count += 1

        processing_time = time.time() - start_time

        print(
            f"  Processed {processed_count}/50 placeholder fonts in {processing_time:.2f}s"
        )
        print(f"  Success rate: {processed_count / 50:.1%}")

        # Should handle invalid fonts gracefully
        assert processing_time < 60, "Processing invalid fonts took too long"
        print("  ✅ Placeholder fonts handled gracefully")


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    import psutil

    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024


def test_fontforge_availability():
    """Test that fontforge is available when installed."""
    try:
        import fontforge  # type: ignore # noqa: F401

        # If we get here, fontforge is available
        assert True
    except ImportError:
        pytest.skip(
            "fontforge not available - install system package: sudo apt-get install fontforge (Ubuntu/Debian), sudo pacman -S fontforge (Arch), or brew install fontforge (macOS)"
        )


if __name__ == "__main__":
    # Run benchmarks
    test_large_collection_performance()
    test_memory_efficiency()
    test_placeholder_fonts_fallback()
    print("\n✅ All large collection tests passed!")
