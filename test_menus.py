from datetime import datetime

async def test_menus(page):
    """
    Test proper implementation of menus and navigation
    """
    try:
        menu_data = await page.evaluate('''
            () => {
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

        return {
            'menus': {
                'pageFlags': menu_data['pageFlags'],
                'details': menu_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }