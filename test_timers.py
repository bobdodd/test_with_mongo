import asyncio
from datetime import datetime

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
                'timestamp': datetime.now().isoformat()
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