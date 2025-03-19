from datetime import datetime

async def test_text_resize(page):
    """
    Test text resize to 200% without content loss or overlap
    """
    try:
        # First get the media query breakpoints
        breakpoints = await page.evaluate('''
            () => {
                const breakpoints = [];
                for (const sheet of document.styleSheets) {
                    try {
                        for (const rule of sheet.cssRules) {
                            if (rule instanceof CSSMediaRule) {
                                breakpoints.push({
                                    query: rule.conditionText,
                                    width: rule.conditionText.match(/min-width:\s*(\d+)px/) || 
                                           rule.conditionText.match(/max-width:\s*(\d+)px/)
                                });
                            }
                        }
                    } catch (e) {
                        // Skip external stylesheets that may cause CORS issues
                        continue;
                    }
                }
                return [...new Set(breakpoints)];
            }
        ''')

        resize_results = []
        
        # Test at each breakpoint
        viewport_sizes = [{'width': 320, 'height': 800}]  # Start with mobile
        if breakpoints:
            for breakpoint in breakpoints:
                if breakpoint.get('width'):
                    viewport_sizes.append({
                        'width': int(breakpoint['width'][1]),
                        'height': 800
                    })

        for viewport in viewport_sizes:
            # Set viewport size
            await page.setViewport(viewport)
            
            # Allow page to settle
            await page.waitFor(500)

            # Analyze text elements and test resizing
            viewport_result = await page.evaluate('''
                () => {
                    function getXPath(element) {
                        if (element.id !== '') {
                            return `//*[@id="${element.id}"]`;
                        }
                        if (element === document.body) {
                            return '/html/body';
                        }
                        let ix = 0;
                        const siblings = element.parentNode.childNodes;
                        for (let i = 0; i < siblings.length; i++) {
                            const sibling = siblings[i];
                            if (sibling === element) {
                                return getXPath(element.parentNode) + 
                                       '/' + element.tagName.toLowerCase() + 
                                       '[' + (ix + 1) + ']';
                            }
                            if (sibling.nodeType === 1 && 
                                sibling.tagName === element.tagName) {
                                ix++;
                            }
                        }
                    }

                    function checkOverlap(element) {
                        const rect = element.getBoundingClientRect();
                        const overlapping = [];
                        
                        // Get all elements that might be overlapped
                        document.querySelectorAll('*').forEach(other => {
                            if (other !== element && 
                                !element.contains(other) && 
                                !other.contains(element)) {
                                
                                const otherRect = other.getBoundingClientRect();
                                const style = window.getComputedStyle(other);
                                
                                // Only check visible elements
                                if (style.display !== 'none' && 
                                    style.visibility !== 'hidden' && 
                                    style.opacity !== '0') {
                                    
                                    // Check for overlap
                                    if (!(otherRect.right < rect.left || 
                                        otherRect.left > rect.right || 
                                        otherRect.bottom < rect.top || 
                                        otherRect.top > rect.bottom)) {
                                        
                                        overlapping.push({
                                            xpath: getXPath(other),
                                            element: other.tagName.toLowerCase(),
                                            id: other.id || null,
                                            text: other.textContent.trim().substring(0, 50),
                                            zIndex: style.zIndex,
                                            overlap: {
                                                horizontal: Math.min(otherRect.right, rect.right) - 
                                                          Math.max(otherRect.left, rect.left),
                                                vertical: Math.min(otherRect.bottom, rect.bottom) - 
                                                        Math.max(otherRect.top, rect.top)
                                            }
                                        });
                                    }
                                }
                            }
                        });
                        
                        return overlapping;
                    }

                    const textElements = Array.from(document.querySelectorAll('*'))
                        .filter(el => {
                            const style = window.getComputedStyle(el);
                            return el.textContent.trim() && 
                                   style.display !== 'none' && 
                                   style.visibility !== 'hidden';
                        });

                    const results = {
                        overlaps: [],
                        truncated: [],
                        originalStates: new Map()
                    };

                    // Store original font sizes
                    textElements.forEach(el => {
                        const style = window.getComputedStyle(el);
                        results.originalStates.set(el, {
                            fontSize: style.fontSize,
                            lineHeight: style.lineHeight,
                            height: style.height,
                            overflow: style.overflow
                        });
                    });

                    // Test each text element
                    textElements.forEach(element => {
                        // Store original style
                        const originalFontSize = window.getComputedStyle(element).fontSize;
                        const originalHeight = element.offsetHeight;
                        
                        // Increase text size
                        element.style.fontSize = '200%';
                        
                        // Check for overlaps
                        const overlapping = checkOverlap(element);
                        if (overlapping.length > 0) {
                            results.overlaps.push({
                                source: {
                                    xpath: getXPath(element),
                                    element: element.tagName.toLowerCase(),
                                    id: element.id || null,
                                    text: element.textContent.trim().substring(0, 50)
                                },
                                overlappingElements: overlapping
                            });
                        }

                        // Check for truncation
                        if (element.scrollHeight > element.offsetHeight) {
                            results.truncated.push({
                                xpath: getXPath(element),
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                text: element.textContent.trim().substring(0, 50)
                            });
                        }

                        // Restore original size
                        element.style.fontSize = originalFontSize;
                    });

                    return {
                        hasIssues: results.overlaps.length > 0 || results.truncated.length > 0,
                        overlaps: results.overlaps,
                        truncated: results.truncated,
                        totalElementsTested: textElements.length
                    };
                }
            ''')

            resize_results.append({
                'viewport': viewport,
                'results': viewport_result
            })

        return {
            'textResize': {
                'pageFlags': {
                    'hasResizeIssues': any(r['results']['hasIssues'] for r in resize_results),
                    'details': {
                        'totalViewportsTested': len(resize_results),
                        'viewportsWithIssues': sum(
                            1 for r in resize_results if r['results']['hasIssues']
                        ),
                        'totalElementsTested': resize_results[0]['results']['totalElementsTested']
                    }
                },
                'results': resize_results,
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'textResize': {
                'pageFlags': {
                    'hasResizeIssues': False,
                    'details': {
                        'totalViewportsTested': 0,
                        'viewportsWithIssues': 0,
                        'totalElementsTested': 0
                    }
                },
                'results': [],
                'timestamp': datetime.now().isoformat()
            }
        }