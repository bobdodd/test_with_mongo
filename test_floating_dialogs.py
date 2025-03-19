from datetime import datetime
import traceback
import asyncio  # Use asyncio for asynchronous sleep

async def test_floating_dialogs(page):
    """
    Test floating dialogs for proper implementation and content obscuring
    across all responsive breakpoints
    """
    try:
        print("\n=== STARTING FLOATING DIALOG TEST WITH RESPONSIVE BREAKPOINTS ===")
        # First, extract all the media query breakpoints from CSS
        print("Step 1: Extracting media query breakpoints from CSS")
        breakpoints = await page.evaluate('''
            () => {
                console.log("Extracting CSS breakpoints");
                // Extract all media queries from stylesheets
                const breakpoints = new Set();
                const mediaRegex = /\@media[^{]+/g;
                const widthRegex = /\((?:max|min)-width:\s*(\d+)(?:px|em|rem)\)/g;
                
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
                    let mediaBlocks = styleContent.match(mediaRegex) || [];
                    
                    mediaBlocks.forEach(mediaBlock => {
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
        # Access viewport as a property, not calling it as a function
        original_viewport = page.viewport
        print(f"Original viewport: {original_viewport}")
        
        # Initialize results container for all breakpoints
        print("Step 3: Initializing results container")
        all_breakpoint_results = []
        
        # Test at each breakpoint
        print("Step 4: Testing at each breakpoint")
        for i, breakpoint in enumerate(breakpoints):
            print(f"\n--- Testing breakpoint {i+1}/{len(breakpoints)}: {breakpoint}px ---")
            
            try:
                # Set viewport width to the breakpoint
                print(f"  Setting viewport width to {breakpoint}px")
                await page.setViewport({
                    'width': breakpoint,
                    'height': original_viewport['height'] 
                })
                
                # Wait for layout to stabilize - using asyncio.sleep for asynchronous waiting
                print("  Waiting for layout to stabilize")
                await asyncio.sleep(0.5)  # 500ms - increased for better reliability
                
                # Run the dialog evaluation at this breakpoint
                # FIXED: using function parameter instead of f-string
                print("  Evaluating dialogs at this breakpoint")
                dialog_data = await page.evaluate('''
                    (currentBreakpoint) => {
                        console.log("Evaluating at width " + currentBreakpoint + "px");
                        
                        function isVisible(element) {
                            const style = window.getComputedStyle(element);
                            return style.display !== 'none' && 
                                   style.visibility !== 'hidden' && 
                                   style.opacity !== '0';
                        }

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

                        function isInteractiveElement(element) {
                            // Check for naturally interactive elements
                            const interactiveTags = [
                                'a', 'button', 'input', 'select', 'textarea', 'details',
                                'audio[controls]', 'video[controls]'
                            ];
                            
                            if (interactiveTags.some(tag => {
                                if (tag.includes('[')) {
                                    const [tagName, attr] = tag.split('[');
                                    const attrName = attr.slice(0, -1);
                                    return element.tagName.toLowerCase() === tagName && 
                                           element.hasAttribute(attrName);
                                }
                                return element.tagName.toLowerCase() === tag;
                            })) {
                                return true;
                            }
                            
                            // Check for ARIA roles that make elements interactive
                            const interactiveRoles = [
                                'button', 'checkbox', 'combobox', 'link', 'menuitem', 
                                'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 
                                'searchbox', 'slider', 'spinbutton', 'switch', 'tab', 
                                'textbox', 'treeitem'
                            ];
                            
                            if (element.hasAttribute('role') && 
                                interactiveRoles.includes(element.getAttribute('role'))) {
                                return true;
                            }
                            
                            // Check for attributes that suggest interactivity
                            if (element.hasAttribute('tabindex') && element.getAttribute('tabindex') >= 0) {
                                return true;
                            }
                            
                            if (element.hasAttribute('onclick') || 
                                element.hasAttribute('onkeydown') || 
                                element.hasAttribute('onkeyup')) {
                                return true;
                            }

                            // Check for event listeners
                            return (typeof element.onclick === 'function' || 
                                    typeof element.onkeydown === 'function' || 
                                    typeof element.onkeyup === 'function');
                        }

                        function containsInteractiveElement(element) {
                            if (isInteractiveElement(element)) {
                                return true;
                            }
                            
                            const children = element.querySelectorAll('*');
                            for (const child of children) {
                                if (isInteractiveElement(child)) {
                                    return true;
                                }
                            }
                            
                            return false;
                        }

                        function getLandmark(element) {
                            const landmarks = {
                                'banner': ['header[role="banner"]', '[role="banner"]', 'header:not([role])'],
                                'contentinfo': ['footer[role="contentinfo"]', '[role="contentinfo"]', 'footer:not([role])'],
                                'main': ['main', '[role="main"]'],
                                'navigation': ['nav', '[role="navigation"]'],
                                'complementary': ['aside', '[role="complementary"]'],
                                'search': ['[role="search"]'],
                                'form': ['form[role="form"]', '[role="form"]']
                            };

                            let current = element;
                            while (current && current !== document.body) {
                                for (const [landmarkName, selectors] of Object.entries(landmarks)) {
                                    if (selectors.some(selector => current.matches(selector))) {
                                        return {
                                            type: landmarkName,
                                            element: current.tagName.toLowerCase(),
                                            id: current.id || null,
                                            label: getAccessibleName(current),
                                            xpath: getFullXPath(current)
                                        };
                                    }
                                }
                                current = current.parentElement;
                            }
                            return null;
                        }

                        function getAccessibleName(element) {
                            if (element.getAttribute('aria-labelledby')) {
                                const labelledBy = element.getAttribute('aria-labelledby')
                                    .split(' ')
                                    .map(id => document.getElementById(id)?.textContent || '')
                                    .join(' ');
                                if (labelledBy.trim()) return labelledBy;
                            }
                            
                            if (element.getAttribute('aria-label')) {
                                return element.getAttribute('aria-label');
                            }
                            
                            return '';
                        }

                        function getHeadingLevel(element) {
                            const ariaLevel = element.getAttribute('aria-level');
                            if (ariaLevel) return parseInt(ariaLevel);

                            const heading = element.querySelector('h1, h2, h3, h4, h5, h6');
                            if (heading) {
                                return parseInt(heading.tagName.substring(1));
                            }

                            return null;
                        }

                        function checkContentOverlap(dialog) {
                            const dialogRect = dialog.getBoundingClientRect();
                            const mainContent = document.querySelector('main') || document.body;
                            const contentElements = mainContent.querySelectorAll('*');
                            const overlappingElements = {
                                interactive: [],
                                nonInteractive: []
                            };

                            contentElements.forEach(element => {
                                if (element !== dialog && !dialog.contains(element)) {
                                    const elementRect = element.getBoundingClientRect();
                                    const style = window.getComputedStyle(element);
                                    
                                    if (style.display === 'none' || 
                                        style.visibility === 'hidden' || 
                                        style.opacity === '0') {
                                        return;
                                    }

                                    if (!(elementRect.right < dialogRect.left || 
                                        elementRect.left > dialogRect.right || 
                                        elementRect.bottom < dialogRect.top || 
                                        elementRect.top > dialogRect.bottom)) {
                                        
                                        const isInteractive = isInteractiveElement(element) || 
                                                             containsInteractiveElement(element);
                                        
                                        const overlapInfo = {
                                            element: element.tagName.toLowerCase(),
                                            id: element.id || null,
                                            class: element.className || null,
                                            text: element.textContent.trim().substring(0, 50),
                                            xpath: getFullXPath(element),
                                            overlap: {
                                                horizontal: Math.min(elementRect.right, dialogRect.right) - 
                                                          Math.max(elementRect.left, dialogRect.left),
                                                vertical: Math.min(elementRect.bottom, dialogRect.bottom) - 
                                                        Math.max(elementRect.top, dialogRect.top)
                                            },
                                            overlapPercentage: {
                                                horizontal: (Math.min(elementRect.right, dialogRect.right) - 
                                                            Math.max(elementRect.left, dialogRect.left)) / 
                                                            (elementRect.width) * 100,
                                                vertical: (Math.min(elementRect.bottom, dialogRect.bottom) - 
                                                        Math.max(elementRect.top, dialogRect.top)) / 
                                                        (elementRect.height) * 100
                                            }
                                        };
                                        
                                        // Calculate how much of the element is covered by the dialog
                                        const elementArea = elementRect.width * elementRect.height;
                                        const overlapArea = overlapInfo.overlap.horizontal * overlapInfo.overlap.vertical;
                                        overlapInfo.coveragePercent = (overlapArea / elementArea) * 100;
                                        
                                        if (isInteractive) {
                                            overlapInfo.interactiveType = isInteractiveElement(element) ? 
                                                'direct' : 'contains interactive elements';
                                            overlappingElements.interactive.push(overlapInfo);
                                        } else {
                                            overlappingElements.nonInteractive.push(overlapInfo);
                                        }
                                    }
                                }
                            });

                            return overlappingElements;
                        }

                        function analyzeCloseButtonFocus(dialog) {
                            const closeButtons = dialog.querySelectorAll(
                                'button[aria-label*="close" i], button[title*="close" i], ' +
                                '[role="button"][aria-label*="close" i], [role="button"][title*="close" i], ' +
                                'button.close, .close-button, .btn-close, ' +
                                'button:has(svg[aria-label*="close"]), ' +
                                'button:has(img[alt*="close"])'
                            );
                            
                            if (!closeButtons || closeButtons.length === 0) {
                                return {
                                    hasCloseButton: false,
                                    focusManagement: {
                                        analyzed: false,
                                        reason: "No close button found"
                                    }
                                };
                            }
                            
                            const closeButtonInfo = {
                                hasCloseButton: true,
                                closeButtons: []
                            };
                            
                            Array.from(closeButtons).forEach((button, index) => {
                                const buttonInfo = {
                                    element: button.tagName.toLowerCase(),
                                    id: button.id || null,
                                    class: button.className || null,
                                    ariaLabel: button.getAttribute('aria-label') || null,
                                    title: button.getAttribute('title') || null,
                                    text: button.textContent.trim().substring(0, 50) || null,
                                    xpath: getFullXPath(button),
                                    focusManagement: {
                                        analyzed: true,
                                        hasEventListeners: false,
                                        clickHandlers: [],
                                        keyDownHandlers: [],
                                        focusTarget: null,
                                        willMoveFocus: false,
                                        targetIsValid: false,
                                        focusViolation: false,
                                        violationReason: null
                                    }
                                };
                                
                                // Check for directly attached event handlers
                                const hasOnClick = button.onclick !== null;
                                const hasOnKeyDown = button.onkeydown !== null;
                                
                                buttonInfo.focusManagement.hasEventListeners = hasOnClick || hasOnKeyDown;
                                
                                // Get click handler info if possible
                                if (hasOnClick) {
                                    // Try to extract function body (works in some browsers)
                                    let handlerText = button.onclick.toString();
                                    buttonInfo.focusManagement.clickHandlers.push({
                                        type: "direct",
                                        handlerSummary: handlerText.substring(0, 200) + (handlerText.length > 200 ? "..." : "")
                                    });
                                }
                                
                                if (hasOnKeyDown) {
                                    let handlerText = button.onkeydown.toString();
                                    buttonInfo.focusManagement.keyDownHandlers.push({
                                        type: "direct", 
                                        handlerSummary: handlerText.substring(0, 200) + (handlerText.length > 200 ? "..." : "")
                                    });
                                }
                                
                                // Analyze button attributes for focus destination clues
                                const hasAriaControls = button.hasAttribute('aria-controls');
                                if (hasAriaControls) {
                                    const controlsId = button.getAttribute('aria-controls');
                                    const controlledElement = document.getElementById(controlsId);
                                    
                                    if (controlledElement) {
                                        buttonInfo.focusManagement.possibleFocusTarget = {
                                            targetType: "aria-controls",
                                            targetId: controlsId,
                                            targetElement: controlledElement.tagName.toLowerCase(),
                                            targetXPath: getFullXPath(controlledElement),
                                            isInteractive: isInteractiveElement(controlledElement),
                                            hasTabIndex: controlledElement.hasAttribute('tabindex'),
                                            tabIndexValue: controlledElement.getAttribute('tabindex')
                                        };
                                    }
                                }
                                
                                // Check for data attributes that might indicate focus targets
                                const dataAttributes = Array.from(button.attributes)
                                    .filter(attr => attr.name.startsWith('data-'))
                                    .map(attr => ({name: attr.name, value: attr.value}));
                                    
                                if (dataAttributes.length > 0) {
                                    buttonInfo.focusManagement.dataAttributes = dataAttributes;
                                    
                                    // Look for common data attributes that might indicate focus targets
                                    const focusTargetAttrs = dataAttributes.filter(attr => 
                                        attr.name.includes('focus') || 
                                        attr.name.includes('target') || 
                                        attr.name.includes('return')
                                    );
                                    
                                    if (focusTargetAttrs.length > 0) {
                                        buttonInfo.focusManagement.potentialFocusAttributes = focusTargetAttrs;
                                    }
                                }
                                
                                // Try to find the expected focus target - usually the first focusable element at the top of the page
                                const potentialTopFocusElements = [];
                                
                                // Elements that might be valid focus targets at the top of the page
                                const topInteractiveElements = document.querySelectorAll('header a, header button, [role="banner"] a, [role="banner"] button, nav a, nav button');
                                if (topInteractiveElements.length > 0) {
                                    Array.from(topInteractiveElements).slice(0, 3).forEach(el => {
                                        potentialTopFocusElements.push({
                                            element: el.tagName.toLowerCase(),
                                            id: el.id || null,
                                            xpath: getFullXPath(el),
                                            isInteractive: true,
                                            isTopOfPage: true
                                        });
                                    });
                                }
                                
                                // Elements with tabindex=-1 near the top
                                const topSkipLinks = document.querySelectorAll('a[tabindex="-1"], [tabindex="-1"]');
                                Array.from(topSkipLinks).slice(0, 2).forEach(el => {
                                    const rect = el.getBoundingClientRect();
                                    if (rect.top < 200) { // Roughly at the top of the page
                                        potentialTopFocusElements.push({
                                            element: el.tagName.toLowerCase(),
                                            id: el.id || null,
                                            xpath: getFullXPath(el),
                                            tabIndex: el.getAttribute('tabindex'),
                                            isTopOfPage: true
                                        });
                                    }
                                });
                                
                                // Main element or first heading as a fallback focus target
                                const mainEl = document.querySelector('main');
                                if (mainEl) {
                                    potentialTopFocusElements.push({
                                        element: 'main',
                                        id: mainEl.id || null,
                                        xpath: getFullXPath(mainEl),
                                        hasTabIndex: mainEl.hasAttribute('tabindex'),
                                        tabIndex: mainEl.getAttribute('tabindex'),
                                        isValidTarget: mainEl.hasAttribute('tabindex') && mainEl.getAttribute('tabindex') === '-1'
                                    });
                                }
                                
                                // Check for issues if potential focus elements were found
                                if (potentialTopFocusElements.length > 0) {
                                    buttonInfo.focusManagement.potentialFocusTargets = potentialTopFocusElements;
                                    
                                    // Check if any of these would be valid focus targets
                                    const hasValidTarget = potentialTopFocusElements.some(el => 
                                        (el.isInteractive || (el.hasTabIndex && el.tabIndex === '-1'))
                                    );
                                    
                                    buttonInfo.focusManagement.hasValidTopFocusTarget = hasValidTarget;
                                    
                                    if (!hasValidTarget) {
                                        buttonInfo.focusManagement.focusViolation = true;
                                        buttonInfo.focusManagement.violationReason = "No valid focus target at top of page";
                                    }
                                } else {
                                    buttonInfo.focusManagement.focusViolation = true;
                                    buttonInfo.focusManagement.violationReason = "No potential focus targets found at top of page";
                                }
                                
                                // Analyze dialog for focus trapping (expected behavior)
                                const dialogHasFocusTrap = hasDialogFocusTrap(dialog);
                                buttonInfo.focusManagement.dialogHasFocusTrap = dialogHasFocusTrap;
                                
                                closeButtonInfo.closeButtons.push(buttonInfo);
                            });
                            
                            return closeButtonInfo;
                        }

                        function hasDialogFocusTrap(dialog) {
                            // Look for common focus trap implementations
                            const hasFocusTrapAttribute = dialog.hasAttribute('aria-modal') && 
                                                         dialog.getAttribute('aria-modal') === 'true';
                                                         
                            // Check for common focus trap libraries by looking at class names
                            const hasCommonTrapClasses = dialog.className && (
                                dialog.className.includes('modal') ||
                                dialog.className.includes('dialog') ||
                                dialog.className.includes('popup') ||
                                dialog.className.includes('focus-trap') ||
                                dialog.className.includes('a11y')
                            );
                            
                            // Check for elements that might be part of a focus trap
                            const hasFocusTrapElements = !!dialog.querySelector('[tabindex="0"][aria-hidden="true"]') ||
                                                       !!dialog.querySelector('[tabindex="-1"][aria-hidden="true"]');
                                                       
                            return {
                                hasAriaModal: hasFocusTrapAttribute,
                                hasCommonTrapClasses: hasCommonTrapClasses,
                                hasTrapElements: hasFocusTrapElements,
                                likelyHasFocusTrap: hasFocusTrapAttribute || hasFocusTrapElements
                            };
                        }

                        const dialogs = [
                            ...Array.from(document.querySelectorAll('dialog')),
                            ...Array.from(document.querySelectorAll('div'))
                                .filter(div => {
                                    const style = window.getComputedStyle(div);
                                    return style.zIndex !== 'auto' && parseInt(style.zIndex) > 0;
                                })
                        ];

                        const visibleDialogs = dialogs.filter(isVisible);
                        const dialogAnalysis = [];
                        const violations = [];
                        const warnings = [];

                        visibleDialogs.forEach(dialog => {
                            const headingLevel = getHeadingLevel(dialog);
                            const style = window.getComputedStyle(dialog);
                            const landmark = getLandmark(dialog);
                            const isHeader = landmark?.type === 'banner';
                            const isFooter = landmark?.type === 'contentinfo';
                            const overlappingElements = checkContentOverlap(dialog);
                            
                            const dialogInfo = {
                                element: dialog.tagName.toLowerCase(),
                                id: dialog.id || null,
                                class: dialog.className || null,
                                xpath: getFullXPath(dialog),
                                headingLevel: headingLevel,
                                landmark: landmark,
                                styling: {
                                    zIndex: style.zIndex,
                                    position: style.position,
                                    display: style.display
                                },
                                content: {
                                    text: dialog.textContent.trim().substring(0, 100),
                                    closeButtonAnalysis: analyzeCloseButtonFocus(dialog)
                                },
                                overlappingElements: overlappingElements
                            };

                            dialogAnalysis.push(dialogInfo);

                            // Only check heading level if not banner
                            if (!isHeader && (!headingLevel || headingLevel !== 2)) {
                                violations.push({
                                    issue: 'Incorrect heading level',
                                    element: dialog.tagName.toLowerCase(),
                                    id: dialog.id || null,
                                    xpath: getFullXPath(dialog),
                                    landmark: landmark?.type || 'none',
                                    details: `Dialog should have a heading level of 2, found: ${headingLevel}`
                                });
                            }

                            // Only check for close button if not banner or footer
                            if (!isHeader && !isFooter && !dialogInfo.content.closeButtonAnalysis.hasCloseButton) {
                                violations.push({
                                    issue: 'Missing close button',
                                    element: dialog.tagName.toLowerCase(),
                                    id: dialog.id || null,
                                    xpath: getFullXPath(dialog),
                                    landmark: landmark?.type || 'none',
                                    details: 'Dialog needs a close button'
                                });
                            }

                            // Check close button focus management
                            if (!isHeader && !isFooter && dialogInfo.content.closeButtonAnalysis.hasCloseButton) {
                                // Check each close button for focus management violations
                                const closeButtons = dialogInfo.content.closeButtonAnalysis.closeButtons || [];
                                for (const button of closeButtons) {
                                    if (button.focusManagement && button.focusManagement.focusViolation) {
                                        violations.push({
                                            issue: 'Improper focus management',
                                            severity: 'high',
                                            element: button.element,
                                            id: button.id || null,
                                            xpath: button.xpath,
                                            details: `Close button does not properly manage focus: ${button.focusManagement.violationReason}`,
                                            focusInfo: button.focusManagement,
                                            potentialTargets: button.focusManagement.potentialFocusTargets || []
                                        });
                                    }
                                }
                            }

                            // Report on interactive elements hidden by the dialog as high priority
                            if (overlappingElements.interactive.length > 0) {
                                violations.push({
                                    issue: 'Hidden interactive content',
                                    severity: 'critical',
                                    element: dialog.tagName.toLowerCase(),
                                    id: dialog.id || null,
                                    xpath: getFullXPath(dialog),
                                    landmark: landmark?.type || 'none',
                                    details: `Dialog obscures ${overlappingElements.interactive.length} interactive elements at ${currentBreakpoint}px width`,
                                    hiddenElements: overlappingElements.interactive
                                });
                            }

                            // Report on non-interactive elements as warnings
                            if (overlappingElements.nonInteractive.length > 0) {
                                warnings.push({
                                    issue: 'Content overlap',
                                    severity: 'moderate',
                                    element: dialog.tagName.toLowerCase(),
                                    id: dialog.id || null,
                                    xpath: getFullXPath(dialog),
                                    landmark: landmark?.type || 'none',
                                    details: `Dialog overlaps ${overlappingElements.nonInteractive.length} non-interactive elements at ${currentBreakpoint}px width`,
                                    overlapping: overlappingElements.nonInteractive
                                });
                            }
                        });

                        console.log(`Evaluation complete at width ${currentBreakpoint}px`);
                        
                        return {
                            breakpoint: currentBreakpoint,
                            viewport: {
                                width: window.innerWidth,
                                height: window.innerHeight
                            },
                            pageFlags: {
                                hasVisibleDialogs: visibleDialogs.length > 0,
                                hasIncorrectHeadings: violations.some(v => v.issue === 'Incorrect heading level'),
                                hasContentOverlap: warnings.length > 0,
                                hasHiddenInteractiveContent: violations.some(v => v.issue === 'Hidden interactive content'),
                                hasMissingCloseButtons: violations.some(v => v.issue === 'Missing close button'),
                                hasImproperFocusManagement: violations.some(v => v.issue === 'Improper focus management'),
                                details: {
                                    totalDialogs: dialogs.length,
                                    visibleDialogs: visibleDialogs.length,
                                    incorrectHeadings: violations.filter(v => v.issue === 'Incorrect heading level').length,
                                    missingCloseButtons: violations.filter(v => v.issue === 'Missing close button').length,
                                    improperFocusManagement: violations.filter(v => v.issue === 'Improper focus management').length,
                                    hiddenInteractiveElements: violations.filter(v => v.issue === 'Hidden interactive content').length,
                                    overlappingNonInteractiveContent: warnings.filter(w => w.issue === 'Content overlap').length
                                }
                            },
                            results: {
                                dialogs: dialogAnalysis,
                                violations: violations,
                                warnings: warnings
                            }
                        };
                    }
                ''', breakpoint)  # Pass breakpoint as a parameter
                
                print(f"  Evaluation complete. Type of result: {type(dialog_data)}")
                
                # Check if dialog_data is what we expect
                if not isinstance(dialog_data, dict):
                    print(f"  ERROR: dialog_data is not a dictionary, got {type(dialog_data)}")
                    dialog_data = {
                        'breakpoint': str(breakpoint),  # Convert to string for MongoDB compatibility
                        'error': f"Unexpected result type: {type(dialog_data)}"
                    }
                
                # Add this breakpoint's results to our collection
                print(f"  Adding result for breakpoint {breakpoint}px to all_breakpoint_results")
                all_breakpoint_results.append(dialog_data)
                
                # Add a short pause between evaluations to avoid overwhelming the browser
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"  ERROR at breakpoint {breakpoint}px: {str(e)}")
                print(traceback.format_exc())
                all_breakpoint_results.append({
                    'breakpoint': str(breakpoint),  # Convert to string for MongoDB compatibility
                    'error': str(e)
                })
        
        # Restore original viewport
        print("\nStep 5: Restoring original viewport")
        await page.setViewport(original_viewport)
        print(f"Viewport restored to: {original_viewport}")
        
        # Wait for the layout to stabilize after returning to original size
        await asyncio.sleep(0.5)
        
        # Check that all_breakpoint_results is valid
        print(f"\nStep 6: Checking all_breakpoint_results (length: {len(all_breakpoint_results)})")
        if not all_breakpoint_results:
            print("WARNING: all_breakpoint_results is empty!")
            all_breakpoint_results = []
        
        # Now process the consolidated results using our defined function
        print("\nStep 7: Consolidating results")
        
        # This should fix the missing function issue
        consolidated_results = consolidate_results(all_breakpoint_results)
        print(f"  Consolidated results type: {type(consolidated_results)}")
        
        # Prepare final response with detailed info for debugging
        print("\nStep 8: Preparing response object")
        response = {
            'dialogs': {
                'breakpoints': [str(bp) for bp in breakpoints],  # Convert to strings for MongoDB compatibility
                'consolidated': consolidated_results,
                'breakpointResults': all_breakpoint_results,
                'timestamp': datetime.now().isoformat(),
                'documentation': generate_documentation()  # Add the documentation
            }
        }
        
        print("Step 9: Returning response")
        return response

    except Exception as e:
        print(f"\nCRITICAL ERROR: {str(e)}")
        print(traceback.format_exc())
        
        # Restore original viewport in case of error
        try:
            if 'original_viewport' in locals():
                print("Attempting to restore viewport after error")
                await page.setViewport(original_viewport)
                print("Viewport restored")
        except Exception as restore_error:
            print(f"Error restoring viewport: {str(restore_error)}")
            
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'dialogs': {
                'pageFlags': {
                    'hasVisibleDialogs': False,
                    'hasIncorrectHeadings': False,
                    'hasContentOverlap': False,
                    'hasHiddenInteractiveContent': False,
                    'hasMissingCloseButtons': False,
                    'hasImproperFocusManagement': False,
                    'details': {
                        'totalDialogs': 0,
                        'visibleDialogs': 0,
                        'incorrectHeadings': 0,
                        'missingCloseButtons': 0,
                        'improperFocusManagement': 0,
                        'hiddenInteractiveElements': 0,
                        'overlappingNonInteractiveContent': 0
                    }
                },
                'details': {
                    'dialogs': [],
                    'violations': [{
                        'issue': 'Error evaluating dialogs',
                        'details': str(e)
                    }],
                    'warnings': []
                },
                'documentation': generate_documentation()  # Add documentation even in error case
            }
        }

def consolidate_results(breakpoint_results):
    """
    Consolidate results from multiple breakpoints, organizing by issue type first
    """
    print("Inside consolidate_results function")
    print(f"breakpoint_results type: {type(breakpoint_results)}")
    print(f"breakpoint_results length: {len(breakpoint_results)}")
    
    if not breakpoint_results:
        print("Warning: Empty breakpoint_results")
        return {}
    
    try:
        # Track all tested breakpoints
        all_breakpoints = []
        
        # Track issues by type first, then by element
        issues_by_type = {
            "violations": {
                "incorrectHeadingLevel": {"elements": {}, "severity": "high"},
                "missingCloseButton": {"elements": {}, "severity": "high"},
                "improperFocusManagement": {"elements": {}, "severity": "high"},
                "hiddenInteractiveContent": {"elements": {}, "severity": "critical"}
            },
            "warnings": {
                "contentOverlap": {"elements": {}, "severity": "moderate"}
            }
        }
        
        # Track all unique dialogs found
        all_dialogs = set()
        
        # Process each breakpoint result
        print("Processing each breakpoint result")
        for i, bp_result in enumerate(breakpoint_results):
            print(f"Processing result {i+1}/{len(breakpoint_results)}")
            
            # Skip results with errors
            if 'error' in bp_result:
                print(f"Skipping result with error: {bp_result.get('error')}")
                continue
                
            # Get breakpoint value and add to list
            if 'breakpoint' not in bp_result:
                continue
                
            breakpoint = str(bp_result['breakpoint'])
            all_breakpoints.append(breakpoint)
            
            # Skip if no results
            if 'results' not in bp_result:
                continue
                
            results = bp_result['results']
            
            # Track dialogs
            if 'dialogs' in results:
                for dialog in results['dialogs']:
                    if 'xpath' in dialog:
                        all_dialogs.add(dialog['xpath'])
            
            # Process violations
            if 'violations' in results:
                for violation in results['violations']:
                    if 'issue' not in violation or 'xpath' not in violation:
                        continue
                        
                    issue_type = violation['issue']
                    element_id = violation['xpath']
                    
                    # Map to our consolidated issue types
                    if issue_type == "Incorrect heading level":
                        issue_key = "incorrectHeadingLevel"
                    elif issue_type == "Missing close button":
                        issue_key = "missingCloseButton"
                    elif issue_type == "Improper focus management":
                        issue_key = "improperFocusManagement"
                    elif issue_type == "Hidden interactive content":
                        issue_key = "hiddenInteractiveContent"
                    else:
                        # Skip unknown issue types
                        continue
                    
                    # If this element hasn't been tracked yet for this issue
                    if element_id not in issues_by_type["violations"][issue_key]["elements"]:
                        issues_by_type["violations"][issue_key]["elements"][element_id] = {
                            "element": violation.get('element', 'unknown'),
                            "id": violation.get('id'),
                            "xpath": element_id,
                            "details": violation.get('details', ''),
                            "breakpoints": [],
                            "breakpointDetails": {}
                        }
                        
                        # Add focus management specific info if applicable
                        if issue_key == "improperFocusManagement" and "focusInfo" in violation:
                            issues_by_type["violations"][issue_key]["elements"][element_id]["focusManagement"] = violation.get("focusInfo")
                            issues_by_type["violations"][issue_key]["elements"][element_id]["focusTargets"] = violation.get("potentialTargets", [])
                    
                    # Add this breakpoint to the affected breakpoints
                    issues_by_type["violations"][issue_key]["elements"][element_id]["breakpoints"].append(breakpoint)
                    
                    # Add breakpoint-specific details for hidden interactive content
                    if issue_key == "hiddenInteractiveContent" and "hiddenElements" in violation:
                        hidden_count = len(violation.get("hiddenElements", []))
                        
                        # Calculate worst coverage
                        worst_coverage = 0
                        direct_interactive = 0
                        contains_interactive = 0
                        
                        for hidden in violation.get("hiddenElements", []):
                            if "coveragePercent" in hidden and hidden["coveragePercent"] is not None:
                                worst_coverage = max(worst_coverage, hidden["coveragePercent"])
                            
                            if hidden.get("interactiveType") == "direct":
                                direct_interactive += 1
                            else:
                                contains_interactive += 1
                        
                        issues_by_type["violations"][issue_key]["elements"][element_id]["breakpointDetails"][breakpoint] = {
                            "count": hidden_count,
                            "worstCoverage": round(worst_coverage, 2),
                            "directInteractive": direct_interactive,
                            "containsInteractive": contains_interactive
                        }
            
            # Process warnings
            if 'warnings' in results:
                for warning in results['warnings']:
                    if 'issue' not in warning or 'xpath' not in warning:
                        continue
                        
                    issue_type = warning['issue']
                    element_id = warning['xpath']
                    
                    # Map to our consolidated issue types
                    if issue_type == "Content overlap":
                        issue_key = "contentOverlap"
                    else:
                        # Skip unknown issue types
                        continue
                    
                    # If this element hasn't been tracked yet for this issue
                    if element_id not in issues_by_type["warnings"][issue_key]["elements"]:
                        issues_by_type["warnings"][issue_key]["elements"][element_id] = {
                            "element": warning.get('element', 'unknown'),
                            "id": warning.get('id'),
                            "xpath": element_id,
                            "details": warning.get('details', ''),
                            "breakpoints": [],
                            "breakpointDetails": {}
                        }
                    
                    # Add this breakpoint to the affected breakpoints
                    issues_by_type["warnings"][issue_key]["elements"][element_id]["breakpoints"].append(breakpoint)
                    
                    # Add breakpoint-specific details for content overlap
                    if "overlapping" in warning:
                        overlap_count = len(warning.get("overlapping", []))
                        
                        # Calculate worst coverage
                        worst_coverage = 0
                        for overlap in warning.get("overlapping", []):
                            if "overlapPercentage" in overlap and "horizontal" in overlap["overlapPercentage"]:
                                if overlap["overlapPercentage"]["horizontal"] is not None:
                                    worst_coverage = max(worst_coverage, overlap["overlapPercentage"]["horizontal"])
                        
                        issues_by_type["warnings"][issue_key]["elements"][element_id]["breakpointDetails"][breakpoint] = {
                            "count": overlap_count,
                            "worstCoverage": round(worst_coverage, 2)
                        }
        
        # Remove empty issue types and count elements affected
        for issue_category in list(issues_by_type.keys()):
            for issue_type in list(issues_by_type[issue_category].keys()):
                if not issues_by_type[issue_category][issue_type]["elements"]:
                    del issues_by_type[issue_category][issue_type]
                else:
                    # Add count of affected elements
                    issues_by_type[issue_category][issue_type]["count"] = len(issues_by_type[issue_category][issue_type]["elements"])
                    
                    # Convert elements dict to list for better presentation
                    elements_list = []
                    for element_id, element_data in issues_by_type[issue_category][issue_type]["elements"].items():
                        # Sort and deduplicate breakpoints
                        element_data["breakpoints"] = sorted(list(set(element_data["breakpoints"])), 
                                                            key=lambda x: int(x) if x.isdigit() else 0)
                        
                        # Add breakpoint range for convenience
                        if len(element_data["breakpoints"]) > 1:
                            min_bp = min([int(bp) for bp in element_data["breakpoints"]])
                            max_bp = max([int(bp) for bp in element_data["breakpoints"]])
                            element_data["breakpointRange"] = f"{min_bp}px to {max_bp}px"
                        elif len(element_data["breakpoints"]) == 1:
                            element_data["breakpointRange"] = f"{element_data['breakpoints'][0]}px"
                        else:
                            element_data["breakpointRange"] = "No breakpoints affected"
                        
                        # Add summary statistics for hidden interactive content
                        if issue_type == "hiddenInteractiveContent":
                            element_data["hiddenElementsSummary"] = {
                                "totalCount": max([details["count"] for bp, details in element_data["breakpointDetails"].items()], default=0),
                                "worstCoveragePercent": round(max([details["worstCoverage"] for bp, details in element_data["breakpointDetails"].items()], default=0), 2),
                                "directInteractive": max([details["directInteractive"] for bp, details in element_data["breakpointDetails"].items()], default=0),
                                "containsInteractive": max([details["containsInteractive"] for bp, details in element_data["breakpointDetails"].items()], default=0)
                            }
                        
                        # Add summary statistics for content overlap
                        if issue_type == "contentOverlap":
                            element_data["overlappingSummary"] = {
                                "totalCount": max([details["count"] for bp, details in element_data["breakpointDetails"].items()], default=0),
                                "worstCoveragePercent": round(max([details["worstCoverage"] for bp, details in element_data["breakpointDetails"].items()], default=0), 2)
                            }
                        
                        elements_list.append(element_data)
                    
                    issues_by_type[issue_category][issue_type]["elements"] = elements_list
            
            # Remove empty categories
            if not any(issues_by_type[issue_category].values()):
                del issues_by_type[issue_category]
        
        # Count total issues and affected elements
        total_issues = sum([len(category) for category in issues_by_type.values()])
        total_elements = sum([sum([issue_type["count"] for issue_type in category.values()]) 
                             for category in issues_by_type.values()])
        
        # Count critical and moderate issues
        critical_issues = 0
        moderate_issues = 0
        
        for category in issues_by_type.values():
            for issue_type, issue_data in category.items():
                if issue_data["severity"] == "critical":
                    critical_issues += issue_data["count"]
                elif issue_data["severity"] == "moderate":
                    moderate_issues += issue_data["count"]
        
        # Generate summary
        summary = {
            "testedBreakpoints": len(set(all_breakpoints)),
            "uniqueDialogs": len(all_dialogs),
            "totalIssues": total_issues,
            "totalAffectedElements": total_elements,
            "criticalIssues": critical_issues,
            "moderateIssues": moderate_issues,
            "breakpointsTested": sorted(list(set(all_breakpoints)), key=lambda x: int(x) if x.isdigit() else 0),
            # Add information about documentation
            "documentation": {
                "available": True,
                "fields": ["testDescription", "methodology", "wcagReferences", "violationTypes", "warningTypes", "fieldDefinitions", "bestPractices"],
                "location": "in the documentation property of the dialogs object"
            }
        }
        
        # Prepare the final consolidated result
        return {
            "summary": summary,
            "issuesByType": issues_by_type
        }
        
    except Exception as e:
        print(f"ERROR in consolidate_results: {str(e)}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "summary": {
                "testedBreakpoints": 0,
                "uniqueDialogs": 0,
                "totalIssues": 0,
                "totalAffectedElements": 0,
                "criticalIssues": 0,
                "moderateIssues": 0
            }
        }

def generate_documentation():
    """
    Generate comprehensive documentation about the test, methodology, and result fields
    to make the results self-documenting.
    """
    return {
        "testDescription": {
            "name": "Floating Dialog Accessibility Test",
            "version": "2.0",
            "purpose": "Evaluates floating dialogs and modal windows for accessibility compliance across responsive breakpoints",
            "capabilities": [
                "Detects floating dialogs visible on page load",
                "Tests dialogs across all responsive breakpoints",
                "Evaluates content hiding and keyboard accessibility issues",
                "Checks close button focus management",
                "Identifies proper heading structure",
                "Validates dialog behaviors against WCAG requirements"
            ]
        },
        "methodology": {
            "overview": "This test evaluates floating dialogs across multiple viewport sizes to ensure accessibility in responsive designs",
            "steps": [
                "Extract CSS breakpoints from stylesheets",
                "Test each responsive breakpoint",
                "Identify visible floating dialogs (modal windows, cookie notices, etc.)",
                "Analyze dialog structure and properties",
                "Detect content overlap and hidden interactive elements",
                "Evaluate close button focus management",
                "Check for proper headings and structure",
                "Consolidate results across breakpoints"
            ],
            "breakpointSelection": "Breakpoints are derived from the page's CSS media queries plus standard device sizes"
        },
        "wcagReferences": {
            "2.4.3": {
                "level": "A",
                "title": "Focus Order",
                "description": "If a webpage can be navigated sequentially and the navigation sequences affect meaning or operation, focusable components receive focus in an order that preserves meaning and operability.",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-order.html"
            },
            "2.4.7": {
                "level": "AA",
                "title": "Focus Visible",
                "description": "Any keyboard operable user interface has a mode of operation where the keyboard focus indicator is visible.",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/focus-visible.html"
            },
            "1.4.13": {
                "level": "AA",
                "title": "Content on Hover or Focus",
                "description": "Where receiving and then removing pointer hover or keyboard focus triggers additional content to become visible and then hidden, the following are true.",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/content-on-hover-or-focus.html"
            },
            "2.1.1": {
                "level": "A",
                "title": "Keyboard",
                "description": "All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes.",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/keyboard.html"
            },
            "2.1.2": {
                "level": "A",
                "title": "No Keyboard Trap",
                "description": "If keyboard focus can be moved to a component of the page using a keyboard interface, then focus can be moved away from that component using only a keyboard interface.",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/no-keyboard-trap.html"
            },
            "4.1.2": {
                "level": "A",
                "title": "Name, Role, Value",
                "description": "For all user interface components, the name and role can be programmatically determined; states, properties, and values can be programmatically set; and notification of changes to these items is available to user agents.",
                "url": "https://www.w3.org/WAI/WCAG21/Understanding/name-role-value.html"
            }
        },
        "violationTypes": {
            "incorrectHeadingLevel": {
                "description": "Dialogs should have a proper heading structure starting with a level 2 heading (h2).",
                "impact": "Screen reader users rely on heading structure to understand content organization.",
                "wcagCriteria": ["4.1.2"],
                "remediation": "Ensure the dialog has a prominent h2 element or an element with role='heading' and aria-level='2'."
            },
            "missingCloseButton": {
                "description": "Dialogs need an accessible close button for keyboard users to dismiss the dialog.",
                "impact": "Keyboard-only users may become trapped in the dialog with no way to exit.",
                "wcagCriteria": ["2.1.1", "2.1.2"],
                "remediation": "Add a visible, clearly labeled close button that can be activated by keyboard."
            },
            "improperFocusManagement": {
                "description": "When a dialog is closed, focus should return to an appropriate element, typically the element that opened the dialog or a logical location in the page.",
                "impact": "Screen reader and keyboard users may lose their place in the page when dialogs are closed.",
                "wcagCriteria": ["2.4.3", "2.4.7"],
                "remediation": "Implement proper focus management by moving focus to a logical element (usually at the top of the page) when the dialog closes."
            },
            "hiddenInteractiveContent": {
                "description": "Interactive elements should not be obscured by floating dialogs as they become inaccessible.",
                "impact": "Users cannot interact with obscured elements, breaking functionality of the page.",
                "wcagCriteria": ["2.1.1", "1.4.13"],
                "remediation": "Ensure dialogs don't overlap interactive elements, or make the dialog modal with proper focus management."
            }
        },
        "warningTypes": {
            "contentOverlap": {
                "description": "Dialogs overlap with non-interactive page content.",
                "impact": "Visual content may be hidden from users, though functionality is not affected.",
                "remediation": "Implement modal dialogs that separate dialog content from page content, or position floating elements to minimize content overlap."
            }
        },
        "fieldDefinitions": {
            "breakpoints": "Array of viewport widths (in pixels) tested during the analysis",
            "consolidated": {
                "description": "Aggregated results across all tested breakpoints",
                "summary": {
                    "testedBreakpoints": "Number of responsive breakpoints tested",
                    "uniqueDialogs": "Number of distinct floating dialogs found on the page",
                    "totalIssues": "Total number of accessibility issues found",
                    "criticalIssues": "Number of critical severity issues that directly impact usability",
                    "moderateIssues": "Number of moderate severity issues that may affect some users"
                },
                "issuesByType": "Issues organized by type and severity with affected elements"
            },
            "closeButtonAnalysis": {
                "description": "Analysis of dialog close buttons and their focus management",
                "fields": {
                    "hasCloseButton": "Whether a close button was found in the dialog",
                    "closeButtons": "List of close buttons with their properties",
                    "focusManagement": {
                        "description": "Analysis of where focus moves when the dialog closes",
                        "fields": {
                            "analyzed": "Whether focus management could be analyzed",
                            "hasEventListeners": "Whether the button has detectable event handlers",
                            "willMoveFocus": "Whether focus will likely move when the dialog closes",
                            "targetIsValid": "Whether the focus target is a valid accessible element",
                            "focusViolation": "Whether a focus management violation was detected",
                            "violationReason": "Description of the focus management issue",
                            "potentialFocusTargets": "Potential elements that could receive focus"
                        }
                    }
                }
            },
            "dialogHasFocusTrap": {
                "description": "Analysis of whether the dialog implements a focus trap",
                "fields": {
                    "hasAriaModal": "Whether the dialog has aria-modal='true'",
                    "hasCommonTrapClasses": "Whether the dialog has classes that suggest a focus trap",
                    "hasTrapElements": "Whether the dialog has elements that implement a focus trap",
                    "likelyHasFocusTrap": "Whether the dialog likely implements a focus trap based on the above"
                }
            }
        },
        "bestPractices": {
            "dialogImplementation": [
                "Use native <dialog> element or add role='dialog' or role='alertdialog'",
                "Include aria-modal='true' for modal dialogs",
                "Start dialog content with a heading level 2 (h2)",
                "Provide a visible close button with clear labeling",
                "Implement a focus trap for modal dialogs",
                "Return focus to the triggering element or logical location when closed",
                "Ensure all dialog content is accessible via keyboard navigation"
            ],
            "focusManagement": [
                "When a dialog closes, focus should move to a logical location",
                "For dialogs present on page load, focus should move to the top of the page when closed",
                "Use tabindex='-1' on non-interactive elements that need to receive focus",
                "Ensure the focus target is visible and within the viewport"
            ]
        }
    }