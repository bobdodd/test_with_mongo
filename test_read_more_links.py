from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Generic Link Text Analysis",
    "description": "Evaluates links and buttons with generic text like 'Read more' or 'Click here' for proper accessibility. This test identifies elements with non-descriptive text that lack proper accessible names to provide context for screen reader users.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.items": "List of generic links with their properties",
        "details.violations": "List of accessibility violations in generic links",
        "details.summary": "Aggregated statistics about generic link usage"
    },
    "tests": [
        {
            "id": "generic-link-detection",
            "name": "Generic Link Text Detection",
            "description": "Identifies links and buttons with non-descriptive text like 'Read more', 'Learn more', 'Click here', etc.",
            "impact": "informational",
            "wcagCriteria": ["2.4.4", "2.4.9"],
            "howToFix": "This test is informational and identifies generic links that may need enhanced accessible names.",
            "resultsFields": {
                "pageFlags.hasGenericReadMoreLinks": "Indicates if generic link text is present",
                "pageFlags.details.totalGenericLinks": "Count of links with generic text",
                "details.items": "List of elements with generic text"
            }
        },
        {
            "id": "accessible-name-quality",
            "name": "Generic Link Accessible Name",
            "description": "Checks if links with generic visible text have proper accessible names that provide additional context.",
            "impact": "high",
            "wcagCriteria": ["2.4.4", "2.4.9"],
            "howToFix": "Add an aria-label attribute to generic links that starts with the visible text and adds descriptive context (e.g., a link with visible text 'Read more' might have aria-label='Read more about our accessibility policy').",
            "resultsFields": {
                "pageFlags.hasInvalidReadMoreLinks": "Indicates if links with generic text lack proper accessible names",
                "pageFlags.details.violationsCount": "Count of links with invalid accessible names",
                "details.violations": "List of generic links with invalid accessible names"
            }
        },
        {
            "id": "accessible-name-pattern",
            "name": "Accessible Name Pattern",
            "description": "Verifies that accessible names for generic links follow the pattern of starting with the visible text.",
            "impact": "medium",
            "wcagCriteria": ["2.5.3"],
            "howToFix": "Ensure the accessible name (via aria-label) begins with the same text that is visibly displayed on the link, then adds additional context.",
            "resultsFields": {
                "details.items[].isValid": "Boolean indicating if a specific link follows the proper accessible name pattern",
                "details.violations": "List of links with pattern violations"
            }
        }
    ]
}

async def test_read_more_links(page):
    """
    Test 'read more' type links and buttons for proper accessible names
    """
    try:
        read_more_data = await page.evaluate('''
            () => {
                function getAccessibleName(element) {
                    // Check various sources for accessible name in correct order
                    const ariaLabel = element.getAttribute('aria-label');
                    if (ariaLabel) return ariaLabel.trim();

                    const ariaLabelledBy = element.getAttribute('aria-labelledby');
                    if (ariaLabelledBy) {
                        const labelElements = ariaLabelledBy.split(' ')
                            .map(id => document.getElementById(id))
                            .filter(el => el);
                        if (labelElements.length > 0) {
                            return labelElements.map(el => el.textContent.trim()).join(' ');
                        }
                    }

                    // For buttons/links, combine text content with aria-label if both exist
                    const visibleText = element.textContent.trim();
                    if (ariaLabel && visibleText) {
                        return `${visibleText} ${ariaLabel}`;
                    }

                    return visibleText;
                }

                const results = {
                    items: [],
                    violations: [],
                    summary: {
                        totalGenericLinks: 0,
                        violationsCount: 0
                    }
                };

                // Regular expressions for matching generic text
                const genericTextPatterns = [
                    /^read more$/i,
                    /^learn more$/i,
                    /^more$/i,
                    /^more\.\.\.$/i,
                    /^read more\.\.\.$/i,
                    /^learn more\.\.\.$/i,
                    /^click here$/i,
                    /^details$/i,
                    /^more details$/i
                ];

                // Find all links and buttons
                const elements = Array.from(document.querySelectorAll('a, button, [role="button"], [role="link"]'));

                elements.forEach(element => {
                    const visibleText = element.textContent.trim();
                    const accessibleName = getAccessibleName(element);
                    
                    // Check if this is a generic "read more" type element
                    const isGenericText = genericTextPatterns.some(pattern => 
                        pattern.test(visibleText)
                    );

                    if (isGenericText) {
                        results.summary.totalGenericLinks++;

                        const elementInfo = {
                            tag: element.tagName.toLowerCase(),
                            role: element.getAttribute('role'),
                            visibleText: visibleText,
                            accessibleName: accessibleName,
                            location: {
                                href: element.href || null,
                                id: element.id || null,
                                path: element.textContent
                            },
                            isValid: accessibleName.length > visibleText.length && 
                                    accessibleName.toLowerCase().startsWith(visibleText.toLowerCase())
                        };

                        results.items.push(elementInfo);

                        // Check for violations
                        if (!elementInfo.isValid) {
                            results.violations.push({
                                type: 'invalid-accessible-name',
                                element: elementInfo.tag,
                                visibleText: visibleText,
                                accessibleName: accessibleName,
                                required: 'Accessible name must be longer than and start with the visible text',
                                location: elementInfo.location
                            });
                            results.summary.violationsCount++;
                        }
                    }
                });

                return {
                    pageFlags: {
                        hasGenericReadMoreLinks: results.summary.totalGenericLinks > 0,
                        hasInvalidReadMoreLinks: results.summary.violationsCount > 0,
                        details: {
                            totalGenericLinks: results.summary.totalGenericLinks,
                            violationsCount: results.summary.violationsCount
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'read_more_links': {
                'pageFlags': read_more_data['pageFlags'],
                'details': read_more_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'read_more_links': {
                'pageFlags': {
                    'hasGenericReadMoreLinks': False,
                    'hasInvalidReadMoreLinks': False,
                    'details': {
                        'totalGenericLinks': 0,
                        'violationsCount': 0
                    }
                },
                'details': {
                    'items': [],
                    'violations': [{
                        'issue': 'Error evaluating read more links',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalGenericLinks': 0,
                        'violationsCount': 0
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }