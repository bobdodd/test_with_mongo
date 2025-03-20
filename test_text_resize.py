from datetime import datetime

# Test documentation with information about the text resize test
TEST_DOCUMENTATION = {
    "testName": "Text Resize Test",
    "description": "Tests the ability of a webpage to support text resizing to 200% without loss of content or functionality. WCAG 1.4.4 requires that text can be resized without assistive technology up to 200% without loss of content or functionality.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "pageFlags": "Boolean flags indicating the presence of accessibility issues",
        "details": "Detailed information about the test results across different viewports",
        "results": "Array of viewport-specific test results, including overlapping and truncated elements"
    },
    "tests": [
        {
            "id": "text-resize-overlap",
            "name": "Text Resize Overlap Test",
            "description": "Checks if text elements overlap with other content when resized to 200%",
            "impact": "high",
            "wcagCriteria": ["1.4.4"],
            "howToFix": "Ensure containers have sufficient padding and use flexible layout techniques like responsive design. Avoid fixed-height containers for text, and implement proper text wrapping and container expansion. Use relative units (em, rem) rather than fixed pixel sizes for font and container dimensions.",
            "resultsFields": {
                "overlaps": "List of text elements that overlap with other elements when resized",
                "source": "The text element that, when resized, caused overlapping",
                "overlappingElements": "Elements that overlap with the resized text"
            }
        },
        {
            "id": "text-resize-truncation",
            "name": "Text Resize Truncation Test",
            "description": "Checks if text is truncated or clipped when resized to 200%",
            "impact": "high",
            "wcagCriteria": ["1.4.4"],
            "howToFix": "Remove fixed-height containers for text content, ensure overflow properties don't hide content, and use flexible layout techniques that allow containers to expand with text. Consider implementing responsive layouts that reflow content at different text sizes.",
            "resultsFields": {
                "truncated": "List of text elements that become truncated when resized",
                "xpath": "XPath of the element with truncation issues",
                "element": "HTML tag of the element with truncation issues",
                "id": "ID attribute of the element if available",
                "text": "Sample of the text content in the truncated element"
            }
        },
        {
            "id": "text-resize-across-breakpoints",
            "name": "Text Resize Across Responsive Breakpoints",
            "description": "Tests text resize behavior across different responsive layout breakpoints",
            "impact": "medium",
            "wcagCriteria": ["1.4.4"],
            "howToFix": "Ensure that responsive layouts maintain proper text sizing and container dimensions across all breakpoints. Test and adjust media queries to handle resized text appropriately at each breakpoint.",
            "resultsFields": {
                "viewport": "The viewport dimensions being tested",
                "results": "Results specific to each viewport size",
                "hasIssues": "Whether any resize issues were found at this viewport size"
            }
        }
    ]
}

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
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION
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
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION
            }
        }