# FontSampler TODO

## Configuration and Architecture

- [x] Extract configuration to YAML file for better maintainability
- [x] Externalize HTML/CSS templates to separate files
- [x] Implement personalized content for testing scenarios

## Font Processing and Validation

- [ ] Verify font embedding in PDF output
- [ ] Improve character set for testing (include accents, ñ, etc.)
- [ ] Implement font character map analysis
- [ ] Add support for non-western scripts
- [ ] Handle icon fonts and emoji fonts appropriately

## Memory and Performance Optimization

- [ ] Implement single-font mode for detailed analysis
- [ ] Add memory management for large font collections
- [ ] Consider temporary file flushing for very large datasets
- [ ] Add user warnings for long processing times (>X fonts)
- [ ] Optimize memory usage for Unicode character mapping

## Feature Enhancements

- [ ] Add detailed font analysis mode
- [ ] Implement font subset analysis (what characters are actually in the font)
- [ ] Consider full Unicode support vs. memory constraints
- [ ] Add progress indicators for long-running operations

## Technical Considerations

- [ ] Evaluate memory impact of full Unicode character sets
- [ ] Research font file character analysis capabilities
- [ ] Consider alternative approaches for very large font collections
- [ ] Implement proper error handling for unsupported font types
