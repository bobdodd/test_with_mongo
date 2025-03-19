from datetime import datetime

async def test_tabindex(page):
    """
    Test tabindex attributes for proper usage across different element types
    """
    try:
        tabindex_data = await page.evaluate('''
            () => {
                function isInteractiveElement(element) {
                    const interactiveTags = [
                        'a', 'button', 'input', 'select', 'textarea', 'video',
                        'audio', 'details', 'summary'
                    ];
                    const interactiveRoles = [
                        'button', 'checkbox', 'combobox', 'link', 'menuitem',
                        'radio', 'slider', 'spinbutton', 'switch', 'tab',
                        'textbox'
                    ];

                    return interactiveTags.includes(element.tagName.toLowerCase()) ||
                           (element.getAttribute('role') && 
                            interactiveRoles.includes(element.getAttribute('role')));
                }

                function isInPageTarget(element) {
                    return !!document.querySelector(`a[href="#${element.id}"]`);
                }

                function isWithinSVG(element) {
                    let current = element;
                    while (current && current !== document.body) {
                        if (current.tagName.toLowerCase() === 'svg') {
                            return true;
                        }
                        current = current.parentElement;
                    }
                    return false;
                }

                const results = {
                    elements: [],
                    violations: [],
                    warnings: [],
                    summary: {
                        totalElementsWithTabindex: 0,
                        elementsWithPositiveTabindex: 0,
                        nonInteractiveWithZeroTabindex: 0,
                        missingRequiredTabindex: 0,
                        svgWithHighTabindex: 0
                    }
                };

                // Find all elements with tabindex
                const elementsWithTabindex = document.querySelectorAll('[tabindex]');
                results.summary.totalElementsWithTabindex = elementsWithTabindex.length;

                // Process each element with tabindex
                elementsWithTabindex.forEach(element => {
                    const tabindex = parseInt(element.getAttribute('tabindex'));
                    const isInteractive = isInteractiveElement(element);
                    const isTarget = isInPageTarget(element);
                    const inSVG = isWithinSVG(element);

                    const elementInfo = {
                        tag: element.tagName.toLowerCase(),
                        role: element.getAttribute('role'),
                        tabindex: tabindex,
                        id: element.id || null,
                        isInteractive: isInteractive,
                        isTarget: isTarget,
                        inSVG: inSVG
                    };

                    results.elements.push(elementInfo);

                    // Check for violations
                    if (tabindex > 0 && !inSVG) {
                        results.violations.push({
                            type: 'positive-tabindex',
                            element: elementInfo.tag,
                            tabindex: tabindex,
                            id: element.id || null
                        });
                        results.summary.elementsWithPositiveTabindex++;
                    }

                    if (tabindex === 0 && !isInteractive) {
                        results.violations.push({
                            type: 'non-interactive-zero-tabindex',
                            element: elementInfo.tag,
                            id: element.id || null
                        });
                        results.summary.nonInteractiveWithZeroTabindex++;
                    }

                    if (inSVG && tabindex > 0) {
                        results.warnings.push({
                            type: 'svg-positive-tabindex',
                            element: elementInfo.tag,
                            tabindex: tabindex,
                            id: element.id || null
                        });
                        results.summary.svgWithHighTabindex++;
                    }
                });

                // Check for missing required tabindex
                const inPageTargets = document.querySelectorAll('*[id]');
                inPageTargets.forEach(element => {
                    if (isInPageTarget(element) && 
                        !isInteractiveElement(element) && 
                        element.getAttribute('tabindex') !== '-1') {
                        results.violations.push({
                            type: 'missing-negative-tabindex',
                            element: element.tagName.toLowerCase(),
                            id: element.id
                        });
                        results.summary.missingRequiredTabindex++;
                    }
                });

                return {
                    pageFlags: {
                        hasPositiveTabindex: results.summary.elementsWithPositiveTabindex > 0,
                        hasNonInteractiveZeroTabindex: results.summary.nonInteractiveWithZeroTabindex > 0,
                        hasMissingRequiredTabindex: results.summary.missingRequiredTabindex > 0,
                        hasSvgTabindexWarnings: results.summary.svgWithHighTabindex > 0,
                        details: {
                            totalElementsWithTabindex: results.summary.totalElementsWithTabindex,
                            elementsWithPositiveTabindex: results.summary.elementsWithPositiveTabindex,
                            nonInteractiveWithZeroTabindex: results.summary.nonInteractiveWithZeroTabindex,
                            missingRequiredTabindex: results.summary.missingRequiredTabindex,
                            svgWithHighTabindex: results.summary.svgWithHighTabindex
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'tabindex': {
                'pageFlags': tabindex_data['pageFlags'],
                'details': tabindex_data['results'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'tabindex': {
                'pageFlags': {
                    'hasPositiveTabindex': False,
                    'hasNonInteractiveZeroTabindex': False,
                    'hasMissingRequiredTabindex': False,
                    'hasSvgTabindexWarnings': False,
                    'details': {
                        'totalElementsWithTabindex': 0,
                        'elementsWithPositiveTabindex': 0,
                        'nonInteractiveWithZeroTabindex': 0,
                        'missingRequiredTabindex': 0,
                        'svgWithHighTabindex': 0
                    }
                },
                'details': {
                    'elements': [],
                    'violations': [{
                        'issue': 'Error evaluating tabindex',
                        'details': str(e)
                    }],
                    'warnings': [],
                    'summary': {
                        'totalElementsWithTabindex': 0,
                        'elementsWithPositiveTabindex': 0,
                        'nonInteractiveWithZeroTabindex': 0,
                        'missingRequiredTabindex': 0,
                        'svgWithHighTabindex': 0
                    }
                }
            }
        }