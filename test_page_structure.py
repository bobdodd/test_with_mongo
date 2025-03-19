# test_page_structure.py
"""
Test module that analyzes page structure to identify common components
like headers, footers, navigation, and other repeated content.
"""
import json
from datetime import datetime

async def test_page_structure(page):
    """
    Analyze the structure of the page to identify header, footer, and other
    repeated components.
    
    Args:
        page: The Puppeteer page object
        
    Returns:
        Dictionary containing structural analysis results
    """
    print("Analyzing page structure...")
    
    # Get the page structure using client-side JS
    structure_data = await page.evaluate('''() => {
        function analyzePageStructure() {
            // Get viewport dimensions
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            
            // Helper function to get computed styles safely
            function getComputedStyleSafe(element, property) {
                try {
                    const style = window.getComputedStyle(element);
                    return style[property];
                } catch(e) {
                    return null;
                }
            }
            
            // Element detail extraction function
            function getElementDetails(element, includeChildren = false, depth = 0) {
                if (!element || !element.tagName) return null;
                
                // Basic info
                const rect = element.getBoundingClientRect();
                const details = {
                    tag: element.tagName.toLowerCase(),
                    id: element.id || null,
                    className: element.className || null,
                    position: getComputedStyleSafe(element, 'position'),
                    accessibleName: element.getAttribute('aria-label') || 
                                   element.getAttribute('title') || 
                                   element.textContent.trim().substring(0, 50) || null,
                    size: {
                        width: rect.width,
                        height: rect.height
                    },
                    location: {
                        top: rect.top,
                        left: rect.left,
                        bottom: rect.bottom,
                        right: rect.right
                    },
                    isFixed: getComputedStyleSafe(element, 'position') === 'fixed',
                    isSticky: getComputedStyleSafe(element, 'position') === 'sticky',
                    zIndex: getComputedStyleSafe(element, 'zIndex'),
                    xpath: getXPath(element)
                };
                
                // Custom attributes for accessibility
                const role = element.getAttribute('role');
                if (role) details.role = role;
                
                // Get child elements if requested
                if (includeChildren && depth < 3) {
                    const childElements = Array.from(element.children || [])
                        .filter(child => {
                            // Only include visible elements
                            const style = window.getComputedStyle(child);
                            return style.display !== 'none' && style.visibility !== 'hidden';
                        });
                    
                    if (childElements.length > 0) {
                        details.children = childElements
                            .map(child => getElementDetails(child, true, depth + 1))
                            .filter(child => child !== null);
                    }
                }
                
                return details;
            }
            
            // Count all descendants of an element
            function countDescendants(element) {
                let count = 0;
                const children = element.children;
                if (children && children.length) {
                    count += children.length;
                    for (let i = 0; i < children.length; i++) {
                        count += countDescendants(children[i]);
                    }
                }
                return count;
            }
            
            // XPath generation function
            function getXPath(element) {
                if (!element) return null;
                
                try {
                    // Special case for HTML
                    if (element.tagName === 'HTML') return '/HTML[1]';
                    
                    // Use the document evaluate API to get an XPath
                    const getElementXPath = function(element) {
                        if (!element) return null;
                        if (element === document.body) return '/HTML[1]/BODY[1]';
                        
                        let ix = 0;
                        const siblings = element.parentNode.childNodes;
                        
                        for (let i = 0; i < siblings.length; i++) {
                            const sibling = siblings[i];
                            if (sibling === element) return getElementXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                            if (sibling.nodeType === 1 && sibling.tagName === element.tagName) ix++;
                        }
                    };
                    
                    return getElementXPath(element);
                } catch (e) {
                    return null;
                }
            }
            
            // Find header candidates
            function findHeaderCandidates() {
                const candidates = [];
                
                // By tag
                const headerTags = document.querySelectorAll('header');
                headerTags.forEach(element => {
                    candidates.push({
                        element,
                        reason: 'Semantic header tag',
                        priority: 10,
                        complexityScore: countDescendants(element),
                        interactiveElements: countInteractiveElements(element)
                    });
                });
                
                // By class/id
                const headerClassIds = document.querySelectorAll('[class*="header"], [id*="header"], [class*="masthead"], [id*="masthead"]');
                headerClassIds.forEach(element => {
                    // Don't duplicate entries from headerTags
                    if (element.tagName.toLowerCase() !== 'header') {
                        candidates.push({
                            element,
                            reason: 'Header class/id pattern',
                            priority: 8,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By position - elements at the top that span most of the width
                Array.from(document.querySelectorAll('div, nav, section'))
                    .filter(element => {
                        const rect = element.getBoundingClientRect();
                        // Top of the page, wide, and not too tall
                        return rect.top < 150 && rect.width > viewportWidth * 0.8 && rect.height < viewportHeight * 0.3;
                    })
                    .forEach(element => {
                        // Check if this element or its parent is already in candidates
                        const isNew = !candidates.some(candidate => 
                            candidate.element === element || element.contains(candidate.element) || candidate.element.contains(element)
                        );
                        
                        if (isNew) {
                            candidates.push({
                                element,
                                reason: 'Top positioning',
                                priority: 6,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // By sticky/fixed position
                Array.from(document.querySelectorAll('*'))
                    .filter(element => {
                        const position = getComputedStyleSafe(element, 'position');
                        const rect = element.getBoundingClientRect();
                        return (position === 'fixed' || position === 'sticky') && 
                               rect.top < 100 && rect.width > viewportWidth * 0.5;
                    })
                    .forEach(element => {
                        candidates.push({
                            element,
                            reason: 'Fixed/sticky position at top',
                            priority: 7,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    });
                
                // Sort by priority and return detailed info
                return candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
            }
            
            // Count interactive elements within a container
            function countInteractiveElements(element) {
                return {
                    links: element.querySelectorAll('a').length,
                    buttons: element.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                    inputs: element.querySelectorAll('input:not([type="button"]):not([type="submit"]), select, textarea').length,
                    images: element.querySelectorAll('img, svg').length
                };
            }
            
            // Find footer candidates
            function findFooterCandidates() {
                const candidates = [];
                
                // By tag
                const footerTags = document.querySelectorAll('footer');
                footerTags.forEach(element => {
                    candidates.push({
                        element,
                        reason: 'Semantic footer tag',
                        priority: 10,
                        complexityScore: countDescendants(element),
                        interactiveElements: countInteractiveElements(element)
                    });
                });
                
                // By class/id
                const footerClassIds = document.querySelectorAll('[class*="footer"], [id*="footer"]');
                footerClassIds.forEach(element => {
                    // Don't duplicate entries from footerTags
                    if (element.tagName.toLowerCase() !== 'footer') {
                        candidates.push({
                            element,
                            reason: 'Footer class/id pattern',
                            priority: 8,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By position - elements at the bottom that span most of the width
                Array.from(document.querySelectorAll('div, section'))
                    .filter(element => {
                        const rect = element.getBoundingClientRect();
                        // Must be visible in viewport to be considered
                        if (rect.bottom < 0 || rect.top > viewportHeight) return false;
                        
                        // Get distance from bottom of the document
                        const docHeight = document.documentElement.scrollHeight;
                        const fromBottom = docHeight - (window.scrollY + rect.bottom);
                        
                        // Bottom of the page, wide, and not too tall
                        return fromBottom < 200 && rect.width > viewportWidth * 0.8 && rect.height < viewportHeight * 0.5;
                    })
                    .forEach(element => {
                        // Check if this element or its parent is already in candidates
                        const isNew = !candidates.some(candidate => 
                            candidate.element === element || element.contains(candidate.element) || candidate.element.contains(element)
                        );
                        
                        if (isNew) {
                            candidates.push({
                                element,
                                reason: 'Bottom positioning',
                                priority: 6,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // Sort by priority and return detailed info
                return candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
            }
            
            // Find main navigation
            function findMainNavigation() {
                const candidates = [];
                
                // By semantic tags and roles
                const navElements = document.querySelectorAll('nav, [role="navigation"]');
                navElements.forEach(element => {
                    candidates.push({
                        element,
                        reason: 'Semantic navigation element',
                        priority: 9,
                        complexityScore: countDescendants(element),
                        interactiveElements: countInteractiveElements(element)
                    });
                });
                
                // By class/id patterns
                const navClassIds = document.querySelectorAll(
                    '[class*="nav-"], [id*="nav-"], [class*="menu"], [id*="menu"], ' +
                    '[class*="navigation"], [id*="navigation"]'
                );
                navClassIds.forEach(element => {
                    // Skip if already found by semantic tag
                    if (element.tagName.toLowerCase() !== 'nav' && !element.hasAttribute('role')) {
                        candidates.push({
                            element,
                            reason: 'Navigation class/id pattern',
                            priority: 7,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By link grouping
                Array.from(document.querySelectorAll('ul, ol, div'))
                    .filter(element => {
                        // Must contain multiple links to be considered navigation
                        const links = element.querySelectorAll('a');
                        return links.length >= 4 && links.length <= 20;
                    })
                    .forEach(element => {
                        // Skip if already found by other methods
                        const alreadyFound = candidates.some(candidate => 
                            candidate.element === element || 
                            candidate.element.contains(element) || 
                            element.contains(candidate.element)
                        );
                        
                        if (!alreadyFound) {
                            candidates.push({
                                element,
                                reason: 'Link grouping pattern',
                                priority: 5,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // Sort by priority and return detailed info
                return candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
            }
            
            // Find main content
            function findMainContent() {
                const candidates = [];
                
                // By semantic tag and role
                const mainElements = document.querySelectorAll('main, [role="main"]');
                mainElements.forEach(element => {
                    candidates.push({
                        element,
                        reason: 'Semantic main element',
                        priority: 10,
                        complexityScore: countDescendants(element),
                        interactiveElements: countInteractiveElements(element)
                    });
                });
                
                // By class/id patterns
                const mainClassIds = document.querySelectorAll('[class*="main"], [id*="main"], [class*="content"], [id*="content"]');
                mainClassIds.forEach(element => {
                    // Skip if already found by semantic tag
                    if (element.tagName.toLowerCase() !== 'main' && !element.getAttribute('role') === 'main') {
                        candidates.push({
                            element,
                            reason: 'Main class/id pattern',
                            priority: 7,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By content size and position
                const possibleContent = Array.from(document.querySelectorAll('article, section, div'))
                    .filter(element => {
                        const rect = element.getBoundingClientRect();
                        
                        // Must be visible with reasonable size
                        if (rect.width < 200 || rect.height < 200) return false;
                        
                        // Get text content length
                        const textLength = element.textContent.trim().length;
                        
                        // Must be positioned in the middle with significant content
                        return rect.top > 100 && 
                               rect.left < viewportWidth * 0.3 &&
                               rect.width > viewportWidth * 0.5 &&
                               textLength > 500; // Look for substantial text content
                    });
                
                possibleContent.forEach(element => {
                    // Check for overlap with existing candidates
                    const isNew = !candidates.some(candidate => 
                        candidate.element === element || 
                        candidate.element.contains(element) || 
                        element.contains(candidate.element)
                    );
                    
                    if (isNew) {
                        candidates.push({
                            element,
                            reason: 'Content positioning and size',
                            priority: 5,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // Sort by priority and return detailed info
                return candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
            }
            
            // Find complementary content (asides, sidebars)
            function findComplementaryContent() {
                const candidates = [];
                
                // By semantic tag and role
                const asideElements = document.querySelectorAll('aside, [role="complementary"]');
                asideElements.forEach(element => {
                    candidates.push({
                        element,
                        reason: 'Semantic complementary element',
                        priority: 10,
                        complexityScore: countDescendants(element),
                        interactiveElements: countInteractiveElements(element)
                    });
                });
                
                // By class/id patterns
                const sidebarClassIds = document.querySelectorAll(
                    '[class*="sidebar"], [id*="sidebar"], [class*="aside"], [id*="aside"], ' +
                    '[class*="secondary"], [id*="secondary"]'
                );
                sidebarClassIds.forEach(element => {
                    // Skip if already found by semantic tag
                    if (element.tagName.toLowerCase() !== 'aside' && !element.getAttribute('role') === 'complementary') {
                        candidates.push({
                            element,
                            reason: 'Sidebar class/id pattern',
                            priority: 7,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By positioning (elements on the sides with smaller width)
                const possibleSidebars = Array.from(document.querySelectorAll('div, section'))
                    .filter(element => {
                        const rect = element.getBoundingClientRect();
                        
                        // Must be visible with reasonable size
                        if (rect.width < 100 || rect.height < 200) return false;
                        
                        // Either left or right positioned, not spanning most of the width
                        return (rect.top > 100 && rect.height > 300) && 
                               ((rect.left < 20 && rect.width < viewportWidth * 0.3) || 
                                (rect.right > viewportWidth - 20 && rect.width < viewportWidth * 0.3));
                    });
                
                possibleSidebars.forEach(element => {
                    // Check for overlap with existing candidates
                    const isNew = !candidates.some(candidate => 
                        candidate.element === element || 
                        candidate.element.contains(element) || 
                        element.contains(candidate.element)
                    );
                    
                    if (isNew) {
                        candidates.push({
                            element,
                            reason: 'Sidebar positioning',
                            priority: 5,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // Sort by priority and return detailed info
                return candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
            }
            
            // Find forms
            function findForms() {
                const forms = [];
                
                // Find all form elements
                document.querySelectorAll('form, [role="form"]').forEach(formElement => {
                    const rect = formElement.getBoundingClientRect();
                    
                    // Skip invisible forms
                    if (rect.width === 0 || rect.height === 0) return;
                    
                    // Get form details
                    const formDetails = {
                        element: formElement,
                        details: getElementDetails(formElement, false),  // Don't include all children to avoid huge objects
                        inputs: [],
                        buttons: [],
                        location: 'unknown',
                        hasSubmit: false,
                        formType: 'unknown'
                    };
                    
                    // Count inputs by type
                    const inputTypes = {};
                    formElement.querySelectorAll('input, select, textarea').forEach(input => {
                        const type = input.type || input.tagName.toLowerCase();
                        inputTypes[type] = (inputTypes[type] || 0) + 1;
                        
                        // Store basic info about each input
                        formDetails.inputs.push({
                            type: type,
                            name: input.name || null,
                            id: input.id || null,
                            hasLabel: !!input.labels?.length || 
                                     !!document.querySelector(`label[for="${input.id}"]`)
                        });
                    });
                    
                    // Count buttons
                    formElement.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(button => {
                        formDetails.buttons.push({
                            type: button.type || button.tagName.toLowerCase(),
                            text: button.textContent?.trim() || button.value || null
                        });
                        
                        if (button.type === 'submit' || button.getAttribute('type') === 'submit') {
                            formDetails.hasSubmit = true;
                        }
                    });
                    
                    // Determine form location
                    if (formElement.closest('header, .header, #header')) {
                        formDetails.location = 'header';
                    } else if (formElement.closest('footer, .footer, #footer')) {
                        formDetails.location = 'footer';
                    } else if (formElement.closest('aside, [role="complementary"], .sidebar, #sidebar')) {
                        formDetails.location = 'complementary';
                    } else if (formElement.closest('main, [role="main"], .content, #content')) {
                        formDetails.location = 'main';
                    }
                    
                    // Try to determine form type based on inputs and content
                    formDetails.formType = determineFormType(formElement, inputTypes);
                    
                    // Calculate unique identifier for deduplication
                    formDetails.fingerprint = generateFormFingerprint(formElement, inputTypes);
                    
                    forms.push(formDetails);
                });
                
                return forms;
            }
            
            function determineFormType(formElement, inputTypes) {
                // Determine form type based on inputs and content
                const formText = formElement.textContent.toLowerCase();
                const inputNames = Array.from(formElement.querySelectorAll('[name]'))
                    .map(el => el.name.toLowerCase());
                
                // Check for search form
                if (inputTypes['search'] || 
                    formElement.querySelector('[type="search"]') ||
                    formText.includes('search') ||
                    inputNames.some(name => name.includes('search') || name.includes('query'))) {
                    return 'search';
                }
                
                // Check for login form
                if (inputTypes['password'] || 
                    formText.includes('login') || 
                    formText.includes('sign in') ||
                    inputNames.some(name => name.includes('password') || name.includes('username'))) {
                    return 'login';
                }
                
                // Check for newsletter/signup
                if (formText.includes('subscribe') || 
                    formText.includes('newsletter') ||
                    inputNames.some(name => name.includes('subscribe') || name.includes('newsletter'))) {
                    return 'newsletter';
                }
                
                // Check for contact form
                if (formText.includes('contact') || 
                    formText.includes('message') ||
                    inputNames.some(name => name.includes('contact') || name.includes('message'))) {
                    return 'contact';
                }
                
                // Default to generic
                return 'generic';
            }
            
            function generateFormFingerprint(formElement, inputTypes) {
                // Create a unique fingerprint for the form to help with deduplication
                const inputTypeKeys = Object.keys(inputTypes).sort().join('-');
                const buttonCount = formElement.querySelectorAll('button, input[type="submit"], input[type="button"]').length;
                const fieldCount = formElement.querySelectorAll('input, select, textarea').length;
                
                // Get form attributes that help identify it
                const id = formElement.id || '';
                const className = formElement.className || '';
                const action = formElement.getAttribute('action') || '';
                
                // Combine factors into a fingerprint
                return `${inputTypeKeys}-${fieldCount}-${buttonCount}-${id}-${className}-${action}`.substring(0, 100);
            }
            
            // Find additional common UI components
            function findCommonUIComponents() {
                return {
                    // Search components
                    search: Array.from(document.querySelectorAll('form, [role="search"], [id*="search"], [class*="search"]'))
                        .map(element => getElementDetails(element, true)),
                    
                    // Social media links/sharing
                    socialMedia: Array.from(document.querySelectorAll(
                        '[class*="social"], [id*="social"], [aria-label*="social"], ' +
                        '[class*="share"], [id*="share"], [aria-label*="share"]'
                    )).map(element => getElementDetails(element, true)),
                    
                    // Cookie notices and similar popups
                    notices: Array.from(document.querySelectorAll(
                        '[class*="cookie"], [id*="cookie"], [aria-label*="cookie"], ' +
                        '[class*="notice"], [id*="notice"], [aria-label*="notice"], ' +
                        '[class*="consent"], [id*="consent"], [aria-label*="consent"]'
                    )).map(element => getElementDetails(element, true)),
                    
                    // Sidebars
                    sidebars: Array.from(document.querySelectorAll(
                        'aside, [role="complementary"], [class*="sidebar"], [id*="sidebar"]'
                    )).map(element => getElementDetails(element, true))
                };
            }
            
            // Find recurring elements across pages
            function findRecurringElements() {
                return {
                    chatbots: Array.from(document.querySelectorAll(
                        '[class*="chat"], [id*="chat"], [aria-label*="chat"], ' +
                        '[class*="bot"], [id*="bot"], [aria-label*="bot"], ' +
                        '[class*="assistant"], [id*="assistant"]'
                    )).map(element => getElementDetails(element, true)),
                    
                    cookieNotices: Array.from(document.querySelectorAll(
                        '[class*="cookie"], [id*="cookie"], [aria-label*="cookie"], ' +
                        '[class*="notice"], [id*="notice"], [class*="consent"], [id*="consent"], ' +
                        '[class*="gdpr"], [id*="gdpr"]'
                    )).map(element => getElementDetails(element, true)),
                    
                    newsletters: Array.from(document.querySelectorAll(
                        '[class*="newsletter"], [id*="newsletter"], [aria-label*="newsletter"], ' +
                        '[class*="subscribe"], [id*="subscribe"], [aria-label*="subscribe"]'
                    )).map(element => getElementDetails(element, true)),
                    
                    popups: Array.from(document.querySelectorAll(
                        '[class*="popup"], [id*="popup"], [class*="modal"], [id*="modal"], ' +
                        '[role="dialog"], [role="alertdialog"]'
                    )).map(element => getElementDetails(element, true)),
                    
                    forms: Array.from(document.querySelectorAll(
                        'form, [role="form"]'
                    )).map(element => getElementDetails(element, true))
                };
            }
            
            return {
                url: window.location.href,
                viewport: {
                    width: viewportWidth,
                    height: viewportHeight
                },
                structure: {
                    header: findHeaderCandidates(),
                    footer: findFooterCandidates(),
                    navigation: findMainNavigation(),
                    mainContent: findMainContent(),
                    complementaryContent: findComplementaryContent(),
                    commonComponents: findCommonUIComponents(),
                    recurringElements: findRecurringElements(),
                    forms: findForms()
                },
                metadata: {
                    timestamp: new Date().toISOString(),
                    userAgent: navigator.userAgent
                }
            };
        }
        
        return analyzePageStructure();
    }''')
    
    # Process the data for summary information
    summary = {
        'header': {
            'found': len(structure_data['structure']['header']) > 0,
            'count': len(structure_data['structure']['header']),
            'types': [item['reason'] for item in structure_data['structure']['header']]
        },
        'footer': {
            'found': len(structure_data['structure']['footer']) > 0,
            'count': len(structure_data['structure']['footer']),
            'types': [item['reason'] for item in structure_data['structure']['footer']]
        },
        'navigation': {
            'found': len(structure_data['structure']['navigation']) > 0,
            'count': len(structure_data['structure']['navigation']),
            'types': [item['reason'] for item in structure_data['structure']['navigation']]
        },
        'mainContent': {
            'found': len(structure_data['structure']['mainContent']) > 0,
            'count': len(structure_data['structure']['mainContent']),
            'types': [item['reason'] for item in structure_data['structure']['mainContent']]
        },
        'complementaryContent': {
            'found': len(structure_data['structure']['complementaryContent']) > 0,
            'count': len(structure_data['structure']['complementaryContent']),
            'types': [item['reason'] for item in structure_data['structure']['complementaryContent']]
        },
        'components': {
            'search': len(structure_data['structure']['commonComponents']['search']) > 0,
            'socialMedia': len(structure_data['structure']['commonComponents']['socialMedia']) > 0,
            'notices': len(structure_data['structure']['commonComponents']['notices']) > 0,
            'sidebars': len(structure_data['structure']['commonComponents']['sidebars']) > 0
        },
        'recurringElements': {
            'chatbots': len(structure_data['structure']['recurringElements']['chatbots']) > 0,
            'cookieNotices': len(structure_data['structure']['recurringElements']['cookieNotices']) > 0,
            'newsletters': len(structure_data['structure']['recurringElements']['newsletters']) > 0,
            'popups': len(structure_data['structure']['recurringElements']['popups']) > 0,
            'forms': len(structure_data['structure']['recurringElements']['forms']) > 0
        },
        'forms': {
            'count': len(structure_data['structure']['forms']),
            'types': {}
        }
    }
    
    # Count form types
    for form in structure_data['structure']['forms']:
        form_type = form.get('formType', 'unknown')
        if form_type not in summary['forms']['types']:
            summary['forms']['types'][form_type] = 0
        summary['forms']['types'][form_type] += 1
    
    # Extract key elements for easier analysis
    key_elements = {
        'header': structure_data['structure']['header'][0]['details'] if structure_data['structure']['header'] else None,
        'footer': structure_data['structure']['footer'][0]['details'] if structure_data['structure']['footer'] else None,
        'navigation': structure_data['structure']['navigation'][0]['details'] if structure_data['structure']['navigation'] else None,
        'mainContent': structure_data['structure']['mainContent'][0]['details'] if structure_data['structure']['mainContent'] else None,
        'complementaryContent': structure_data['structure']['complementaryContent'][0]['details'] if structure_data['structure']['complementaryContent'] else None
    }
    
    # Extract complexity data
    complexity_data = {
        'header': structure_data['structure']['header'][0].get('complexityScore', 0) if structure_data['structure']['header'] else 0,
        'footer': structure_data['structure']['footer'][0].get('complexityScore', 0) if structure_data['structure']['footer'] else 0,
        'navigation': structure_data['structure']['navigation'][0].get('complexityScore', 0) if structure_data['structure']['navigation'] else 0,
        'mainContent': structure_data['structure']['mainContent'][0].get('complexityScore', 0) if structure_data['structure']['mainContent'] else 0,
        'complementaryContent': structure_data['structure']['complementaryContent'][0].get('complexityScore', 0) if structure_data['structure']['complementaryContent'] else 0
    }
    
    # Extract interactive elements data
    interactive_elements = {
        'header': structure_data['structure']['header'][0].get('interactiveElements', {}) if structure_data['structure']['header'] else {},
        'footer': structure_data['structure']['footer'][0].get('interactiveElements', {}) if structure_data['structure']['footer'] else {},
        'navigation': structure_data['structure']['navigation'][0].get('interactiveElements', {}) if structure_data['structure']['navigation'] else {},
        'mainContent': structure_data['structure']['mainContent'][0].get('interactiveElements', {}) if structure_data['structure']['mainContent'] else {},
        'complementaryContent': structure_data['structure']['complementaryContent'][0].get('interactiveElements', {}) if structure_data['structure']['complementaryContent'] else {}
    }
    
    # Create page flags for key structural findings
    page_flags = {
        'hasHeader': summary['header']['found'],
        'hasFooter': summary['footer']['found'],
        'hasMainNavigation': summary['navigation']['found'],
        'hasMainContent': summary['mainContent']['found'],
        'hasComplementaryContent': summary['complementaryContent']['found'],
        'hasSearchComponent': summary['components']['search'],
        'hasSocialMediaLinks': summary['components']['socialMedia'],
        'hasCookieNotice': summary['components']['notices'],
        'hasSidebars': summary['components']['sidebars'],
        'hasChatbot': summary['recurringElements']['chatbots'],
        'hasNewsletterSignup': summary['recurringElements']['newsletters'],
        'hasPopups': summary['recurringElements']['popups'],
        'hasForms': summary['recurringElements']['forms'],
        'hasFormsCount': summary['forms']['count']
    }
    
    # Return complete test results
    return {
        'page_structure': {
            'timestamp': datetime.now().isoformat(),
            'url': structure_data['url'],
            'viewport': structure_data['viewport'],
            'pageFlags': page_flags,
            'summary': summary,
            'keyElements': key_elements,
            'complexityData': complexity_data,
            'interactiveElements': interactive_elements,
            'fullStructure': structure_data['structure']
        }
    }