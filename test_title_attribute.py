from datetime import datetime


# Test documentation with information about the title attribute test
TEST_DOCUMENTATION = {
    "testName": "Title Attribute Test",
    "description": "Tests for proper usage of the title attribute on HTML elements. According to accessibility guidelines, the title attribute should primarily be used on iframe elements to provide descriptive labels. Using title attributes on other elements can create issues for screen reader users and is generally not recommended.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "pageFlags": "Boolean flags indicating the presence of accessibility issues",
        "details": "Detailed information about the test results"
    },
    "tests": [
        {
            "id": "title-attribute-usage",
            "name": "Title Attribute Usage",
            "description": "Checks if title attributes are used properly (only on iframe elements)",
            "impact": "medium",
            "wcagCriteria": ["2.4.1", "2.4.2", "4.1.2"],
            "howToFix": "Remove title attributes from non-iframe elements. For elements like links, buttons, and controls, use properly associated text labels, aria-label, or aria-labelledby instead. For iframes, use the title attribute to provide a descriptive label for the frame content.",
            "resultsFields": {
                "improperUse": "List of elements with improperly used title attributes",
                "properUse": "List of elements with properly used title attributes (iframes)",
                "violations": "Detailed descriptions of each title attribute violation"
            }
        }
    ]
}


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
async def test_title_attribute(page):
    """
    Test proper usage of title attribute - should only be used on iframes
    """
    try:
        title_data = await page.evaluate('''
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
                function analyzeTitleAttributes() {
                    const elementsWithTitle = Array.from(document.querySelectorAll('[title]'))
                    const improperTitleUse = []
                    const properTitleUse = []

                    elementsWithTitle.forEach(element => {
                        const titleValue = element.getAttribute('title')
                        const elementInfo = {
                            element: element.tagName.toLowerCase(),
                            id: element.id || null,
                            class: element.className || null,
                            title: titleValue,
                            textContent: element.textContent.trim().substring(0, 100),
                            location: {
                                inHeader: element.closest('header') !== null,
                                inNav: element.closest('nav') !== null,
                                inMain: element.closest('main') !== null,
                                inFooter: element.closest('footer') !== null
                            }
                        }

                        if (element.tagName.toLowerCase() !== 'iframe') {
                            improperTitleUse.push(elementInfo)
                        } else {
                            properTitleUse.push(elementInfo)
                        }
                    })

                    return {
                        improperTitleUse,
                        properTitleUse,
                        summary: {
                            totalTitleAttributes: elementsWithTitle.length,
                            improperUseCount: improperTitleUse.length,
                            properUseCount: properTitleUse.length
                         }
                    }
                }

                const titleResults = analyzeTitleAttributes()

                return {
                    pageFlags: {
                        hasImproperTitleAttributes: titleResults.improperTitleUse.length > 0,
                        details: {
                            totalTitleAttributes: titleResults.summary.totalTitleAttributes,
                            improperUseCount: titleResults.summary.improperUseCount,
                            properUseCount: titleResults.summary.properUseCount
                         }
                    },
                    results: {
                        improperUse: titleResults.improperTitleUse,
                        properUse: titleResults.properTitleUse,
                        violations: titleResults.improperTitleUse.map(item => ({
                            issue: 'Improper use of title attribute',
                            element: item.element,
                            details: `Title attribute should only be used on iframes. Found on ${item.element}` +
                                   `${item.id ? ` with id "${item.id}"` : ''} with title "${item.title}"`
                        }))
                    }
                }
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'titleAttribute': {
                'pageFlags': title_data['pageFlags'],
                'details': title_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'titleAttribute': {
                'pageFlags': {
                    'hasImproperTitleAttributes': False,
                    'details': {
                        'totalTitleAttributes': 0,
                        'improperUseCount': 0,
                        'properUseCount': 0
                     }
                },
                'details': {
                    'improperUse': [],
                    'properUse': [],
                    'violations': [{
                        'issue': 'Error evaluating title attributes',
                        'details': str(e)
                    }]
                },
                'documentation': TEST_DOCUMENTATION }
        }