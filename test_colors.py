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
    "testName": "Color and Contrast Analysis",
    "description": "Evaluates color usage and contrast ratios on the page to ensure content is perceivable by users with low vision, color vision deficiencies, or those who use high contrast modes. This test examines text contrast, color-only distinctions, non-text contrast, color references, and adjacent element contrast.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "pageFlags": "Boolean flags indicating key color and contrast issues",
        "details": "Full color data including contrast measurements and violations",
        "timestamp": "ISO timestamp when the test was run"
    },
    "tests": [
        {
            "id": "color-text-contrast",
            "name": "Text Contrast Ratio",
            "description": "Evaluates the contrast ratio between text color and its background to ensure readability. Normal text should have a contrast ratio of at least 4.5:1, while large text should have a ratio of at least 3:1.",
            "impact": "high",
            "wcagCriteria": ["1.4.3", "1.4.6"],
            "howToFix": "Increase the contrast between text and background colors. Options include:\n1. Darkening the text color (for light backgrounds)\n2. Lightening the text color (for dark backgrounds)\n3. Changing the background color to increase contrast\n4. Using a contrast checker tool to verify ratios meet WCAG standards",
            "resultsFields": {
                "pageFlags.hasContrastIssues": "Indicates if any text has insufficient contrast",
                "pageFlags.details.contrastViolations": "Count of text elements with contrast issues",
                "details.textContrast.violations": "Detailed information about each contrast violation"
            }
        },
        {
            "id": "color-only-distinction",
            "name": "Color-Only Distinctions",
            "description": "Identifies cases where color alone is used to convey information, particularly for links that are distinguished only by color without additional visual cues.",
            "impact": "high",
            "wcagCriteria": ["1.4.1"],
            "howToFix": "Add non-color distinctions to links and interactive elements:\n1. Add underlines to links\n2. Use icons or symbols alongside color\n3. Apply text styles like bold or italic\n4. Add borders or background changes on hover/focus",
            "resultsFields": {
                "pageFlags.hasColorOnlyLinks": "Indicates if links are distinguished only by color",
                "pageFlags.details.colorOnlyLinks": "Count of links with color-only distinction",
                "details.links.violations": "List of links that rely solely on color"
            }
        },
        {
            "id": "color-non-text-contrast",
            "name": "Non-Text Contrast",
            "description": "Evaluates contrast for UI components and graphical objects to ensure they're perceivable by users with low vision.",
            "impact": "medium",
            "wcagCriteria": ["1.4.11"],
            "howToFix": "Ensure UI components (buttons, form controls, focus indicators) and graphics required for understanding have a contrast ratio of at least 3:1 against adjacent colors.",
            "resultsFields": {
                "pageFlags.hasNonTextContrastIssues": "Indicates if non-text elements have contrast issues",
                "pageFlags.details.nonTextContrastViolations": "Count of non-text contrast violations",
                "details.nonText.violations": "List of non-text elements with contrast issues"
            }
        },
        {
            "id": "color-references",
            "name": "Color References in Content",
            "description": "Identifies text that refers to color as the only means of conveying information, which can be problematic for users with color vision deficiencies.",
            "impact": "medium",
            "wcagCriteria": ["1.4.1"],
            "howToFix": "Supplement color references with additional descriptors:\n1. Use patterns, shapes, or labels in addition to color\n2. Add text that doesn't rely on perceiving color\n3. Use 'located at [position]' instead of 'in red'",
            "resultsFields": {
                "pageFlags.hasColorReferences": "Indicates if content references color as an identifier",
                "pageFlags.details.colorReferences": "Count of color references in text",
                "details.colorReferences.instances": "Text fragments containing color references"
            }
        },
        {
            "id": "color-adjacent-contrast",
            "name": "Adjacent Element Contrast",
            "description": "Examines contrast between adjacent UI elements to ensure boundaries are perceivable.",
            "impact": "medium",
            "wcagCriteria": ["1.4.11"],
            "howToFix": "Increase contrast between adjacent elements by:\n1. Adding borders between sections\n2. Increasing the color difference between adjacent elements\n3. Adding visual separators like lines or spacing",
            "resultsFields": {
                "pageFlags.hasAdjacentContrastIssues": "Indicates if adjacent elements lack sufficient contrast",
                "pageFlags.details.adjacentContrastViolations": "Count of adjacent contrast violations",
                "details.adjacentDivs.violations": "List of adjacent elements with insufficient contrast"
            }
        },
        {
            "id": "color-media-queries",
            "name": "Contrast and Color Scheme Preferences",
            "description": "Checks if the page respects user preferences for increased contrast and color schemes through media queries.",
            "impact": "medium",
            "wcagCriteria": ["1.4.12"],
            "howToFix": "Implement media queries to support user preferences:\n@media (prefers-contrast: more) { /* high contrast styles */ }\n@media (prefers-color-scheme: dark) { /* dark mode styles */ }",
            "resultsFields": {
                "pageFlags.supportsContrastPreferences": "Indicates if prefers-contrast media query is used",
                "pageFlags.supportsColorSchemePreferences": "Indicates if prefers-color-scheme media query is used",
                "details.mediaQueries": "Details about detected media queries"
            }
        }
    ]
}

async def test_colors(page):
    """
    Test color usage and contrast requirements across the page
    """
    try:
        color_data = await page.evaluate('''
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
                // Color utility functions
                function getLuminance(r, g, b) {
                    const [rs, gs, bs] = [r, g, b].map(c => {
                        c = c / 255
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4)
                    })
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs
                }

                function getContrastRatio(l1, l2) {
                    const lighter = Math.max(l1, l2)
                    const darker = Math.min(l1, l2)
                    return (lighter + 0.05) / (darker + 0.05)
                }

                function parseColor(color) {
                    const temp = document.createElement('div')
                    temp.style.color = color
                    document.body.appendChild(temp)
                    const style = window.getComputedStyle(temp)
                    const rgb = style.color.match(/\\d+/g).map(Number)
                    document.body.removeChild(temp)
                    return rgb
                }

                function hasBackgroundImage(element) {
                    const style = window.getComputedStyle(element)
                    return style.backgroundImage !== 'none'
                }

                function getEffectiveBackground(element) {
                    let current = element
                    while (current && current !== document.body) {
                        const style = window.getComputedStyle(current)
                        if (style.backgroundColor !== 'rgba(0, 0, 0, 0)' && 
                            style.backgroundColor !== 'transparent') {
                            return parseColor(style.backgroundColor)
                        }
                        if (hasBackgroundImage(current)) {
                            return null
                        }
                        current = current.parentElement
                    }
                    return parseColor(window.getComputedStyle(document.body).backgroundColor)
                }

                function isLargeText(element) {
                    const style = window.getComputedStyle(element)
                    const fontSize = parseFloat(style.fontSize)
                    const fontWeight = style.fontWeight
                    return (fontSize >= 18.66) || (fontSize >= 14 && fontWeight >= 700)
                }

                function hasNonColorDistinction(element) {
                    const style = window.getComputedStyle(element)
                    return style.textDecoration !== 'none' || 
                           element.getAttribute('role') === 'link' ||
                           !!element.querySelector('u, underline')
                }

                function findColorReferences(text) {
                    const colorTerms = /\\b(red|blue|green|yellow|white|black|purple|orange|pink|brown|grey|gray|colored|coloured|marked in|shown in|displayed in|indicated by|marked with|in the color)\\b/gi
                    return text.match(colorTerms) || []
                }

                const results = {
                    mediaQueries: {
                        prefersContrast: false,
                        prefersColorScheme: false
                    },
                    textContrast: {
                        violations: [],
                        elements: []
                    },
                    links: {
                        violations: [],
                        elements: []
                    },
                    nonText: {
                        violations: [],
                        elements: []
                    },
                    colorReferences: {
                        instances: [],
                        elements: []
                    },
                    adjacentDivs: {
                        violations: [],
                        pairs: []
                    },
                    summary: {
                        totalTextElements: 0,
                        contrastViolations: 0,
                        colorOnlyLinks: 0,
                        nonTextContrastViolations: 0,
                        colorReferenceCount: 0,
                        adjacentContrastViolations: 0
                    }
                }

                // Check for media query support
                Array.from(document.styleSheets).forEach(sheet => {
                    try {
                        Array.from(sheet.cssRules).forEach(rule => {
                            if (rule instanceof CSSMediaRule) {
                                const query = rule.conditionText.toLowerCase()
                                if (query.includes('prefers-contrast')) {
                                    results.mediaQueries.prefersContrast = true
                                }
                                if (query.includes('prefers-color-scheme')) {
                                    results.mediaQueries.prefersColorScheme = true
                                }
                            }
                        })
                    } catch (e) {
                        // Skip inaccessible stylesheets
                    }
                })

                // Test text contrast
                const textElements = document.evaluate(
                    '//body//text()[normalize-space()]',
                    document,
                    null,
                    XPathResult.ORDERED_NODE_SNAPSHOT_TYPE,
                    null
                )

                for (let i = 0; i < textElements.snapshotLength; i++) {
                    const textNode = textElements.snapshotItem(i)
                    const element = textNode.parentElement
                    
                    if (!element.offsetHeight) continue

                    const style = window.getComputedStyle(element)
                    const foreground = parseColor(style.color)
                    const background = getEffectiveBackground(element)
                    
                    if (background) {
                        const foreLum = getLuminance(...foreground)
                        const backLum = getLuminance(...background)
                        const ratio = getContrastRatio(foreLum, backLum)
                        const isLarge = isLargeText(element)
                        const requiredRatio = isLarge ? 3 : 4.5

                        results.textContrast.elements.push({
                            text: textNode.textContent.trim(),
                            contrast: ratio,
                            isLarge: isLarge,
                            colors: {
                                foreground: foreground,
                                background: background
                            }
                        })

                        if (ratio < requiredRatio) {
                            results.textContrast.violations.push({
                                element: element.tagName.toLowerCase(),
                                text: textNode.textContent.trim(),
                                contrast: ratio,
                                required: requiredRatio,
                                colors: {
                                    foreground: foreground,
                                    background: background
                                }
                            })
                            results.summary.contrastViolations++
                        }
                    }
                }

                // Test links
                document.querySelectorAll('a').forEach(link => {
                    if (!hasNonColorDistinction(link)) {
                        results.links.violations.push({
                            href: link.href,
                            text: link.textContent.trim(),
                            issue: 'Color-only distinction'
                        })
                        results.summary.colorOnlyLinks++
                    }
                })

                // Test HR elements
                document.querySelectorAll('hr').forEach(hr => {
                    const style = window.getComputedStyle(hr)
                    const hrColor = parseColor(style.borderColor)
                    const background = getEffectiveBackground(hr)
                    
                    if (background) {
                        const hrLum = getLuminance(...hrColor)
                        const backLum = getLuminance(...background)
                        const ratio = getContrastRatio(hrLum, backLum)

                        if (ratio < 3) {
                            results.nonText.violations.push({
                                element: 'hr',
                                contrast: ratio,
                                colors: {
                                    foreground: hrColor,
                                    background: background
                                }
                            })
                            results.summary.nonTextContrastViolations++
                        }
                    }
                })

                // Test button edges
                document.querySelectorAll('button').forEach(button => {
                    const style = window.getComputedStyle(button)
                    const hasBorder = style.borderStyle !== 'none'
                    const edgeColor = hasBorder ? 
                        parseColor(style.borderColor) :
                        parseColor(style.backgroundColor)
                    const background = getEffectiveBackground(button)
                    
                    if (background && !hasBackgroundImage(button)) {
                        const edgeLum = getLuminance(...edgeColor)
                        const backLum = getLuminance(...background)
                        const ratio = getContrastRatio(edgeLum, backLum)

                        if (ratio < 3) {
                            results.nonText.violations.push({
                                element: 'button',
                                contrast: ratio,
                                type: hasBorder ? 'border' : 'background',
                                colors: {
                                    edge: edgeColor,
                                    background: background
                                }
                            })
                            results.summary.nonTextContrastViolations++
                        }
                    }
                })

                // Check for color references
                document.querySelectorAll('p, li, td, th, div, span').forEach(element => {
                    const text = element.textContent
                    const colorRefs = findColorReferences(text)
                    if (colorRefs.length > 0) {
                        results.colorReferences.instances.push({
                            element: element.tagName.toLowerCase(),
                            text: text,
                            references: colorRefs
                        })
                        results.summary.colorReferenceCount += colorRefs.length
                    }
                })

                // Test adjacent divs
                const divs = Array.from(document.querySelectorAll('div'))
                divs.forEach((div, index) => {
                    if (index === 0) return
                    
                    const current = div
                    const previous = divs[index - 1]
                    
                    if (hasBackgroundImage(current) || hasBackgroundImage(previous)) {
                        return
                    }

                    const currentStyle = window.getComputedStyle(current)
                    const previousStyle = window.getComputedStyle(previous)
                    
                    if (currentStyle.backgroundColor !== previousStyle.backgroundColor &&
                        currentStyle.backgroundColor !== 'transparent' &&
                        previousStyle.backgroundColor !== 'transparent') {
                        
                        const color1 = parseColor(currentStyle.backgroundColor)
                        const color2 = parseColor(previousStyle.backgroundColor)
                        
                        const lum1 = getLuminance(...color1)
                        const lum2 = getLuminance(...color2)
                        const ratio = getContrastRatio(lum1, lum2)

                        if (ratio < 3) {
                            results.adjacentDivs.violations.push({
                                elements: [
                                    current.tagName.toLowerCase() + 
                                    (current.id ? `#${current.id}` : ''),
                                    previous.tagName.toLowerCase() + 
                                    (previous.id ? `#${previous.id}` : '')
                                ],
                                contrast: ratio,
                                colors: {
                                    first: color1,
                                    second: color2
                                }
                            })
                            results.summary.adjacentContrastViolations++
                        }
                    }
                })

                return {
                    pageFlags: {
                        hasContrastIssues: results.summary.contrastViolations > 0,
                        hasColorOnlyLinks: results.summary.colorOnlyLinks > 0,
                        hasNonTextContrastIssues: results.summary.nonTextContrastViolations > 0,
                        hasColorReferences: results.summary.colorReferenceCount > 0,
                        hasAdjacentContrastIssues: results.summary.adjacentContrastViolations > 0,
                        supportsContrastPreferences: results.mediaQueries.prefersContrast,
                        supportsColorSchemePreferences: results.mediaQueries.prefersColorScheme,
                        details: {
                            contrastViolations: results.summary.contrastViolations,
                            colorOnlyLinks: results.summary.colorOnlyLinks,
                            nonTextContrastViolations: results.summary.nonTextContrastViolations,
                            colorReferences: results.summary.colorReferenceCount,
                            adjacentContrastViolations: results.summary.adjacentContrastViolations
                         }
                    },
                    results: results
                }
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'colors': {
                'pageFlags': color_data['pageFlags'],
                'details': color_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'colors': {
                'pageFlags': {
                    'hasContrastIssues': False,
                    'hasColorOnlyLinks': False,
                    'hasNonTextContrastIssues': False,
                    'hasColorReferences': False,
                    'hasAdjacentContrastIssues': False,
                    'supportsContrastPreferences': False,
                    'supportsColorSchemePreferences': False,
                    'details': {
                        'contrastViolations': 0,
                        'colorOnlyLinks': 0,
                        'nonTextContrastViolations': 0,
                        'colorReferences': 0,
                        'adjacentContrastViolations': 0
                     }
                },
                'details': {
                    'mediaQueries': {
                        'prefersContrast': False,
                        'prefersColorScheme': False
                    },
                    'violations': [{
                        'issue': 'Error evaluating colors',
                        'details': str(e)
                    }]
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }