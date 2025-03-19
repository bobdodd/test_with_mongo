from datetime import datetime

async def test_lists(page):
    """
    Test proper implementation of lists and their styling
    """
    try:
        list_data = await page.evaluate('''
            () => {
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

        return {
            'lists': {
                'pageFlags': list_data['pageFlags'],
                'details': list_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }