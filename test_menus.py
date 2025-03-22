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
    "testName": "Navigation Menu Analysis",
    "description": "Evaluates website navigation menus and landmarks for proper semantic structure and ARIA attributes. This test identifies navigation elements without accessible names, current page indicators, and inappropriate menu role usage.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.menus": "List of all navigation menus with their properties",
        "details.invalidRoles": "List of elements with inappropriate menu roles",
        "details.violations": "List of navigation accessibility violations",
        "details.warnings": "List of potential issues that are not violations"
    },
    "tests": [
        {
            "id": "nav-accessible-name",
            "name": "Navigation Accessible Name",
            "description": "Checks if navigation elements have accessible names to distinguish them from each other.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Add an aria-label or aria-labelledby attribute to each <nav> element that clearly describes its purpose (e.g., 'Main Navigation', 'Footer Links', 'User Account Menu').",
            "resultsFields": {
                "pageFlags.hasUnnamedMenus": "Indicates if any navigation elements lack accessible names",
                "pageFlags.details.unnamedMenus": "Count of navigation elements without accessible names",
                "details.violations": "List of violations including unnamed navigation elements"
            }
        },
        {
            "id": "duplicate-menu-names",
            "name": "Duplicate Navigation Names",
            "description": "Identifies navigation elements that share the same accessible name.",
            "impact": "medium",
            "wcagCriteria": ["2.4.1"],
            "howToFix": "Ensure each navigation landmark has a unique accessible name that describes its specific purpose.",
            "resultsFields": {
                "pageFlags.hasDuplicateMenuNames": "Indicates if any navigation elements share the same name",
                "details.violations": "List of violations including duplicate navigation names"
            }
        },
        {
            "id": "current-page-indicator",
            "name": "Current Page Indicator",
            "description": "Checks if navigation menus indicate the current page or section.",
            "impact": "medium",
            "wcagCriteria": ["2.4.8"],
            "howToFix": "Add aria-current='page' to the navigation link that corresponds to the current page, or aria-current='true' for the current section.",
            "resultsFields": {
                "pageFlags.hasMenusWithoutCurrent": "Indicates if any navigation menus don't mark the current page",
                "pageFlags.details.menusWithoutCurrent": "Count of navigation menus without current page indicators",
                "details.warnings": "List of warnings including navigation without current indicators"
            }
        },
        {
            "id": "inappropriate-menu-roles",
            "name": "Inappropriate Menu Roles",
            "description": "Identifies improper use of menu roles for site navigation.",
            "impact": "high",
            "wcagCriteria": ["4.1.2"],
            "howToFix": "Don't use role='menu' or role='menuitem' for website navigation. These roles are specifically for application menus, not website navigation. Use <nav> elements with lists of links instead.",
            "resultsFields": {
                "pageFlags.hasInvalidMenuRoles": "Indicates if inappropriate menu roles are present",
                "pageFlags.details.invalidRoles": "Count of elements with inappropriate menu roles",
                "details.invalidRoles": "List of elements with inappropriate menu roles"
            }
        }
    ]
}

async def test_menus(page):
    """
    Test proper implementation of menus and navigation
    """
    try:
        menu_data = await page.evaluate('''
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
                function getAccessibleName(element) {
                    // Get accessible name following ARIA naming precedence
                    if (element.getAttribute('aria-labelledby')) {
                        const labelledBy = element.getAttribute('aria-labelledby')
                            .split(' ')
                            .map(id => document.getElementById(id)?.textContent || '')
                            .join(' ');
                        if (labelledBy.trim()) return labelledBy;
                    }
                    
                    if (element.getAttribute('aria-label')) {
                        return element.getAttribute('aria-label');
                    }
                    
                    if (element.getAttribute('title')) {
                        return element.getAttribute('title');
                    }
                    
                    return '';
                }

                function getLandmark(element) {
                    const landmarks = [
                        'main', 'header', 'footer', 'aside', 'banner', 
                        'complementary', 'contentinfo'
                    ];
                    let current = element;
                    
                    while (current && current !== document.body) {
                        const tagName = current.tagName.toLowerCase();
                        const role = current.getAttribute('role');
                        
                        if (landmarks.includes(tagName) || landmarks.includes(role)) {
                            return {
                                type: landmarks.includes(tagName) ? tagName : role,
                                name: getAccessibleName(current)
                             };
                        }
                        current = current.parentElement;
                    }
                    return null;
                }

                function analyzeMenus() {
                    const violations = [];
                    const warnings = [];
                    const menus = [];
                    const invalidRoles = [];

                    // Check for invalid menu roles
                    document.querySelectorAll('[role="menu"], [role="menuitem"]').forEach(element => {
                        invalidRoles.push({
                            element: element.tagName.toLowerCase(),
                            role: element.getAttribute('role'),
                            id: element.id || null,
                            class: element.className || null,
                            location: {
                                parent: element.parentElement.tagName.toLowerCase(),
                                path: element.parentElement.tagName.toLowerCase()
                            }
                        });
                    });

                    // Analyze navigation elements
                    const navElements = [
                        ...document.querySelectorAll('nav'),
                        ...document.querySelectorAll('[role="navigation"]')
                    ];

                    navElements.forEach(nav => {
                        const accessibleName = getAccessibleName(nav);
                        const landmark = getLandmark(nav);
                        const items = nav.querySelectorAll('a, button');
                        const listItems = nav.querySelectorAll('ul > li > a, ul > li > button');
                        const hasCurrentItem = Array.from(items)
                            .some(item => item.hasAttribute('aria-current'));
                        
                        const menuInfo = {
                            element: nav.tagName.toLowerCase(),
                            id: nav.id || null,
                            class: nav.className || null,
                            accessibleName: accessibleName,
                            landmark: landmark,
                            itemCount: items.length,
                            isListBased: listItems.length > 0,
                            hasCurrentItem: hasCurrentItem,
                            items: Array.from(items).map(item => ({
                                element: item.tagName.toLowerCase(),
                                text: item.textContent.trim(),
                                hasCurrent: item.hasAttribute('aria-current'),
                                current: item.getAttribute('aria-current')
                            }))
                        };

                        menus.push(menuInfo);

                        // Check for missing accessible name
                        if (!accessibleName) {
                            violations.push({
                                issue: 'Missing accessible name',
                                element: nav.tagName.toLowerCase(),
                                id: nav.id || null,
                                details: 'Navigation needs an accessible name via aria-label or aria-labelledby'
                            });
                        }

                        // Check for missing aria-current
                        if (!hasCurrentItem) {
                            warnings.push({
                                issue: 'No current item indicated',
                                element: nav.tagName.toLowerCase(),
                                accessibleName: accessibleName,
                                details: 'No item in the navigation has aria-current attribute'
                            });
                        }
                    });

                    // Check for duplicate accessible names
                    const accessibleNames = menus
                        .map(menu => menu.accessibleName)
                        .filter(name => name);
                    const duplicateNames = accessibleNames
                        .filter((name, index) => accessibleNames.indexOf(name) !== index);

                    if (duplicateNames.length > 0) {
                        violations.push({
                            issue: 'Duplicate accessible names',
                            details: 'Multiple navigations share the same accessible name',
                            duplicates: [...new Set(duplicateNames)]
                        });
                    }

                    return {
                        summary: {
                            totalMenus: menus.length,
                            invalidRoleCount: invalidRoles.length,
                            menusWithoutNames: menus.filter(m => !m.accessibleName).length,
                            menusWithoutCurrent: menus.filter(m => !m.hasCurrentItem).length
                         },
                        details: {
                            menus,
                            invalidRoles,
                            violations,
                            warnings
                        }
                    };
                }

                const menuResults = analyzeMenus();

                return {
                    pageFlags: {
                        hasInvalidMenuRoles: menuResults.summary.invalidRoleCount > 0,
                        hasUnnamedMenus: menuResults.summary.menusWithoutNames > 0,
                        hasMenusWithoutCurrent: menuResults.summary.menusWithoutCurrent > 0,
                        hasDuplicateMenuNames: menuResults.details.violations
                            .some(v => v.issue === 'Duplicate accessible names'),
                        details: {
                            totalMenus: menuResults.summary.totalMenus,
                            invalidRoles: menuResults.summary.invalidRoleCount,
                            unnamedMenus: menuResults.summary.menusWithoutNames,
                            menusWithoutCurrent: menuResults.summary.menusWithoutCurrent
                         }
                    },
                    results: menuResults.details
                };
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'menus': {
                'pageFlags': menu_data['pageFlags'],
                'details': menu_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'menus': {
                'pageFlags': {
                    'hasInvalidMenuRoles': False,
                    'hasUnnamedMenus': False,
                    'hasMenusWithoutCurrent': False,
                    'hasDuplicateMenuNames': False,
                    'details': {
                        'totalMenus': 0,
                        'invalidRoles': 0,
                        'unnamedMenus': 0,
                        'menusWithoutCurrent': 0
                     }
                },
                'details': {
                    'menus': [],
                    'invalidRoles': [],
                    'violations': [{
                        'issue': 'Error evaluating menus',
                        'details': str(e)
                    }],
                    'warnings': []
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }