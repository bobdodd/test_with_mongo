from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "CSS Animations Analysis",
    "description": "Evaluates CSS animations on the page for accessibility considerations, focusing on prefers-reduced-motion media query support, infinite animations, and animation duration. This test helps ensure content is accessible to users who may experience motion sickness, vestibular disorders, or other conditions affected by movement on screen.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "pageFlags": "Boolean flags indicating key animation issues",
        "details": "Full animation data including keyframes, animated elements, and media queries",
        "timestamp": "ISO timestamp when the test was run"
    },
    "tests": [
        {
            "id": "animations-reduced-motion",
            "name": "Reduced Motion Support",
            "description": "Checks if the page provides prefers-reduced-motion media query support for users who have indicated they prefer reduced motion in their system settings.",
            "impact": "high",
            "wcagCriteria": ["2.3.3"],
            "howToFix": "Add a prefers-reduced-motion media query in your CSS to disable or reduce animations for users who prefer reduced motion:\n@media (prefers-reduced-motion: reduce) {\n  * {\n    animation-duration: 0.001ms !important;\n    animation-iteration-count: 1 !important;\n    transition-duration: 0.001ms !important;\n  }\n}",
            "resultsFields": {
                "pageFlags.lacksReducedMotionSupport": "Indicates if animations are present without prefers-reduced-motion support",
                "pageFlags.details.hasReducedMotionSupport": "Indicates if prefers-reduced-motion media query is present",
                "details.mediaQueries": "List of media queries related to reduced motion"
            }
        },
        {
            "id": "animations-infinite",
            "name": "Infinite Animations",
            "description": "Identifies animations set to run indefinitely (animation-iteration-count: infinite). These can cause significant accessibility issues for users with vestibular disorders or attention-related disabilities.",
            "impact": "high",
            "wcagCriteria": ["2.2.2", "2.3.3"],
            "howToFix": "Modify infinite animations to either:\n1. Have a defined, short duration (less than 5 seconds)\n2. Only play once (animation-iteration-count: 1)\n3. Add controls to pause animation\n4. Respect prefers-reduced-motion media query",
            "resultsFields": {
                "pageFlags.hasInfiniteAnimations": "Indicates if page contains infinite animations",
                "pageFlags.details.infiniteAnimations": "Count of infinite animations on the page",
                "details.violations": "List of elements with infinite animations"
            }
        },
        {
            "id": "animations-duration",
            "name": "Long Duration Animations",
            "description": "Identifies animations that run for an extended period (over 5 seconds), which can be distracting or disorienting for some users.",
            "impact": "medium",
            "wcagCriteria": ["2.2.2"],
            "howToFix": "Reduce the duration of animations to be under 5 seconds or provide a mechanism to pause, stop, or hide the animation.",
            "resultsFields": {
                "pageFlags.hasLongAnimations": "Indicates if page contains long-running animations",
                "pageFlags.details.longDurationAnimations": "Count of animations exceeding 5 seconds",
                "details.animatedElements": "List of animated elements with their durations"
            }
        }
    ]
}

async def test_animations(page):
    """
    Test CSS animations for accessibility requirements
    """
    try:
        animation_data = await page.evaluate('''
            () => {
                function getAnimationDetails(styleSheet) {
                    const animations = [];
                    try {
                        if (!styleSheet.cssRules) {
                            return [{
                                type: 'inaccessible',
                                source: styleSheet.href || 'inline',
                                reason: 'CORS or security restriction'
                            }];
                        }
                        
                        Array.from(styleSheet.cssRules).forEach(rule => {
                            if (rule instanceof CSSKeyframesRule) {
                                animations.push({
                                    type: 'keyframes',
                                    name: rule.name,
                                    rules: Array.from(rule.cssRules).length,
                                    source: styleSheet.href || 'inline'
                                });
                            }
                            else if (rule instanceof CSSStyleRule) {
                                const style = rule.style;
                                const hasAnimation = style.animation || 
                                                  style.animationName ||
                                                  style.animationDuration;
                                
                                if (hasAnimation) {
                                    animations.push({
                                        type: 'style',
                                        selector: rule.selectorText,
                                        source: styleSheet.href || 'inline',
                                        properties: {
                                            animation: style.animation,
                                            animationName: style.animationName,
                                            animationDuration: style.animationDuration,
                                            animationIterationCount: style.animationIterationCount,
                                            animationPlayState: style.animationPlayState
                                        }
                                    });
                                }
                            }
                            else if (rule instanceof CSSMediaRule) {
                                const isReducedMotion = rule.conditionText.includes('prefers-reduced-motion');
                                if (isReducedMotion) {
                                    animations.push({
                                        type: 'media-query',
                                        condition: rule.conditionText,
                                        source: styleSheet.href || 'inline',
                                        rules: Array.from(rule.cssRules).map(r => ({
                                            selector: r.selectorText,
                                            properties: r.style ? {
                                                animation: r.style.animation,
                                                animationName: r.style.animationName,
                                                animationDuration: r.style.animationDuration,
                                                animationPlayState: r.style.animationPlayState
                                            } : null
                                        }))
                                    });
                                }
                            }
                        });
                    } catch (e) {
                        animations.push({
                            type: 'error',
                            source: styleSheet.href || 'inline',
                            error: e.message
                        });
                    }
                    return animations;
                }

                function findAnimatedElements() {
                    const elements = [];
                    // Only look for elements within the body
                    const all = document.body.querySelectorAll('*');
                    
                    all.forEach(element => {
                        const style = window.getComputedStyle(element);
                        if (style.animation || style.animationName !== 'none') {
                            elements.push({
                                tag: element.tagName.toLowerCase(),
                                id: element.id || null,
                                class: element.className || null,
                                animation: {
                                    name: style.animationName,
                                    duration: style.animationDuration,
                                    iterationCount: style.animationIterationCount,
                                    playState: style.animationPlayState
                                }
                            });
                        }
                    });
                    
                    return elements;
                }
                                             
                const results = {
                    styleSheets: Array.from(document.styleSheets).map(sheet => sheet.href || 'inline'),
                    animations: [],
                    animatedElements: [],
                    mediaQueries: [],
                    violations: [],
                    summary: {
                        totalAnimations: 0,
                        hasReducedMotionSupport: false,
                        infiniteAnimations: 0,
                        longDurationAnimations: 0
                    }
                };

                // Process all stylesheets
                Array.from(document.styleSheets).forEach(styleSheet => {
                    const animations = getAnimationDetails(styleSheet);
                    results.animations.push(...animations.filter(a => 
                        a.type !== 'media-query' && a.type !== 'error'));
                    results.mediaQueries.push(...animations.filter(a => 
                        a.type === 'media-query'));
                });

                // Find elements with computed animations
                results.animatedElements = findAnimatedElements();

                // Check for reduced motion support
                results.summary.hasReducedMotionSupport = results.mediaQueries.some(
                    mq => mq.condition.includes('prefers-reduced-motion')
                );

                // Update summary and check for violations
                results.summary.totalAnimations = results.animations.filter(
                    a => a.type === 'keyframes' || a.type === 'style'
                ).length;

                if (results.summary.totalAnimations > 0 && !results.summary.hasReducedMotionSupport) {
                    results.violations.push({
                        type: 'no-reduced-motion-support',
                        details: 'Animations present without prefers-reduced-motion media query'
                    });
                }

                results.animatedElements.forEach(element => {
                    const iterationCount = element.animation.iterationCount;
                    if (iterationCount === 'infinite') {
                        results.summary.infiniteAnimations++;
                        results.violations.push({
                            type: 'infinite-animation',
                            element: element.tag,
                            id: element.id,
                            class: element.class
                        });
                    }

                    const duration = parseFloat(element.animation.duration) * 
                        (element.animation.duration.includes('ms') ? 1 : 1000);
                    if (duration > 5000) {
                        results.summary.longDurationAnimations++;
                        results.violations.push({
                            type: 'long-duration-animation',
                            element: element.tag,
                            id: element.id,
                            class: element.class,
                            duration: element.animation.duration
                        });
                    }
                });

                return {
                    pageFlags: {
                        hasAnimations: results.summary.totalAnimations > 0,
                        lacksReducedMotionSupport: results.summary.totalAnimations > 0 && 
                                                 !results.summary.hasReducedMotionSupport,
                        hasInfiniteAnimations: results.summary.infiniteAnimations > 0,
                        hasLongAnimations: results.summary.longDurationAnimations > 0,
                        details: {
                            totalAnimations: results.summary.totalAnimations,
                            infiniteAnimations: results.summary.infiniteAnimations,
                            longDurationAnimations: results.summary.longDurationAnimations,
                            hasReducedMotionSupport: results.summary.hasReducedMotionSupport
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'animations': {
                'pageFlags': animation_data['pageFlags'],
                'details': animation_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'animations': {
                'pageFlags': {
                    'hasAnimations': False,
                    'lacksReducedMotionSupport': False,
                    'hasInfiniteAnimations': False,
                    'hasLongAnimations': False,
                    'details': {
                        'totalAnimations': 0,
                        'infiniteAnimations': 0,
                        'longDurationAnimations': 0,
                        'hasReducedMotionSupport': False
                    }
                },
                'details': {
                    'animations': [],
                    'animatedElements': [],
                    'mediaQueries': [],
                    'violations': [{
                        'issue': 'Error evaluating animations',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalAnimations': 0,
                        'hasReducedMotionSupport': False,
                        'infiniteAnimations': 0,
                        'longDurationAnimations': 0
                    }
                }
            }
        }