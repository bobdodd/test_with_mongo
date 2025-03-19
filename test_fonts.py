from datetime import datetime

async def test_fonts(page):
    try:
        font_data = await page.evaluate('''
            () => {
                // Helper function to extract units from CSS values
                function extractUnit(value) {
                    if (typeof value !== 'string') return null;
                    const match = value.match(/[a-zA-Z%]+$/);
                    return match ? match[0] : null;
                }

                // Helper function to convert any CSS unit to pixels
                function convertToPixels(value, element) {
                    if (!value) return null;
                    if (typeof value === 'number') return value;
                    
                    // Create a temporary element
                    const temp = document.createElement('div');
                    temp.style.visibility = 'hidden';
                    temp.style.position = 'absolute';
                    element.appendChild(temp);
                    
                    // Set the value and get computed pixels
                    temp.style.fontSize = value;
                    const pixels = parseFloat(window.getComputedStyle(temp).fontSize);
                    
                    // Clean up
                    element.removeChild(temp);
                    return pixels;
                }

                // Helper function to get computed property with source information
                function getComputedPropertyWithSource(element, property) {
                    const computed = window.getComputedStyle(element)[property];
                    const inline = element.style[property];
                    
                    // Check if property is set inline
                    if (inline) {
                        return {
                            value: inline,
                            source: 'inline',
                            selector: null
                        };
                    }
                    
                    // Check stylesheets for matching rules
                    for (const sheet of document.styleSheets) {
                        try {
                            const rules = sheet.cssRules || sheet.rules;
                            for (const rule of rules) {
                                if (element.matches(rule.selectorText)) {
                                    const declaration = rule.style[property];
                                    if (declaration) {
                                        return {
                                            value: declaration,
                                            source: 'stylesheet',
                                            selector: rule.selectorText
                                        };
                                    }
                                }
                            }
                        } catch (e) {
                            // Skip cross-origin stylesheets
                            continue;
                        }
                    }
                    
                    return {
                        value: computed,
                        source: 'computed',
                        selector: null
                    };
                }

                const fontUsage = {};
                const testResults = {
                    hasSmallText: false,
                    hasSmallLineHeight: false,
                    hasItalicText: false,
                    hasBoldNonHeadingLargerThanHeadings: false,
                    hasRightAlignedText: false,
                    hasJustifiedText: false,
                    smallestHeadingSize: null,
                    violations: {
                        smallText: [],
                        smallLineHeight: [],
                        italicText: [],
                        boldNonHeadingIssues: [],
                        rightAlignedText: [],
                        justifiedText: []
                    }
                };

                // Create a TreeWalker to traverse text nodes
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    {
                        acceptNode: function(node) {
                            // Skip empty text nodes and nodes in scripts/styles
                            if (!node.textContent.trim() || 
                                ['SCRIPT', 'STYLE'].includes(node.parentElement.tagName)) {
                                return NodeFilter.FILTER_REJECT;
                            }
                            return NodeFilter.FILTER_ACCEPT;
                        }
                    }
                );

                // Collect heading sizes
                const headingSizes = [];
                document.querySelectorAll('h1, h2, h3, h4, h5, h6').forEach(heading => {
                    const size = parseFloat(window.getComputedStyle(heading).fontSize);
                    headingSizes.push(size);
                });
                
                if (headingSizes.length > 0) {
                    testResults.smallestHeadingSize = Math.min(...headingSizes);
                }

                while (walker.nextNode()) {
                    const node = walker.currentNode;
                    const element = node.parentElement;
                    const computedStyle = window.getComputedStyle(element);
                    
                    if (node.textContent.trim()) {
                        const fontFamily = getComputedPropertyWithSource(element, 'fontFamily');
                        const fontSize = getComputedPropertyWithSource(element, 'fontSize');
                        const lineHeight = getComputedPropertyWithSource(element, 'lineHeight');
                        const fontWeight = getComputedPropertyWithSource(element, 'fontWeight');
                        const fontStyle = getComputedPropertyWithSource(element, 'fontStyle');
                        
                        const fontFamilyValue = fontFamily ? fontFamily.value.split(',')[0].trim().replace(/["']/g, '') : 'system-default';
                        const computedFontSize = parseFloat(computedStyle.fontSize);
                        const computedLineHeight = parseFloat(computedStyle.lineHeight);
                        
                        // Get text alignment
                        const textAlign = computedStyle.textAlign;

                        // Add alignment to each declaration
                        if (!fontUsage[fontFamilyValue]) {
                            fontUsage[fontFamilyValue] = {
                                declarations: [],
                                source: fontFamily ? fontFamily.source : 'computed'
                            };
                        }

                        // Test for right-aligned text
                        if (textAlign === 'right') {
                            testResults.hasRightAlignedText = true;
                            testResults.violations.rightAlignedText.push({
                                text: node.textContent.trim().substring(0, 50),
                                element: element.tagName.toLowerCase(),
                                selector: fontSize?.selector
                            });
                        }

                        // Test for justified text
                        if (textAlign === 'justify') {
                            testResults.hasJustifiedText = true;
                            testResults.violations.justifiedText.push({
                                text: node.textContent.trim().substring(0, 50),
                                element: element.tagName.toLowerCase(),
                                selector: fontSize?.selector
                            });
                        }

                        // Check for small text
                        if (computedFontSize < 16) {
                            testResults.hasSmallText = true;
                            testResults.violations.smallText.push({
                                text: node.textContent.trim().substring(0, 50),
                                size: computedFontSize,
                                element: element.tagName.toLowerCase(),
                                selector: fontSize?.selector
                            });
                        }

                        // Check for small line height
                        if (computedLineHeight && (computedLineHeight / computedFontSize) < 1.5) {
                            testResults.hasSmallLineHeight = true;
                            testResults.violations.smallLineHeight.push({
                                text: node.textContent.trim().substring(0, 50),
                                lineHeight: computedLineHeight,
                                fontSize: computedFontSize,
                                ratio: computedLineHeight / computedFontSize,
                                element: element.tagName.toLowerCase(),
                                selector: lineHeight?.selector
                            });
                        }

                        // Check for italic text
                        if (fontStyle.value === 'italic') {
                            testResults.hasItalicText = true;
                            testResults.violations.italicText.push({
                                text: node.textContent.trim().substring(0, 50),
                                element: element.tagName.toLowerCase(),
                                selector: fontStyle?.selector
                            });
                        }

                        // Check for bold text larger than headings
                        if (fontWeight.value >= 700 && !element.matches('h1, h2, h3, h4, h5, h6')) {
                            if (testResults.smallestHeadingSize && computedFontSize > testResults.smallestHeadingSize) {
                                testResults.hasBoldNonHeadingLargerThanHeadings = true;
                                testResults.violations.boldNonHeadingIssues.push({
                                    text: node.textContent.trim().substring(0, 50),
                                    size: computedFontSize,
                                    element: element.tagName.toLowerCase(),
                                    selector: fontSize?.selector
                                });
                            }
                        }

                        fontUsage[fontFamilyValue].declarations.push({
                            text: node.textContent.trim().substring(0, 50) + 
                                 (node.textContent.length > 50 ? '...' : ''),
                            tag: element.tagName.toLowerCase(),
                            font: fontFamilyValue,
                            fontSize: fontSize ? fontSize.value : computedStyle.fontSize,
                            fontSizeUnit: extractUnit(fontSize ? fontSize.value : computedStyle.fontSize),
                            fontSizeSource: fontSize ? fontSize.source : 'computed',
                            lineHeight: lineHeight ? lineHeight.value : computedStyle.lineHeight,
                            fontWeight: fontWeight ? fontWeight.value : computedStyle.fontWeight,
                            selector: fontSize ? fontSize.selector : null,
                            computedSize: computedStyle.fontSize,
                            textAlign: textAlign
                        });
                    }
                }

                return {
                    fonts: fontUsage,
                    totalFonts: Object.keys(fontUsage).length,
                    accessibility: {
                        tests: testResults,
                        smallestHeadingSize: testResults.smallestHeadingSize
                    }
                };
            }
        ''')

        return {
            'font_analysis': font_data,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'font_analysis': {
                'fonts': {},
                'totalFonts': 0,
                'accessibility': {
                    'tests': {
                        'hasSmallText': False,
                        'hasSmallLineHeight': False,
                        'hasItalicText': False,
                        'hasBoldNonHeadingLargerThanHeadings': False,
                        'hasRightAlignedText': False,
                        'hasJustifiedText': False,
                        'violations': {
                            'smallText': [],
                            'smallLineHeight': [],
                            'italicText': [],
                            'boldNonHeadingIssues': [],
                            'rightAlignedText': [],
                            'justifiedText': []
                        }
                    },
                    'smallestHeadingSize': None
                }
            }
        }