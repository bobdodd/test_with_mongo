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
    "testName": "Font Accessibility Analysis",
    "description": "Evaluates webpage font usage and typography for accessibility concerns, including font size, line height, and text alignment. This test identifies small text, insufficient line spacing, and other typographic issues that may impact readability for users with visual impairments.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "font_analysis.fonts": "Dictionary of font families used with their properties",
        "font_analysis.totalFonts": "Count of unique font families used on the page",
        "font_analysis.accessibility.tests": "Test results for specific font accessibility issues",
        "font_analysis.accessibility.violations": "Lists of text elements with accessibility issues"
    },
    "tests": [
        {
            "id": "small-text",
            "name": "Small Text Size",
            "description": "Identifies text with font size smaller than 16px that may be difficult to read.",
            "impact": "high",
            "wcagCriteria": ["1.4.4"],
            "howToFix": "Ensure all body text is at least 16px (1rem) in size. If using relative units, make sure they resolve to at least 16px at standard zoom levels.",
            "resultsFields": {
                "font_analysis.accessibility.tests.hasSmallText": "Indicates if small text is present",
                "font_analysis.accessibility.tests.violations.smallText": "List of text elements with small font sizes"
            }
        },
        {
            "id": "line-height",
            "name": "Insufficient Line Height",
            "description": "Checks if line height is adequate for readability (at least 1.5 times the font size).",
            "impact": "medium",
            "wcagCriteria": ["1.4.8"],
            "howToFix": "Set line-height to at least 1.5 for paragraph text to improve readability and accommodate users who need more spacing between lines.",
            "resultsFields": {
                "font_analysis.accessibility.tests.hasSmallLineHeight": "Indicates if insufficient line height is present",
                "font_analysis.accessibility.tests.violations.smallLineHeight": "List of text elements with insufficient line spacing"
            }
        },
        {
            "id": "italic-text",
            "name": "Excessive Italic Text",
            "description": "Identifies usage of italic text that may be difficult to read for some users.",
            "impact": "medium",
            "wcagCriteria": ["1.4.8"],
            "howToFix": "Limit the use of italic text, especially for longer passages. Consider using alternative styling for emphasis.",
            "resultsFields": {
                "font_analysis.accessibility.tests.hasItalicText": "Indicates if italic text is present",
                "font_analysis.accessibility.tests.violations.italicText": "List of text elements with italic styling"
            }
        },
        {
            "id": "text-alignment",
            "name": "Text Alignment Issues",
            "description": "Checks for justified or right-aligned text that may create readability problems.",
            "impact": "medium",
            "wcagCriteria": ["1.4.8"],
            "howToFix": "Avoid fully justified text which creates uneven spacing between words. Use left-aligned text (or right-aligned for RTL languages) instead of centered or right-aligned text for longer passages.",
            "resultsFields": {
                "font_analysis.accessibility.tests.hasJustifiedText": "Indicates if justified text is present",
                "font_analysis.accessibility.tests.hasRightAlignedText": "Indicates if right-aligned text is present",
                "font_analysis.accessibility.tests.violations.justifiedText": "List of elements with justified text",
                "font_analysis.accessibility.tests.violations.rightAlignedText": "List of elements with right-aligned text"
            }
        },
        {
            "id": "visual-hierarchy",
            "name": "Visual Hierarchy Issues",
            "description": "Identifies cases where non-heading text appears more prominent than actual headings.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Maintain a clear visual hierarchy where headings are visually more prominent than non-heading text. Don't use large, bold text as a substitute for proper heading elements.",
            "resultsFields": {
                "font_analysis.accessibility.tests.hasBoldNonHeadingLargerThanHeadings": "Indicates if bold non-heading text larger than headings is present",
                "font_analysis.accessibility.tests.violations.boldNonHeadingIssues": "List of elements with bold text larger than the smallest heading",
                "font_analysis.accessibility.smallestHeadingSize": "Size of the smallest heading for comparison"
            }
        }
    ]
}

async def test_fonts(page):
    try:
        font_data = await page.evaluate('''
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
            'timestamp': datetime.now().isoformat(),
            'documentation': TEST_DOCUMENTATION  # Include test documentation in results
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
            },
            'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
        }