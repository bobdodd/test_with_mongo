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
    "testName": "ARIA Landmark Analysis",
    "description": "Evaluates webpage landmark structure to ensure proper semantic organization and navigation for screen reader users. This test checks for required landmarks, proper nesting, and appropriate labeling of content regions.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key landmark issues",
        "details.landmarks": "List of all landmarks with their properties",
        "details.violations": "List of landmark structure violations",
        "details.contentOutsideLandmarks": "List of text content outside of landmarks",
        "details.summary": "Aggregated statistics about landmark structure"
    },
    "tests": [
        {
            "id": "main-landmark",
            "name": "Main Landmark Presence",
            "description": "Checks if the page has a main landmark that contains the primary content.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Add a <main> element or an element with role='main' that contains the primary content of the page.",
            "resultsFields": {
                "pageFlags.missingRequiredLandmarks": "Indicates if any required landmarks are missing",
                "pageFlags.details.missingLandmarks.main": "Indicates if the main landmark is missing",
                "details.summary.hasMain": "Boolean indicating if main landmark exists"
            }
        },
        {
            "id": "banner-landmark",
            "name": "Banner Landmark",
            "description": "Verifies that the page has a banner landmark for site-wide header content.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Use a top-level <header> element or an element with role='banner' for the site header that contains site-wide information.",
            "resultsFields": {
                "pageFlags.details.missingLandmarks.banner": "Indicates if the banner landmark is missing",
                "details.summary.hasBanner": "Boolean indicating if banner landmark exists"
            }
        },
        {
            "id": "contentinfo-landmark",
            "name": "Contentinfo Landmark",
            "description": "Checks if the page has a contentinfo landmark for footer content.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Use a top-level <footer> element or an element with role='contentinfo' for the site footer that contains information about the document.",
            "resultsFields": {
                "pageFlags.details.missingLandmarks.contentinfo": "Indicates if the contentinfo landmark is missing",
                "details.summary.hasContentinfo": "Boolean indicating if contentinfo landmark exists"
            }
        },
        {
            "id": "content-in-landmarks",
            "name": "Content Within Landmarks",
            "description": "Evaluates whether all content on the page is contained within appropriate landmarks.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Ensure all page content is contained within appropriate landmark regions to provide context and structure for screen reader users.",
            "resultsFields": {
                "pageFlags.hasContentOutsideLandmarks": "Indicates if content exists outside of landmarks",
                "pageFlags.details.contentOutsideLandmarksCount": "Count of text nodes outside landmarks",
                "details.contentOutsideLandmarks": "List of content found outside landmark regions"
            }
        },
        {
            "id": "duplicate-landmarks",
            "name": "Duplicate Landmark Identification",
            "description": "Checks if multiple landmarks of the same type have unique labels to distinguish them.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "When using multiple landmarks of the same type (e.g., navigation, complementary), provide unique names using aria-label or aria-labelledby attributes.",
            "resultsFields": {
                "pageFlags.hasDuplicateLandmarksWithoutNames": "Indicates if duplicate landmarks lack unique names",
                "pageFlags.details.duplicateLandmarks": "Count of each landmark type and unique names",
                "details.violations": "List of landmark violations including duplicates without labels"
            }
        },
        {
            "id": "landmark-nesting",
            "name": "Landmark Nesting",
            "description": "Evaluates proper nesting of landmarks to ensure top-level landmarks aren't nested inside others.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Ensure main, banner, contentinfo and complementary landmarks are not nested inside other landmarks.",
            "resultsFields": {
                "pageFlags.hasNestedTopLevelLandmarks": "Indicates if top-level landmarks are improperly nested",
                "details.violations": "List of landmark violations including nested landmarks"
            }
        }
    ]
}

async def test_landmarks(page):
    """
    Test page landmark structure and requirements, with proper handling of
    implicit landmark roles for header and footer elements
    """
    try:
        landmarks_data = await page.evaluate('''
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
                function getLandmarkName(element) {
                    const ariaLabel = element.getAttribute('aria-label');
                    if (ariaLabel) return ariaLabel.trim();

                    const labelledBy = element.getAttribute('aria-labelledby');
                    if (labelledBy) {
                        const labelElements = labelledBy.split(' ')
                            .map(id => document.getElementById(id))
                            .filter(el => el);
                        if (labelElements.length > 0) {
                            return labelElements.map(el => el.textContent.trim()).join(' ');
                        }
                    }

                    // Check for heading as label for forms
                    if (element.tagName.toLowerCase() === 'form' || element.getAttribute('role') === 'form') {
                        const heading = element.querySelector('h1, h2, h3, h4, h5, h6');
                        if (heading) {
                            return heading.textContent.trim();
                        }
                    }

                    return null;
                }

                function isTopLevelElement(element) {
                    // Check if the element is a direct child of body
                    if (element.parentElement === document.body) return true;

                    // Check if the element is within article or main or other sectioning content
                    let parent = element.parentElement;
                    while (parent && parent !== document.body) {
                        const parentTag = parent.tagName.toLowerCase();
                        if (['article', 'aside', 'main', 'nav', 'section'].includes(parentTag)) {
                            return false;
                        }
                        parent = parent.parentElement;
                    }
                    return true;
                }

                function getElementPath(element) {
                    const path = [];
                    let current = element;
                    while (current && current !== document.body) {
                        path.unshift({
                            tag: current.tagName.toLowerCase(),
                            role: current.getAttribute('role'),
                            name: getLandmarkName(current)
                        });
                        current = current.parentElement;
                    }
                    return path;
                }

                const results = {
                    landmarks: [],
                    violations: [],
                    contentOutsideLandmarks: [],
                    summary: {
                        hasMain: false,
                        hasBanner: false,
                        hasContentinfo: false,
                        hasSearch: false,
                        totalLandmarks: 0,
                        duplicateLandmarks: {}
                    }
                };

                // Track landmark names for uniqueness check
                const landmarkCounts = {};
                const landmarkNames = {};

                // Find all landmarks
                const landmarkElements = [
                    ...document.querySelectorAll(
                        'main, [role="main"], header, [role="banner"], footer, [role="contentinfo"], ' +
                        'nav, [role="navigation"], [role="search"], form, [role="form"], ' +
                        'aside, [role="complementary"], section[aria-label], section[aria-labelledby], ' +
                        '[role="region"][aria-label], [role="region"][aria-labelledby]'
                    )
                ];

                landmarkElements.forEach(element => {
                    const tag = element.tagName.toLowerCase();
                    let role = element.getAttribute('role');
                    const isTopLevel = isTopLevelElement(element);
                    
                    // Handle implicit roles with special cases for header and footer
                    if (!role) {
                        switch (tag) {
                            case 'main': 
                                role = 'main'; 
                                break;
                            case 'header': 
                                // header is banner only if it's at the top level
                                role = isTopLevel ? 'banner' : 'region';
                                break;
                            case 'footer': 
                                // footer is contentinfo only if it's at the top level
                                role = isTopLevel ? 'contentinfo' : 'region';
                                break;
                            case 'nav': 
                                role = 'navigation'; 
                                break;
                            case 'aside': 
                                role = 'complementary'; 
                                break;
                            case 'form': 
                                role = 'form'; 
                                break;
                            case 'section': 
                                role = 'region'; 
                                break;
                        }
                    }

                    const name = getLandmarkName(element);
                    const path = getElementPath(element);

                    // Track landmark counts and names
                    landmarkCounts[role] = (landmarkCounts[role] || 0) + 1;
                    if (name) {
                        if (!landmarkNames[role]) landmarkNames[role] = new Set();
                        landmarkNames[role].add(name);
                    }

                    const landmarkInfo = {
                        role: role,
                        tag: tag,
                        name: name,
                        path: path,
                        hasValidName: !!name,
                        isTopLevel: ['banner', 'contentinfo', 'main', 'complementary'].includes(role),
                        isImplicitRole: !element.getAttribute('role')
                    };

                    results.landmarks.push(landmarkInfo);

                    // Update summary for main landmark
                    if (role === 'main') {
                        results.summary.hasMain = true;
                    }

                    // Update summary for banner (including top-level header)
                    if (role === 'banner' || (tag === 'header' && isTopLevel)) {
                        results.summary.hasBanner = true;
                    }

                    // Update summary for contentinfo (including top-level footer)
                    if (role === 'contentinfo' || (tag === 'footer' && isTopLevel)) {
                        results.summary.hasContentinfo = true;
                    }

                    // Update summary for search
                    if (role === 'search') {
                        results.summary.hasSearch = true;
                    }

                    // Check for violations
                    if (landmarkCounts[role] > 1 && !name) {
                        results.violations.push({

                            xpath: getFullXPath(element),
                            type: 'duplicate-landmark-without-name',
                            role: role,
                            element: tag
                        });
                    }

                    // Check for nested top-level landmarks
                    if (landmarkInfo.isTopLevel) {
                        const parentLandmarks = path.slice(0, -1)
                            .filter(p => ['banner', 'contentinfo', 'main', 'complementary']
                            .includes(p.role));
                        if (parentLandmarks.length > 0) {
                            results.violations.push({

                                xpath: getFullXPath(element),
                                type: 'nested-top-level-landmark',
                                role: role,
                                element: tag,
                                nestedWithin: parentLandmarks.map(p => p.role)
                            });
                        }
                    }

                    // Check for forms without labels
                    if (role === 'form' && !name) {
                        results.violations.push({

                            xpath: getFullXPath(element),
                            type: 'unlabelled-form',
                            element: tag
                        });
                    }

                    // Check for sections/regions without labels
                    if (role === 'region' && !name) {
                        results.violations.push({

                            xpath: getFullXPath(element),
                            type: 'unlabelled-region',
                            element: tag
                        });
                    }
                });

                // Find content outside landmarks
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: function(node) {
                            if (node.textContent.trim().length === 0) return NodeFilter.FILTER_REJECT;
                            
                            // Check if node is within a landmark
                            let current = node.parentElement;
                            while (current && current !== document.body) {
                                if (current.matches(
                                    'main, [role="main"], header, [role="banner"], ' +
                                    'footer, [role="contentinfo"], nav, [role="navigation"], ' +
                                    '[role="search"], form, [role="form"], aside, ' +
                                    '[role="complementary"], section[aria-label], ' +
                                    'section[aria-labelledby], [role="region"][aria-label], ' +
                                    '[role="region"][aria-labelledby]'
                                )) {
                                    return NodeFilter.FILTER_REJECT;
                                }
                                current = current.parentElement;
                            }
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    }
                );

                while (walker.nextNode()) {
                    const node = walker.currentNode;
                    results.contentOutsideLandmarks.push({
                        text: node.textContent.trim().substring(0, 50),
                        path: getElementPath(node.parentElement)
                    });
                }

                // Update summary
                results.summary.totalLandmarks = landmarkElements.length;
                results.summary.duplicateLandmarks = Object.entries(landmarkCounts)
                    .filter(([role, count]) => count > 1)
                    .reduce((acc, [role, count]) => {
                        acc[role] = {
                            count: count,
                            uniqueNames: landmarkNames[role] ? landmarkNames[role].size : 0
                        };
                        return acc;
                    }, {});

                return {
                    pageFlags: {
                        missingRequiredLandmarks: !results.summary.hasMain || 
                                                !results.summary.hasBanner || 
                                                !results.summary.hasContentinfo,
                        hasContentOutsideLandmarks: results.contentOutsideLandmarks.length > 0,
                        hasDuplicateLandmarksWithoutNames: results.violations
                            .some(v => v.type === 'duplicate-landmark-without-name'),
                        hasNestedTopLevelLandmarks: results.violations
                            .some(v => v.type === 'nested-top-level-landmark'),
                        details: {
                            missingLandmarks: {
                                main: !results.summary.hasMain,
                                banner: !results.summary.hasBanner,
                                contentinfo: !results.summary.hasContentinfo,
                                search: !results.summary.hasSearch
                             },
                            contentOutsideLandmarksCount: results.contentOutsideLandmarks.length,
                            duplicateLandmarks: results.summary.duplicateLandmarks
                        }
                    },
                    results: results
                };
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'landmarks': {
                'pageFlags': landmarks_data['pageFlags'],
                'details': landmarks_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'landmarks': {
                'pageFlags': {
                    'missingRequiredLandmarks': True,
                    'hasContentOutsideLandmarks': False,
                    'hasDuplicateLandmarksWithoutNames': False,
                    'hasNestedTopLevelLandmarks': False,
                    'details': {
                        'missingLandmarks': {
                            'main': True,
                            'banner': True,
                            'contentinfo': True,
                            'search': True
                         },
                        'contentOutsideLandmarksCount': 0,
                        'duplicateLandmarks': {}
                    }
                },
                'details': {
                    'landmarks': [],
                    'violations': [{
                        'issue': 'Error evaluating landmarks',
                        'details': str(e)
                    }],
                    'contentOutsideLandmarks': [],
                    'summary': {
                        'hasMain': False,
                        'hasBanner': False,
                        'hasContentinfo': False,
                        'hasSearch': False,
                        'totalLandmarks': 0,
                        'duplicateLandmarks': {}
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }