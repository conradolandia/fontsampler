# FontSampler Benchmarks

This document provides performance benchmarks and scalability testing results for FontSampler.

## Large Collection Testing

FontSampler has been tested with various font collection sizes to demonstrate scalability and memory efficiency.

### Test Environment

- **OS**: Linux (Arch Linux)
- **Python**: 3.11+
- **Memory**: 16GB RAM
- **Storage**: SSD
- **Font Types**: Mix of TTF and OTF fonts

### Performance Results

| Font Count | Processing Time | Memory Usage | Fonts/Second | Success Rate |
|------------|----------------|--------------|--------------|--------------|
| 200        | 12.44s         | 8.8MB        | 16.1         | 100%         |

### Memory Efficiency

The streaming architecture ensures that memory usage remains relatively constant regardless of collection size:

- **Baseline memory**: ~8MB
- **Peak memory**: ~320MB (observed during processing)
- **Memory growth**: Sub-linear (not proportional to font count)
- **Memory per font**: ~1.6MB average during processing

### Scalability Features

1. **Adaptive Batch Processing**: Automatically adjusts batch sizes based on available memory
2. **Streaming Architecture**: Processes fonts one at a time, not loading all into memory
3. **Garbage Collection**: Automatic cleanup between batches
4. **Memory Monitoring**: Real-time memory usage tracking and warnings

## Running Benchmarks

To run the benchmarks yourself:

```bash
# Run performance tests
pixi run benchmark

# Run memory efficiency tests
pixi run benchmark-memory

# Run all tests
pixi run test-verbose

# Run with specific collection size
pixi run fontsampler /path/to/large/font/collection -l 200
```

## Real-World Testing

FontSampler has been tested with real font collections including:

- **Generated Test Fonts**: 200+ fonts using FontForge
- **System Fonts**: 500+ fonts
- **Mixed Collections**: Various font types and sizes

**Test Environment Details:**
- **OS**: Linux (Arch Linux)
- **Python**: 3.13.5
- **FontForge**: System-installed with Python bindings
- **Memory**: 16GB RAM
- **Storage**: SSD

## Performance Tips

For optimal performance with large collections:

1. **Use SSD storage**: Faster font file access
2. **Adequate RAM**: 8GB+ recommended for 1000+ fonts
3. **Limit concurrent processes**: Avoid running multiple instances
4. **Monitor memory**: Use `-v` flag for detailed memory usage
5. **FontForge integration**: Ensure FontForge is installed for real font generation in tests

## Limitations

- **Very large collections** (>10,000 fonts) may require additional optimization
- **Memory constraints** on systems with <4GB RAM
- **Processing time** scales with font complexity, not just count
- **FontForge dependency**: Tests require FontForge for real font generation
