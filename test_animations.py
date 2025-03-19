from datetime import datetime

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
                'timestamp': datetime.now().isoformat()
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