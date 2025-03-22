from datetime import datetime



# Handle import errors gracefully - allows both package and direct imports
try:
    # Try direct import first (for when run as a script)
    from src.test_with_mongo.section_reporting_template import add_section_info_to_test_results, print_violations_with_sections
except ImportError:
    try:
        # Then try relative import (for when imported as a module)
        from .section_reporting_template import add_section_info_to_test_results, print_violations_with_sections
    except ImportError:
        # Fallback to non-relative import 
        from section_reporting_template import add_section_info_to_test_results, print_violations_with_sections
# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Heading Structure Analysis",
    "description": "Evaluates the document's heading structure to ensure proper hierarchy, positioning, and semantic markup. Properly structured headings are essential for screen reader users to navigate content and understand document organization.",
    "version": "1.2.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key heading issues",
        "details.headings": "List of all heading elements with their properties",
        "details.hierarchy": "Count of headings at each level",
        "details.violations": "List of heading violations",
        "details.summary": "Aggregated statistics about heading structure"
    },
    "tests": [
        {
            "id": "h1-presence",
            "name": "H1 Presence and Uniqueness",
            "description": "Checks if the page has exactly one H1 heading that serves as the main title of the page.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1", "2.4.6"],
            "howToFix": "Ensure that each page has exactly one H1 element that clearly describes the page content. The H1 should typically be within the main content area.",
            "resultsFields": {
                "pageFlags.missingH1": "Indicates if the page is missing an H1 heading",
                "pageFlags.multipleH1s": "Indicates if the page has more than one H1 heading",
                "details.summary.h1Count": "Count of H1 headings on the page"
            }
        },
        {
            "id": "heading-hierarchy",
            "name": "Heading Hierarchy",
            "description": "Verifies that headings follow a logical hierarchy without skipping levels (e.g., H1 to H3 without H2).",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.10"],
            "howToFix": "Ensure headings follow a logical order (H1, H2, H3, etc.) without skipping levels. Each subsection should be under the appropriate parent heading level.",
            "resultsFields": {
                "pageFlags.hasHierarchyGaps": "Indicates if the heading structure has gaps in hierarchy",
                "pageFlags.details.hierarchyGaps": "List of heading levels that were skipped",
                "details.hierarchy": "Count of headings at each level"
            }
        },
        {
            "id": "heading-landmark-position",
            "name": "Heading Landmark Position",
            "description": "Checks if headings are properly positioned within landmarks, particularly that the main H1 is within the main content area.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Place the primary H1 heading within the main content area. Use appropriate heading levels in other landmarks based on their semantic importance.",
            "resultsFields": {
                "pageFlags.hasHeadingsBeforeMain": "Indicates if headings appear before the main content area",
                "details.summary.headingsBeforeMain": "Count of headings outside the main content area",
                "details.summary.headingsInMain": "Count of headings inside the main content area"
            }
        },
        {
            "id": "visual-heading-hierarchy",
            "name": "Visual Heading Hierarchy",
            "description": "Evaluates if the visual presentation of headings matches their semantic level (e.g., H2s should not appear larger than H1s).",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Ensure that the visual styling of headings (font size, weight, etc.) corresponds to their semantic level, with higher-level headings having greater visual prominence.",
            "resultsFields": {
                "pageFlags.hasVisualHierarchyIssues": "Indicates if visual styling contradicts semantic hierarchy",
                "pageFlags.details.visualHierarchyIssues": "List of heading level pairs where visual hierarchy is incorrect"
            }
        },
        {
            "id": "empty-headings",
            "name": "Empty Headings",
            "description": "Identifies headings that have no text content or contain only whitespace.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.6"],
            "howToFix": "Ensure all heading elements contain descriptive text content. Remove empty headings or replace them with appropriate content.",
            "resultsFields": {
                "details.violations": "List of heading violations including empty headings"
            }
        },
        {
            "id": "heading-accessibility-attributes",
            "name": "Heading Accessibility Attributes",
            "description": "Checks for proper ARIA attributes on headings, including correct aria-level on role='heading' elements and tabindex on link targets.",
            "impact": "medium",
            "wcagCriteria": ["4.1.2"],
            "howToFix": "Add aria-level attribute to elements with role='heading'. Add tabindex='-1' to heading elements that are targets of in-page links.",
            "resultsFields": {
                "details.violations": "List of heading violations including missing ARIA attributes"
            }
        }
    ]
}

async def test_headings(page):
    """
    Test heading structure and requirements including:
    - H1 presence and uniqueness
    - Heading hierarchy
    - Location relative to landmarks
    - Visual styling and alignment
    - Accessibility attributes
    """
    try:
        headings_data = await page.evaluate('''
            () => {
                function isInLandmark(element, landmarkRole) {
                    let current = element;
                    while (current && current !== document.body) {
                        if (current.getAttribute('role') === landmarkRole ||
                            (landmarkRole === 'main' && current.tagName.toLowerCase() === 'main') ||
                            (landmarkRole === 'contentinfo' && current.tagName.toLowerCase() === 'footer')) {
                            return true;
                        }
                        current = current.parentElement;
                    }
                    return false;
                }

                function getHeadingLevel(element) {
                    if (element.tagName.match(/^H[1-6]$/i)) {
                        return parseInt(element.tagName[1]);
                    }
                    if (element.getAttribute('role') === 'heading') {
                        const level = element.getAttribute('aria-level');
                        return level ? parseInt(level) : null;
                    }
                    return null;
                }

                function isHeadingNested(heading) {
                    let parent = heading.parentElement;
                    while (parent && parent !== document.body) {
                        if (parent.tagName.match(/^H[1-6]$/i) ||
                            (parent.getAttribute('role') === 'heading')) {
                            return true;
                        }
                        parent = parent.parentElement;
                    }
                    return false;
                }

                function checkAlignment(heading, content) {
                    const headingStyle = window.getComputedStyle(heading);
                    const headingRect = heading.getBoundingClientRect();
                    const contentRect = content ? content.getBoundingClientRect() : null;

                    const textAlign = headingStyle.textAlign;
                    
                    if (contentRect) {
                        const isLeftAligned = Math.abs(headingRect.left - contentRect.left) < 5;
                        return {
                            alignment: textAlign,
                            alignedWithContent: isLeftAligned,
                            isAcceptable: textAlign === 'left' || textAlign === 'center'
                         };
                    }

                    return {
                        alignment: textAlign,
                        alignedWithContent: null,
                        isAcceptable: textAlign === 'left' || textAlign === 'center'
                     };
                }

                function getFontSize(element) {
                    return parseFloat(window.getComputedStyle(element).fontSize);
                }

                const results = {
                    headings: [],
                    hierarchy: {},
                    violations: [],
                    summary: {
                        totalHeadings: 0,
                        h1Count: 0,
                        headingsBeforeMain: 0,
                        headingsInMain: 0,
                        hasContentinfoH2: false,
                        hierarchyGaps: [],
                        visualHierarchyIssues: []
                    }
                };

                // Get main landmark for reference
                const mainElement = document.querySelector('main, [role="main"]');
                const contentinfoElement = document.querySelector('footer, [role="contentinfo"]');

                // Track font sizes for visual hierarchy check
                const levelFontSizes = {};

                // Get all headings
                const headingElements = document.querySelectorAll(
                    'h1, h2, h3, h4, h5, h6, [role="heading"]'
                );

                // First pass to collect levels and check H1
                headingElements.forEach(heading => {
                    const level = getHeadingLevel(heading);
                    if (level) {
                        results.hierarchy[level] = (results.hierarchy[level] || 0) + 1;
                        if (level === 1) results.summary.h1Count++;
                    }
                });

                // Check for hierarchy gaps
                for (let i = 1; i < 6; i++) {
                    if (!results.hierarchy[i] && results.hierarchy[i + 1]) {
                        results.summary.hierarchyGaps.push(i);
                    }
                }

                // Process each heading
                headingElements.forEach((heading, index) => {
                    const level = getHeadingLevel(heading);
                    const isInMain = isInLandmark(heading, 'main');
                    const isInContentinfo = isInLandmark(heading, 'contentinfo');
                    const text = heading.textContent.trim();
                    const fontSize = getFontSize(heading);
                    
                    // Track font sizes for visual hierarchy
                    if (level) {
                        if (!levelFontSizes[level]) {
                            levelFontSizes[level] = fontSize;
                        } else {
                            levelFontSizes[level] = Math.max(levelFontSizes[level], fontSize);
                        }
                    }

                    // Check alignment with following content
                    const nextElement = heading.nextElementSibling;
                    const alignmentInfo = checkAlignment(heading, nextElement);

                    const headingInfo = {
                        tag: heading.tagName.toLowerCase(),
                        level: level,
                        text: text,
                        isInMain: isInMain,
                        isInContentinfo: isInContentinfo,
                        hasTabIndex: heading.getAttribute('tabindex') === '-1',
                        isLinkTarget: document.querySelector(`a[href="#${heading.id}"]`) !== null,
                        isNested: isHeadingNested(heading),
                        alignment: alignmentInfo,
                        fontSize: fontSize,
                        attributes: {
                            role: heading.getAttribute('role'),
                            ariaLevel: heading.getAttribute('aria-level'),
                            id: heading.id || null
                        }
                    };

                    results.headings.push(headingInfo);

                    // Check for violations
                    if (!level || level < 1 || level > 6) {
                        results.violations.push({
                            type: 'invalid-heading-level',
                            element: headingInfo.tag,
                            details: 'Heading level must be between 1 and 6'
                        });
                    }

                    if (!text) {
                        results.violations.push({
                            type: 'empty-heading',
                            element: headingInfo.tag,
                            level: level
                        });
                    }

                    if (heading.getAttribute('role') === 'heading' && !heading.getAttribute('aria-level')) {
                        results.violations.push({
                            type: 'missing-aria-level',
                            element: headingInfo.tag
                        });
                    }

                    if (headingInfo.isLinkTarget && !headingInfo.hasTabIndex) {
                        results.violations.push({
                            type: 'missing-tabindex',
                            element: headingInfo.tag,
                            id: heading.id
                        });
                    }

                    if (headingInfo.isNested) {
                        results.violations.push({
                            type: 'nested-heading',
                            element: headingInfo.tag,
                            level: level
                        });
                    }

                    // Track location-specific information
                    if (!isInMain) {
                        results.summary.headingsBeforeMain++;
                        if (level === 1) {
                            results.violations.push({
                                type: 'h1-outside-main',
                                location: 'before-main'
                            });
                        }
                        if (level && level < 2) {
                            results.violations.push({
                                type: 'invalid-level-before-main',
                                level: level
                            });
                        }
                    } else {
                        results.summary.headingsInMain++;
                    }

                    // Check contentinfo H2
                    if (isInContentinfo && index === 0 && level !== 2) {
                        results.violations.push({
                            type: 'contentinfo-wrong-heading-level',
                            level: level
                        });
                    }
                });

                // Check visual hierarchy
                let previousSize = Infinity;
                for (let i = 1; i <= 6; i++) {
                    if (levelFontSizes[i]) {
                        if (levelFontSizes[i] > previousSize) {
                            results.summary.visualHierarchyIssues.push({
                                level: i,
                                fontSize: levelFontSizes[i],
                                previousSize: previousSize
                            });
                        }
                        previousSize = levelFontSizes[i];
                    }
                }

                // Update summary
                results.summary.totalHeadings = headingElements.length;

                return {
                    pageFlags: {
                        missingH1: results.summary.h1Count === 0,
                        multipleH1s: results.summary.h1Count > 1,
                        hasHierarchyGaps: results.summary.hierarchyGaps.length > 0,
                        hasHeadingsBeforeMain: results.summary.headingsBeforeMain > 0,
                        hasVisualHierarchyIssues: results.summary.visualHierarchyIssues.length > 0,
                        details: {
                            h1Count: results.summary.h1Count,
                            hierarchyGaps: results.summary.hierarchyGaps,
                            headingsBeforeMain: results.summary.headingsBeforeMain,
                            visualHierarchyIssues: results.summary.visualHierarchyIssues
                         }
                    },
                    results: results
                };
            }
        ''')

        # Add section information to results
        headings_data['results'] = add_section_info_to_test_results(page, headings_data['results'])
        
        # Print violations with section information for debugging
        print_violations_with_sections(headings_data['results']['violations'])
        
        return {
            'headings': {
                'pageFlags': headings_data['pageFlags'],
                'details': headings_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'headings': {
                'pageFlags': {
                    'missingH1': True,
                    'multipleH1s': False,
                    'hasHierarchyGaps': False,
                    'hasHeadingsBeforeMain': False,
                    'hasVisualHierarchyIssues': False,
                    'details': {
                        'h1Count': 0,
                        'hierarchyGaps': [],
                        'headingsBeforeMain': 0,
                        'visualHierarchyIssues': []
                     }
                },
                'details': {
                    'headings': [],
                    'violations': [{
                        'issue': 'Error evaluating headings',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalHeadings': 0,
                        'h1Count': 0,
                        'headingsBeforeMain': 0,
                        'headingsInMain': 0,
                        'hasContentinfoH2': False,
                        'hierarchyGaps': [],
                        'visualHierarchyIssues': []
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }