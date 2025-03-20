import asyncio
from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "JavaScript Timer Control Analysis",
    "description": "Evaluates JavaScript timers (setTimeout and setInterval) for proper user control mechanisms. This test identifies automatically starting timers and content that changes without user initiation, which may cause issues for users with cognitive disabilities.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.timers": "List of all JavaScript timers with their properties",
        "details.controls": "List of interactive elements that control timers",
        "details.violations": "List of timer-related accessibility violations",
        "details.summary": "Aggregated statistics about timer usage"
    },
    "tests": [
        {
            "id": "auto-start-timers",
            "name": "Auto-Starting Timers",
            "description": "Identifies timers that start automatically on page load without user interaction.",
            "impact": "high",
            "wcagCriteria": ["2.2.1", "2.2.2"],
            "howToFix": "Add user controls for starting any timed content or animations. Auto-starting timers should be avoided unless they are essential for the functionality of the page.",
            "resultsFields": {
                "pageFlags.hasAutoStartTimers": "Indicates if any timers start automatically",
                "pageFlags.details.autoStartTimers": "Count of auto-starting timers",
                "details.violations": "List of violations including auto-start timer issues"
            }
        },
        {
            "id": "timer-controls",
            "name": "Timer Control Mechanisms",
            "description": "Checks if timers have associated user interface controls (play, pause, stop).",
            "impact": "high",
            "wcagCriteria": ["2.2.1", "2.2.2"],
            "howToFix": "Provide visible, accessible controls that allow users to pause, stop, or hide any content that automatically moves, blinks, scrolls, or auto-updates.",
            "resultsFields": {
                "pageFlags.hasTimersWithoutControls": "Indicates if any timers lack user controls",
                "pageFlags.details.timersWithoutControls": "Count of timers without user controls",
                "details.controls": "List of timer control elements found on the page",
                "details.violations": "List of violations including missing timer controls"
            }
        },
        {
            "id": "timer-detection",
            "name": "JavaScript Timer Detection",
            "description": "Identifies JavaScript timers used on the page for informational purposes.",
            "impact": "informational",
            "wcagCriteria": [],
            "howToFix": "This test is informational and identifies all timers (setTimeout and setInterval) used on the page.",
            "resultsFields": {
                "pageFlags.hasTimers": "Indicates if any JavaScript timers are present",
                "pageFlags.details.totalTimers": "Count of timers found on the page",
                "details.timers": "List of all timers with their properties"
            }
        }
    ]
}

async def test_timers(page):
    """
    Test for presence and control of timers in JavaScript
    """
    try:
        # First inject the timer tracking code and immediately execute tracking setup
        await page.evaluate('''
            () => {
                // Create global tracking object
                window._timerTracking = {
                    timers: new Map(),
                    intervals: new Map(),
                    autoStartTimers: new Set()
                };

                // Track setTimeout calls
                const originalSetTimeout = window.setTimeout;
                window.setTimeout = function (callback, delay, ...args) {
                    const stack = new Error().stack;
                    const timerId = originalSetTimeout.call(this, callback, delay, ...args);
                    window._timerTracking.timers.set(timerId, {
                        type: 'timeout',
                        delay: delay,
                        stack: stack,
                        startTime: Date.now(),
                        autoStart: true
                    });
                    return timerId;
                };

                // Track setInterval calls
                const originalSetInterval = window.setInterval;
                window.setInterval = function (callback, delay, ...args) {
                    const stack = new Error().stack;
                    const timerId = originalSetInterval.call(this, callback, delay, ...args);
                    window._timerTracking.intervals.set(timerId, {
                        type: 'interval',
                        delay: delay,
                        stack: stack,
                        startTime: Date.now(),
                        autoStart: true
                    });
                    return timerId;
                };

                // Track clearTimeout calls
                const originalClearTimeout = window.clearTimeout;
                window.clearTimeout = function (timerId) {
                    window._timerTracking.timers.delete(timerId);
                    return originalClearTimeout.call(this, timerId);
                };

                // Track clearInterval calls
                const originalClearInterval = window.clearInterval;
                window.clearInterval = function (timerId) {
                    window._timerTracking.intervals.delete(timerId);
                    return originalClearInterval.call(this, timerId);
                };
            }
        ''')

        # Wait for any initial timers to be set
        await asyncio.sleep(1)

        # Now analyze the timers and their controls
        timer_data = await page.evaluate('''
            () => {
                // Verify tracking object exists
                if (!window._timerTracking) {
                    return {
                        pageFlags: {
                            hasTimers: false,
                            hasAutoStartTimers: false,
                            hasTimersWithoutControls: false,
                            details: {
                                totalTimers: 0,
                                autoStartTimers: 0,
                                timersWithoutControls: 0
                            }
                        },
                        results: {
                            timers: [],
                            controls: [],
                            violations: [],
                            summary: {
                                totalTimers: 0,
                                autoStartTimers: 0,
                                timersWithoutControls: 0
                            }
                        }
                    };
                }

                function findTimerControls() {
                    const controls = [];
                    const interactiveElements = document.querySelectorAll(
                        'button, input[type="button"], input[type="submit"], [role="button"], ' +
                        'a[href], [onclick], [onkeydown], [onkeyup], [onmousedown], [onmouseup]'
                    );

                    interactiveElements.forEach(element => {
                        const inlineHandlers = [
                            element.getAttribute('onclick'),
                            element.getAttribute('onkeydown'),
                            element.getAttribute('onkeyup'),
                            element.getAttribute('onmousedown'),
                            element.getAttribute('onmouseup')
                        ].filter(Boolean);

                        const hasTimerControl = inlineHandlers.some(handler => 
                            handler.includes('setTimeout') || 
                            handler.includes('setInterval') ||
                            handler.includes('clearTimeout') ||
                            handler.includes('clearInterval')
                        );

                        if (hasTimerControl) {
                            controls.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                text: element.textContent.trim(),
                                type: 'timer-control'
                            });
                        }
                    });

                    return controls;
                }

                const results = {
                    timers: [],
                    controls: [],
                    violations: [],
                    summary: {
                        totalTimers: 0,
                        autoStartTimers: 0,
                        timersWithoutControls: 0
                    }
                };

                // Process timeouts
                window._timerTracking.timers.forEach((timer, id) => {
                    results.timers.push({
                        id: id,
                        type: 'timeout',
                        delay: timer.delay,
                        autoStart: timer.autoStart,
                        startTime: timer.startTime,
                        stack: timer.stack
                    });
                });

                // Process intervals
                window._timerTracking.intervals.forEach((interval, id) => {
                    results.timers.push({
                        id: id,
                        type: 'interval',
                        delay: interval.delay,
                        autoStart: interval.autoStart,
                        startTime: interval.startTime,
                        stack: interval.stack
                    });
                });

                // Find timer controls
                results.controls = findTimerControls();

                // Update summary and check for violations
                results.summary.totalTimers = results.timers.length;
                results.summary.autoStartTimers = results.timers
                    .filter(t => t.autoStart).length;

                // Check for timers without controls
                if (results.timers.length > results.controls.length) {
                    results.summary.timersWithoutControls = 
                        results.timers.length - results.controls.length;
                    
                    results.violations.push({
                        type: 'timers-without-controls',
                        count: results.summary.timersWithoutControls,
                        details: 'Some timers lack interactive controls'
                    });
                }

                // Add violation for auto-start timers
                if (results.summary.autoStartTimers > 0) {
                    results.violations.push({
                        type: 'auto-start-timers',
                        count: results.summary.autoStartTimers,
                        details: 'Timers start automatically on page load'
                    });
                }

                return {
                    pageFlags: {
                        hasTimers: results.summary.totalTimers > 0,
                        hasAutoStartTimers: results.summary.autoStartTimers > 0,
                        hasTimersWithoutControls: results.summary.timersWithoutControls > 0,
                        details: {
                            totalTimers: results.summary.totalTimers,
                            autoStartTimers: results.summary.autoStartTimers,
                            timersWithoutControls: results.summary.timersWithoutControls
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'timers': {
                'pageFlags': timer_data['pageFlags'],
                'details': timer_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'timers': {
                'pageFlags': {
                    'hasTimers': False,
                    'hasAutoStartTimers': False,
                    'hasTimersWithoutControls': False,
                    'details': {
                        'totalTimers': 0,
                        'autoStartTimers': 0,
                        'timersWithoutControls': 0
                    }
                },
                'details': {
                    'timers': [],
                    'controls': [],
                    'violations': [{
                        'issue': 'Error evaluating timers',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalTimers': 0,
                        'autoStartTimers': 0,
                        'timersWithoutControls': 0
                    }
                }
            }
        }