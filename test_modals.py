from datetime import datetime

async def test_modals(page):
    """
    Test modal dialogs for accessibility requirements including proper headings
    """
    try:
        modals_data = await page.evaluate('''
            () => {
                function findModals() {
                    const dialogElements = Array.from(document.querySelectorAll('dialog'))
                    const roleDialogs = Array.from(document.querySelectorAll('[role="dialog"]'))
                    const modalDivs = Array.from(document.querySelectorAll('div[class*="modal" i]'))
                    
                    return [...dialogElements, ...roleDialogs, ...modalDivs]
                }

                function checkDialogHeading(modal) {
                    const children = Array.from(modal.childNodes)
                    const firstElement = children.find(node => 
                        node.nodeType === 1 && 
                        !['script', 'style'].includes(node.tagName.toLowerCase())
                    )

                    if (!firstElement || !['h1', 'h2'].includes(firstElement.tagName.toLowerCase())) {
                        return {
                            hasProperHeading: false,
                            firstElement: firstElement ? firstElement.tagName.toLowerCase() : null
                        }
                    }

                    return {
                        hasProperHeading: true,
                        heading: {
                            level: firstElement.tagName.toLowerCase(),
                            text: firstElement.textContent.trim()
                        }
                    }
                }

                function findTriggers(modal) {
                    const triggers = []
                    const allInteractive = document.querySelectorAll(
                        'button, a, [role="button"], [tabindex="0"]'
                    )

                    allInteractive.forEach(element => {
                        // Check onclick handlers
                        const onclickAttr = element.getAttribute('onclick')
                        if (onclickAttr) {
                            if (onclickAttr.includes(modal.id) || 
                                onclickAttr.includes('modal') ||
                                onclickAttr.includes('dialog')) {
                                triggers.push({
                                    element: element.tagName.toLowerCase(),
                                    id: element.id,
                                    text: element.textContent.trim(),
                                    handler: 'onclick'
                                })
                            }
                        }

                        // Check event listeners through class names and data attributes
                        const classAndData = element.className + ' ' + 
                            Array.from(element.attributes)
                                .map(attr => attr.name + ' ' + attr.value)
                                .join(' ')

                        if (classAndData.toLowerCase().includes('modal-trigger') ||
                            classAndData.toLowerCase().includes('open-dialog') ||
                            (modal.id && classAndData.includes(modal.id))) {
                            triggers.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id,
                                text: element.textContent.trim(),
                                handler: 'class/data-attribute'
                            })
                        }
                    })

                    return triggers
                }

                function findCloseElements(modal) {
                    const closeElements = []
                    const interactiveElements = modal.querySelectorAll(
                        'button, a, [role="button"], [tabindex="0"]'
                    )

                    interactiveElements.forEach(element => {
                        const text = element.textContent.trim().toLowerCase()
                        const ariaLabel = element.getAttribute('aria-label')?.toLowerCase()
                        const title = element.getAttribute('title')?.toLowerCase()
                        
                        if ((text && text.includes('close')) ||
                            (ariaLabel && ariaLabel.includes('close')) ||
                            (title && title.includes('close')) ||
                            element.className.toLowerCase().includes('close') ||
                            element.id.toLowerCase().includes('close')) {
                            
                            closeElements.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id,
                                text: text,
                                ariaLabel: ariaLabel,
                                title: title
                            })
                        }
                    })

                    return closeElements
                }

                function analyzeModalInteractions(modal) {
                    const interactiveElements = modal.querySelectorAll(
                        'button, a, [role="button"], [tabindex="0"]'
                    )
                    
                    const interactions = []
                    interactiveElements.forEach(element => {
                        const hasOnClick = element.hasAttribute('onclick')
                        const hasClickClass = element.className.toLowerCase().includes('click') ||
                                           element.className.toLowerCase().includes('button')
                        const onclickContent = hasOnClick ? element.getAttribute('onclick') : ''
                        
                        if (hasOnClick || hasClickClass) {
                            interactions.push({
                                element: element.tagName.toLowerCase(),
                                id: element.id,
                                text: element.textContent.trim(),
                                type: hasOnClick ? 'onclick' : 'class-based',
                                affectsDisplay: hasOnClick ? 
                                    onclickContent.includes('display') ||
                                    onclickContent.includes('visibility') : 
                                    false,
                                hasFocusManagement: hasOnClick ?
                                    onclickContent.includes('focus') :
                                    false
                            })
                        }
                    })

                    return interactions
                }

                function checkFocusManagement(modal) {
                    const focusableElements = modal.querySelectorAll(
                        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                    )
                    
                    return {
                        hasFocusableElements: focusableElements.length > 0,
                        firstFocusable: focusableElements.length > 0 ? {
                            element: focusableElements[0].tagName.toLowerCase(),
                            id: focusableElements[0].id,
                            text: focusableElements[0].textContent.trim()
                        } : null,
                        totalFocusable: focusableElements.length
                    }
                }

                const results = {
                    modals: [],
                    summary: {
                        totalModals: 0,
                        modalsWithoutTriggers: 0,
                        modalsWithoutClose: 0,
                        modalsWithoutFocusManagement: 0,
                        modalsWithoutProperHeading: 0
                    }
                }

                const modals = findModals()
                results.summary.totalModals = modals.length

                modals.forEach(modal => {
                    const triggers = findTriggers(modal)
                    const closeElements = findCloseElements(modal)
                    const interactions = analyzeModalInteractions(modal)
                    const focusInfo = checkFocusManagement(modal)
                    const headingInfo = checkDialogHeading(modal)

                    const modalInfo = {
                        type: modal.tagName.toLowerCase() === 'dialog' ? 'dialog' :
                              modal.getAttribute('role') === 'dialog' ? 'role-dialog' : 
                              'div-modal',
                        id: modal.id || null,
                        class: modal.className,
                        heading: headingInfo,
                        isHidden: window.getComputedStyle(modal).display === 'none' ||
                                window.getComputedStyle(modal).visibility === 'hidden',
                        triggers: triggers,
                        closeElements: closeElements,
                        interactions: interactions,
                        focusManagement: focusInfo,
                        violations: []
                    }

                    // Check for violations
                    if (!headingInfo.hasProperHeading) {
                        modalInfo.violations.push({
                            type: 'no-heading',
                            message: 'Dialog does not start with H1 or H2 heading',
                            details: headingInfo.firstElement ? 
                                `First element is: ${headingInfo.firstElement}` : 
                                'No content elements found'
                        })
                        results.summary.modalsWithoutProperHeading++
                    }

                    if (triggers.length === 0) {
                        modalInfo.violations.push({
                            type: 'no-triggers',
                            message: 'No interactive elements found that trigger this modal'
                        })
                        results.summary.modalsWithoutTriggers++
                    }

                    if (closeElements.length === 0) {
                        modalInfo.violations.push({
                            type: 'no-close',
                            message: 'No elements found with "close" in their accessible name'
                        })
                        results.summary.modalsWithoutClose++
                    }

                    const hasFocusCall = interactions.some(i => i.hasFocusManagement)
                    if (!hasFocusCall && focusInfo.hasFocusableElements) {
                        modalInfo.violations.push({
                            type: 'no-focus-management',
                            message: 'No explicit focus management found in interactions'
                        })
                        results.summary.modalsWithoutFocusManagement++
                    }

                    results.modals.push(modalInfo)
                })

                return {
                    pageFlags: {
                        hasModals: results.summary.totalModals > 0,
                        hasModalViolations: results.summary.modalsWithoutTriggers > 0 ||
                                          results.summary.modalsWithoutClose > 0 ||
                                          results.summary.modalsWithoutFocusManagement > 0 ||
                                          results.summary.modalsWithoutProperHeading > 0,
                        details: {
                            totalModals: results.summary.totalModals,
                            modalsWithoutTriggers: results.summary.modalsWithoutTriggers,
                            modalsWithoutClose: results.summary.modalsWithoutClose,
                            modalsWithoutFocusManagement: results.summary.modalsWithoutFocusManagement,
                            modalsWithoutProperHeading: results.summary.modalsWithoutProperHeading
                        }
                    },
                    results: results
                }
            }
        ''')

        return {
            'modals': {
                'pageFlags': modals_data['pageFlags'],
                'details': modals_data['results'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'modals': {
                'pageFlags': {
                    'hasModals': False,
                    'hasModalViolations': False,
                    'details': {
                        'totalModals': 0,
                        'modalsWithoutTriggers': 0,
                        'modalsWithoutClose': 0,
                        'modalsWithoutFocusManagement': 0,
                        'modalsWithoutProperHeading': 0
                    }
                },
                'details': {
                    'modals': [],
                    'violations': [{
                        'issue': 'Error evaluating modals',
                        'details': str(e)
                    }]
                }
            }
        }