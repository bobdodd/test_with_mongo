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
    "testName": "Media Queries Analysis",
    "description": "Analyzes CSS styles loaded on the page for media queries, with a focus on responsive design breakpoints. This test helps identify how the site adapts to different screen sizes and device capabilities, which is essential for ensuring accessibility across various devices.",
    "version": "1.0.0",
    "date": "2025-03-21",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating key characteristics of media query usage",
        "details": "Detailed information about media queries found on the page",
        "details.breakpoints": "List of breakpoints (width values) found in media queries",
        "details.mediaQueries": "List of all media queries with their properties",
        "details.summary": "Summary statistics about media query usage"
    },
    "tests": [
        {
            "id": "responsive-breakpoints",
            "name": "Responsive Breakpoints",
            "description": "Identifies width-based breakpoints in media queries that control responsive layout changes. These breakpoints determine how content adapts to different screen sizes.",
            "impact": "medium",
            "wcagCriteria": ["1.4.4", "1.4.10"],
            "howToFix": "Ensure breakpoints are used consistently and create layouts that adapt well to different screen sizes without loss of information or functionality. Consider using standard breakpoints (e.g., 320px, 768px, 1024px) for common device sizes.",
            "resultsFields": {
                "details.breakpoints": "Width-based breakpoints extracted from media queries",
                "pageFlags.hasResponsiveBreakpoints": "Indicates if responsive breakpoints are used on the page"
            }
        },
        {
            "id": "print-stylesheets",
            "name": "Print Stylesheets",
            "description": "Checks for print-specific styles that optimize content for printing. Print stylesheets are important for making content accessible in printed form.",
            "impact": "medium",
            "wcagCriteria": ["1.4.8"],
            "howToFix": "Add print-specific media queries (e.g., @media print) to optimize content for printing. Consider removing unnecessary elements, adjusting colors for better contrast on paper, and ensuring all important content is visible in the print version.",
            "resultsFields": {
                "details.mediaQueries": "List of media queries, including print-specific ones",
                "pageFlags.hasPrintStyles": "Indicates if print-specific styles are defined"
            }
        },
        {
            "id": "prefers-reduced-motion",
            "name": "Reduced Motion Support",
            "description": "Checks for media queries that respect user preferences for reduced motion. This is important for users who experience motion sickness or vestibular disorders.",
            "impact": "high",
            "wcagCriteria": ["2.3.3"],
            "howToFix": "Add @media (prefers-reduced-motion: reduce) queries to provide alternative styles that minimize or eliminate animations and transitions for users who have indicated a preference for reduced motion in their system settings.",
            "resultsFields": {
                "details.mediaQueries": "List of media queries, including those for reduced motion",
                "pageFlags.hasReducedMotionSupport": "Indicates if reduced motion preferences are supported"
            }
        },
        {
            "id": "dark-mode-support",
            "name": "Dark Mode Support",
            "description": "Checks for media queries that provide dark mode alternatives. Dark mode can improve accessibility for users with light sensitivity or those using devices in low-light environments.",
            "impact": "medium",
            "wcagCriteria": ["1.4.8"],
            "howToFix": "Add @media (prefers-color-scheme: dark) queries to provide appropriate color schemes for users who prefer dark mode interfaces in their system settings.",
            "resultsFields": {
                "details.mediaQueries": "List of media queries, including those for color scheme preferences",
                "pageFlags.hasDarkModeSupport": "Indicates if dark mode is supported"
            }
        },
        {
            "id": "orientation-specific-styles",
            "name": "Orientation-Specific Styles",
            "description": "Checks for media queries that adapt layouts based on device orientation (portrait vs. landscape). This ensures content is accessible regardless of how a device is held.",
            "impact": "medium",
            "wcagCriteria": ["1.3.4"],
            "howToFix": "Use @media (orientation: portrait) and @media (orientation: landscape) queries to optimize layouts for different device orientations, ensuring all content and functionality remains accessible.",
            "resultsFields": {
                "details.mediaQueries": "List of media queries, including orientation-specific ones",
                "pageFlags.hasOrientationStyles": "Indicates if orientation-specific styles are defined"
            }
        }
    ]
}

async def test_media_queries(page):
    """
    Test for media queries in CSS including responsive breakpoints, print styles,
    and accessibility-related media features like prefers-reduced-motion.
    """
    try:
        media_queries_data = await page.evaluate('''
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
        
        function extractMediaQueries() {
                    const mediaQueries = [];
                    const breakpoints = new Set();
                    
                    // Process all stylesheets
                    for (const stylesheet of document.styleSheets) {
                        try {
                            // Skip external stylesheets from different origins (CORS restriction)
                            if (stylesheet.href && 
                                new URL(stylesheet.href).origin !== window.location.origin) {
                                continue;
                            }
                            
                            // Process rules in each stylesheet
                            const rules = stylesheet.cssRules || [];
                            for (let i = 0; i < rules.length; i++) {
                                const rule = rules[i];
                                
                                // Handle @media rules
                                if (rule.type === CSSRule.MEDIA_RULE) {
                                    const mediaText = rule.media.mediaText;
                                    
                                    // Create a media query object
                                    const mediaQuery = {
                                        text: mediaText,
                                        cssText: rule.cssText,
                                        features: {},
                                        source: stylesheet.href || 'inline',
                                        ruleCount: rule.cssRules.length
                                    };
                                    
                                    // Track specific features
                                    mediaQuery.features.isWidthBased = /width/.test(mediaText);
                                    mediaQuery.features.isPrint = /print/.test(mediaText);
                                    mediaQuery.features.isReducedMotion = /prefers-reduced-motion/.test(mediaText);
                                    mediaQuery.features.isDarkMode = /prefers-color-scheme/.test(mediaText);
                                    mediaQuery.features.isOrientation = /orientation/.test(mediaText);
                                    
                                    // Extract width values for breakpoints
                                    if (mediaQuery.features.isWidthBased) {
                                        const widthMatches = mediaText.match(/(min-width|max-width)\\s*:\\s*(\\d+)(px|em|rem)/g);
                                        if (widthMatches) {
                                            mediaQuery.widthValues = widthMatches.map(match => {
                                                const [type, value, unit] = match.match(/(min-width|max-width)\\s*:\\s*(\\d+)(px|em|rem)/).slice(1);
                                                
                                                // Convert em/rem to px for standardization
                                                let pxValue = parseInt(value);
                                                if (unit === 'em' || unit === 'rem') {
                                                    // Assume 1em/rem = 16px for calculation purposes
                                                    pxValue = pxValue * 16;
                                                }
                                                
                                                // Add to breakpoints set
                                                breakpoints.add(pxValue);
                                                
                                                return {
                                                    type: type,
                                                    value: parseInt(value),
                                                    unit: unit,
                                                    pxValue: pxValue
                                                 };
                                            });
                                        }
                                    }
                                    
                                    mediaQueries.push(mediaQuery);
                                }
                                
                                // Handle @import rules with media queries
                                if (rule.type === CSSRule.IMPORT_RULE && rule.media && rule.media.mediaText) {
                                    mediaQueries.push({
                                        text: rule.media.mediaText,
                                        cssText: rule.cssText,
                                        source: rule.href,
                                        isImport: true,
                                        features: {
                                            isWidthBased: /width/.test(rule.media.mediaText),
                                            isPrint: /print/.test(rule.media.mediaText),
                                            isReducedMotion: /prefers-reduced-motion/.test(rule.media.mediaText),
                                            isDarkMode: /prefers-color-scheme/.test(rule.media.mediaText),
                                            isOrientation: /orientation/.test(rule.media.mediaText)
                                        }
                                    });
                                }
                            }
                        } catch (e) {
                            // Skip stylesheet if access is restricted by CORS
                            console.warn('Could not access stylesheet:', e.message);
                        }
                    }
                    
                    // Extract and sort breakpoints
                    const sortedBreakpoints = Array.from(breakpoints).sort((a, b) => a - b);
                    
                    // Group breakpoints for easier analysis
                    const breakpointGroups = {
                        mobile: sortedBreakpoints.filter(bp => bp <= 480),
                        tablet: sortedBreakpoints.filter(bp => bp > 480 && bp <= 768),
                        desktop: sortedBreakpoints.filter(bp => bp > 768 && bp <= 1200),
                        largeScreen: sortedBreakpoints.filter(bp => bp > 1200)
                    };
                    
                    // Create breakpoint objects with types
                    const breakpointObjects = sortedBreakpoints.map(bp => {
                        let type = 'unknown';
                        if (bp <= 480) type = 'mobile';
                        else if (bp <= 768) type = 'tablet';
                        else if (bp <= 1200) type = 'desktop';
                        else type = 'largeScreen';
                        
                        return {
                            breakpoint: bp,
                            type: type,
                            unit: 'px'
                         };
                    });
                    
                    return {
                        mediaQueries: mediaQueries,
                        breakpoints: sortedBreakpoints,
                        breakpointObjects: breakpointObjects,
                        breakpointGroups: breakpointGroups,
                        summary: {
                            totalMediaQueries: mediaQueries.length,
                            widthBasedQueries: mediaQueries.filter(mq => mq.features.isWidthBased).length,
                            printQueries: mediaQueries.filter(mq => mq.features.isPrint).length,
                            reducedMotionQueries: mediaQueries.filter(mq => mq.features.isReducedMotion).length,
                            darkModeQueries: mediaQueries.filter(mq => mq.features.isDarkMode).length,
                            orientationQueries: mediaQueries.filter(mq => mq.features.isOrientation).length
                         }
                    };
                }
                
                return extractMediaQueries();
        }
        ''')
        
        # Print a summary of the media queries found
        print("\nMedia Queries Analysis Summary:")
        print(f"Total Media Queries: {media_queries_data['summary']['totalMediaQueries']}")
        
        breakpoints = media_queries_data.get('breakpoints', [])
        if breakpoints and len(breakpoints) > 0:
            print("\nResponsive Breakpoints Found:")
            for breakpoint in breakpoints:
                print(f"  - {breakpoint}px")
            
            # Print breakpoints by group
            breakpoint_groups = media_queries_data.get('breakpointGroups', {})
            if breakpoint_groups:
                print("\nBreakpoints by Device Category:")
                mobile_breakpoints = breakpoint_groups.get('mobile', [])
                if mobile_breakpoints and len(mobile_breakpoints) > 0:
                    print("  Mobile:", ', '.join([f"{bp}px" for bp in mobile_breakpoints]))
                
                tablet_breakpoints = breakpoint_groups.get('tablet', [])
                if tablet_breakpoints and len(tablet_breakpoints) > 0:
                    print("  Tablet:", ', '.join([f"{bp}px" for bp in tablet_breakpoints]))
                
                desktop_breakpoints = breakpoint_groups.get('desktop', [])
                if desktop_breakpoints and len(desktop_breakpoints) > 0:
                    print("  Desktop:", ', '.join([f"{bp}px" for bp in desktop_breakpoints]))
                
                large_screen_breakpoints = breakpoint_groups.get('largeScreen', [])
                if large_screen_breakpoints and len(large_screen_breakpoints) > 0:
                    print("  Large Screen:", ', '.join([f"{bp}px" for bp in large_screen_breakpoints]))
                
        print("\nFeatures Detected:")
        print(f"  - Width-based Media Queries: {media_queries_data['summary']['widthBasedQueries']}")
        print(f"  - Print Stylesheets: {media_queries_data['summary']['printQueries']}")
        print(f"  - Reduced Motion Support: {media_queries_data['summary']['reducedMotionQueries']}")
        print(f"  - Dark Mode Support: {media_queries_data['summary']['darkModeQueries']}")
        print(f"  - Orientation-specific Styles: {media_queries_data['summary']['orientationQueries']}")
        
        # Set flags based on findings
        page_flags = {
            'hasResponsiveBreakpoints': len(media_queries_data['breakpoints']) > 0,
            'hasPrintStyles': media_queries_data['summary']['printQueries'] > 0,
            'hasReducedMotionSupport': media_queries_data['summary']['reducedMotionQueries'] > 0,
            'hasDarkModeSupport': media_queries_data['summary']['darkModeQueries'] > 0,
            'hasOrientationStyles': media_queries_data['summary']['orientationQueries'] > 0
        }
        
        # Construct recommendations based on findings
        recommendations = []
        
        if not page_flags['hasResponsiveBreakpoints']:
            recommendations.append({
                'issue': 'No responsive breakpoints detected',
                'impact': 'medium',
                'wcag': '1.4.10',
                'recommendation': 'Implement responsive design with appropriate media queries for different screen sizes.'
            })
            
        if not page_flags['hasPrintStyles']:
            recommendations.append({
                'issue': 'No print styles detected',
                'impact': 'medium',
                'wcag': '1.4.8',
                'recommendation': 'Add @media print styles to optimize content for printing.'
            })
            
        if not page_flags['hasReducedMotionSupport']:
            recommendations.append({
                'issue': 'No support for reduced motion preferences',
                'impact': 'high',
                'wcag': '2.3.3',
                'recommendation': 'Add @media (prefers-reduced-motion: reduce) queries to provide alternatives for users who prefer reduced motion.'
            })
        
        # Create a separate object for responsive breakpoints that can be easily queried
        responsive_breakpoints = {
            'allBreakpoints': media_queries_data.get('breakpoints', []),
            'byCategory': media_queries_data.get('breakpointGroups', {
                'mobile': [],
                'tablet': [],
                'desktop': [],
                'largeScreen': []
            }),
            'breakpointObjects': media_queries_data.get('breakpointObjects', [])
        }
        
        # Add media_queries_data to a variable called 'data' so the section reporting template can use it
        data = {
            'results': {
                'mediaQueries': media_queries_data['mediaQueries'],
                'violations': recommendations,  # Treat recommendations as violations for section reporting
                'summary': media_queries_data['summary']
            }
        }
        
        # Add section information to results
        data['results'] = add_section_info_to_test_results(page, data['results'])
        
        # Print violations with section information for debugging
        print_violations_with_sections(data['results']['violations'])
        
        return {
            'media_queries': {
                'pageFlags': page_flags,
                'details': {
                    'mediaQueries': media_queries_data['mediaQueries'],
                    'breakpoints': media_queries_data['breakpoints'],
                    'breakpointGroups': media_queries_data['breakpointGroups'],
                    'summary': media_queries_data['summary'],
                    'recommendations': recommendations,
                    'section_statistics': data['results'].get('section_statistics', {})
                },
                'responsiveBreakpoints': responsive_breakpoints,  # Dedicated field for easy database queries
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }
    except Exception as e:
        print(f"Error analyzing media queries: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'media_queries': {
                'pageFlags': {
                    'hasResponsiveBreakpoints': False,
                    'hasPrintStyles': False,
                    'hasReducedMotionSupport': False,
                    'hasDarkModeSupport': False,
                    'hasOrientationStyles': False
                 },
                'details': {
                    'mediaQueries': [],
                    'breakpoints': [],
                    'breakpointGroups': {
                        'mobile': [],
                        'tablet': [],
                        'desktop': [],
                        'largeScreen': []
                    },
                    'summary': {
                        'totalMediaQueries': 0,
                        'widthBasedQueries': 0,
                        'printQueries': 0,
                        'reducedMotionQueries': 0,
                        'darkModeQueries': 0,
                        'orientationQueries': 0
                    },
                    'recommendations': [{
                        'issue': 'Error analyzing media queries',
                        'details': str(e)
                    }]
                },
                'responsiveBreakpoints': {
                    'allBreakpoints': [],
                    'byCategory': {
                        'mobile': [],
                        'tablet': [],
                        'desktop': [],
                        'largeScreen': []
                    },
                    'breakpointObjects': []
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }