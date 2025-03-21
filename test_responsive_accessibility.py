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
import asyncio  # For sleep operations

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Responsive Accessibility Analysis",
    "description": "Evaluates accessibility across different viewport sizes, focusing on issues that only appear at specific breakpoints. This test ensures content remains accessible regardless of screen size or device.",
    "version": "1.0.0",
    "date": "2025-03-21",
    "dataSchema": {
        "breakpoints": "List of viewport widths tested",
        "pageFlags": "Boolean flags indicating key responsive accessibility issues",
        "results": "Test results for each responsive breakpoint",
        "consolidated": "Summary of findings across all breakpoints",
        "timestamp": "ISO timestamp when the test was run"
    },
    "tests": [
        {
            "id": "content-overflow",
            "name": "Content Overflow Analysis",
            "description": "Identifies elements that overflow the viewport or their container at specific breakpoints, potentially creating horizontal scrolling or hidden content.",
            "impact": "high",
            "wcagCriteria": ["1.4.10"],
            "howToFix": "Ensure content properly wraps, scales, or reflows at all viewport sizes. Use relative units (%, em, rem) and CSS techniques like flexbox or grid for responsive layouts.",
            "resultsFields": {
                "pageFlags.hasOverflowIssues": "Indicates if overflow issues were detected",
                "pageFlags.details.overflowBreakpoints": "Which breakpoints have overflow issues",
                "results.breakpointResults.*.tests.overflow": "Overflow test results for each breakpoint"
            }
        },
        {
            "id": "touch-target-size",
            "name": "Touch Target Size Analysis",
            "description": "Checks whether interactive elements have adequate tap/touch target sizes at mobile breakpoints. Small touch targets are difficult for users with motor impairments.",
            "impact": "high",
            "wcagCriteria": ["2.5.5"],
            "howToFix": "Ensure interactive elements have touch targets at least 44x44 pixels at mobile breakpoints. Use min-width, min-height, and padding to increase the target size without necessarily changing the visual appearance.",
            "resultsFields": {
                "pageFlags.hasSmallTouchTargets": "Indicates if small touch targets were detected",
                "pageFlags.details.smallTargetBreakpoints": "Which breakpoints have small touch target issues",
                "results.breakpointResults.*.tests.touchTargets": "Touch target test results for each breakpoint"
            }
        },
        {
            "id": "font-scaling",
            "name": "Font Scaling Analysis",
            "description": "Evaluates how text size scales across different viewport widths and whether text becomes too small to read at any breakpoint.",
            "impact": "medium",
            "wcagCriteria": ["1.4.4"],
            "howToFix": "Use relative font sizes (em, rem) and ensure text never falls below 12px at any viewport size. Implement a type scale that maintains readability across all breakpoints.",
            "resultsFields": {
                "pageFlags.hasSmallText": "Indicates if small text issues were detected",
                "pageFlags.details.smallTextBreakpoints": "Which breakpoints have small text issues",
                "results.breakpointResults.*.tests.fontScaling": "Font scaling test results for each breakpoint"
            }
        },
        {
            "id": "fixed-positioning",
            "name": "Fixed Position Element Analysis",
            "description": "Identifies elements with fixed positioning that may obscure content or be inaccessible on small viewports.",
            "impact": "medium",
            "wcagCriteria": ["1.4.10", "2.4.7"],
            "howToFix": "Ensure fixed elements (like sticky headers or floating buttons) are properly adjusted or removed at small viewports. Test that they don't obscure important content or trap keyboard focus.",
            "resultsFields": {
                "pageFlags.hasFixedPositionIssues": "Indicates if fixed position issues were detected",
                "pageFlags.details.fixedPositionBreakpoints": "Which breakpoints have fixed position issues",
                "results.breakpointResults.*.tests.fixedPosition": "Fixed position test results for each breakpoint"
            }
        },
        {
            "id": "content-stacking",
            "name": "Content Stacking Order Analysis",
            "description": "Evaluates how content reflows and stacks at different breakpoints, checking for logical reading order and proper semantic structure.",
            "impact": "medium",
            "wcagCriteria": ["1.3.2"],
            "howToFix": "Ensure content maintains a logical reading order when it reflows at different viewport sizes. Use proper HTML structure and CSS order properties to maintain a sensible DOM order.",
            "resultsFields": {
                "pageFlags.hasStackingOrderIssues": "Indicates if stacking order issues were detected",
                "pageFlags.details.stackingOrderBreakpoints": "Which breakpoints have stacking order issues",
                "results.breakpointResults.*.tests.contentStacking": "Content stacking test results for each breakpoint"
            }
        }
    ]
}

async def test_responsive_accessibility(page, breakpoint):
    """
    Test accessibility issues specific to a given responsive breakpoint
    
    Args:
        page: The Puppeteer page object
        breakpoint: The viewport width being tested
        
    Returns:
        dict: Results of responsive accessibility tests at this breakpoint
    """
    try:
        print(f"Running responsive accessibility tests at {breakpoint}px breakpoint")
        
        # Initialize results for this breakpoint
        results = {
            'breakpoint': breakpoint,
            'timestamp': datetime.now().isoformat(),
            'tests': {}
        }
        
        # 1. Test for content overflow issues
        print("  Testing for content overflow issues...")
        overflow_results = await test_content_overflow(page, breakpoint)
        results['tests']['overflow'] = overflow_results
        
        # 2. Test for touch target size issues (especially important at mobile breakpoints)
        print("  Testing for touch target size issues...")
        touch_target_results = await test_touch_targets(page, breakpoint)
        results['tests']['touchTargets'] = touch_target_results
        
        # 3. Test for font scaling issues
        print("  Testing for font scaling issues...")
        font_scaling_results = await test_font_scaling(page, breakpoint)
        results['tests']['fontScaling'] = font_scaling_results
        
        # 4. Test for fixed position elements that might cause issues
        print("  Testing for fixed position element issues...")
        fixed_position_results = await test_fixed_position(page, breakpoint)
        results['tests']['fixedPosition'] = fixed_position_results
        
        # 5. Test for content stacking order issues
        print("  Testing for content stacking order issues...")
        stacking_order_results = await test_content_stacking(page, breakpoint)
        results['tests']['contentStacking'] = stacking_order_results
        
        return results
        
    except Exception as e:
        print(f"Error in responsive accessibility testing at {breakpoint}px: {str(e)}")

        return {
            'breakpoint': breakpoint,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def test_content_overflow(page, breakpoint):
    """Test for elements that overflow the viewport or their container"""
    try:
        # Initialize test data structure for section-aware reporting
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        overflow_data = await page.evaluate('''
            (breakpoint) => {
                // Find elements that overflow the viewport horizontally
                function findOverflowingElements() {
                    const viewportWidth = window.innerWidth;
                    const viewportHeight = window.innerHeight;
                    const bodyWidth = document.body.scrollWidth;
                    
                    const results = {
                        viewportDimensions: {
                            width: viewportWidth,
                            height: viewportHeight
                        },
                        bodyDimensions: {
                            width: bodyWidth,
                            height: document.body.scrollHeight
                        },
                        hasHorizontalOverflow: bodyWidth > viewportWidth,
                        horizontalOverflowAmount: Math.max(0, bodyWidth - viewportWidth),
                        overflowingElements: []
                    };
                    
                    // Check all elements for overflow
                    const allElements = document.querySelectorAll('*');
                    for (const element of allElements) {
                        // Skip invisible elements
                        const style = window.getComputedStyle(element);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                            continue;
                        }
                        
                        const rect = element.getBoundingClientRect();
                        
                        // Check if element extends beyond viewport width
                        if (rect.width > 0 && (rect.right > viewportWidth || rect.left < 0)) {
                            results.overflowingElements.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                className: element.className || null,
                                text: element.textContent?.substring(0, 50)?.trim() || null,
                                dimensions: {
                                    width: rect.width,
                                    height: rect.height
                                },
                                position: {
                                    left: rect.left,
                                    right: rect.right
                                },
                                overflowAmount: {
                                    left: Math.max(0, -rect.left),
                                    right: Math.max(0, rect.right - viewportWidth)
                                },
                                isInteractive: isInteractiveElement(element),
                                isContentElement: isContentElement(element)
                            });
                        }
                        
                        // Check elements with overflow set to hidden for potential clipped content
                        if (style.overflow === 'hidden' || 
                            style.overflowX === 'hidden' || 
                            style.overflowY === 'hidden') {
                            
                            // Check if it has children larger than itself
                            let hasOverflowingChildren = false;
                            let childWidth = 0;
                            
                            for (const child of element.children) {
                                const childRect = child.getBoundingClientRect();
                                childWidth = Math.max(childWidth, childRect.width);
                                
                                if (childRect.width > rect.width) {
                                    hasOverflowingChildren = true;
                                    break;
                                }
                            }
                            
                            if (hasOverflowingChildren) {
                                results.overflowingElements.push({
                                    element: element.tagName.toLowerCase(),
                                    id: element.id || null,
                                    className: element.className || null,
                                    text: element.textContent?.substring(0, 50)?.trim() || null,
                                    dimensions: {
                                        width: rect.width,
                                        height: rect.height
                                    },
                                    childWidth: childWidth,
                                    overflowStyle: {
                                        overflow: style.overflow,
                                        overflowX: style.overflowX,
                                        overflowY: style.overflowY
                                    },
                                    isContainer: true,
                                    hasClippedContent: true
                                });
                            }
                        }
                    }
                    
                    return results;
                }
                
                // Helper function to check if element is interactive
                function isInteractiveElement(element) {
                    const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'details'];
                    
                    if (interactiveTags.includes(element.tagName.toLowerCase())) {
                        return true;
                    }
                    
                    if (element.hasAttribute('tabindex') && element.getAttribute('tabindex') >= 0) {
                        return true;
                    }
                    
                    if (element.hasAttribute('role')) {
                        const interactiveRoles = ['button', 'link', 'checkbox', 'menuitem', 'tab', 'radio'];
                        if (interactiveRoles.includes(element.getAttribute('role'))) {
                            return true;
                        }
                    }
                    
                    return false;
                }
                
                // Helper function to identify main content elements
                function isContentElement(element) {
                    const contentTags = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'article', 'section', 'main'];
                    
                    if (contentTags.includes(element.tagName.toLowerCase())) {
                        return true;
                    }
                    
                    if (element.hasAttribute('role')) {
                        const contentRoles = ['main', 'article', 'heading'];
                        if (contentRoles.includes(element.getAttribute('role'))) {
                            return true;
                        }
                    }
                    
                    return false;
                }
                
                return findOverflowingElements();
            }
        ''', breakpoint)
        
        # Process findings and determine severity
        issues = []
        pageFlags = {
            'hasOverflowIssues': len(overflow_data.get('overflowingElements', [])) > 0,
            'horizontalScrollingDetected': overflow_data.get('horizontalOverflowAmount', 0) > 5, # 5px threshold
            'details': {
                'overflowCount': len(overflow_data.get('overflowingElements', [])),
                'interactiveElementsOverflow': 0,
                'contentElementsOverflow': 0,
                'containersWithClippedContent': 0
            }
        }
        
        # Count specific issue types
        for element in overflow_data.get('overflowingElements', []):
            if element.get('isInteractive'):
                pageFlags['details']['interactiveElementsOverflow'] += 1
            if element.get('isContentElement'):
                pageFlags['details']['contentElementsOverflow'] += 1
            if element.get('hasClippedContent'):
                pageFlags['details']['containersWithClippedContent'] += 1
                
            # Create issue entries for significant problems
            if element.get('isInteractive') or element.get('isContentElement'):
                issues.append({
                    'element': element.get('element'),
                    'id': element.get('id'),
                    'className': element.get('className'),
                    'issueType': 'overflow',
                    'severity': 'high' if element.get('isInteractive') else 'medium',
                    'details': f"{'Interactive' if element.get('isInteractive') else 'Content'} element overflows at {breakpoint}px breakpoint",
                    'overflowAmount': element.get('overflowAmount')
                })

        
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])
        
        return {
            'pageFlags': pageFlags,
            'data': overflow_data,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error testing content overflow: {str(e)}")

        # Initialize test data structure for section-aware reporting if it doesn't exist
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])

        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def test_touch_targets(page, breakpoint):
    """Test for touch targets that are too small at the current breakpoint"""
    try:
        # Initialize test data structure for section-aware reporting
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        # This test is most relevant at mobile breakpoints
        is_mobile_breakpoint = breakpoint <= 768
        
        touch_target_data = await page.evaluate('''
            (breakpoint, isMobile) => {
                // Find interactive elements with small touch targets
                function analyzeTouchTargets() {
                    // Minimum recommended touch target size (WCAG 2.5.5)
                    const minTargetSize = 44; // 44x44 pixels
                    
                    const results = {
                        isMobileBreakpoint: isMobile,
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        smallTouchTargets: [],
                        adjacentTouchTargets: []
                    };
                    
                    // Only do detailed analysis for mobile breakpoints
                    if (!isMobile) {
                        return results;
                    }
                    
                    // Find all interactive elements
                    const interactiveSelectors = [
                        'a', 'button', 'input', 'select', 'textarea',
                        '[role="button"]', '[role="link"]', '[role="checkbox"]',
                        '[role="radio"]', '[role="tab"]', '[role="menuitem"]',
                        '[tabindex]:not([tabindex="-1"])'
                    ];
                    
                    const interactiveElements = document.querySelectorAll(interactiveSelectors.join(','));
                    
                    // Track all touch targets for adjacency check
                    const allTargets = [];
                    
                    // Analyze each interactive element
                    for (const element of interactiveElements) {
                        // Skip invisible elements
                        const style = window.getComputedStyle(element);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                            continue;
                        }
                        
                        const rect = element.getBoundingClientRect();
                        
                        // Skip elements that are not visible in the viewport
                        if (rect.right < 0 || rect.bottom < 0 || 
                            rect.left > window.innerWidth || rect.top > window.innerHeight) {
                            continue;
                        }
                        
                        // Add to all targets for adjacency check
                        allTargets.push({
                            element: element,
                            rect: rect
                        });
                        
                        // Check size
                        if (rect.width < minTargetSize || rect.height < minTargetSize) {
                            // Get accessible name
                            let accessibleName = '';
                            if (element.hasAttribute('aria-label')) {
                                accessibleName = element.getAttribute('aria-label');
                            } else if (element.hasAttribute('aria-labelledby')) {
                                const labelId = element.getAttribute('aria-labelledby');
                                const labelElement = document.getElementById(labelId);
                                if (labelElement) {
                                    accessibleName = labelElement.textContent;
                                }
                            } else {
                                accessibleName = element.textContent || '';
                            }
                            
                            results.smallTouchTargets.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                className: element.className || null,
                                accessibleName: accessibleName.trim().substring(0, 50),
                                type: element.type || null,
                                dimensions: {
                                    width: rect.width,
                                    height: rect.height
                                },
                                position: {
                                    top: rect.top,
                                    left: rect.left
                                },
                                role: element.getAttribute('role') || null
                            });
                        }
                    }
                    
                    // Check for adjacent touch targets that are too close together
                    if (allTargets.length > 1) {
                        for (let i = 0; i < allTargets.length; i++) {
                            for (let j = i + 1; j < allTargets.length; j++) {
                                const a = allTargets[i].rect;
                                const b = allTargets[j].rect;
                                
                                // Calculate distance between center points
                                const aCenter = { x: a.left + a.width / 2, y: a.top + a.height / 2 };
                                const bCenter = { x: b.left + b.width / 2, y: b.top + b.height / 2 };
                                
                                const distance = Math.sqrt(
                                    Math.pow(aCenter.x - bCenter.x, 2) + 
                                    Math.pow(aCenter.y - bCenter.y, 2)
                                );
                                
                                // If centers are closer than 44px, they're too close
                                if (distance < minTargetSize) {
                                    results.adjacentTouchTargets.push({
                                        element1: {
                                            element: allTargets[i].element.tagName.toLowerCase(),
                                            id: allTargets[i].element.id || null,
                                            text: allTargets[i].element.textContent?.trim().substring(0, 30) || null
                                        },
                                        element2: {
                                            element: allTargets[j].element.tagName.toLowerCase(),
                                            id: allTargets[j].element.id || null,
                                            text: allTargets[j].element.textContent?.trim().substring(0, 30) || null
                                        },
                                        distance: distance,
                                        positions: {
                                            element1: {
                                                top: a.top,
                                                left: a.left,
                                                width: a.width,
                                                height: a.height
                                            },
                                            element2: {
                                                top: b.top,
                                                left: b.left,
                                                width: b.width,
                                                height: b.height
                                            }
                                        }
                                    });
                                }
                            }
                        }
                    }
                    
                    return results;
                }
                
                return analyzeTouchTargets();
            }
        ''', breakpoint, is_mobile_breakpoint)
        
        # Process the results
        issues = []
        pageFlags = {
            'hasSmallTouchTargets': len(touch_target_data.get('smallTouchTargets', [])) > 0,
            'hasAdjacentTouchTargets': len(touch_target_data.get('adjacentTouchTargets', [])) > 0,
            'isMobileBreakpoint': touch_target_data.get('isMobileBreakpoint', False),
            'details': {
                'smallTouchTargetCount': len(touch_target_data.get('smallTouchTargets', [])),
                'adjacentTouchTargetCount': len(touch_target_data.get('adjacentTouchTargets', []))
            }
        }
        
        # Create issues for each small touch target
        for target in touch_target_data.get('smallTouchTargets', []):
            width = target.get('dimensions', {}).get('width', 0)
            height = target.get('dimensions', {}).get('height', 0)
            
            issues.append({
                'element': target.get('element'),
                'id': target.get('id'),
                'className': target.get('className'),
                'issueType': 'smallTouchTarget',
                'severity': 'high' if is_mobile_breakpoint else 'medium',
                'details': f"Touch target size ({width:.1f}x{height:.1f}px) is too small. Should be at least 44x44px.",
                'accessibleName': target.get('accessibleName')
            })
            
        # Create issues for adjacent touch targets
        for adjacent in touch_target_data.get('adjacentTouchTargets', []):
            issues.append({
                'elements': [adjacent.get('element1'), adjacent.get('element2')],
                'issueType': 'adjacentTouchTargets',
                'severity': 'medium',
                'details': f"Touch targets are too close together ({adjacent.get('distance', 0):.1f}px apart). Should be at least 44px apart.",
                'distance': adjacent.get('distance')
            })
            
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])
            
        return {
            'pageFlags': pageFlags,
            'data': touch_target_data,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error testing touch targets: {str(e)}")

        # Initialize test data structure for section-aware reporting if it doesn't exist
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])

        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def test_font_scaling(page, breakpoint):
    """Test for text that is too small at the current breakpoint"""
    try:
        # Initialize test data structure for section-aware reporting
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        font_data = await page.evaluate('''
            (breakpoint) => {
                // Analyze text elements for size issues
                function analyzeFontScaling() {
                    const minFontSize = 12; // Minimum readable font size in pixels
                    
                    const results = {
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        textElements: [],
                        smallTextElements: []
                    };
                    
                    // Find text-containing elements
                    const textSelectors = [
                        'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'li', 'a', 'button',
                        'label', 'td', 'th', 'figcaption'
                    ];
                    
                    const potentialTextElements = document.querySelectorAll(textSelectors.join(','));
                    
                    // Track unique font sizes for statistics
                    const fontSizes = new Set();
                    
                    // Analyze visible text elements
                    for (const element of potentialTextElements) {
                        // Skip elements without text
                        const textContent = element.textContent?.trim();
                        if (!textContent) continue;
                        
                        // Skip invisible elements
                        const style = window.getComputedStyle(element);
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                            continue;
                        }
                        
                        const rect = element.getBoundingClientRect();
                        
                        // Skip elements that are not in viewport
                        if (rect.right < 0 || rect.bottom < 0 || 
                            rect.left > window.innerWidth || rect.top > window.innerHeight) {
                            continue;
                        }
                        
                        // Get computed font size
                        const fontSize = parseFloat(style.fontSize);
                        fontSizes.add(fontSize);
                        
                        // Skip elements that are already analyzed parents
                        if (element.hasAttribute('data-analyzed')) {
                            continue;
                        }
                        
                        // Check if it has other text element children
                        const childTextElements = element.querySelectorAll(textSelectors.join(','));
                        for (const child of childTextElements) {
                            child.setAttribute('data-analyzed', 'true');
                        }
                        
                        // Check if font size is too small
                        if (fontSize < minFontSize) {
                            results.smallTextElements.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                className: element.className || null,
                                text: textContent.substring(0, 50),
                                fontSize: fontSize,
                                fontUnit: style.fontSize.replace(/[0-9.]/g, ''),
                                fontWeight: style.fontWeight,
                                color: style.color,
                                backgroundColor: style.backgroundColor,
                                dimensions: {
                                    width: rect.width,
                                    height: rect.height
                                },
                                isHeader: /^h[1-6]$/.test(element.tagName.toLowerCase()),
                                isInteractive: isInteractiveElement(element)
                            });
                        }
                        
                        // Add to all text elements for statistics
                        results.textElements.push({
                            element: element.tagName.toLowerCase(),
                            fontSize: fontSize,
                            fontUnit: style.fontSize.replace(/[0-9.]/g, ''),
                            isHeader: /^h[1-6]$/.test(element.tagName.toLowerCase()),
                            isInteractive: isInteractiveElement(element)
                        });
                    }
                    
                    // Remove data-analyzed attributes
                    document.querySelectorAll('[data-analyzed]').forEach(el => {
                        el.removeAttribute('data-analyzed');
                    });
                    
                    // Generate statistics
                    results.statistics = {
                        textElementCount: results.textElements.length,
                        smallTextCount: results.smallTextElements.length,
                        smallTextPercentage: results.textElements.length > 0 ? 
                            (results.smallTextElements.length / results.textElements.length) * 100 : 0,
                        uniqueFontSizes: Array.from(fontSizes).sort((a, b) => a - b),
                        smallestFontSize: Math.min(...fontSizes),
                        largestFontSize: Math.max(...fontSizes)
                    };
                    
                    return results;
                }
                
                // Helper function to check if element is interactive
                function isInteractiveElement(element) {
                    const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'details'];
                    
                    if (interactiveTags.includes(element.tagName.toLowerCase())) {
                        return true;
                    }
                    
                    if (element.hasAttribute('tabindex') && element.getAttribute('tabindex') >= 0) {
                        return true;
                    }
                    
                    if (element.hasAttribute('role')) {
                        const interactiveRoles = ['button', 'link', 'checkbox', 'menuitem', 'tab', 'radio'];
                        if (interactiveRoles.includes(element.getAttribute('role'))) {
                            return true;
                        }
                    }
                    
                    return false;
                }
                
                return analyzeFontScaling();
            }
        ''', breakpoint)
        
        # Process the results
        issues = []
        pageFlags = {
            'hasSmallText': len(font_data.get('smallTextElements', [])) > 0,
            'details': {
                'smallTextCount': len(font_data.get('smallTextElements', [])),
                'textElementCount': font_data.get('statistics', {}).get('textElementCount', 0),
                'smallTextPercentage': font_data.get('statistics', {}).get('smallTextPercentage', 0),
                'smallestFontSize': font_data.get('statistics', {}).get('smallestFontSize', 0)
            }
        }
        
        # Create issues for small text elements
        for element in font_data.get('smallTextElements', []):
            issues.append({
                'element': element.get('element'),
                'id': element.get('id'),
                'className': element.get('className'),
                'issueType': 'smallText',
                'severity': 'high' if element.get('isInteractive') else 'medium',
                'details': f"Text size ({element.get('fontSize')}px) is too small. Should be at least 12px.",
                'text': element.get('text'),
                'fontSize': element.get('fontSize'),
                'isInteractive': element.get('isInteractive')
            })
            
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])
            
        return {
            'pageFlags': pageFlags,
            'data': font_data,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error testing font scaling: {str(e)}")

        # Initialize test data structure for section-aware reporting if it doesn't exist
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])

        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def test_fixed_position(page, breakpoint):
    """Test for fixed position elements that might cause issues"""
    try:
        # Initialize test data structure for section-aware reporting
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        fixed_position_data = await page.evaluate('''
            (breakpoint) => {
                // Find fixed or sticky positioned elements
                function analyzeFixedElements() {
                    const results = {
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        fixedElements: [],
                        stickyElements: [],
                        fixedElementsWithIssues: []
                    };
                    
                    // Find all elements with fixed or sticky positioning
                    const allElements = document.querySelectorAll('*');
                    for (const element of allElements) {
                        const style = window.getComputedStyle(element);
                        
                        // Skip invisible elements
                        if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                            continue;
                        }
                        
                        const rect = element.getBoundingClientRect();
                        
                        // Track fixed position elements
                        if (style.position === 'fixed') {
                            const elementData = {
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                className: element.className || null,
                                text: element.textContent?.trim().substring(0, 50) || null,
                                dimensions: {
                                    width: rect.width,
                                    height: rect.height
                                },
                                position: {
                                    top: rect.top,
                                    right: rect.right,
                                    bottom: rect.bottom,
                                    left: rect.left
                                },
                                computedStyle: {
                                    top: style.top,
                                    right: style.right,
                                    bottom: style.bottom,
                                    left: style.left,
                                    zIndex: style.zIndex
                                },
                                isInteractive: isInteractiveElement(element) || containsInteractiveElements(element),
                                containsText: element.textContent?.trim().length > 0,
                                hasAriaHidden: element.hasAttribute('aria-hidden') && element.getAttribute('aria-hidden') === 'true'
                            };
                            
                            results.fixedElements.push(elementData);
                            
                            // Check for issues with this fixed element
                            const issues = checkFixedElementIssues(element, rect, style, breakpoint);
                            if (issues.length > 0) {
                                elementData.issues = issues;
                                results.fixedElementsWithIssues.push(elementData);
                            }
                        }
                        
                        // Track sticky position elements
                        if (style.position === 'sticky') {
                            results.stickyElements.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                className: element.className || null,
                                dimensions: {
                                    width: rect.width,
                                    height: rect.height
                                },
                                position: {
                                    top: rect.top,
                                    right: rect.right,
                                    bottom: rect.bottom,
                                    left: rect.left
                                },
                                computedStyle: {
                                    top: style.top,
                                    right: style.right,
                                    bottom: style.bottom,
                                    left: style.left,
                                    zIndex: style.zIndex
                                }
                            });
                        }
                    }
                    
                    return results;
                }
                
                // Check for specific issues with fixed elements
                function checkFixedElementIssues(element, rect, style, breakpoint) {
                    const issues = [];
                    const viewportWidth = window.innerWidth;
                    const viewportHeight = window.innerHeight;
                    
                    // Check if it takes too much viewport space on small screens
                    if (breakpoint <= 768) { // Mobile breakpoint
                        const viewportCoverage = (rect.width * rect.height) / (viewportWidth * viewportHeight);
                        if (viewportCoverage > 0.25) { // Takes up more than 25% of viewport
                            issues.push({
                                type: 'excessiveSize',
                                details: `Fixed element covers ${(viewportCoverage * 100).toFixed(1)}% of viewport`,
                                viewportCoverage: viewportCoverage
                            });
                        }
                    }
                    
                    // Check if it obscures important content
                    if (rect.top < 150 && rect.height > 50) {
                        // Look for headings or key content beneath
                        const headingsUnder = document.elementsFromPoint(
                            rect.left + rect.width/2, 
                            rect.bottom + 10
                        ).filter(el => /^h[1-6]$/.test(el.tagName.toLowerCase()));
                        
                        if (headingsUnder.length > 0) {
                            issues.push({
                                type: 'obscuresContent',
                                details: 'Fixed element may obscure headings',
                                obscuredElements: headingsUnder.map(h => ({
                                    element: h.tagName.toLowerCase(),
                                    text: h.textContent?.trim().substring(0, 30) || null
                                }))
                            });
                        }
                    }
                    
                    // Check if it contains interactive elements but not keyboard accessible
                    const containsInteractive = containsInteractiveElements(element);
                    if (containsInteractive) {
                        const isKeyboardAccessible = element.querySelectorAll('a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])').length > 0;
                        
                        if (!isKeyboardAccessible) {
                            issues.push({
                                type: 'notKeyboardAccessible',
                                details: 'Fixed element contains interactive content not accessible by keyboard'
                            });
                        }
                    }
                    
                    // Check if it's full-width on mobile but not at the top or bottom edge
                    if (breakpoint <= 768 && 
                        rect.width >= viewportWidth - 5 && // Almost full width (allowing for rounding)
                        rect.top > 5 && rect.bottom < viewportHeight - 5) { // Not at edge
                        issues.push({
                            type: 'floatingFullWidth',
                            details: 'Full-width fixed element is floating in middle of viewport',
                            position: {
                                top: rect.top,
                                bottom: rect.bottom
                            }
                        });
                    }
                    
                    return issues;
                }
                
                // Helper function to check if element is interactive
                function isInteractiveElement(element) {
                    const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'details'];
                    
                    if (interactiveTags.includes(element.tagName.toLowerCase())) {
                        return true;
                    }
                    
                    if (element.hasAttribute('tabindex') && element.getAttribute('tabindex') >= 0) {
                        return true;
                    }
                    
                    if (element.hasAttribute('role')) {
                        const interactiveRoles = ['button', 'link', 'checkbox', 'menuitem', 'tab', 'radio'];
                        if (interactiveRoles.includes(element.getAttribute('role'))) {
                            return true;
                        }
                    }
                    
                    return false;
                }
                
                // Helper function to check if element contains interactive elements
                function containsInteractiveElements(element) {
                    const interactiveSelectors = [
                        'a', 'button', 'input', 'select', 'textarea',
                        '[role="button"]', '[role="link"]', '[role="checkbox"]',
                        '[role="radio"]', '[role="tab"]', '[role="menuitem"]',
                        '[tabindex]:not([tabindex="-1"])'
                    ];
                    
                    return element.querySelector(interactiveSelectors.join(',')) !== null;
                }
                
                return analyzeFixedElements();
            }
        ''', breakpoint)
        
        # Process the results
        issues = []
        pageFlags = {
            'hasFixedPositionElements': len(fixed_position_data.get('fixedElements', [])) > 0,
            'hasStickyPositionElements': len(fixed_position_data.get('stickyElements', [])) > 0,
            'hasFixedPositionIssues': len(fixed_position_data.get('fixedElementsWithIssues', [])) > 0,
            'details': {
                'fixedElementCount': len(fixed_position_data.get('fixedElements', [])),
                'stickyElementCount': len(fixed_position_data.get('stickyElements', [])),
                'fixedElementsWithIssuesCount': len(fixed_position_data.get('fixedElementsWithIssues', []))
            }
        }
        
        # Create issues for problematic fixed elements
        for element in fixed_position_data.get('fixedElementsWithIssues', []):
            for issue in element.get('issues', []):
                issues.append({
                    'element': element.get('element'),
                    'id': element.get('id'),
                    'className': element.get('className'),
                    'issueType': f"fixedPosition_{issue.get('type')}",
                    'severity': 'high' if issue.get('type') == 'notKeyboardAccessible' else 'medium',
                    'details': issue.get('details'),
                    'position': element.get('position')
                })
                
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])
                
        return {
            'pageFlags': pageFlags,
            'data': fixed_position_data,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error testing fixed position elements: {str(e)}")

        # Initialize test data structure for section-aware reporting if it doesn't exist
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])

        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

async def test_content_stacking(page, breakpoint):
    """Test for content stacking order issues at this breakpoint"""
    try:
        # Initialize test data structure for section-aware reporting
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        stacking_data = await page.evaluate('''
            (breakpoint) => {
                // Analyze how content stacks at this breakpoint
                function analyzeContentStacking() {
                    const results = {
                        viewport: {
                            width: window.innerWidth,
                            height: window.innerHeight
                        },
                        domOrder: [],
                        visualOrder: [],
                        orderViolations: []
                    };
                    
                    // Find main content area
                    const mainContent = document.querySelector('main') || document.body;
                    
                    // Get key content sections in DOM order
                    const keySelectors = [
                        'header', 'nav', 'main', 'article', 'section', 'aside', 'footer',
                        '[role="banner"]', '[role="navigation"]', '[role="main"]', 
                        '[role="complementary"]', '[role="contentinfo"]'
                    ];
                    
                    // Get them in DOM order
                    const contentSections = Array.from(document.querySelectorAll(keySelectors.join(',')));
                    
                    // Filter to visible sections
                    const visibleSections = contentSections.filter(section => {
                        const style = window.getComputedStyle(section);
                        return style.display !== 'none' && 
                               style.visibility !== 'hidden' && 
                               style.opacity !== '0';
                    });
                    
                    // Record DOM order
                    results.domOrder = visibleSections.map(section => {
                        return {
                            element: section.tagName.toLowerCase(),
                            role: section.getAttribute('role') || null,
                            id: section.id || null,
                            heading: section.querySelector('h1, h2, h3')?.textContent?.trim().substring(0, 30) || null
                        };
                    });
                    
                    // Sort by visual position (top to bottom)
                    const visualOrder = [...visibleSections].sort((a, b) => {
                        const aRect = a.getBoundingClientRect();
                        const bRect = b.getBoundingClientRect();
                        return aRect.top - bRect.top;
                    });
                    
                    // Record visual order
                    results.visualOrder = visualOrder.map(section => {
                        const rect = section.getBoundingClientRect();
                        return {
                            element: section.tagName.toLowerCase(),
                            role: section.getAttribute('role') || null,
                            id: section.id || null,
                            heading: section.querySelector('h1, h2, h3')?.textContent?.trim().substring(0, 30) || null,
                            position: {
                                top: rect.top,
                                left: rect.left
                            }
                        };
                    });
                    
                    // Check for violations of logical order
                    // Look at pairs of elements where visual order differs from DOM order
                    for (let i = 0; i < visibleSections.length; i++) {
                        const domPosition = visibleSections.indexOf(visualOrder[i]);
                        if (domPosition !== i) {
                            // This element is in a different position in the DOM than visually
                            const element = visualOrder[i];
                            const domElement = visibleSections[i];
                            const rect = element.getBoundingClientRect();
                            
                            results.orderViolations.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                heading: element.querySelector('h1, h2, h3')?.textContent?.trim().substring(0, 30) || null,
                                visualPosition: i,
                                domPosition: domPosition,
                                positionDifference: Math.abs(domPosition - i),
                                coordinates: {
                                    top: rect.top,
                                    left: rect.left
                                },
                                expectedElement: {
                                    element: domElement.tagName.toLowerCase(),
                                    id: domElement.id || null,
                                    heading: domElement.querySelector('h1, h2, h3')?.textContent?.trim().substring(0, 30) || null
                                }
                            });
                        }
                    }
                    
                    // Look for cases where flexbox or grid changes order
                    const flexContainers = document.querySelectorAll('[style*="display: flex"], [style*="display:flex"]');
                    for (const container of flexContainers) {
                        const style = window.getComputedStyle(container);
                        
                        // Skip if not visible
                        if (style.display !== 'flex' || 
                            style.visibility === 'hidden' || 
                            style.opacity === '0') {
                            continue;
                        }
                        
                        const children = Array.from(container.children);
                        if (children.length < 2) continue;
                        
                        // Check for order property
                        for (const child of children) {
                            const childStyle = window.getComputedStyle(child);
                            const orderValue = parseInt(childStyle.order);
                            
                            if (orderValue !== 0) {
                                // This element has its order changed with CSS
                                results.orderViolations.push({
                                    element: child.tagName.toLowerCase(),
                                    id: child.id || null,
                                    text: child.textContent?.trim().substring(0, 30) || null,
                                    issueType: 'css-order',
                                    cssProperties: {
                                        order: orderValue
                                    },
                                    container: {
                                        element: container.tagName.toLowerCase(),
                                        id: container.id || null
                                    }
                                });
                            }
                        }
                    }
                    
                    return results;
                }
                
                return analyzeContentStacking();
            }
        ''', breakpoint)
        
        # Process the results
        issues = []
        pageFlags = {
            'hasStackingOrderIssues': len(stacking_data.get('orderViolations', [])) > 0,
            'details': {
                'orderViolationCount': len(stacking_data.get('orderViolations', [])),
                'visualSectionsCount': len(stacking_data.get('visualOrder', []))
            }
        }
        
        # Create issues for stacking order problems
        for violation in stacking_data.get('orderViolations', []):
            # Determine severity based on how far the element is from its expected position
            position_difference = violation.get('positionDifference', 0)
            severity = 'low'
            if position_difference > 3:
                severity = 'high'
            elif position_difference > 1:
                severity = 'medium'
                
            if violation.get('issueType') == 'css-order':
                issues.append({
                    'element': violation.get('element'),
                    'id': violation.get('id'),
                    'issueType': 'cssOrderProperty',
                    'severity': 'medium',
                    'details': f"Element uses CSS order property which can create a mismatch between visual and DOM order.",
                    'orderValue': violation.get('cssProperties', {}).get('order')
                })
            else:
                issues.append({
                    'element': violation.get('element'),
                    'id': violation.get('id'),
                    'issueType': 'visualDomMismatch',
                    'severity': severity,
                    'details': f"Element appears visually at position {violation.get('visualPosition')} but is at position {violation.get('domPosition')} in the DOM order.",
                    'visualPosition': violation.get('visualPosition'),
                    'domPosition': violation.get('domPosition'),
                    'difference': position_difference
                })
                
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])
                
        return {
            'pageFlags': pageFlags,
            'data': stacking_data,
            'issues': issues,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error testing content stacking: {str(e)}")

        # Initialize test data structure for section-aware reporting if it doesn't exist
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        # Add section information to results
        test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
        
        # Print violations with section information for debugging
        if 'violations' in test_data['results']:
            print_violations_with_sections(test_data['results']['violations'])
        elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
            print_violations_with_sections(test_data['results']['details']['violations'])

        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def consolidate_responsive_results(breakpoint_results, page=None):
    """
    Consolidate results from multiple breakpoints into a summary
    
    Args:
        breakpoint_results: Dictionary of results from each breakpoint
        page: Optional Puppeteer page object for section-aware reporting
        
    Returns:
        dict: Consolidated summary of issues across breakpoints
    """
    try:
        print("Consolidating responsive test results...")
        print(f"DEBUG: breakpoint_results keys: {list(breakpoint_results.keys())}")
        
        # Initialize test data structure for section-aware reporting
        test_data = {
            'results': {
                'violations': [],
                'summary': {}
            }
        }
        
        if not breakpoint_results:
            print("ERROR: No breakpoint results to consolidate")
            # Add section information to results if page is provided
            if page:
                test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
                
                # Print violations with section information for debugging
                if 'violations' in test_data['results']:
                    print_violations_with_sections(test_data['results']['violations'])
                elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
                    print_violations_with_sections(test_data['results']['details']['violations'])

            return {
                'error': 'No breakpoint results to consolidate',
                'timestamp': datetime.now().isoformat()
            }
        
        # Initialize consolidated data structure
        consolidated = {
            'breakpoints': sorted([int(bp) for bp in breakpoint_results.keys()]),
            'testsSummary': {
                'overflow': {
                    'issueCount': 0,
                    'affectedBreakpoints': [],
                    'elementsByBreakpoint': {}
                },
                'touchTargets': {
                    'issueCount': 0,
                    'affectedBreakpoints': [],
                    'elementsByBreakpoint': {}
                },
                'fontScaling': {
                    'issueCount': 0,
                    'affectedBreakpoints': [],
                    'elementsByBreakpoint': {}
                },
                'fixedPosition': {
                    'issueCount': 0,
                    'affectedBreakpoints': [],
                    'elementsByBreakpoint': {}
                },
                'contentStacking': {
                    'issueCount': 0,
                    'affectedBreakpoints': [],
                    'elementsByBreakpoint': {}
                }
            },
            'elements': {},
            'issuesByType': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Process each breakpoint
        for breakpoint, results in breakpoint_results.items():
            print(f"DEBUG: Processing breakpoint {breakpoint}")
            
            # Get nested test data structure
            # In a11yTestMongo.py, we store the responsive results as:
            # breakpoint_results[bp]['tests']['responsive']
            responsive_data = None
            
            # First, check if this is already the tests structure or if we need to go deeper
            if 'tests' in results:
                print(f"DEBUG: Found 'tests' key in breakpoint results with keys: {list(results['tests'].keys())}")
                if 'responsive' in results['tests']:
                    responsive_data = results['tests']['responsive']
                    print(f"DEBUG: Found 'responsive' key with keys: {list(responsive_data.keys()) if isinstance(responsive_data, dict) else 'Not a dict'}")
                else:
                    # Direct test structure - the structure used in test_responsive_accessibility
                    responsive_data = results['tests']
            else:
                # It might be the direct data structure from test_responsive_accessibility function
                # where each test result is stored directly
                print(f"DEBUG: No 'tests' key found, using direct breakpoint results with keys: {list(results.keys())}")
                responsive_data = results
            
            # Skip this breakpoint if no responsive data was found
            if not responsive_data:
                print(f"DEBUG: No responsive data found for breakpoint {breakpoint}")
                continue
                
            # Handle different data structures - extract the actual test results
            tests = {}
            
            # Check if we have a tests dict inside responsive_data
            if isinstance(responsive_data, dict) and 'tests' in responsive_data:
                tests = responsive_data['tests']
                print(f"DEBUG: Found 'tests' inside responsive_data with keys: {list(tests.keys()) if isinstance(tests, dict) else 'Not a dict'}")
            elif isinstance(responsive_data, dict):
                # Maybe the test results are directly in responsive_data
                for test_name in ['overflow', 'touchTargets', 'fontScaling', 'fixedPosition', 'contentStacking']:
                    if test_name in responsive_data:
                        tests[test_name] = responsive_data[test_name]
                        print(f"DEBUG: Found test '{test_name}' directly in responsive_data")
            
            # Add fallback structure detection - check if this is a direct result from test_responsive_accessibility
            if not tests and isinstance(responsive_data, dict) and 'pageFlags' in responsive_data:
                print(f"DEBUG: This appears to be a direct test result with 'pageFlags'")
                # This is a direct test result, extract its test name from the data
                test_name = None
                for possible_name in ['overflow', 'touchTargets', 'fontScaling', 'fixedPosition', 'contentStacking']:
                    if possible_name.lower() in str(responsive_data).lower():
                        test_name = possible_name
                        break
                
                if test_name:
                    tests[test_name] = responsive_data
                    print(f"DEBUG: Created test entry for '{test_name}' from direct result")
            
            # If we found nothing, log and continue to next breakpoint
            if not tests:
                print(f"WARNING: Could not extract any tests from breakpoint {breakpoint} data")
                continue
                
            # Process each test type
            for test_name in ['overflow', 'touchTargets', 'fontScaling', 'fixedPosition', 'contentStacking']:
                if test_name not in tests:
                    continue
                    
                test_data = tests[test_name]
                
                # Ensure test_data is a dictionary
                if not isinstance(test_data, dict):
                    print(f"Warning: {test_name} test data is not a dictionary (value: {test_data})")
                    continue  # Skip this test
                
                # We need to handle different data structures:
                # 1. Direct issues array in test_data
                # 2. Issues nested inside pageFlags
                issues = []
                
                if 'issues' in test_data and test_data['issues']:
                    issues = test_data['issues']
                    print(f"DEBUG: Found {len(issues)} issues directly in {test_name}")
                elif 'pageFlags' in test_data:
                    # Extract issues from pageFlags data
                    for flag_key, flag_value in test_data['pageFlags'].items():
                        if isinstance(flag_value, bool) and flag_value and 'has' in flag_key.lower():
                            issue_type = flag_key.replace('has', '').lower()
                            # Create synthetic issue
                            issues.append({
                                'element': 'page',
                                'id': None,
                                'issueType': issue_type,
                                'details': f"Page has {issue_type} issues at {breakpoint}px breakpoint"
                            })
                            print(f"DEBUG: Created synthetic issue for '{issue_type}' from pageFlags")
                
                # If we found no issues from any source, skip this test
                if not issues:
                    print(f"DEBUG: No issues found for {test_name} at breakpoint {breakpoint}")
                    continue
                
                # Update test summary
                consolidated['testsSummary'][test_name]['issueCount'] += len(issues)
                if breakpoint not in consolidated['testsSummary'][test_name]['affectedBreakpoints']:
                    consolidated['testsSummary'][test_name]['affectedBreakpoints'].append(breakpoint)
                
                # Record elements with issues for this breakpoint
                if breakpoint not in consolidated['testsSummary'][test_name]['elementsByBreakpoint']:
                    consolidated['testsSummary'][test_name]['elementsByBreakpoint'][breakpoint] = []
                
                # Process each issue for this test
                for issue in issues:
                    issue_type = issue.get('issueType', 'unknown')
                    element_id = issue.get('id') or issue.get('element') or 'unknown'
                    
                    # Create unique key for this element
                    element_key = f"{test_name}_{issue_type}_{element_id}"
                    
                    # Add to elements by breakpoint
                    consolidated['testsSummary'][test_name]['elementsByBreakpoint'][breakpoint].append({
                        'element': issue.get('element'),
                        'id': issue.get('id'),
                        'issueType': issue_type,
                        'details': issue.get('details')
                    })
                    
                    # Update elements tracking
                    if element_key not in consolidated['elements']:
                        consolidated['elements'][element_key] = {
                            'element': issue.get('element'),
                            'id': issue.get('id'),
                            'issueType': issue_type,
                            'testName': test_name,
                            'breakpoints': [],
                            'details': issue.get('details')
                        }
                    
                    if breakpoint not in consolidated['elements'][element_key]['breakpoints']:
                        consolidated['elements'][element_key]['breakpoints'].append(breakpoint)
                    
                    # Update issues by type
                    if issue_type not in consolidated['issuesByType']:
                        consolidated['issuesByType'][issue_type] = {
                            'count': 0,
                            'severity': issue.get('severity', 'medium'),
                            'affectedElements': [],
                            'affectedBreakpoints': []
                        }
                    
                    consolidated['issuesByType'][issue_type]['count'] += 1
                    
                    if element_key not in consolidated['issuesByType'][issue_type]['affectedElements']:
                        consolidated['issuesByType'][issue_type]['affectedElements'].append(element_key)
                    
                    if breakpoint not in consolidated['issuesByType'][issue_type]['affectedBreakpoints']:
                        consolidated['issuesByType'][issue_type]['affectedBreakpoints'].append(breakpoint)
        
        # Sort all breakpoint lists
        for test_name in consolidated['testsSummary']:
            consolidated['testsSummary'][test_name]['affectedBreakpoints'] = sorted(
                [int(bp) for bp in consolidated['testsSummary'][test_name]['affectedBreakpoints']]
            )
        
        for element_key in consolidated['elements']:
            consolidated['elements'][element_key]['breakpoints'] = sorted(
                [int(bp) for bp in consolidated['elements'][element_key]['breakpoints']]
            )
        
        for issue_type in consolidated['issuesByType']:
            consolidated['issuesByType'][issue_type]['affectedBreakpoints'] = sorted(
                [int(bp) for bp in consolidated['issuesByType'][issue_type]['affectedBreakpoints']]
            )
        
        # Create a high-level summary
        total_issues = sum([consolidated['testsSummary'][test]['issueCount'] for test in consolidated['testsSummary']])
        affected_elements = len(consolidated['elements'])
        total_breakpoints = len(consolidated['breakpoints'])
        affected_breakpoints = len(set().union(*[
            set(consolidated['testsSummary'][test]['affectedBreakpoints']) 
            for test in consolidated['testsSummary']
            if consolidated['testsSummary'][test]['affectedBreakpoints']
        ])) if any(consolidated['testsSummary'][test]['affectedBreakpoints'] for test in consolidated['testsSummary']) else 0
        
        # Add summary to consolidated results
        consolidated['summary'] = {
            'totalIssues': total_issues,
            'affectedElements': affected_elements,
            'totalBreakpoints': total_breakpoints,
            'affectedBreakpoints': affected_breakpoints,
            'overflowIssues': consolidated['testsSummary']['overflow']['issueCount'],
            'touchTargetIssues': consolidated['testsSummary']['touchTargets']['issueCount'],
            'fontScalingIssues': consolidated['testsSummary']['fontScaling']['issueCount'],
            'fixedPositionIssues': consolidated['testsSummary']['fixedPosition']['issueCount'],
            'contentStackingIssues': consolidated['testsSummary']['contentStacking']['issueCount']
        }
        
        # Print summary for debugging
        print(f"Consolidated summary: {consolidated['summary']}")
        
        # Add section information to results if page is provided
        if page and hasattr(page, '_accessibility_context'):
            try:
                # Make sure test_data has a 'results' key with expected structure
                if 'results' not in test_data:
                    test_data['results'] = {
                        'violations': [],
                        'summary': {}
                    }
                
                test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
                
                # Print violations with section information for debugging
                if 'violations' in test_data['results']:
                    print_violations_with_sections(test_data['results']['violations'])
                elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
                    print_violations_with_sections(test_data['results']['details']['violations'])
            except Exception as e:
                print(f"Error adding section information: {str(e)}")
                # Don't let this error prevent returning the consolidated results
        
        return consolidated
        
    except Exception as e:
        print(f"Error consolidating responsive results: {str(e)}")
        import traceback
        traceback.print_exc()

        # Create a minimal valid result structure
        result = {
            'summary': {
                'totalIssues': 0,
                'affectedElements': 0,
                'totalBreakpoints': 0,
                'affectedBreakpoints': 0
            },
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
        # Try to add section information if possible
        if page and hasattr(page, '_accessibility_context'):
            try:
                # Initialize test data structure for section-aware reporting
                test_data = {
                    'results': {
                        'violations': [],
                        'summary': {}
                    }
                }
                
                test_data['results'] = add_section_info_to_test_results(page, test_data['results'])
                
                # Print violations with section information for debugging
                if 'violations' in test_data['results']:
                    print_violations_with_sections(test_data['results']['violations'])
                elif 'details' in test_data['results'] and 'violations' in test_data['results']['details']:
                    print_violations_with_sections(test_data['results']['details']['violations'])
            except Exception as section_error:
                print(f"Error adding section information: {str(section_error)}")
                # Don't let this error prevent returning a result
        
        return result