from datetime import datetime


# Test documentation with information about the event handler tests
TEST_DOCUMENTATION = {
    "testName": "Event Handler Accessibility Tests",
    "description": "Analyzes page for event handling accessibility issues and keyboard navigation patterns. Checks for proper implementation of keyboard access for interactive elements, correct tab order, and escape key functionality for modal dialogs.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "pageFlags": "Top-level flags indicating presence of various issues",
        "details": "Detailed information about event handlers and tab order",
        "events.handlers": "All event handlers categorized by type (mouse, keyboard, etc.)",
        "events.violations": "Elements with accessibility violations in their event handling",
        "tabOrder.tabOrder": "All focusable elements in their tab sequence",
        "tabOrder.violations": "Tab order sequence violations",
        "violationCounts": "Summary counts of each type of violation",
        "violationFlags": "Boolean flags for each violation category"
    },
    "tests": [
        {
            "id": "missing-tabindex",
            "name": "Non-interactive Elements with Event Handlers Missing Tabindex",
            "description": "Tests for non-interactive elements (div, span, etc.) that have event handlers but no tabindex attribute. These elements must have tabindex to be keyboard accessible.",
            "impact": "critical",
            "wcagCriteria": ["2.1.1", "2.1.3"],
            "howToFix": "Add tabindex='0' to any non-interactive element that has event handlers",
            "resultsFields": {
                "pageFlags.hasMissingTabindex": "Boolean flag indicating if issue was found",
                "details.violationCounts.missing-tabindex": "Number of elements with this issue",
                "details.events.violations": "Array of specific elements with this violation"
            }
        },
        {
            "id": "mouse-only",
            "name": "Elements with Mouse Events but no Keyboard Events",
            "description": "Identifies elements that respond to mouse events (click, hover) but have no keyboard event handlers, making them inaccessible to keyboard users",
            "impact": "high",
            "wcagCriteria": ["2.1.1", "2.1.3"],
            "howToFix": "Add keyboard event handlers (keydown, keypress) to elements that have mouse handlers",
            "resultsFields": {
                "pageFlags.hasMouseOnlyHandlers": "Boolean flag indicating if issue was found",
                "details.violationCounts.mouse-only": "Number of elements with this issue",
                "details.events.summary.mouseOnlyElements": "Information about mouse-only interactive elements"
            }
        },
        {
            "id": "modal-without-escape",
            "name": "Modal Dialogs without Keyboard Escape",
            "description": "Checks if modal dialogs provide keyboard escape functionality (ESC key)",
            "impact": "high",
            "wcagCriteria": ["2.1.2"],
            "howToFix": "Add a keydown event handler to modal dialogs that closes them on Escape key",
            "resultsFields": {
                "pageFlags.hasModalsWithoutEscape": "Boolean flag indicating if issue was found",
                "details.violationCounts.modal-without-escape": "Number of modals with this issue",
                "details.events.summary.modalEscapeSupport": "Information about modals and their escape key support"
            }
        },
        {
            "id": "visual-order",
            "name": "Tab Order Doesn't Follow Visual Layout",
            "description": "Checks if the tab order of interactive elements follows their visual arrangement",
            "impact": "medium", 
            "wcagCriteria": ["2.4.3"],
            "howToFix": "Rearrange DOM order or use tabindex to ensure tab order matches visual layout",
            "resultsFields": {
                "pageFlags.hasVisualOrderViolations": "Boolean flag indicating if issue was found",
                "details.violationCounts.visual-order": "Number of tab order violations",
                "details.tabOrder.violations": "Specific information about tab order violation pairs"
            }
        },
        {
            "id": "negative-tabindex",
            "name": "Elements with Negative Tabindex",
            "description": "Identifies elements using negative tabindex which removes them from the natural tab order but keeps them focusable programmatically",
            "impact": "medium",
            "wcagCriteria": ["2.4.3"],
            "howToFix": "Replace negative tabindex with tabindex='0' for elements that should be in the normal tab sequence",
            "resultsFields": {
                "pageFlags.hasNegativeTabindex": "Boolean flag indicating if issue was found",
                "details.violationCounts.negative-tabindex": "Number of elements using negative tabindex",
                "details.tabOrder.summary.elementsWithExplicitTabIndex": "Count of elements with explicit tabindex"
            }
        },
        {
            "id": "high-tabindex",
            "name": "Elements with Unusually High Tabindex",
            "description": "Identifies elements with tabindex values > 10, which is a poor practice that can create maintenance issues",
            "impact": "low",
            "wcagCriteria": ["2.4.3"],
            "howToFix": "Restructure DOM or use smaller sequential tabindex values (preferably 0)",
            "resultsFields": {
                "pageFlags.hasHighTabindex": "Boolean flag indicating if issue was found",
                "details.violationCounts.high-tabindex": "Number of elements with high tabindex values",
                "details.tabOrder.summary.elementsWithExplicitTabIndex": "Count of elements with explicit tabindex"
            }
        }
    ]
}


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
async def test_event_handlers(page):
    """
    Test event handlers and tab order accessibility requirements
    """
    try:
        # Inject a helper function that always generates full Chrome-style XPath
        await page.evaluate('''
            window.getFullXPath = function(element) {
                if (!element) return '';
                
                const path = [];
                while (element && element.nodeType === 1) {
                    let index = 0;
                    for (let sibling = element.previousSibling; sibling; sibling = sibling.previousSibling) {
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            index++;
                        }
                    }
                    
                    const tagName = element.tagName.toLowerCase();
                    const pathIndex = index ? `[${index + 1}]` : '';
                    path.unshift(tagName + pathIndex);
                    
                    element = element.parentNode;
                }
                
                return '/' + path.join('/');
            };
        ''')
        
        event_data = await page.evaluate('''
            () => {
                function categorizeEvent(eventName) {
                    if (['click', 'mousedown', 'mouseup', 'mouseover', 'mouseout', 'mousemove', 'dblclick'].includes(eventName)) {
                        return 'mouse'
                    }
                    if (['keydown', 'keyup', 'keypress'].includes(eventName)) {
                        return 'keyboard'
                    }
                    if (['setTimeout', 'setInterval'].includes(eventName)) {
                        return 'timer'
                    }
                    if (['focus', 'blur', 'focusin', 'focusout'].includes(eventName)) {
                        return 'focus'
                    }
                    if (['touchstart', 'touchend', 'touchmove'].includes(eventName)) {
                        return 'touch'
                    }
                    if (['load', 'unload', 'DOMContentLoaded'].includes(eventName)) {
                        return 'lifecycle'
                    }
                    return 'other'
                }

                function isIntrinsicInteractive(element) {
                    const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'details', 'summary']
                    const interactiveRoles = ['button', 'link', 'menuitem', 'tab', 'checkbox', 'radio', 'switch']
                    
                    return interactiveTags.includes(element.tagName.toLowerCase()) ||
                           (element.getAttribute('role') && 
                            interactiveRoles.includes(element.getAttribute('role')))
                }

                function analyzeTabOrder() {
                    const focusableElements = Array.from(document.querySelectorAll(`
                        a, button, input, select, textarea, [tabindex], 
                        [contentEditable=true], audio[controls], video[controls]
                    `)).filter(el => {
                        const style = window.getComputedStyle(el)
                        return style.display !== 'none' && style.visibility !== 'hidden'
                    })

                    const tabOrder = []
                    let previousRect = null
                    let currentRow = []
                    let rows = []
                    const violations = []

                    focusableElements.forEach((element, index) => {
                        const rect = element.getBoundingClientRect()
                        const tabindex = element.getAttribute('tabindex')
                        const isIntrinsicFocusable = !tabindex && 
                            ['a', 'button', 'input', 'select', 'textarea'].includes(
                                element.tagName.toLowerCase()
                            )

                        const elementInfo = {
                            element: element.tagName.toLowerCase(),
                            id: element.id || null,
                            text: element.textContent.trim(),
                            tabindex: tabindex,
                            isIntrinsicFocusable,
                            xpath: getFullXPath(element),
                            position: {
                                top: rect.top,
                                left: rect.left,
                                bottom: rect.bottom,
                                right: rect.right
                            }
                        }

                        if (previousRect && (rect.top - previousRect.bottom > 10)) {
                            rows.push(currentRow)
                            currentRow = []
                        }

                        currentRow.push(elementInfo)
                        tabOrder.push(elementInfo)
                        previousRect = rect

                        if (currentRow.length > 1) {
                            const previous = currentRow[currentRow.length - 2]
                            if (rect.left < previous.position.left) {
                                violations.push({
                                    type: 'visual-order',
                                    message: 'Tab order does not follow visual left-to-right order',
                                    elements: [previous, elementInfo]
                                })
                            }
                        }

                        if (rows.length > 0) {
                            const previousRow = rows[rows.length - 1]
                            previousRow.forEach(prevElement => {
                                if (rect.left < prevElement.position.left && 
                                    rect.top > prevElement.position.bottom) {
                                    violations.push({
                                        type: 'column-order',
                                        message: 'Tab order does not follow visual column order',
                                        elements: [prevElement, elementInfo]
                                    })
                                }
                            })
                        }
                    })

                    if (currentRow.length > 0) {
                        rows.push(currentRow)
                    }

                    // Count violations by type
                    const violationsByType = {};
                    violations.forEach(violation => {
                        violationsByType[violation.type] = (violationsByType[violation.type] || 0) + 1;
                    });

                    // Check for negative tabindex (used for removing from tab order but keeping focusable)
                    const negativeTabIndexElements = tabOrder.filter(item => 
                        item.tabindex !== null && parseInt(item.tabindex) < 0
                    );
                    
                    // Check for very high tabindex values (poor practice)
                    const highTabIndexElements = tabOrder.filter(item => 
                        item.tabindex !== null && parseInt(item.tabindex) > 10
                    );
                    
                    if (negativeTabIndexElements.length > 0) {
                        violations.push({
                            type: 'negative-tabindex',
                            message: 'Elements with negative tabindex are focusable but removed from keyboard tab order',
                            elements: negativeTabIndexElements
                        });
                        violationsByType['negative-tabindex'] = negativeTabIndexElements.length;
                    }
                    
                    if (highTabIndexElements.length > 0) {
                        violations.push({
                            type: 'high-tabindex',
                            message: 'Elements with unusually high tabindex values (>10) may cause navigation issues',
                            elements: highTabIndexElements
                        });
                        violationsByType['high-tabindex'] = highTabIndexElements.length;
                    }

                    return {
                        tabOrder,
                        rows,
                        violations,
                        summary: {
                            totalFocusableElements: tabOrder.length,
                            elementsWithExplicitTabIndex: tabOrder.filter(
                                el => el.tabindex !== null
                            ).length,
                            visualOrderViolations: violations.length,
                            violationsByType: violationsByType,
                            hasNegativeTabindex: negativeTabIndexElements.length > 0,
                            hasHighTabindex: highTabIndexElements.length > 0,
                            hasVisualOrderViolations: violationsByType['visual-order'] > 0,
                            hasColumnOrderViolations: violationsByType['column-order'] > 0
                         }
                    }
                }

                function findEventHandlers() {
                    const handlers = {
                        mouse: [],
                        keyboard: [],
                        timer: [],
                        focus: [],
                        touch: [],
                        lifecycle: [],
                        other: []
                    }
                    
                    const elementsWithViolations = [];

                    document.querySelectorAll('*').forEach(element => {
                        let hasViolation = false;
                        
                        Array.from(element.attributes).forEach(attr => {
                            if (attr.name.startsWith('on')) {
                                const eventType = attr.name.slice(2)
                                const category = categorizeEvent(eventType)
                                
                                const handlerInfo = {
                                    element: element.tagName.toLowerCase(),
                                    id: element.id || null,
                                    class: element.className || null,
                                    xpath: getFullXPath(element),
                                    eventType: eventType,
                                    handler: attr.value,
                                    isIntrinsicInteractive: isIntrinsicInteractive(element),
                                    hasTabindex: element.hasAttribute('tabindex'),
                                    tabindex: element.getAttribute('tabindex'),
                                    location: {
                                        inModal: element.closest(
                                            'dialog, [role="dialog"], [class*="modal"]'
                                        ) !== null
                                    }
                                }
                                
                                handlers[category].push(handlerInfo)
                                
                                // Mark as violation if non-interactive without tabindex
                                if (!handlerInfo.isIntrinsicInteractive && !handlerInfo.hasTabindex) {
                                    hasViolation = true;
                                }
                            }
                        })

                        const classAndData = element.className + ' ' + 
                            Array.from(element.attributes)
                                .map(attr => attr.name + ' ' + attr.value)
                                .join(' ')

                        if (classAndData.toLowerCase().includes('click') ||
                            classAndData.toLowerCase().includes('button') ||
                            classAndData.toLowerCase().includes('trigger')) {
                            const handlerInfo = {
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                class: element.className,
                                xpath: getFullXPath(element),
                                eventType: 'click',
                                handler: 'class-based',
                                isIntrinsicInteractive: isIntrinsicInteractive(element),
                                hasTabindex: element.hasAttribute('tabindex'),
                                tabindex: element.getAttribute('tabindex'),
                                location: {
                                    inModal: element.closest(
                                        'dialog, [role="dialog"], [class*="modal"]'
                                    ) !== null
                                }
                            }
                            
                            handlers.mouse.push(handlerInfo)
                            
                            // Mark as violation if non-interactive without tabindex
                            if (!handlerInfo.isIntrinsicInteractive && !handlerInfo.hasTabindex) {
                                hasViolation = true;
                            }
                        }
                        
                        if (hasViolation) {
                            elementsWithViolations.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id || null,
                                class: element.className || null,
                                xpath: getFullXPath(element),
                                violationType: 'missing-tabindex',
                                message: 'Non-interactive element with event handler missing tabindex attribute'
                            });
                        }
                    })

                    const modals = document.querySelectorAll(
                        'dialog, [role="dialog"], [class*="modal"]'
                    )
                    const hasModalEscapeHandler = Array.from(modals).some(modal => {
                        const onkeydown = modal.getAttribute('onkeydown')
                        return onkeydown && 
                               (onkeydown.includes('Escape') || 
                                onkeydown.includes('Esc') || 
                                onkeydown.includes('27'))
                    })
                    
                    // Add modals without escape handling to violations
                    const modalsWithoutEscape = [];
                    if (modals.length > 0 && !hasModalEscapeHandler) {
                        Array.from(modals).forEach(modal => {
                            modalsWithoutEscape.push({
                                element: modal.tagName.toLowerCase(),
                                id: modal.id || null,
                                class: modal.className || null,
                                xpath: getFullXPath(modal),
                                violationType: 'modal-without-escape',
                                message: 'Modal element without keyboard escape handler'
                            });
                        });
                    }

                    // Check for elements with mouse handlers but no keyboard handlers
                    const elementsWithMouseHandlers = new Map();
                    handlers.mouse.forEach(h => {
                        const key = JSON.stringify({
                            element: h.element,
                            id: h.id,
                            class: h.class
                        });
                        elementsWithMouseHandlers.set(key, h);
                    });

                    const elementsWithKeyboardHandlers = new Set(
                        handlers.keyboard.map(h => JSON.stringify({
                            element: h.element,
                            id: h.id,
                            class: h.class
                        }))
                    );

                    const mouseOnlyElements = [];
                    elementsWithMouseHandlers.forEach((handlerInfo, key) => {
                        if (!elementsWithKeyboardHandlers.has(key)) {
                            const elementInfo = JSON.parse(key);
                            mouseOnlyElements.push({
                                ...elementInfo,
                                xpath: handlerInfo.xpath,
                                violationType: 'mouse-only',
                                message: 'Element has mouse handler but no keyboard handler'
                            });
                        }
                    });

                    // Combine all violations
                    const allViolations = [
                        ...elementsWithViolations,
                        ...modalsWithoutEscape,
                        ...mouseOnlyElements
                    ];
                    
                    // Count violations by type
                    const violationsByType = {
                        'missing-tabindex': elementsWithViolations.length,
                        'modal-without-escape': modalsWithoutEscape.length,
                        'mouse-only': mouseOnlyElements.length
                    };

                    return {
                        handlers: handlers,
                        violations: allViolations,
                        summary: {
                            totalHandlers: Object.values(handlers)
                                .reduce((sum, arr) => sum + arr.length, 0),
                            byType: Object.fromEntries(
                                Object.entries(handlers)
                                    .map(([type, arr]) => [type, arr.length])
                            ),
                            nonInteractiveWithHandlers: Object.values(handlers)
                                .flat()
                                .filter(h => !h.isIntrinsicInteractive)
                                .length,
                            missingTabindex: Object.values(handlers)
                                .flat()
                                .filter(h => !h.isIntrinsicInteractive && !h.hasTabindex)
                                .length,
                            modalEscapeSupport: {
                                hasModals: modals.length > 0,
                                hasEscapeHandler: hasModalEscapeHandler
                             },
                            mouseOnlyElements: {
                                count: mouseOnlyElements.length
                            },
                            totalViolations: allViolations.length,
                            violationsByType: violationsByType,
                            hasMissingTabindex: elementsWithViolations.length > 0,
                            hasModalsWithoutEscape: modalsWithoutEscape.length > 0,
                            hasMouseOnlyHandlers: mouseOnlyElements.length > 0
                        }
                    }
                }

                // Documentation is now defined at the module level as TEST_DOCUMENTATION

                const eventResults = findEventHandlers()
                const tabOrderResults = analyzeTabOrder()
                
                // Combine all violation counts for page-level summary
                const allViolationCounts = {
                    ...eventResults.summary.violationsByType,
                    ...(tabOrderResults.summary.violationsByType || {})
                };
                
                // Create page-level violation flags
                const violationFlags = {
                    // Event handler violation flags
                    hasMissingTabindex: eventResults.summary.hasMissingTabindex,
                    hasModalsWithoutEscape: eventResults.summary.hasModalsWithoutEscape,
                    hasMouseOnlyHandlers: eventResults.summary.hasMouseOnlyHandlers,
                    
                    // Tab order violation flags
                    hasVisualOrderViolations: tabOrderResults.summary.hasVisualOrderViolations,
                    hasColumnOrderViolations: tabOrderResults.summary.hasColumnOrderViolations,
                    hasNegativeTabindex: tabOrderResults.summary.hasNegativeTabindex,
                    hasHighTabindex: tabOrderResults.summary.hasHighTabindex,
                    
                    // Additional flags for specific counts
                    violations: {
                        missingTabindex: allViolationCounts['missing-tabindex'] || 0,
                        modalsWithoutEscape: allViolationCounts['modal-without-escape'] || 0,
                        mouseOnly: allViolationCounts['mouse-only'] || 0,
                        visualOrder: allViolationCounts['visual-order'] || 0,
                        columnOrder: allViolationCounts['column-order'] || 0,
                        negativeTabindex: allViolationCounts['negative-tabindex'] || 0,
                        highTabindex: allViolationCounts['high-tabindex'] || 0
                    }
                };
                
                return {
                    pageFlags: {
                        hasEventHandlers: eventResults.summary.totalHandlers > 0,
                        hasNonInteractiveHandlers: eventResults.summary.nonInteractiveWithHandlers > 0,
                        hasMissingTabindex: eventResults.summary.hasMissingTabindex,
                        hasModalsWithoutEscape: eventResults.summary.hasModalsWithoutEscape,
                        hasTabOrderViolations: tabOrderResults.violations.length > 0,
                        hasMouseOnlyHandlers: eventResults.summary.hasMouseOnlyHandlers,
                        hasVisualOrderViolations: tabOrderResults.summary.hasVisualOrderViolations,
                        hasColumnOrderViolations: tabOrderResults.summary.hasColumnOrderViolations,
                        hasNegativeTabindex: tabOrderResults.summary.hasNegativeTabindex,
                        hasHighTabindex: tabOrderResults.summary.hasHighTabindex,
                        details: {
                            totalHandlers: eventResults.summary.totalHandlers,
                            byType: eventResults.summary.byType,
                            nonInteractiveWithHandlers: eventResults.summary.nonInteractiveWithHandlers,
                            missingTabindex: eventResults.summary.missingTabindex,
                            modalEscapeSupport: eventResults.summary.modalEscapeSupport,
                            mouseOnlyElements: eventResults.summary.mouseOnlyElements,
                            tabOrder: {
                                totalFocusableElements: tabOrderResults.summary.totalFocusableElements,
                                elementsWithExplicitTabIndex: 
                                    tabOrderResults.summary.elementsWithExplicitTabIndex,
                                visualOrderViolations: tabOrderResults.summary.violationsByType['visual-order'] || 0,
                                columnOrderViolations: tabOrderResults.summary.violationsByType['column-order'] || 0,
                                negativeTabindex: tabOrderResults.summary.violationsByType['negative-tabindex'] || 0,
                                highTabindex: tabOrderResults.summary.violationsByType['high-tabindex'] || 0
                             },
                            violationCounts: allViolationCounts,
                            violationFlags: violationFlags,
                            totalViolations: eventResults.summary.totalViolations + 
                                (tabOrderResults.violations ? tabOrderResults.violations.length : 0)
                        }
                    },
                    results: {
                        events: eventResults,
                        tabOrder: tabOrderResults
                    }
                }
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'events': {
                'pageFlags': event_data['pageFlags'],
                'details': event_data['results'],
                'documentation': TEST_DOCUMENTATION,
                'timestamp': datetime.now().isoformat()
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'events': {
                'pageFlags': {
                    'hasEventHandlers': False,
                    'hasNonInteractiveHandlers': False,
                    'hasMissingTabindex': False,
                    'hasModalsWithoutEscape': False,
                    'hasTabOrderViolations': False,
                    'hasMouseOnlyHandlers': False,
                    'hasVisualOrderViolations': False,
                    'hasColumnOrderViolations': False,
                    'hasNegativeTabindex': False,
                    'hasHighTabindex': False,
                    'details': {
                        'totalHandlers': 0,
                        'byType': {
                            'mouse': 0,
                            'keyboard': 0,
                            'timer': 0,
                            'focus': 0,
                            'touch': 0,
                            'lifecycle': 0,
                            'other': 0
                         },
                        'nonInteractiveWithHandlers': 0,
                        'missingTabindex': 0,
                        'modalEscapeSupport': {
                            'hasModals': False,
                            'hasEscapeHandler': False
                        },
                        'mouseOnlyElements': {
                            'count': 0
                        },
                        'tabOrder': {
                            'totalFocusableElements': 0,
                            'elementsWithExplicitTabIndex': 0,
                            'visualOrderViolations': 0,
                            'columnOrderViolations': 0,
                            'negativeTabindex': 0,
                            'highTabindex': 0
                        },
                        'violationCounts': {},
                        'violationFlags': {
                            'hasMissingTabindex': False,
                            'hasModalsWithoutEscape': False,
                            'hasMouseOnlyHandlers': False,
                            'hasVisualOrderViolations': False,
                            'hasColumnOrderViolations': False,
                            'hasNegativeTabindex': False,
                            'hasHighTabindex': False,
                            'violations': {
                                'missingTabindex': 0,
                                'modalsWithoutEscape': 0,
                                'mouseOnly': 0,
                                'visualOrder': 0,
                                'columnOrder': 0,
                                'negativeTabindex': 0,
                                'highTabindex': 0
                            }
                        },
                        'totalViolations': 0
                    }
                },
                'details': {
                    'events': {
                        'handlers': {
                            'mouse': [],
                            'keyboard': [],
                            'timer': [],
                            'focus': [],
                            'touch': [],
                            'lifecycle': [],
                            'other': []
                        },
                        'violations': []
                    },
                    'tabOrder': {
                        'tabOrder': [],
                        'rows': [],
                        'violations': []
                    },
                    'violations': [{
                        'issue': 'Error evaluating events and tab order',
                        'details': str(e)
                    }]
                },
                'documentation': TEST_DOCUMENTATION }
        }