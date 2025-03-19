from datetime import datetime

async def test_landmarks(page):
    """
    Test page landmark structure and requirements, with proper handling of
    implicit landmark roles for header and footer elements
    """
    try:
        landmarks_data = await page.evaluate('''
            () => {
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
                            type: 'unlabelled-form',
                            element: tag
                        });
                    }

                    // Check for sections/regions without labels
                    if (role === 'region' && !name) {
                        results.violations.push({
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

        return {
            'landmarks': {
                'pageFlags': landmarks_data['pageFlags'],
                'details': landmarks_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }