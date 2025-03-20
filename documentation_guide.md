# Accessibility Test Documentation Guide

This guide explains how to document accessibility tests in the project. The documentation is automatically collected during test runs and included in generated reports.

## Overview

Each test module includes a `TEST_DOCUMENTATION` object that describes:
- The purpose of the test
- What accessibility issues it detects
- How it maps to WCAG criteria
- How to fix identified issues
- What the test results mean

## Documentation Flow

1. **Test Modules**: Each test module contains a `TEST_DOCUMENTATION` object.
2. **a11yTestMongo.py**: Automatically collects documentation from all test modules during test execution.
3. **Test Run**: Documentation is stored in the MongoDB `test_runs` collection.
4. **Reports**: The XLS generator and other report tools retrieve documentation from the database.

## Adding Documentation to a Test File

1. **Using the Template Script**:
   
   ```bash
   python add_documentation_template.py path/to/test_file.py
   ```
   
   This adds a documentation template to the file that you can customize.

2. **Manual Method**:
   
   Add the `TEST_DOCUMENTATION` object at the top of the test file, after imports and docstrings.

## Documentation Structure

The `TEST_DOCUMENTATION` object has the following structure:

```python
TEST_DOCUMENTATION = {
    "testName": "Test Module Name",
    "description": "General description of what this test does",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "field1": "Description of field1",
        "field2": "Description of field2",
        # Other top-level fields in test results
    },
    "tests": [
        {
            "id": "specific-test-id",
            "name": "Specific Test Name",
            "description": "What this specific test checks for",
            "impact": "high|medium|low",
            "wcagCriteria": ["1.1.1", "1.3.1"],  # List applicable WCAG criteria
            "howToFix": "Instructions on fixing this issue",
            "resultsFields": {
                "pageFlags.hasSomeFlag": "Description of this flag",
                "keyElements.primaryElement": "Description of this element"
                # Result fields specific to this test
            }
        },
        # Additional test objects for each subtest or check
    ]
}
```

## Best Practices

1. **Be Thorough**: 
   - Include detailed descriptions of what each test checks
   - Explain why the issue matters for accessibility
   - Provide clear instructions on how to fix issues

2. **Map to WCAG**: 
   - Include relevant WCAG success criteria for each test
   - This helps report users understand compliance implications

3. **Document Result Fields**: 
   - Explain what each output field in the test results means
   - Include descriptions of boolean flags, counts, and data structures

4. **Test-Specific Documentation**:
   - Focus on the specific accessibility concerns related to the test
   - Include known limitations or edge cases

## Example Documentation

See `test_page_structure.py`, `test_images.py`, or `test_tables.py` for complete examples of comprehensive test documentation.