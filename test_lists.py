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
    "testName": "List Structure Analysis",
    "description": "Evaluates the implementation and styling of HTML lists to ensure proper semantic structure for screen reader users. This test identifies improper list implementations, excessive nesting, empty lists, and custom bullet styling that may impact accessibility.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.nestedLists": "Information about nested list structures",
        "details.customBulletUsage": "Information about custom bullet styling",
        "details.violations": "List of list structure violations",
        "details.warnings": "List of potential issues that are not violations"
    },
    "tests": [
        {
            "id": "fake-lists",
            "name": "Fake List Detection",
            "description": "Identifies elements that visually appear as lists but don't use proper list markup (ul/ol and li elements).",
            "impact": "high",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Replace fake lists with proper semantic HTML list elements (<ul> or <ol> with <li> elements) to ensure screen readers can identify and announce them correctly.",
            "resultsFields": {
                "pageFlags.hasFakeLists": "Indicates if fake lists are present",
                "pageFlags.details.fakeLists": "Count of fake list implementations",
                "details.violations": "List of violations including fake list implementations"
            }
        },
        {
            "id": "empty-lists",
            "name": "Empty List Detection",
            "description": "Identifies list elements (ul/ol) that contain no list items.",
            "impact": "medium",
            "wcagCriteria": ["4.1.1"],
            "howToFix": "Remove empty list elements, or add appropriate list items. Empty lists can confuse screen reader users who hear a list announced but find no items.",
            "resultsFields": {
                "pageFlags.hasEmptyLists": "Indicates if empty lists are present",
                "details.violations": "List of violations including empty lists"
            }
        },
        {
            "id": "deep-nesting",
            "name": "Excessive List Nesting",
            "description": "Identifies lists with excessive nesting depth that may cause navigation difficulties.",
            "impact": "medium",
            "wcagCriteria": ["2.4.10"],
            "howToFix": "Limit list nesting to 3 levels or fewer. For deeply nested information, consider alternative structures such as headings with content.",
            "resultsFields": {
                "pageFlags.hasDeepNesting": "Indicates if deeply nested lists are present",
                "pageFlags.details.maxNestingDepth": "Maximum nesting depth found",
                "details.warnings": "List of warnings including deep nesting issues"
            }
        },
        {
            "id": "custom-bullets",
            "name": "Custom Bullet Styling",
            "description": "Identifies lists with custom bullet styling that may impact screen reader announcements.",
            "impact": "low",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "When using custom bullets via CSS, ensure they don't replace the semantic list structure. Use list-style-type or list-style-image properties rather than replacing list items with non-list elements.",
            "resultsFields": {
                "pageFlags.hasCustomBullets": "Indicates if custom bullet styling is present",
                "pageFlags.details.customBullets": "Count of custom bullet implementations",
                "details.customBulletUsage": "List of list items with custom bullet styling"
            }
        }
    ]
}

async def test_lists(page):
    """
    Test proper implementation of lists and their styling
    """
    try:
        list_data = await page.evaluate('''
    () => {
        // Function to generate XPath for elements
        function getFullXPath(element) {
            if (!element) return '';
            
            function getElementIdx(el) {
                let count = 1;
                for (let sib = el.previousSibling; sib; sib = sib.previousSibling) {
                    if (sib.nodeType === 1 && sib.tagName === el.tagName) {
                        count++;
                    }
                }
                return count;
            }

            let path = '';
            while (element && element.nodeType === 1) {
                let idx = getElementIdx(element);
                let tagName = element.tagName.toLowerCase();
                path = `/${tagName}[${idx}]${path}`;
                element = element.parentNode;
            }
            return path;
        }
        
        {
                function analyzeListStyling(element) {
                    const computedStyle = window.getComputedStyle(element);
                    const beforePseudo = window.getComputedStyle(element, '::before');
                    
                    // Check for custom bullets using icons/images
                    const hasCustomBullet = {
                        hasIconFont: beforePseudo.getPropertyValue('font-family').includes('icon') ||
                                   beforePseudo.getPropertyValue('content').match(/[^\u0000-\u007F]/),
                        hasImage: beforePseudo.getPropertyValue('background-image') !== 'none' ||
                                element.querySelector('img, svg'),
                        hasExplicitContent: beforePseudo.getPropertyValue('content') !== 'none' &&
                                          beforePseudo.getPropertyValue('content') !== '""',
                        styleType: computedStyle.getPropertyValue('list-style-type')
                    }

                    return hasCustomBullet;
                }

                function calculateListDepth(element) {
                    let depth = 0;
                    let current = element;
                    
                    while (current.parentElement) {
                        if (current.parentElement.tagName.match(/^(UL|OL)$/)) {
                            depth++;
                        }
                        current = current.parentElement;
                    }
                    
                    return depth;
                }

                function analyzeListStructure() {
                    const allLists = document.querySelectorAll('ul, ol');
                    const violations = [];
                    const warnings = [];
                    const nestedLists = [];
                    const customBulletUsage = [];

                    // Find fake lists (elements styled as lists but not using ul/ol)
                    const potentialFakeLists = Array.from(document.querySelectorAll('div, span'))
                        .filter(el => {
                            const style = window.getComputedStyle(el);
                            return style.display === 'list-item' || 
                                   (el.innerHTML.includes('•') || el.innerHTML.includes('·')) ||
                                   el.querySelector('[class*="bullet"], [class*="list"]');
                        });

                    potentialFakeLists.forEach(element => {
                        violations.push({
                            issue: 'Fake list implementation',
                            element: element.tagName.toLowerCase(),
                            id: element.id || null,
                            class: element.className || null,
                            location: {
                                path: element.parentElement.tagName.toLowerCase(),
                                innerHTML: element.innerHTML.substring(0, 100)
                            }
                        });
                    });

                    allLists.forEach(list => {
                        const items = list.querySelectorAll('li');
                        const depth = calculateListDepth(list);
                        
                        // Check for empty lists
                        if (items.length === 0) {
                            violations.push({
                                issue: 'Empty list',
                                element: list.tagName.toLowerCase(),
                                id: list.id || null,
                                class: list.className || null
                            });
                        }

                        // Check nesting
                        if (depth > 0) {
                            nestedLists.push({
                                element: list.tagName.toLowerCase(),
                                id: list.id || null,
                                class: list.className || null,
                                depth: depth,
                                location: {
                                    parentList: list.parentElement.tagName.toLowerCase(),
                                    path: list.parentElement.tagName.toLowerCase()
                                }
                            });
                        }

                        // Check styling of list items
                        items.forEach(item => {
                            const bulletStyling = analyzeListStyling(item);
                            
                            if (bulletStyling.hasIconFont || 
                                bulletStyling.hasImage || 
                                bulletStyling.hasExplicitContent) {
                                customBulletUsage.push({
                                    element: item.tagName.toLowerCase(),
                                    id: item.id || null,
                                    class: item.className || null,
                                    styling: bulletStyling,
                                    location: {
                                        listType: list.tagName.toLowerCase(),
                                        path: item.parentElement.tagName.toLowerCase()
                                    }
                                });
                            }
                        });
                    });

                    // Generate warnings for deep nesting
                    const maxRecommendedDepth = 3;
                    nestedLists.forEach(nested => {
                        if (nested.depth > maxRecommendedDepth) {
                            warnings.push({
                                issue: 'Deep list nesting',
                                element: nested.element,
                                details: `List is nested ${nested.depth} levels deep (recommended max: ${maxRecommendedDepth})`,
                                location: nested.location
                            });
                        }
                    });

                    return {
                        summary: {
                            totalLists: allLists.length,
                            nestedListsCount: nestedLists.length,
                            customBulletCount: customBulletUsage.length,
                            fakeListsCount: potentialFakeLists.length,
                            maxNestingDepth: nestedLists.length > 0 ? 
                                Math.max(...nestedLists.map(n => n.depth)) : 0
                         },
                        details: {
                            nestedLists,
                            customBulletUsage,
                            violations,
                            warnings
                        }
                    };
                }

                const listResults = analyzeListStructure();

                return {
                    pageFlags: {
                        hasEmptyLists: listResults.details.violations.some(v => v.issue === 'Empty list'),
                        hasFakeLists: listResults.summary.fakeListsCount > 0,
                        hasCustomBullets: listResults.summary.customBulletCount > 0,
                        hasDeepNesting: listResults.summary.maxNestingDepth > 3,
                        details: {
                            totalLists: listResults.summary.totalLists,
                            nestedLists: listResults.summary.nestedListsCount,
                            customBullets: listResults.summary.customBulletCount,
                            fakeLists: listResults.summary.fakeListsCount,
                            maxNestingDepth: listResults.summary.maxNestingDepth
                         }
                    },
                    results: listResults.details
                };
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'lists': {
                'pageFlags': list_data['pageFlags'],
                'details': list_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'lists': {
                'pageFlags': {
                    'hasEmptyLists': False,
                    'hasFakeLists': False,
                    'hasCustomBullets': False,
                    'hasDeepNesting': False,
                    'details': {
                        'totalLists': 0,
                        'nestedLists': 0,
                        'customBullets': 0,
                        'fakeLists': 0,
                        'maxNestingDepth': 0
                     }
                },
                'details': {
                    'nestedLists': [],
                    'customBulletUsage': [],
                    'violations': [{
                        'issue': 'Error evaluating lists',
                        'details': str(e)
                    }],
                    'warnings': []
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }