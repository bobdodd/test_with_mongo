from datetime import datetime

async def test_read_more_links(page):
    """
    Test 'read more' type links and buttons for proper accessible names
    """
    try:
        read_more_data = await page.evaluate('''
            () => {
                function getAccessibleName(element) {
                    // Check various sources for accessible name in correct order
                    const ariaLabel = element.getAttribute('aria-label');
                    if (ariaLabel) return ariaLabel.trim();

                    const ariaLabelledBy = element.getAttribute('aria-labelledby');
                    if (ariaLabelledBy) {
                        const labelElements = ariaLabelledBy.split(' ')
                            .map(id => document.getElementById(id))
                            .filter(el => el);
                        if (labelElements.length > 0) {
                            return labelElements.map(el => el.textContent.trim()).join(' ');
                        }
                    }

                    // For buttons/links, combine text content with aria-label if both exist
                    const visibleText = element.textContent.trim();
                    if (ariaLabel && visibleText) {
                        return `${visibleText} ${ariaLabel}`;
                    }

                    return visibleText;
                }

                const results = {
                    items: [],
                    violations: [],
                    summary: {
                        totalGenericLinks: 0,
                        violationsCount: 0
                    }
                };

                // Regular expressions for matching generic text
                const genericTextPatterns = [
                    /^read more$/i,
                    /^learn more$/i,
                    /^more$/i,
                    /^more\.\.\.$/i,
                    /^read more\.\.\.$/i,
                    /^learn more\.\.\.$/i,
                    /^click here$/i,
                    /^details$/i,
                    /^more details$/i
                ];

                // Find all links and buttons
                const elements = Array.from(document.querySelectorAll('a, button, [role="button"], [role="link"]'));

                elements.forEach(element => {
                    const visibleText = element.textContent.trim();
                    const accessibleName = getAccessibleName(element);
                    
                    // Check if this is a generic "read more" type element
                    const isGenericText = genericTextPatterns.some(pattern => 
                        pattern.test(visibleText)
                    );

                    if (isGenericText) {
                        results.summary.totalGenericLinks++;

                        const elementInfo = {
                            tag: element.tagName.toLowerCase(),
                            role: element.getAttribute('role'),
                            visibleText: visibleText,
                            accessibleName: accessibleName,
                            location: {
                                href: element.href || null,
                                id: element.id || null,
                                path: element.textContent
                            },
                            isValid: accessibleName.length > visibleText.length && 
                                    accessibleName.toLowerCase().startsWith(visibleText.toLowerCase())
                        };

                        results.items.push(elementInfo);

                        // Check for violations
                        if (!elementInfo.isValid) {
                            results.violations.push({
                                type: 'invalid-accessible-name',
                                element: elementInfo.tag,
                                visibleText: visibleText,
                                accessibleName: accessibleName,
                                required: 'Accessible name must be longer than and start with the visible text',
                                location: elementInfo.location
                            });
                            results.summary.violationsCount++;
                        }
                    }
                });

                return {
                    pageFlags: {
                        hasGenericReadMoreLinks: results.summary.totalGenericLinks > 0,
                        hasInvalidReadMoreLinks: results.summary.violationsCount > 0,
                        details: {
                            totalGenericLinks: results.summary.totalGenericLinks,
                            violationsCount: results.summary.violationsCount
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'read_more_links': {
                'pageFlags': read_more_data['pageFlags'],
                'details': read_more_data['results'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'read_more_links': {
                'pageFlags': {
                    'hasGenericReadMoreLinks': False,
                    'hasInvalidReadMoreLinks': False,
                    'details': {
                        'totalGenericLinks': 0,
                        'violationsCount': 0
                    }
                },
                'details': {
                    'items': [],
                    'violations': [{
                        'issue': 'Error evaluating read more links',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalGenericLinks': 0,
                        'violationsCount': 0
                    }
                }
            }
        }