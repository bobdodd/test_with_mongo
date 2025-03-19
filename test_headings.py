from datetime import datetime

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

        return {
            'headings': {
                'pageFlags': headings_data['pageFlags'],
                'details': headings_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }