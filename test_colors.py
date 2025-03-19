from datetime import datetime

async def test_colors(page):
    """
    Test color usage and contrast requirements across the page
    """
    try:
        color_data = await page.evaluate('''
            () => {
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

        return {
            'colors': {
                'pageFlags': color_data['pageFlags'],
                'details': color_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }