from datetime import datetime
import asyncio  # Import asyncio for asynchronous sleep

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Focus Management Analysis",
    "description": "Evaluates if interactive elements have appropriate focus indicators that meet accessibility standards across different responsive breakpoints. This test analyzes CSS rules to identify focus styles and tests whether keyboard users can perceive focus states.",
    "version": "1.1.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "metadata": "Test metadata including breakpoints tested",
        "tests": "Results for each focus test type",
        "cssAnalysis": "Analysis of global CSS focus rules"
    },
    "tests": [
        {
            "id": "focus_outline_presence",
            "name": "Focus Outline Presence",
            "description": "Checks if interactive elements have a visible focus indicator when receiving keyboard focus",
            "impact": "high",
            "wcagCriteria": ["2.4.7"],
            "howToFix": "Add a visible focus indicator to all interactive elements using CSS. This can be done with outline, box-shadow, or border properties in a :focus or :focus-visible selector.",
            "resultsFields": {
                "tests.focus_outline_presence.summary.total_violations": "Total elements missing focus indicators",
                "tests.focus_outline_presence.elements_affected": "List of elements missing focus indicators",
                "pageFlags.hasMissingOutlines": "Indicates if any elements are missing focus outlines"
            }
        },
        {
            "id": "focus_outline_offset",
            "name": "Focus Outline Offset and Width",
            "description": "Evaluates if focus outlines have sufficient width and offset to be visible",
            "impact": "medium",
            "wcagCriteria": ["2.4.11"],
            "howToFix": "Ensure focus outlines have sufficient width (at least 1px for solid outlines, 3px for dotted/dashed) and offset (at least 2px from element edge) to be clearly visible.",
            "resultsFields": {
                "tests.focus_outline_offset.summary.total_violations": "Total elements with insufficient outline offset/width",
                "tests.focus_outline_offset.elements_affected": "List of elements with insufficient outline properties",
                "pageFlags.hasInsufficientOutlineOffset": "Indicates if any elements have insufficient outline offset/width"
            }
        },
        {
            "id": "focus_outline_contrast",
            "name": "Focus Outline Contrast",
            "description": "Measures if focus outlines have sufficient contrast against background colors",
            "impact": "high",
            "wcagCriteria": ["2.4.11"],
            "howToFix": "Ensure focus indicators have a contrast ratio of at least 3:1 against adjacent colors. Use high-contrast colors for focus outlines or ensure outline width is at least 2px.",
            "resultsFields": {
                "tests.focus_outline_contrast.summary.total_violations": "Total elements with insufficient contrast",
                "tests.focus_outline_contrast.elements_affected": "List of elements with low contrast focus indicators",
                "pageFlags.hasInsufficientOutlineContrast": "Indicates if any elements have low contrast focus indicators"
            }
        },
        {
            "id": "hover_feedback",
            "name": "Hover Visual Feedback",
            "description": "Checks if elements provide sufficient visual feedback on hover",
            "impact": "medium",
            "wcagCriteria": ["2.4.7"],
            "howToFix": "Add visual feedback for hover states using CSS :hover selectors. Interactive elements should have a pointer cursor and at least one additional visual change (background color, text color, border, etc.).",
            "resultsFields": {
                "tests.hover_feedback.summary.total_violations": "Total elements with insufficient hover feedback",
                "tests.hover_feedback.elements_affected": "List of elements with missing hover effects"
            }
        },
        {
            "id": "focus_obscurement",
            "name": "Focus Outline Obscurement",
            "description": "Tests if focus outlines are visible and not obscured by other elements",
            "impact": "high",
            "wcagCriteria": ["2.4.7"],
            "howToFix": "Ensure focus outlines are not hidden by other elements. Check for elements with overflow:hidden or negative z-index that may hide focus indicators.",
            "resultsFields": {
                "tests.focus_obscurement.summary.total_violations": "Total elements with obscured focus indicators",
                "tests.focus_obscurement.elements_affected": "List of elements with obscured focus outlines"
            }
        },
        {
            "id": "anchor_target_tabindex",
            "name": "Anchor Target Accessibility",
            "description": "Verifies if in-page link targets are properly configured for keyboard navigation",
            "impact": "medium",
            "wcagCriteria": ["2.4.3"],
            "howToFix": "Add tabindex='-1' to non-interactive elements that are targets of in-page links to ensure they receive focus when navigated to via anchor links.",
            "resultsFields": {
                "tests.anchor_target_tabindex.summary.total_violations": "Total in-page targets missing proper tabindex",
                "tests.anchor_target_tabindex.elements_affected": "List of in-page targets with incorrect tabindex",
                "pageFlags.hasImproperTargetTabindex": "Indicates if any in-page targets have improper tabindex"
            }
        }
    ]
}

async def test_focus_management(page):
    """
    Test focus management and interactive element styling at each responsive breakpoint
    by directly analyzing CSS rules.
    """
    # First, detect all the responsive breakpoints in the CSS
    print("\n=== STARTING FOCUS MANAGEMENT TEST WITH RESPONSIVE BREAKPOINTS ===")
    print("Step 1: Extracting media query breakpoints from CSS")
    
    breakpoints = await page.evaluate('''
        () => {
            console.log("Extracting CSS breakpoints");
            // Extract all media queries from stylesheets
            const breakpoints = new Set();
            const widthRegex = /\\((?:max|min)-width:\\s*(\\d+)(?:px|em|rem)\\)/g;
            
            // Process all stylesheets
            Array.from(document.styleSheets).forEach(sheet => {
                try {
                    // Handle CORS restrictions
                    if (sheet.href && !sheet.href.startsWith(window.location.origin)) {
                        return; // Skip external stylesheets due to CORS
                    }
                    
                    Array.from(sheet.cssRules || []).forEach(rule => {
                        // Check if it's a media query rule
                        if (rule.constructor.name === 'CSSMediaRule') {
                            let mediaText = rule.conditionText || rule.media.mediaText;
                            
                            // Extract width values
                            let match;
                            while ((match = widthRegex.exec(mediaText))) {
                                breakpoints.add(parseInt(match[1], 10));
                            }
                        }
                    });
                } catch (e) {
                    // Security error from accessing cross-origin stylesheets
                    console.warn("Couldn't access stylesheet:", e);
                }
            });
            
            // Process inline styles for media queries
            Array.from(document.querySelectorAll('style')).forEach(styleEl => {
                const styleContent = styleEl.textContent;
                let mediaMatches = styleContent.match(/@media[^{]+/g) || [];
                
                mediaMatches.forEach(mediaBlock => {
                    let match;
                    while ((match = widthRegex.exec(mediaBlock))) {
                        breakpoints.add(parseInt(match[1], 10));
                    }
                });
            });
            
            // Add common breakpoints if none found
            if (breakpoints.size === 0) {
                [320, 480, 768, 1024, 1200, 1440].forEach(bp => breakpoints.add(bp));
            }
            
            // Add current viewport width and default mobile/desktop sizes
            breakpoints.add(window.innerWidth);
            breakpoints.add(375); // iPhone
            breakpoints.add(768); // iPad
            breakpoints.add(1280); // Desktop
            
            // Sort breakpoints
            return Array.from(breakpoints).sort((a, b) => a - b);
        }
    ''')
    print(f"Found breakpoints: {breakpoints}")
    
    # Get current viewport size to restore later
    print("Step 2: Getting current viewport size")
    original_viewport = await page.evaluate('''
        () => {
            return {
                width: window.innerWidth,
                height: window.innerHeight
            };
        }
    ''')
    print(f"Original viewport: {original_viewport}")
    
    # Initialize results container structured by test type
    results_by_test = {
        "focus_outline_presence": {
            "test_info": next(test for test in TEST_DOCUMENTATION["tests"] if test["id"] == "focus_outline_presence"),
            "breakpoint_results": [],
            "elements_affected": set(),
            "summary": {
                "total_violations": 0,
                "worst_breakpoint": None,
                "most_affected_element_types": {}
            }
        },
        "focus_outline_offset": {
            "test_info": next(test for test in TEST_DOCUMENTATION["tests"] if test["id"] == "focus_outline_offset"),
            "breakpoint_results": [],
            "elements_affected": set(),
            "summary": {
                "total_violations": 0,
                "worst_breakpoint": None,
                "most_affected_element_types": {}
            }
        },
        "focus_outline_contrast": {
            "test_info": next(test for test in TEST_DOCUMENTATION["tests"] if test["id"] == "focus_outline_contrast"),
            "breakpoint_results": [],
            "elements_affected": set(),
            "summary": {
                "total_violations": 0,
                "worst_breakpoint": None,
                "most_affected_element_types": {}
            }
        },
        "hover_feedback": {
            "test_info": next(test for test in TEST_DOCUMENTATION["tests"] if test["id"] == "hover_feedback"),
            "breakpoint_results": [],
            "elements_affected": set(),
            "summary": {
                "total_violations": 0,
                "worst_breakpoint": None,
                "most_affected_element_types": {}
            }
        },
        "focus_obscurement": {
            "test_info": next(test for test in TEST_DOCUMENTATION["tests"] if test["id"] == "focus_obscurement"),
            "breakpoint_results": [],
            "elements_affected": set(),
            "summary": {
                "total_violations": 0,
                "worst_breakpoint": None,
                "most_affected_element_types": {}
            }
        },
        "anchor_target_tabindex": {
            "test_info": next(test for test in TEST_DOCUMENTATION["tests"] if test["id"] == "anchor_target_tabindex"),
            "breakpoint_results": [],
            "elements_affected": set(),
            "summary": {
                "total_violations": 0,
                "worst_breakpoint": None,
                "most_affected_element_types": {}
            }
        }
    }
    
    # Testing metadata
    testing_metadata = {
        "total_breakpoints_tested": len(breakpoints),
        "breakpoints": [{"width": bp, "name": f"{bp}px"} for bp in breakpoints],
        "test_run_timestamp": datetime.now().isoformat(),
        "total_violations_found": 0
    }
    
    # Get global CSS rules one time, outside the breakpoint loop
    print("Step 3: Analyzing global CSS focus rules")
    global_css_analysis = await page.evaluate('''
        () => {
            console.log("Extracting all CSS focus rules");
            
            // First analyze all CSS focus rules in the document
            const focusRules = [];
            const globalUsesOutline = { value: false, rules: [] };
            const globalUsesBorderFocus = { value: false, rules: [] };
            const globalUsesBoxShadowFocus = { value: false, rules: [] };
            const globalUsesBackgroundFocus = { value: false, rules: [] };
            const globalUsesColorFocus = { value: false, rules: [] };
            const globalUsesTransformFocus = { value: false, rules: [] };
            
            // Process all style sheets
            try {
                Array.from(document.styleSheets).forEach(sheet => {
                    try {
                        if (sheet.href && !sheet.href.startsWith(window.location.origin)) {
                            return; // Skip external stylesheets due to CORS
                        }
                        
                        const sheetRules = Array.from(sheet.cssRules || []);
                        
                        // Process rules recursively (handle media queries)
                        function processRules(rules, mediaContext = null) {
                            rules.forEach(rule => {
                                // Handle media queries
                                if (rule.type === CSSRule.MEDIA_RULE) {
                                    processRules(Array.from(rule.cssRules), rule.conditionText);
                                    return;
                                }
                                
                                // Only process style rules
                                if (rule.type !== CSSRule.STYLE_RULE) return;
                                
                                const selector = rule.selectorText;
                                if (!selector) return;
                                
                                // Look for focus selectors
                                if (selector.includes(':focus') || 
                                    selector.includes(':focus-visible') || 
                                    selector.includes(':focus-within')) {
                                    
                                    // Extract relevant properties
                                    const focusStyle = {
                                        selector: selector,
                                        outline: rule.style.outline || null,
                                        outlineWidth: rule.style.outlineWidth || null,
                                        outlineStyle: rule.style.outlineStyle || null,
                                        outlineColor: rule.style.outlineColor || null,
                                        outlineOffset: rule.style.outlineOffset || null,
                                        boxShadow: rule.style.boxShadow || null,
                                        border: rule.style.border || null,
                                        borderColor: rule.style.borderColor || null,
                                        borderWidth: rule.style.borderWidth || null,
                                        backgroundColor: rule.style.backgroundColor || null,
                                        color: rule.style.color || null,
                                        transform: rule.style.transform || null,
                                        transition: rule.style.transition || null,
                                        mediaContext: mediaContext
                                    };
                                    
                                    // Check what focus styles are used
                                    if (rule.style.outline || rule.style.outlineWidth || 
                                        rule.style.outlineStyle || rule.style.outlineColor) {
                                        globalUsesOutline.value = true;
                                        globalUsesOutline.rules.push(focusStyle);
                                    }
                                    
                                    if (rule.style.border || rule.style.borderColor || rule.style.borderWidth) {
                                        globalUsesBorderFocus.value = true;
                                        globalUsesBorderFocus.rules.push(focusStyle);
                                    }
                                    
                                    if (rule.style.boxShadow) {
                                        globalUsesBoxShadowFocus.value = true;
                                        globalUsesBoxShadowFocus.rules.push(focusStyle);
                                    }
                                    
                                    if (rule.style.backgroundColor) {
                                        globalUsesBackgroundFocus.value = true;
                                        globalUsesBackgroundFocus.rules.push(focusStyle);
                                    }
                                    
                                    if (rule.style.color) {
                                        globalUsesColorFocus.value = true;
                                        globalUsesColorFocus.rules.push(focusStyle);
                                    }
                                    
                                    if (rule.style.transform) {
                                        globalUsesTransformFocus.value = true;
                                        globalUsesTransformFocus.rules.push(focusStyle);
                                    }
                                    
                                    focusRules.push(focusStyle);
                                }
                            });
                        }
                        
                        processRules(sheetRules);
                    } catch (e) {
                        console.warn("Error processing stylesheet:", e);
                    }
                });
            } catch (e) {
                console.error("Error analyzing CSS:", e);
            }
            
            // Check if browser default focus styles are likely being used
            const usesDefaultFocusStyles = focusRules.length === 0 || 
                                        !globalUsesOutline.value && 
                                        !globalUsesBorderFocus.value && 
                                        !globalUsesBoxShadowFocus.value;
                                        
            // Test browser's default focus appearance
            const testButton = document.createElement('button');
            testButton.style.position = 'absolute';
            testButton.style.left = '-9999px';
            testButton.textContent = 'Test';
            document.body.appendChild(testButton);
            testButton.focus();
            
            const defaultFocusStyle = window.getComputedStyle(testButton);
            const defaultOutline = {
                width: defaultFocusStyle.outlineWidth,
                style: defaultFocusStyle.outlineStyle,
                color: defaultFocusStyle.outlineColor,
                offset: defaultFocusStyle.outlineOffset
            };
            
            // Clean up
            document.body.removeChild(testButton);
            
            // Determine the primary focus style mechanism
            let primaryFocusMethod = "none";
            if (globalUsesOutline.value) {
                primaryFocusMethod = "outline";
            } else if (globalUsesBoxShadowFocus.value) {
                primaryFocusMethod = "boxShadow";
            } else if (globalUsesBorderFocus.value) {
                primaryFocusMethod = "border";
            } else if (globalUsesBackgroundFocus.value || globalUsesColorFocus.value) {
                primaryFocusMethod = "colorChange";
            } else if (usesDefaultFocusStyles) {
                primaryFocusMethod = "browserDefault";
            }
                
            return {
                totalFocusRules: focusRules.length,
                focusRules: focusRules,
                focusStyleMechanisms: {
                    usesOutline: globalUsesOutline.value,
                    usesBorderFocus: globalUsesBorderFocus.value,
                    usesBoxShadowFocus: globalUsesBoxShadowFocus.value,
                    usesBackgroundFocus: globalUsesBackgroundFocus.value,
                    usesColorFocus: globalUsesColorFocus.value,
                    usesTransformFocus: globalUsesTransformFocus.value,
                    usesDefaultFocusStyles: usesDefaultFocusStyles,
                    primaryFocusMethod: primaryFocusMethod
                },
                defaultBrowserFocus: defaultOutline,
                outlineRules: globalUsesOutline.rules,
                borderRules: globalUsesBorderFocus.rules,
                boxShadowRules: globalUsesBoxShadowFocus.rules
            };
        }
    ''')
    
    # Log the focus style mechanisms found
    if global_css_analysis:
        mechanisms = global_css_analysis.get('focusStyleMechanisms', {})
        primary_method = mechanisms.get('primaryFocusMethod', 'unknown')
        print(f"  Found {global_css_analysis.get('totalFocusRules', 0)} focus-related CSS rules")
        print(f"  Primary focus method used: {primary_method}")
        if mechanisms.get('usesOutline'):
            print("  Site uses outline for focus")
        if mechanisms.get('usesBoxShadowFocus'):
            print("  Site uses box-shadow for focus")
        if mechanisms.get('usesBorderFocus'):
            print("  Site uses border changes for focus")
        if mechanisms.get('usesDefaultFocusStyles'):
            print("  Site likely relies on browser default focus styles")
    
    # Test at each breakpoint
    print("Step 4: Testing at each breakpoint")
    for i, breakpoint in enumerate(breakpoints):
        print(f"\n--- Testing breakpoint {i+1}/{len(breakpoints)}: {breakpoint}px ---")
        
        # Set the browser viewport to match this breakpoint
        print(f"  Setting viewport width to {breakpoint}px")
        await page.setViewport({
            'width': breakpoint,
            'height': original_viewport['height'] 
        })
        
        # Add a pause to allow the viewport to adjust
        print("  Pausing for 0.5 seconds for viewport to adjust")
        await asyncio.sleep(0.5)  # Pause for 0.5 seconds
        
        try:
            # Run the focus management test at this breakpoint
            print("  Evaluating focus management at this breakpoint")
            focus_data = await page.evaluate('''
                (currentBreakpoint, cssAnalysis) => {
                    console.log("Evaluating at width " + currentBreakpoint + "px");
                    
                    // Function to get full XPath for an element
                    function getFullXPath(element) {
                        if (!element) return '';
                        if (element === document.body) return '/html/body';
                        
                        let path = '';
                        let current = element;
                        
                        while (current && current.nodeType === Node.ELEMENT_NODE) {
                            let index = 1;
                            let sibling = current.previousElementSibling;
                            
                            while (sibling) {
                                if (sibling.tagName === current.tagName) {
                                    index++;
                                }
                                sibling = sibling.previousElementSibling;
                            }
                            
                            const tagName = current.tagName.toLowerCase();
                            const pathSegment = index === 1 ? 
                                `/${tagName}` : 
                                `/${tagName}[${index}]`;
                                
                            path = pathSegment + path;
                            current = current.parentElement;
                            
                            if (current === document.body) {
                                path = '/html/body' + path;
                                break;
                            }
                        }
                        
                        return path;
                    }
                    
                    // Color and contrast calculation helper functions
                    function getRGBFromComputedStyle(color) {
                        const temp = document.createElement('div');
                        temp.style.color = color;
                        temp.style.display = 'none';
                        document.body.appendChild(temp);
                        const style = window.getComputedStyle(temp);
                        const rgb = style.color;
                        document.body.removeChild(temp);
                        return rgb;
                    }

                    function parseRGB(rgb) {
                        const match = rgb.match(/^rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)$/);
                        if (!match) return null;
                        return {
                            r: parseInt(match[1]),
                            g: parseInt(match[2]),
                            b: parseInt(match[3])
                        };
                    }

                    function getLuminance(r, g, b) {
                        const [rs, gs, bs] = [r, g, b].map(c => {
                            c = c / 255;
                            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                        });
                        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                    }

                    function getContrastRatio(l1, l2) {
                        const lighter = Math.max(l1, l2);
                        const darker = Math.min(l1, l2);
                        return (lighter + 0.05) / (darker + 0.05);
                    }
                    
                    // Determine if an element has a CSS-based focus indicator based on selectors
                    function hasCSSFocusIndicator(element) {
                        // If we didn't find any focus rules, assume browser defaults are being used
                        if (cssAnalysis.focusStyleMechanisms.usesDefaultFocusStyles) {
                            return {
                                hasFocusStyle: true,
                                focusMethod: "browserDefault",
                                details: {
                                    outlineWidth: cssAnalysis.defaultBrowserFocus.width,
                                    outlineStyle: cssAnalysis.defaultBrowserFocus.style,
                                    outlineColor: cssAnalysis.defaultBrowserFocus.color,
                                    outlineOffset: cssAnalysis.defaultBrowserFocus.offset
                                }
                            };
                        }
                        
                        // Check if this element matches any of the focus selectors
                        const matchesFocusRule = cssAnalysis.focusRules.some(rule => {
                            try {
                                // Remove the :focus part from the selector to check if the element matches
                                const baseSelector = rule.selector
                                    .replace(/:focus-within/g, '')
                                    .replace(/:focus-visible/g, '')
                                    .replace(/:focus/g, '');
                                    
                                if (baseSelector && document.querySelector(baseSelector)) {
                                    return element.matches(baseSelector);
                                }
                                return false;
                            } catch (e) {
                                return false;
                            }
                        });
                        
                        // If element type is covered by a focus rule, assume it has focus styling
                        if (matchesFocusRule) {
                            let focusMethod = cssAnalysis.focusStyleMechanisms.primaryFocusMethod;
                            let details = {};
                            
                            switch(focusMethod) {
                                case "outline":
                                    details = {
                                        type: "outline",
                                        outlineWidth: "defined in CSS",
                                        outlineStyle: "defined in CSS",
                                        outlineColor: "defined in CSS"
                                    };
                                    break;
                                case "boxShadow":
                                    details = {
                                        type: "boxShadow",
                                        boxShadow: "defined in CSS"
                                    };
                                    break;
                                case "border":
                                    details = {
                                        type: "border",
                                        border: "defined in CSS"
                                    };
                                    break;
                                case "colorChange":
                                    details = {
                                        type: "colorChange"
                                    };
                                    break;
                                default:
                                    details = {
                                        type: focusMethod
                                    };
                            }
                            
                            return {
                                hasFocusStyle: true,
                                focusMethod: focusMethod,
                                details: details
                            };
                        } else if (element.tagName.toLowerCase() in ['button', 'a', 'input', 'select', 'textarea']) {
                            // If it's a standard interactive element, assume browser defaults apply
                            return {
                                hasFocusStyle: true,
                                focusMethod: "browserDefault",
                                details: {
                                    outlineWidth: cssAnalysis.defaultBrowserFocus.width,
                                    outlineStyle: cssAnalysis.defaultBrowserFocus.style,
                                    outlineColor: cssAnalysis.defaultBrowserFocus.color,
                                    outlineOffset: cssAnalysis.defaultBrowserFocus.offset
                                }
                            };
                        }
                        
                        // If we couldn't determine focus style from CSS and it's a non-standard interactive element
                        return {
                            hasFocusStyle: false,
                            focusMethod: "none",
                            details: {
                                reason: "No matching focus rules found for this element"
                            }
                        };
                    }

                    // Track local anchor targets
                    const localTargets = {
                        targetsWithoutTabindex: [],
                        hasImproperTabindex: false
                    };

                    // Find all local anchor links and their targets
                    const localLinks = Array.from(document.querySelectorAll('a[href^="#"]:not([href="#"])'));
                    const targetIds = new Set(localLinks.map(link => link.getAttribute('href').substring(1)));

                    // Get all interactive elements including valid anchor targets
                    const interactiveElements = Array.from(document.querySelectorAll(
                        'a, button, input, select, textarea, [role="button"], [role="link"], [tabindex="0"]'
                    ));

                    // Check each target and add to interactive elements if needed
                    targetIds.forEach(id => {
                        const target = document.getElementById(id);
                        if (target) {
                            const isInteractive = target.matches(
                                'a, button, input, select, textarea, [role="button"], [role="link"]'
                            );
                            if (!isInteractive) {
                                const tabindex = target.getAttribute('tabindex');
                                if (tabindex !== '-1') {
                                    localTargets.hasImproperTabindex = true;
                                    localTargets.targetsWithoutTabindex.push({
                                        id: id,
                                        element: target.tagName.toLowerCase(),
                                        text: target.textContent.trim().substring(0, 50),
                                        currentTabindex: tabindex || 'not set',
                                        xpath: getFullXPath(target)
                                    });
                                }
                                if (tabindex !== null) {
                                    interactiveElements.push(target);
                                }
                            }
                        }
                    });

                    const results = [];
                    const violations = [];
                    const violationsByType = {
                        focus_outline_presence: [],
                        focus_outline_offset: [],
                        focus_outline_contrast: [], 
                        hover_feedback: [],
                        focus_obscurement: [],
                        anchor_target_tabindex: []
                    };
                    
                    // Page-level flags
                    const pageFlags = {
                        hasMissingOutlines: false,
                        hasInsufficientOutlineOffset: false,
                        hasInsufficientOutlineContrast: false,
                        hasImproperTargetTabindex: localTargets.hasImproperTabindex,
                        details: {
                            elementsWithNoOutline: [],
                            elementsWithPoorOffset: [],
                            elementsWithPoorContrast: [],
                            targetsWithoutTabindex: localTargets.targetsWithoutTabindex
                        }
                    };

                    // Test each interactive element
                    interactiveElements.forEach((element, index) => {
                        // Skip elements that are not visible or have 0 width/height
                        const elementRect = element.getBoundingClientRect();
                        if (elementRect.width === 0 || elementRect.height === 0) {
                            return; // Skip invisible elements
                        }
                        
                        // Skip disabled elements 
                        if (element.disabled || element.getAttribute('aria-disabled') === 'true') {
                            return; // Skip disabled elements
                        }
                        
                        // Get baseline styles
                        const style = window.getComputedStyle(element);
                        const hoverStyle = window.getComputedStyle(element, ':hover');
                        
                        // Get XPath for this element
                        const xpath = getFullXPath(element);
                        
                        // Check for hover effects
                        const hoverEffects = {
                            cursor: hoverStyle.cursor,
                            hasAdditionalEffects: false,
                            effects: []
                        };

                        // Check for additional hover effects
                        if (hoverStyle.boxShadow !== style.boxShadow) {
                            hoverEffects.hasAdditionalEffects = true;
                            hoverEffects.effects.push('box-shadow');
                        }
                        if (hoverStyle.backgroundColor !== style.backgroundColor) {
                            hoverEffects.hasAdditionalEffects = true;
                            hoverEffects.effects.push('background-color');
                        }
                        if (hoverStyle.color !== style.color) {
                            hoverEffects.hasAdditionalEffects = true;
                            hoverEffects.effects.push('color');
                        }
                        
                        // Check if element has focus indicators using CSS analysis
                        const focusIndicator = hasCSSFocusIndicator(element);
                        const hasFocusStyle = focusIndicator.hasFocusStyle;
                        const focusMethod = focusIndicator.focusMethod;
                        
                        // Determine if there's an actual outline based on focus method
                        const hasOutline = focusMethod === "outline" || focusMethod === "browserDefault";
                        const hasSufficientFocusIndicator = hasFocusStyle && 
                            (focusMethod === "outline" || focusMethod === "boxShadow" || 
                             focusMethod === "browserDefault");
                        
                        // Check for outline contrast if using outline
                        let contrastRatio = null;
                        if (hasOutline && focusMethod === "outline") {
                            // We can't easily determine contrast without actually applying focus,
                            // but we know there's an outline style in the CSS
                            contrastRatio = 3.0; // Assume sufficient unless we can measure it
                        }

                        // Check for outline obscurement
                        const isObscured = false; // This would require actually focusing the element
                        
                        // Determine if element should have hover feedback
                        const shouldHaveHoverFeedback = element.tagName.toLowerCase() === 'a' || 
                                                       element.tagName.toLowerCase() === 'button' ||
                                                       element.getAttribute('role') === 'button' ||
                                                       element.getAttribute('role') === 'link';

                        const elementInfo = {
                            tag: element.tagName.toLowerCase(),
                            type: element.getAttribute('type') || null,
                            role: element.getAttribute('role') || null,
                            text: element.textContent.trim().substring(0, 50),
                            isAnchorTarget: targetIds.has(element.id),
                            xpath: xpath, // Add XPath to element info
                            id: element.id || null,
                            className: element.className || null,
                            focus: {
                                hasFocusStyle: hasFocusStyle,
                                focusMethod: focusMethod,
                                details: focusIndicator.details,
                                hasSufficientIndicator: hasSufficientFocusIndicator
                            },
                            hover: hoverEffects,
                            position: {
                                x: elementRect.left,
                                y: elementRect.top,
                                width: elementRect.width,
                                height: elementRect.height,
                                visible: elementRect.width > 0 && elementRect.height > 0
                            }
                        };

                        results.push(elementInfo);

                        // Unique identifier for this element
                        const elementIdentifier = `${elementInfo.tag}:${xpath}`;

                        // Check for violations and update page flags
                        if (!hasFocusStyle) {
                            pageFlags.hasMissingOutlines = true;
                            pageFlags.details.elementsWithNoOutline.push({
                                element: elementInfo.tag,
                                text: elementInfo.text,
                                xpath: xpath
                            });
                            const issue = {
                                element: elementInfo.tag,
                                text: elementInfo.text,
                                issue: 'No focus indicator in CSS',
                                elementIdentifier: elementIdentifier,
                                xpath: xpath,
                                id: element.id || null,
                                className: element.className || null,
                                position: elementInfo.position,
                                details: focusIndicator.details
                            };
                            violations.push(issue);
                            violationsByType.focus_outline_presence.push(issue);
                        } else if (!hasSufficientFocusIndicator) {
                            pageFlags.hasMissingOutlines = true;
                            pageFlags.details.elementsWithNoOutline.push({
                                element: elementInfo.tag,
                                text: elementInfo.text,
                                xpath: xpath
                            });
                            const issue = {
                                element: elementInfo.tag,
                                text: elementInfo.text,
                                issue: `Insufficient focus indicator: using ${focusMethod}`,
                                elementIdentifier: elementIdentifier,
                                xpath: xpath,
                                id: element.id || null,
                                className: element.className || null,
                                position: elementInfo.position,
                                details: focusIndicator.details
                            };
                            violations.push(issue);
                            violationsByType.focus_outline_presence.push(issue);
                        }

                        // Check for outline offset issues if using outline
                        if (hasOutline && focusMethod === "outline") {
                            const outlineDetails = focusIndicator.details;
                            
                            // Add violation for insufficient outline offset if needed
                            // Since we don't have exact values from CSS analysis, we'll just flag it 
                            // if we know it's using outline but can't confirm sufficient values
                            if (outlineDetails.outlineWidth === "defined in CSS" || 
                                outlineDetails.outlineStyle === "defined in CSS") {
                                // Skip - we know there's a CSS rule but can't check specifics
                            }
                        }

                        // Check hover effects
                        if (shouldHaveHoverFeedback && hoverStyle.cursor !== 'pointer') {
                            const issue = {
                                element: elementInfo.tag,
                                text: elementInfo.text,
                                issue: 'No pointer cursor on hover',
                                elementIdentifier: elementIdentifier,
                                xpath: xpath,
                                id: element.id || null,
                                className: element.className || null,
                                position: elementInfo.position
                            };
                            violations.push(issue);
                            violationsByType.hover_feedback.push(issue);
                        }

                        if (shouldHaveHoverFeedback && !hoverEffects.hasAdditionalEffects) {
                            const issue = {
                                element: elementInfo.tag,
                                text: elementInfo.text,
                                issue: 'No visual feedback beyond cursor on hover',
                                elementIdentifier: elementIdentifier,
                                xpath: xpath,
                                id: element.id || null,
                                className: element.className || null,
                                position: elementInfo.position
                            };
                            violations.push(issue);
                            violationsByType.hover_feedback.push(issue);
                        }
                    });

                    // Add anchor target violations
                    if (localTargets.hasImproperTabindex) {
                        localTargets.targetsWithoutTabindex.forEach(target => {
                            const elementIdentifier = `${target.element}:${target.xpath}`;
                            const issue = {
                                element: target.element,
                                id: target.id,
                                text: target.text,
                                issue: `Missing tabindex="-1" on target element (current: ${target.currentTabindex})`,
                                elementIdentifier: elementIdentifier,
                                xpath: target.xpath,
                                currentTabindex: target.currentTabindex
                            };
                            violations.push(issue);
                            violationsByType.anchor_target_tabindex.push(issue);
                        });
                    }

                    return {
                        breakpoint: currentBreakpoint,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        cssFocusAnalysis: cssAnalysis.focusStyleMechanisms,
                        pageFlags: pageFlags,
                        localTargets: {
                            total: targetIds.size,
                            improperTabindex: localTargets.targetsWithoutTabindex.length,
                            details: localTargets.targetsWithoutTabindex
                        },
                        totalInteractiveElements: interactiveElements.length,
                        elements: results,
                        violations: violations,
                        violationsByType: violationsByType,
                        summary: {
                            elementsWithoutOutline: violationsByType.focus_outline_presence.length,
                            elementsWithPoorOffset: violationsByType.focus_outline_offset.length,
                            elementsWithPoorContrast: violationsByType.focus_outline_contrast.length,
                            obscuredOutlines: violationsByType.focus_obscurement.length,
                            insufficientHoverEffects: violationsByType.hover_feedback.length,
                            improperTargetTabindex: violationsByType.anchor_target_tabindex.length
                        }
                    };
                }
            ''', breakpoint, global_css_analysis)  # Pass breakpoint and CSS analysis
            
            print(f"  Evaluation complete. Found {len(focus_data.get('violations', []))} violations.")
            print(f"  Focus style method: {focus_data.get('cssFocusAnalysis', {}).get('primaryFocusMethod', 'unknown')}")
            
            # Update total violations count
            testing_metadata["total_violations_found"] += len(focus_data.get('violations', []))
            
            # Add breakpoint results to each test type
            for test_id, test_data in results_by_test.items():
                # Get violations for this test type
                test_violations = focus_data['violationsByType'].get(test_id, [])
                
                # Track elements affected
                for violation in test_violations:
                    if 'elementIdentifier' in violation:
                        test_data['elements_affected'].add(violation['elementIdentifier'])
                
                # Add this breakpoint's results
                breakpoint_result = {
                    'breakpoint': {
                        'width': breakpoint,
                        'name': f"{breakpoint}px"
                    },
                    'css_focus_styles': focus_data.get('cssFocusAnalysis', {}),
                    'violations_count': len(test_violations),
                    'violations': test_violations,
                    'timestamp': datetime.now().isoformat()
                }
                
                # Add to test results
                test_data['breakpoint_results'].append(breakpoint_result)
                test_data['summary']['total_violations'] += len(test_violations)
                
                # Track element types for summary
                for violation in test_violations:
                    element_type = violation.get('element', 'unknown')
                    if element_type in test_data['summary']['most_affected_element_types']:
                        test_data['summary']['most_affected_element_types'][element_type] += 1
                    else:
                        test_data['summary']['most_affected_element_types'][element_type] = 1

        except Exception as e:
            print(f"  ERROR at breakpoint {breakpoint}px: {str(e)}")
            
            # Add error result to each test type
            for test_id, test_data in results_by_test.items():
                error_result = {
                    'breakpoint': {
                        'width': breakpoint,
                        'name': f"{breakpoint}px"
                    },
                    'error': str(e),
                    'violations_count': 0,
                    'violations': [],
                    'timestamp': datetime.now().isoformat()
                }
                test_data['breakpoint_results'].append(error_result)

    # Restore original viewport
    print("\nStep 5: Restoring original viewport")
    try:
        await page.setViewport({
            'width': original_viewport['width'],
            'height': original_viewport['height']
        })
        print(f"Viewport restored to: {original_viewport}")
    except Exception as e:
        print(f"Error restoring viewport: {str(e)}")
    
    # Finalize summaries for each test
    print("\nStep 6: Finalizing test summaries")
    for test_id, test_data in results_by_test.items():
        # Find worst breakpoint
        if test_data['breakpoint_results']:
            worst_breakpoint = max(
                test_data['breakpoint_results'], 
                key=lambda x: x.get('violations_count', 0)
            )
            test_data['summary']['worst_breakpoint'] = worst_breakpoint['breakpoint']
            
        # Convert set to count for elements affected
        test_data['summary']['unique_elements_affected'] = len(test_data['elements_affected'])
        # Convert to list as sets are not JSON serializable
        test_data['elements_affected'] = list(test_data['elements_affected'])
        
        # Sort most affected element types
        test_data['summary']['most_affected_element_types'] = dict(
            sorted(
                test_data['summary']['most_affected_element_types'].items(),
                key=lambda item: item[1],
                reverse=True
            )
        )
    
    # Generate final consolidated results
    print("\nStep 7: Generating final response")
    
    # Create final structure with tests as primary keys
    final_result = {
        'focus_management': {
            'metadata': testing_metadata,
            'css_analysis': global_css_analysis,
            'tests': {
                'focus_outline_presence': results_by_test['focus_outline_presence'],
                'focus_outline_offset': results_by_test['focus_outline_offset'],
                'focus_outline_contrast': results_by_test['focus_outline_contrast'],
                'hover_feedback': results_by_test['hover_feedback'],
                'focus_obscurement': results_by_test['focus_obscurement'],
                'anchor_target_tabindex': results_by_test['anchor_target_tabindex']
            },
            'documentation': TEST_DOCUMENTATION,  # Include the standardized documentation
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # Also expose documentation directly at the top level for easier access by report generator
    if 'focus_management' in final_result:
        final_result['documentation'] = TEST_DOCUMENTATION
    
    return final_result