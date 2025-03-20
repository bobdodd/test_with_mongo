from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Tabindex Attribute Analysis",
    "description": "Evaluates the proper usage of tabindex attributes across different element types. This test identifies improper use of positive tabindex values, non-interactive elements with tabindex='0', and missing negative tabindex on in-page targets.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.elements": "List of elements with tabindex attributes",
        "details.violations": "List of tabindex usage violations",
        "details.warnings": "List of potential issues that are not violations",
        "details.summary": "Aggregated statistics about tabindex usage"
    },
    "tests": [
        {
            "id": "positive-tabindex",
            "name": "Positive Tabindex Values",
            "description": "Identifies elements with positive tabindex values that can disrupt natural tab order.",
            "impact": "high",
            "wcagCriteria": ["2.4.3"],
            "howToFix": "Replace positive tabindex values with tabindex='0'. Positive values override the natural tab order and make pages difficult to navigate for keyboard users.",
            "resultsFields": {
                "pageFlags.hasPositiveTabindex": "Indicates if any elements have positive tabindex values",
                "pageFlags.details.elementsWithPositiveTabindex": "Count of elements with positive tabindex values",
                "details.violations": "List of elements with positive tabindex values"
            }
        },
        {
            "id": "non-interactive-zero-tabindex",
            "name": "Non-interactive Elements with Zero Tabindex",
            "description": "Checks for non-interactive elements that have been made focusable with tabindex='0'.",
            "impact": "medium",
            "wcagCriteria": ["2.1.1", "4.1.2"],
            "howToFix": "Only apply tabindex='0' to elements that function as interactive controls with keyboard event handlers. Non-interactive elements should not be made focusable.",
            "resultsFields": {
                "pageFlags.hasNonInteractiveZeroTabindex": "Indicates if any non-interactive elements have tabindex='0'",
                "pageFlags.details.nonInteractiveWithZeroTabindex": "Count of non-interactive elements with tabindex='0'",
                "details.violations": "List of non-interactive elements with tabindex='0'"
            }
        },
        {
            "id": "missing-negative-tabindex",
            "name": "Missing Negative Tabindex on In-Page Targets",
            "description": "Verifies that non-interactive elements that are targets of in-page links have tabindex='-1'.",
            "impact": "medium",
            "wcagCriteria": ["2.4.3"],
            "howToFix": "Add tabindex='-1' to non-interactive elements that are targets of in-page links (e.g., id targets of anchor links) to allow them to receive focus programmatically.",
            "resultsFields": {
                "pageFlags.hasMissingRequiredTabindex": "Indicates if any in-page targets are missing tabindex='-1'",
                "pageFlags.details.missingRequiredTabindex": "Count of in-page targets missing tabindex='-1'",
                "details.violations": "List of in-page targets missing tabindex='-1'"
            }
        },
        {
            "id": "svg-tabindex",
            "name": "SVG Element Tabindex",
            "description": "Checks tabindex usage on SVG elements, which may have special considerations.",
            "impact": "low",
            "wcagCriteria": ["2.1.1"],
            "howToFix": "For SVG elements that need to be interactive, ensure proper roles and keyboard event handlers are added along with appropriate tabindex values.",
            "resultsFields": {
                "pageFlags.hasSvgTabindexWarnings": "Indicates if any SVG elements have potentially problematic tabindex values",
                "pageFlags.details.svgWithHighTabindex": "Count of SVG elements with high tabindex values",
                "details.warnings": "List of warnings related to SVG tabindex usage"
            }
        }
    ]
}

async def test_tabindex(page):
    """
    Test tabindex attributes for proper usage across different element types
    """
    try:
        tabindex_data = await page.evaluate('''
            () => {
                function isInteractiveElement(element) {
                    const interactiveTags = [
                        'a', 'button', 'input', 'select', 'textarea', 'video',
                        'audio', 'details', 'summary'
                    ];
                    const interactiveRoles = [
                        'button', 'checkbox', 'combobox', 'link', 'menuitem',
                        'radio', 'slider', 'spinbutton', 'switch', 'tab',
                        'textbox'
                    ];

                    return interactiveTags.includes(element.tagName.toLowerCase()) ||
                           (element.getAttribute('role') && 
                            interactiveRoles.includes(element.getAttribute('role')));
                }

                function isInPageTarget(element) {
                    return !!document.querySelector(`a[href="#${element.id}"]`);
                }

                function isWithinSVG(element) {
                    let current = element;
                    while (current && current !== document.body) {
                        if (current.tagName.toLowerCase() === 'svg') {
                            return true;
                        }
                        current = current.parentElement;
                    }
                    return false;
                }

                const results = {
                    elements: [],
                    violations: [],
                    warnings: [],
                    summary: {
                        totalElementsWithTabindex: 0,
                        elementsWithPositiveTabindex: 0,
                        nonInteractiveWithZeroTabindex: 0,
                        missingRequiredTabindex: 0,
                        svgWithHighTabindex: 0
                    }
                };

                // Find all elements with tabindex
                const elementsWithTabindex = document.querySelectorAll('[tabindex]');
                results.summary.totalElementsWithTabindex = elementsWithTabindex.length;

                // Process each element with tabindex
                elementsWithTabindex.forEach(element => {
                    const tabindex = parseInt(element.getAttribute('tabindex'));
                    const isInteractive = isInteractiveElement(element);
                    const isTarget = isInPageTarget(element);
                    const inSVG = isWithinSVG(element);

                    const elementInfo = {
                        tag: element.tagName.toLowerCase(),
                        role: element.getAttribute('role'),
                        tabindex: tabindex,
                        id: element.id || null,
                        isInteractive: isInteractive,
                        isTarget: isTarget,
                        inSVG: inSVG
                    };

                    results.elements.push(elementInfo);

                    // Check for violations
                    if (tabindex > 0 && !inSVG) {
                        results.violations.push({
                            type: 'positive-tabindex',
                            element: elementInfo.tag,
                            tabindex: tabindex,
                            id: element.id || null
                        });
                        results.summary.elementsWithPositiveTabindex++;
                    }

                    if (tabindex === 0 && !isInteractive) {
                        results.violations.push({
                            type: 'non-interactive-zero-tabindex',
                            element: elementInfo.tag,
                            id: element.id || null
                        });
                        results.summary.nonInteractiveWithZeroTabindex++;
                    }

                    if (inSVG && tabindex > 0) {
                        results.warnings.push({
                            type: 'svg-positive-tabindex',
                            element: elementInfo.tag,
                            tabindex: tabindex,
                            id: element.id || null
                        });
                        results.summary.svgWithHighTabindex++;
                    }
                });

                // Check for missing required tabindex
                const inPageTargets = document.querySelectorAll('*[id]');
                inPageTargets.forEach(element => {
                    if (isInPageTarget(element) && 
                        !isInteractiveElement(element) && 
                        element.getAttribute('tabindex') !== '-1') {
                        results.violations.push({
                            type: 'missing-negative-tabindex',
                            element: element.tagName.toLowerCase(),
                            id: element.id
                        });
                        results.summary.missingRequiredTabindex++;
                    }
                });

                return {
                    pageFlags: {
                        hasPositiveTabindex: results.summary.elementsWithPositiveTabindex > 0,
                        hasNonInteractiveZeroTabindex: results.summary.nonInteractiveWithZeroTabindex > 0,
                        hasMissingRequiredTabindex: results.summary.missingRequiredTabindex > 0,
                        hasSvgTabindexWarnings: results.summary.svgWithHighTabindex > 0,
                        details: {
                            totalElementsWithTabindex: results.summary.totalElementsWithTabindex,
                            elementsWithPositiveTabindex: results.summary.elementsWithPositiveTabindex,
                            nonInteractiveWithZeroTabindex: results.summary.nonInteractiveWithZeroTabindex,
                            missingRequiredTabindex: results.summary.missingRequiredTabindex,
                            svgWithHighTabindex: results.summary.svgWithHighTabindex
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'tabindex': {
                'pageFlags': tabindex_data['pageFlags'],
                'details': tabindex_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'tabindex': {
                'pageFlags': {
                    'hasPositiveTabindex': False,
                    'hasNonInteractiveZeroTabindex': False,
                    'hasMissingRequiredTabindex': False,
                    'hasSvgTabindexWarnings': False,
                    'details': {
                        'totalElementsWithTabindex': 0,
                        'elementsWithPositiveTabindex': 0,
                        'nonInteractiveWithZeroTabindex': 0,
                        'missingRequiredTabindex': 0,
                        'svgWithHighTabindex': 0
                    }
                },
                'details': {
                    'elements': [],
                    'violations': [{
                        'issue': 'Error evaluating tabindex',
                        'details': str(e)
                    }],
                    'warnings': [],
                    'summary': {
                        'totalElementsWithTabindex': 0,
                        'elementsWithPositiveTabindex': 0,
                        'nonInteractiveWithZeroTabindex': 0,
                        'missingRequiredTabindex': 0,
                        'svgWithHighTabindex': 0
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }