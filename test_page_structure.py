# test_page_structure.py
"""
Test module that analyzes page structure to identify common components
like headers, footers, navigation, and other repeated content.

Improvements:
- Enhanced header and footer detection with multiple recognition strategies
- Detection of multiple instances of headers/footers on a single page
- Better analysis of common content blocks across pages
- Improved structure fingerprinting for cross-page comparison
- More detailed analysis of element relationships and containment
"""


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
    "testName": "Page Structure Analysis",
    "description": "Evaluates the structural organization of web pages to identify key components like headers, footers, navigation menus, and content blocks. This test helps understand the overall page architecture and structural patterns.",
    "version": "2.1.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "url": "The URL of the page being analyzed",
        "viewport": "The dimensions of the browser viewport used for testing",
        "pageFlags": "Boolean flags indicating presence of key structural elements",
        "summary": "Aggregated statistics about the page structure",
        "keyElements": "Detailed information about primary structural elements",
        "complexityData": "Metrics on the complexity of different page regions",
        "interactiveElements": "Counts of interactive elements in different page regions",
        "fullStructure": "Complete structural analysis data"
    },
    "tests": [
        {
            "id": "page-structure-header",
            "name": "Header Detection",
            "description": "Identifies and analyzes page headers using multiple detection strategies including semantic tags, ARIA roles, class/id patterns, logo detection, and positional analysis.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Implement a semantic header element with appropriate ARIA roles. Place the header at the top of the page and include site branding and main navigation.",
            "resultsFields": {
                "pageFlags.hasHeader": "Indicates if a primary header was found",
                "pageFlags.hasMultipleHeaders": "Indicates if multiple headers were detected",
                "pageFlags.hasSecondaryHeaders": "Indicates if secondary headers were found",
                "summary.header.count": "Total number of header elements detected",
                "summary.header.types": "Types of headers found using different detection methods",
                "keyElements.primaryHeader": "Details of the main header structure"
            }
        },
        {
            "id": "page-structure-footer",
            "name": "Footer Detection",
            "description": "Identifies and analyzes page footers using multiple detection strategies including semantic tags, ARIA roles, class/id patterns, copyright detection, and positional analysis.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Implement a semantic footer element with appropriate ARIA roles. Place the footer at the bottom of the page and include copyright information, site links, and other supplementary content.",
            "resultsFields": {
                "pageFlags.hasFooter": "Indicates if a primary footer was found",
                "pageFlags.hasMultipleFooters": "Indicates if multiple footers were detected",
                "pageFlags.hasSecondaryFooters": "Indicates if secondary footers were found",
                "summary.footer.count": "Total number of footer elements detected",
                "summary.footer.types": "Types of footers found using different detection methods",
                "keyElements.primaryFooter": "Details of the main footer structure"
            }
        },
        {
            "id": "page-structure-navigation",
            "name": "Navigation Detection",
            "description": "Identifies main navigation elements using semantic tags, ARIA roles, class/id patterns, and link grouping analysis.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1", "2.4.8"],
            "howToFix": "Implement navigation using semantic nav elements with appropriate ARIA roles. Ensure navigation is consistent across pages and accessible via keyboard.",
            "resultsFields": {
                "pageFlags.hasMainNavigation": "Indicates if main navigation was found",
                "summary.navigation.count": "Total number of navigation elements detected",
                "summary.navigation.types": "Types of navigation found using different detection methods",
                "keyElements.navigation": "Details of the main navigation structure"
            }
        },
        {
            "id": "page-structure-main-content",
            "name": "Main Content Detection",
            "description": "Identifies the main content area of the page using semantic tags, ARIA roles, class/id patterns, and content analysis.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Implement main content using a semantic main element with appropriate ARIA roles. Ensure main content is clearly identifiable and contains the primary page content.",
            "resultsFields": {
                "pageFlags.hasMainContent": "Indicates if main content was found",
                "summary.mainContent.count": "Total number of main content elements detected",
                "summary.mainContent.types": "Types of main content found using different detection methods",
                "keyElements.mainContent": "Details of the main content structure"
            }
        },
        {
            "id": "page-structure-complementary",
            "name": "Complementary Content Detection",
            "description": "Identifies complementary content areas like sidebars using semantic tags, ARIA roles, class/id patterns, and positional analysis.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Implement complementary content using semantic aside elements with appropriate ARIA roles. Use for content that supplements the main content but is not essential.",
            "resultsFields": {
                "pageFlags.hasComplementaryContent": "Indicates if complementary content was found",
                "pageFlags.hasSidebars": "Indicates if sidebars were detected",
                "summary.complementaryContent.count": "Total number of complementary content elements",
                "keyElements.complementaryContent": "Details of the complementary content structure"
            }
        },
        {
            "id": "page-structure-content-blocks",
            "name": "Content Block Detection",
            "description": "Identifies common content block patterns like hero sections, card grids, feature sections, and carousels.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Use appropriate semantic elements and ARIA roles for content blocks. Ensure consistent structure and accessible implementation for interactive components.",
            "resultsFields": {
                "pageFlags.hasHeroSection": "Indicates if hero sections were found",
                "pageFlags.hasCardGrids": "Indicates if card grid layouts were found",
                "pageFlags.hasFeatureSections": "Indicates if feature sections were found",
                "pageFlags.hasCarousels": "Indicates if carousels/sliders were found",
                "summary.contentBlocks": "Counts of different content block types"
            }
        },
        {
            "id": "page-structure-consistency",
            "name": "Structural Consistency Detection",
            "description": "Analyzes repetitive patterns and recurring elements to assess structural consistency within the page.",
            "impact": "medium",
            "wcagCriteria": ["3.2.3", "3.2.4"],
            "howToFix": "Maintain consistent navigation and identification of components across pages. Use templates consistently for repeated content patterns.",
            "resultsFields": {
                "pageFlags.hasRepetitivePatterns": "Indicates if repetitive patterns were found",
                "summary.repetitivePatterns.count": "Total number of repetitive patterns detected",
                "summary.repetitivePatterns.highConsistencyPatterns": "Number of highly consistent patterns"
            }
        },
        {
            "id": "page-structure-components",
            "name": "UI Component Detection",
            "description": "Identifies specialized UI components like search boxes, popups, cookie notices, and forms.",
            "impact": "medium",
            "wcagCriteria": ["2.4.3", "2.4.4", "3.2.1", "3.2.2"],
            "howToFix": "Implement UI components with appropriate ARIA roles and ensure they're keyboard accessible. Make forms clear and provide feedback on errors.",
            "resultsFields": {
                "pageFlags.hasSearchComponent": "Indicates if search functionality was found",
                "pageFlags.hasCookieNotice": "Indicates if cookie notices were found",
                "pageFlags.hasPopups": "Indicates if popups or modals were found",
                "pageFlags.hasForms": "Indicates if forms were found",
                "summary.components": "Status of different component types",
                "summary.forms": "Information about forms by type"
            }
        }
    ]
}
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
    structure_data = await page.evaluate('''
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
        
        {
        function analyzePageStructure() {
            // Get viewport dimensions
            const viewportHeight = window.innerHeight;
            const viewportWidth = window.innerWidth;
            const documentHeight = document.documentElement.scrollHeight;
            
            // Helper function to get computed styles safely
            function getComputedStyleSafe(element, property) {
                try {
                    const style = window.getComputedStyle(element);
                    return style[property];
                } catch(e) {
                    return null;
                }
            }
            
            // Helper function to check if element is visible
            function isElementVisible(element) {
                if (!element) return false;
                
                try {
                    const style = window.getComputedStyle(element);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           style.opacity !== '0' &&
                           element.offsetWidth > 0 &&
                           element.offsetHeight > 0;
                } catch (e) {
                    return false;
                }
            }
            
            // Element detail extraction function with enhanced information
            function getElementDetails(element, includeChildren = false, depth = 0, maxDepth = 3) {
                if (!element || !element.tagName) return null;
                
                // Basic info
                const rect = element.getBoundingClientRect();
                
                // Extract background and border styles for better visual region detection
                const background = getComputedStyleSafe(element, 'backgroundColor');
                const backgroundTransparent = background === 'rgba(0, 0, 0, 0)' || background === 'transparent';
                const hasBorder = getComputedStyleSafe(element, 'borderWidth') !== '0px';
                const boxShadow = getComputedStyleSafe(element, 'boxShadow');
                const hasBoxShadow = boxShadow && boxShadow !== 'none';
                
                // Extract classes as array for easier analysis
                const classArray = element.className ? 
                    element.className.split(' ').filter(c => c.trim().length > 0) : 
                    [];
                
                // Check for accessibility-specific attributes
                const ariaLabel = element.getAttribute('aria-label');
                const ariaLabelledby = element.getAttribute('aria-labelledby');
                const ariaDescribedby = element.getAttribute('aria-describedby');
                const role = element.getAttribute('role');
                
                // Get text content for this element only (not descendants)
                const textNodes = Array.from(element.childNodes)
                    .filter(node => node.nodeType === 3); // Text nodes only
                const ownTextContent = textNodes
                    .map(node => node.textContent.trim())
                    .filter(text => text.length > 0)
                    .join(' ');
                
                // Basic details
                const details = {
                    tag: element.tagName.toLowerCase(),
                    id: element.id || null,
                    className: element.className || null,
                    classArray: classArray,
                    position: getComputedStyleSafe(element, 'position'),
                    display: getComputedStyleSafe(element, 'display'),
                    accessibleName: ariaLabel || 
                                   element.getAttribute('title') || 
                                   ownTextContent.substring(0, 50) || null,
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
                    styles: {
                        background: background,
                        backgroundTransparent: backgroundTransparent,
                        hasBorder: hasBorder,
                        hasBoxShadow: hasBoxShadow,
                        zIndex: getComputedStyleSafe(element, 'zIndex')
                    },
                    isFixed: getComputedStyleSafe(element, 'position') === 'fixed',
                    isSticky: getComputedStyleSafe(element, 'position') === 'sticky',
                    isVisible: isElementVisible(element),
                    xpath: getXPath(element),
                    textSignature: generateTextSignature(element),
                    linkSignature: generateLinkSignature(element),
                    ownTextContent: ownTextContent
                };
                
                // Add accessibility attributes
                if (role) details.role = role;
                if (ariaLabel) details.ariaLabel = ariaLabel;
                if (ariaLabelledby) details.ariaLabelledby = ariaLabelledby;
                if (ariaDescribedby) details.ariaDescribedby = ariaDescribedby;
                
                // Get child elements if requested and not too deep
                if (includeChildren && depth < maxDepth) {
                    const childElements = Array.from(element.children || [])
                        .filter(child => isElementVisible(child));
                    
                    if (childElements.length > 0) {
                        details.children = childElements
                            .map(child => getElementDetails(child, true, depth + 1, maxDepth))
                            .filter(child => child !== null);
                        
                        // Create a simplified DOM structure for easier matching
                        details.childStructure = childElements
                            .map(child => child.tagName.toLowerCase())
                            .join(',');
                    }
                }
                
                return details;
            }
            
            // Generate a signature based on text content patterns
            function generateTextSignature(element) {
                if (!element) return null;
                
                try {
                    // Extract all text nodes from this element (not just direct children)
                    const texts = [];
                    const walker = document.createTreeWalker(
                        element, 
                        NodeFilter.SHOW_TEXT, 
                        null, 
                        false
                    );
                    
                    while(walker.nextNode()) {
                        const text = walker.currentNode.textContent.trim();
                        if (text) texts.push(text);
                    }
                    
                    // Join the first few text fragments to create a signature
                    // (truncate to avoid excessive memory usage)
                    return texts.slice(0, 5).join('|').substring(0, 100);
                } catch (e) {
                    return '';
                }
            }
            
            // Generate a signature based on link patterns
            function generateLinkSignature(element) {
                if (!element) return null;
                
                try {
                    // Extract href values from links
                    const links = Array.from(element.querySelectorAll('a'));
                    const hrefs = links.map(link => {
                        const href = link.getAttribute('href');
                        if (!href) return '';
                        
                        // Simplify URLs to base path
                        try {
                            const url = new URL(href, window.location.href);
                            return url.pathname.split('/').slice(0, 3).join('/');
                        } catch (e) {
                            return href.split('?')[0]; // Remove query parameters
                        }
                    }).filter(href => href);
                    
                    // Create a signature from link patterns (truncate to reasonable size)
                    return hrefs.slice(0, 10).join('|').substring(0, 200);
                } catch (e) {
                    return '';
                }
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
            
            // Count interactive elements within a container
            function countInteractiveElements(element) {
                return {
                    links: element.querySelectorAll('a').length,
                    buttons: element.querySelectorAll('button, input[type="button"], input[type="submit"]').length,
                    inputs: element.querySelectorAll('input:not([type="button"]):not([type="submit"]), select, textarea').length,
                    images: element.querySelectorAll('img, svg').length
                 };
            }
            
            // Find all header candidates with enhanced detection
            function findHeaderCandidates() {
                const candidates = [];
                
                // By semantic tag - highest priority
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
                
                // By ARIA role - also high priority
                const headerRoles = document.querySelectorAll('[role="banner"]');
                headerRoles.forEach(element => {
                    // Check if this is not already found via tag
                    if (element.tagName.toLowerCase() !== 'header') {
                        candidates.push({
                            element,
                            reason: 'ARIA banner role',
                            priority: 9,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By class/id naming patterns
                const headerClassIds = document.querySelectorAll(
                    '[class*="header"], [id*="header"], [class*="masthead"], [id*="masthead"], ' +
                    '[class*="site-header"], [id*="site-header"], [class*="main-header"], [id*="main-header"], ' +
                    '[class*="page-header"], [id*="page-header"], [class*="global-header"], [id*="global-header"]'
                );
                headerClassIds.forEach(element => {
                    // Check if not already found
                    if (element.tagName.toLowerCase() !== 'header' && !element.getAttribute('role') === 'banner') {
                        candidates.push({
                            element,
                            reason: 'Header class/id pattern',
                            priority: 8,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // Add logo detection - site logos are often in the header
                document.querySelectorAll('img, svg').forEach(element => {
                    // Check for logo in src, alt, or class attributes
                    const src = element.getAttribute('src') || '';
                    const alt = element.getAttribute('alt') || '';
                    const className = element.className || '';
                    
                    if (src.toLowerCase().includes('logo') || 
                        alt.toLowerCase().includes('logo') || 
                        className.toLowerCase().includes('logo')) {
                        
                        // Find the logo container - likely a parent element with reasonable size
                        let container = element;
                        let foundContainer = false;
                        
                        // Traverse up to find a suitable container (limit to 3 levels)
                        for (let i = 0; i < 3; i++) {
                            if (!container.parentElement) break;
                            container = container.parentElement;
                            
                            const rect = container.getBoundingClientRect();
                            if (rect.width > viewportWidth * 0.5 && rect.height > 40) {
                                foundContainer = true;
                                break;
                            }
                        }
                        
                        if (foundContainer && container.tagName.toLowerCase() !== 'body') {
                            // Check if this container isn't already in candidates
                            const isNew = !candidates.some(candidate => 
                                candidate.element === container || 
                                container.contains(candidate.element) || 
                                candidate.element.contains(container)
                            );
                            
                            if (isNew) {
                                candidates.push({
                                    element: container,
                                    reason: 'Contains site logo',
                                    priority: 7,
                                    complexityScore: countDescendants(container),
                                    interactiveElements: countInteractiveElements(container)
                                });
                            }
                        }
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
                        const isNew = !candidates.some(candidate => 
                            candidate.element === element || element.contains(candidate.element) || candidate.element.contains(element)
                        );
                        
                        if (isNew) {
                            candidates.push({
                                element,
                                reason: 'Fixed/sticky position at top',
                                priority: 7,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // By content analysis - look for common header patterns
                Array.from(document.querySelectorAll('div, section, nav'))
                    .filter(element => {
                        // Must be at top of page
                        const rect = element.getBoundingClientRect();
                        if (rect.top > 200) return false;
                        
                        // Check for header patterns: site navigation + branding elements
                        return element.querySelector('nav, ul > li > a') && 
                               (element.querySelector('img, svg') || // has logo/image
                                element.querySelector('h1, h2, h3')); // has heading
                    })
                    .forEach(element => {
                        const isNew = !candidates.some(candidate => 
                            candidate.element === element || element.contains(candidate.element) || candidate.element.contains(element)
                        );
                        
                        if (isNew) {
                            candidates.push({
                                element,
                                reason: 'Header content patterns',
                                priority: 5,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // Sort by priority and return detailed info
                const sortedCandidates = candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
                
                // Identify primary vs. secondary headers
                const result = {
                    primary: sortedCandidates.length > 0 ? sortedCandidates[0] : null,
                    all: sortedCandidates
                };
                
                // Add classification of different types of headers
                if (sortedCandidates.length > 1) {
                    result.secondary = [];
                    
                    // Check if we have multiple headers (might be secondary/section headers)
                    for (let i = 1; i < sortedCandidates.length; i++) {
                        const candidate = sortedCandidates[i];
                        
                        // Skip candidates that are parents or children of higher priority candidates
                        const isUnique = !sortedCandidates.slice(0, i).some(higher => {
                            const element = candidate.details;
                            const higherElement = higher.details;
                            
                            // Check if the current element is contained within a higher priority element
                            return (element.xpath && higherElement.xpath && 
                                    element.xpath.startsWith(higherElement.xpath)) || 
                                   (element.xpath && higherElement.xpath && 
                                    higherElement.xpath.startsWith(element.xpath));
                        });
                        
                        if (isUnique) {
                            result.secondary.push(candidate);
                        }
                    }
                }
                
                return result;
            }
            
            // Find footer candidates with enhanced detection
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
                
                // By ARIA role
                const footerRoles = document.querySelectorAll('[role="contentinfo"]');
                footerRoles.forEach(element => {
                    // Don't duplicate entries from footerTags
                    if (element.tagName.toLowerCase() !== 'footer') {
                        candidates.push({
                            element,
                            reason: 'ARIA contentinfo role',
                            priority: 9,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By class/id
                const footerClassIds = document.querySelectorAll(
                    '[class*="footer"], [id*="footer"], [class*="site-footer"], [id*="site-footer"], ' +
                    '[class*="page-footer"], [id*="page-footer"], [class*="global-footer"], [id*="global-footer"]'
                );
                footerClassIds.forEach(element => {
                    // Don't duplicate entries from footerTags
                    if (element.tagName.toLowerCase() !== 'footer' && !element.getAttribute('role') === 'contentinfo') {
                        candidates.push({
                            element,
                            reason: 'Footer class/id pattern',
                            priority: 8,
                            complexityScore: countDescendants(element),
                            interactiveElements: countInteractiveElements(element)
                        });
                    }
                });
                
                // By copyright text - very common in footers
                Array.from(document.querySelectorAll('div, section, p'))
                    .filter(element => {
                        const text = element.textContent.toLowerCase();
                        return text.includes('copyright') || text.includes('©') || text.includes('all rights reserved');
                    })
                    .forEach(element => {
                        // Find suitable container for the copyright text
                        let container = element;
                        let foundContainer = false;
                        
                        // Traverse up to find a suitable container (limit to 3 levels)
                        for (let i = 0; i < 3; i++) {
                            if (!container.parentElement || container.parentElement.tagName.toLowerCase() === 'body') break;
                            container = container.parentElement;
                            
                            const rect = container.getBoundingClientRect();
                            if (rect.width > viewportWidth * 0.5 && rect.height > 40) {
                                foundContainer = true;
                                break;
                            }
                        }
                        
                        if (foundContainer && container.tagName.toLowerCase() !== 'body') {
                            // Check if this container isn't already in candidates
                            const isNew = !candidates.some(candidate => 
                                candidate.element === container || 
                                container.contains(candidate.element) || 
                                candidate.element.contains(container)
                            );
                            
                            if (isNew) {
                                candidates.push({
                                    element: container,
                                    reason: 'Contains copyright info',
                                    priority: 7,
                                    complexityScore: countDescendants(container),
                                    interactiveElements: countInteractiveElements(container)
                                });
                            }
                        }
                    });
                
                // By position - elements at the bottom that span most of the width
                Array.from(document.querySelectorAll('div, section'))
                    .filter(element => {
                        const rect = element.getBoundingClientRect();
                        
                        // Get distance from bottom of the document
                        const fromBottom = documentHeight - (window.scrollY + rect.bottom);
                        
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
                
                // By content analysis - look for common footer patterns
                Array.from(document.querySelectorAll('div, section'))
                    .filter(element => {
                        // Check distance from bottom
                        const rect = element.getBoundingClientRect();
                        const fromBottom = documentHeight - (window.scrollY + rect.bottom);
                        if (fromBottom > 400) return false; // Must be toward the bottom
                        
                        const text = element.textContent.toLowerCase();
                        
                        // Look for typical footer content
                        return element.querySelectorAll('a').length >= 3 && // Has multiple links
                               (text.includes('privacy') || 
                                text.includes('terms') || 
                                text.includes('contact') ||
                                text.includes('copyright') ||
                                text.includes('©') ||
                                text.includes('social'));
                    })
                    .forEach(element => {
                        const isNew = !candidates.some(candidate => 
                            candidate.element === element || element.contains(candidate.element) || candidate.element.contains(element)
                        );
                        
                        if (isNew) {
                            candidates.push({
                                element,
                                reason: 'Footer content patterns',
                                priority: 5,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // Sort by priority and return detailed info
                const sortedCandidates = candidates
                    .sort((a, b) => b.priority - a.priority)
                    .map(candidate => ({
                        details: getElementDetails(candidate.element, true),
                        reason: candidate.reason,
                        priority: candidate.priority,
                        complexityScore: candidate.complexityScore,
                        interactiveElements: candidate.interactiveElements
                    }));
                
                // Identify primary vs. secondary footers
                const result = {
                    primary: sortedCandidates.length > 0 ? sortedCandidates[0] : null,
                    all: sortedCandidates
                };
                
                // Add classification of different types of footers
                if (sortedCandidates.length > 1) {
                    result.secondary = [];
                    
                    // Check if we have multiple footers (might be section footers)
                    for (let i = 1; i < sortedCandidates.length; i++) {
                        const candidate = sortedCandidates[i];
                        
                        // Skip candidates that are parents or children of higher priority candidates
                        const isUnique = !sortedCandidates.slice(0, i).some(higher => {
                            const element = candidate.details;
                            const higherElement = higher.details;
                            
                            // Check if the current element is contained within a higher priority element
                            return (element.xpath && higherElement.xpath && 
                                    element.xpath.startsWith(higherElement.xpath)) || 
                                   (element.xpath && higherElement.xpath && 
                                    higherElement.xpath.startsWith(element.xpath));
                        });
                        
                        if (isUnique) {
                            result.secondary.push(candidate);
                        }
                    }
                }
                
                return result;
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
                    '[class*="nav-"], [id*="nav-"], [class*="main-menu"], [id*="main-menu"], ' +
                    '[class*="primary-menu"], [id*="primary-menu"], [class*="navigation"], [id*="navigation"], ' +
                    '[class*="site-menu"], [id*="site-menu"], [class*="main-nav"], [id*="main-nav"]'
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
                
                // By structured link grouping
                Array.from(document.querySelectorAll('ul, ol'))
                    .filter(element => {
                        // Must contain multiple links to be considered navigation
                        const links = element.querySelectorAll('a');
                        const listItems = element.querySelectorAll('li');
                        
                        return links.length >= 4 && 
                               listItems.length >= 4 &&
                               // Most list items should contain links
                               listItems.length <= links.length * 1.5;
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
                                reason: 'Structured link list pattern',
                                priority: 6,
                                complexityScore: countDescendants(element),
                                interactiveElements: countInteractiveElements(element)
                            });
                        }
                    });
                
                // By unstructured link grouping
                Array.from(document.querySelectorAll('div'))
                    .filter(element => {
                        // Must contain multiple links to be considered navigation
                        const links = element.querySelectorAll('a');
                        
                        // Check link density - high link density suggests navigation menu
                        const textContent = element.textContent?.trim() || '';
                        const linkDensity = textContent.length > 0 ? 
                            links.length / textContent.length : 0;
                        
                        return links.length >= 4 && 
                               links.length <= 20 &&
                               linkDensity > 0.05; // Relatively high link density
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
                
                // Add hamburger menu detection
                Array.from(document.querySelectorAll('button, [role="button"]'))
                    .filter(element => {
                        const rect = element.getBoundingClientRect();
                        if (rect.width > 50 || rect.height > 50) return false; // Too large
                        
                        // Check for common hamburger button indicators
                        const hasHamburgerClass = element.className?.toLowerCase().includes('hamburger') ||
                                                element.className?.toLowerCase().includes('menu-toggle') ||
                                                element.className?.toLowerCase().includes('menu-button');
                        
                        // Look for ≡ symbol or multiple horizontal lines (common hamburger icons)
                        const hasHamburgerSymbol = element.textContent?.includes('≡') ||
                                                element.innerHTML?.includes('bar') ||
                                                element.querySelector('.bar, .line, [class*="bar"], [class*="line"]');
                        
                        return hasHamburgerClass || hasHamburgerSymbol;
                    })
                    .forEach(element => {
                        candidates.push({
                            element,
                            reason: 'Hamburger menu button',
                            priority: 6,
                            complexityScore: 1,
                            interactiveElements: {links: 0, buttons: 1, inputs: 0, images: 0}
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
            
            // Find main content with improved accuracy
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
                const mainClassIds = document.querySelectorAll(
                    '[class*="main"], [id*="main"], [class*="content"], [id*="content"], ' +
                    '[class*="primary"], [id*="primary"], [class*="page-content"], [id*="page-content"]'
                );
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
                
                // By article tag
                const articleElements = document.querySelectorAll('article');
                articleElements.forEach(element => {
                    candidates.push({
                        element,
                        reason: 'Article element',
                        priority: 8,
                        complexityScore: countDescendants(element),
                        interactiveElements: countInteractiveElements(element)
                    });
                });
                
                // By heading + content pattern
                Array.from(document.querySelectorAll('h1, h2')).forEach(heading => {
                    // Find a suitable container that has the heading + significant content
                    let container = heading.parentElement;
                    
                    // Skip if heading is in header or footer
                    if (container && (
                        container.tagName.toLowerCase() === 'header' || 
                        container.tagName.toLowerCase() === 'footer' ||
                        container.getAttribute('role') === 'banner' ||
                        container.getAttribute('role') === 'contentinfo')) {
                        return;
                    }
                    
                    // Look for container with significant content
                    while (container && container.tagName.toLowerCase() !== 'body') {
                        // Check if container has other content and reasonable size
                        const textLength = container.textContent.trim().length;
                        const rect = container.getBoundingClientRect();
                        
                        if (textLength > 200 && rect.width > viewportWidth * 0.5 && rect.height > 200) {
                            // Check if not already found
                            const alreadyFound = candidates.some(candidate => 
                                candidate.element === container || 
                                container.contains(candidate.element) || 
                                candidate.element.contains(container)
                            );
                            
                            if (!alreadyFound) {
                                candidates.push({
                                    element: container,
                                    reason: 'Heading + content pattern',
                                    priority: 6,
                                    complexityScore: countDescendants(container),
                                    interactiveElements: countInteractiveElements(container)
                                });
                            }
                            break;
                        }
                        container = container.parentElement;
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
                    '[class*="secondary"], [id*="secondary"], [class*="widget-area"], [id*="widget-area"]'
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
                
                // Look for widget containers (common in sidebars)
                const widgetContainers = document.querySelectorAll('[class*="widget"]');
                // Group widgets by common parent to find sidebar container
                const widgetsByParent = {};
                
                widgetContainers.forEach(widget => {
                    if (!widget.parentElement) return;
                    
                    const parentXPath = getXPath(widget.parentElement);
                    if (!parentXPath) return;
                    
                    if (!widgetsByParent[parentXPath]) {
                        widgetsByParent[parentXPath] = {
                            parent: widget.parentElement,
                            widgets: []
                        };
                    }
                    widgetsByParent[parentXPath].widgets.push(widget);
                });
                
                // Find parents with multiple widgets
                Object.values(widgetsByParent).forEach(entry => {
                    if (entry.widgets.length >= 2) {
                        // Check if parent element isn't already in candidates
                        const isNew = !candidates.some(candidate => 
                            candidate.element === entry.parent || 
                            entry.parent.contains(candidate.element) || 
                            candidate.element.contains(entry.parent)
                        );
                        
                        if (isNew) {
                            candidates.push({
                                element: entry.parent,
                                reason: 'Widget container',
                                priority: 6,
                                complexityScore: countDescendants(entry.parent),
                                interactiveElements: countInteractiveElements(entry.parent)
                            });
                        }
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
            
            // Find forms with improved detection and categorization
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
                    if (formElement.closest('header, .header, #header, [role="banner"]')) {
                        formDetails.location = 'header';
                    } else if (formElement.closest('footer, .footer, #footer, [role="contentinfo"]')) {
                        formDetails.location = 'footer';
                    } else if (formElement.closest('aside, [role="complementary"], .sidebar, #sidebar')) {
                        formDetails.location = 'complementary';
                    } else if (formElement.closest('main, [role="main"], .content, #content')) {
                        formDetails.location = 'main';
                    } else if (formElement.closest('body > div > div, body > div > section')) {
                        const container = formElement.closest('body > div > div, body > div > section');
                        const rect = container.getBoundingClientRect();
                        if (rect.top < 150) {
                            formDetails.location = 'top';
                        } else if (documentHeight - rect.bottom < 300) {
                            formDetails.location = 'bottom';
                        } else {
                            formDetails.location = 'middle';
                        }
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
                    formElement.getAttribute('role') === 'search' ||
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
                    formElement.querySelector('textarea') ||
                    inputNames.some(name => name.includes('contact') || name.includes('message'))) {
                    return 'contact';
                }
                
                // Check for registration/signup
                if (formText.includes('register') || 
                    formText.includes('sign up') ||
                    formText.includes('create account') ||
                    inputNames.some(name => 
                        name.includes('register') || 
                        name.includes('signup') ||
                        name.includes('firstname') || 
                        name.includes('lastname'))) {
                    return 'registration';
                }
                
                // Check for e-commerce forms
                if (formText.includes('checkout') || 
                    formText.includes('payment') ||
                    formText.includes('shipping') ||
                    formText.includes('billing') ||
                    inputNames.some(name => 
                        name.includes('card') || 
                        name.includes('payment') ||
                        name.includes('billing') || 
                        name.includes('shipping'))) {
                    return 'ecommerce';
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
                    search: Array.from(document.querySelectorAll('form[role="search"], [id*="search"], [class*="search"]'))
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
            
            // Find common content blocks across pages
            function findCommonContentBlocks() {
                // Look for standard content blocks and patterns
                const contentBlocks = {
                    // Hero sections (large image/banner sections at the top)
                    heroSections: Array.from(document.querySelectorAll(
                        '[class*="hero"], [id*="hero"], [class*="banner"], [id*="banner"], ' +
                        '[class*="jumbotron"], [id*="jumbotron"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'hero',
                        location: {
                            top: element.getBoundingClientRect().top,
                            isPageTop: element.getBoundingClientRect().top < 200
                        }
                    })),
                    
                    // Card sections (grid of similar content items)
                    cardGrids: findCardGrids(),
                    
                    // Feature sections
                    featureSections: Array.from(document.querySelectorAll(
                        '[class*="feature"], [id*="feature"], [class*="benefit"], [id*="benefit"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'feature',
                        childCount: element.children.length
                    })),
                    
                    // Testimonial sections
                    testimonials: Array.from(document.querySelectorAll(
                        '[class*="testimonial"], [id*="testimonial"], [class*="review"], [id*="review"], ' +
                        '[class*="quote"], [id*="quote"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'testimonial'
                    })),
                    
                    // Call-to-action sections
                    ctaSections: Array.from(document.querySelectorAll(
                        '[class*="cta"], [id*="cta"], [class*="call-to-action"], [id*="call-to-action"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'cta',
                        hasButton: !!element.querySelector('a.button, button, a[class*="btn"], [class*="button"]')
                    })),
                    
                    // Tabbed content
                    tabbedContent: Array.from(document.querySelectorAll(
                        '[role="tablist"], [class*="tab-"], [id*="tab-"], [class*="tabs"], [id*="tabs"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'tabbed',
                        tabCount: element.querySelectorAll('[role="tab"], .tab, [class*="tab-"]').length
                    })),
                    
                    // Accordions
                    accordions: Array.from(document.querySelectorAll(
                        '[class*="accordion"], [id*="accordion"], [class*="collapse"], [id*="collapse"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'accordion',
                        sectionCount: element.querySelectorAll('[class*="accordion-item"], [class*="collapse-item"]').length
                    })),
                    
                    // Carousels/sliders
                    carousels: Array.from(document.querySelectorAll(
                        '[class*="carousel"], [id*="carousel"], [class*="slider"], [id*="slider"], ' +
                        '[class*="slideshow"], [id*="slideshow"]'
                    )).map(element => ({
                        details: getElementDetails(element, true),
                        type: 'carousel',
                        slideCount: element.querySelectorAll('[class*="slide"], [class*="item"]').length
                    }))
                };
                
                return contentBlocks;
            }
            
            // Helper function to find card grid layouts
            function findCardGrids() {
                const possibleCardContainers = Array.from(document.querySelectorAll(
                    '[class*="grid"], [class*="card"], [class*="tiles"], ' +
                    '[class*="blocks"], [class*="items"], [class*="products"]'
                ));
                
                const cardGrids = [];
                
                possibleCardContainers.forEach(container => {
                    // Look for child elements that have similar structure - common in card layouts
                    const childElements = Array.from(container.children);
                    
                    // Need multiple children to be a grid
                    if (childElements.length < 3) return;
                    
                    // Check tag consistency
                    const childTags = childElements.map(child => child.tagName);
                    const tagCounts = {};
                    childTags.forEach(tag => {
                        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
                    });
                    
                    // Find the most common tag
                    let mostCommonTag = null;
                    let maxCount = 0;
                    for (const tag in tagCounts) {
                        if (tagCounts[tag] > maxCount) {
                            maxCount = tagCounts[tag];
                            mostCommonTag = tag;
                        }
                    }
                    
                    // If most children have the same tag, it's likely a grid
                    if (maxCount >= childElements.length * 0.7) {
                        // Get direct children with the most common tag
                        const cards = childElements.filter(child => child.tagName === mostCommonTag);
                        
                        // Check if cards have similar structure
                        const cardPatterns = {};
                        cards.forEach(card => {
                            // Create a simple structure fingerprint
                            const signature = Array.from(card.children)
                                .map(child => child.tagName.toLowerCase())
                                .join(',');
                            
                            cardPatterns[signature] = (cardPatterns[signature] || 0) + 1;
                        });
                        
                        // Find the most common pattern
                        let mostCommonPattern = null;
                        let maxPatternCount = 0;
                        for (const pattern in cardPatterns) {
                            if (cardPatterns[pattern] > maxPatternCount) {
                                maxPatternCount = cardPatterns[pattern];
                                mostCommonPattern = pattern;
                            }
                        }
                        
                        // If most cards have the same structure, it's almost certainly a card grid
                        if (maxPatternCount >= cards.length * 0.5) {
                            cardGrids.push({
                                details: getElementDetails(container, false),  // Don't include all children
                                type: 'card_grid',
                                cardCount: cards.length,
                                cardTag: mostCommonTag,
                                cardPatternConsistency: maxPatternCount / cards.length,
                                sampleCard: getElementDetails(cards[0], true)  // Include one sample card with children
                            });
                        }
                    }
                });
                
                return cardGrids;
            }
            
            // Analyze page for repetitive patterns
            function findRepetitivePatterns() {
                // Analyze the page for repetitive patterns in the DOM structure
                // This can help identify templates and common reusable components
                
                // 1. Find elements with multiple similar children
                const containers = Array.from(document.querySelectorAll('div, section, ul, ol, nav')).filter(el => el.children.length >= 3);
                
                const patternContainers = [];
                
                containers.forEach(container => {
                    // Skip small containers
                    if (container.children.length < 3) return;
                    
                    // Track child patterns
                    const patterns = {};
                    
                    Array.from(container.children).forEach(child => {
                        // Create a simple structural fingerprint
                        let fingerprint = child.tagName.toLowerCase();
                        
                        // Add child tag structure to fingerprint
                        const childTags = Array.from(child.children)
                            .map(el => el.tagName.toLowerCase())
                            .join(',');
                        
                        if (childTags) {
                            fingerprint += `[${childTags}]`;
                        }
                        
                        // Check if child has an image
                        if (child.querySelector('img, svg')) {
                            fingerprint += ':has-img';
                        }
                        
                        // Check if child has a heading
                        if (child.querySelector('h1, h2, h3, h4, h5, h6')) {
                            fingerprint += ':has-heading';
                        }
                        
                        // Check if child has a link
                        if (child.querySelector('a')) {
                            fingerprint += ':has-link';
                        }
                        
                        patterns[fingerprint] = (patterns[fingerprint] || 0) + 1;
                    });
                    
                    // Find the dominant pattern
                    let maxCount = 0;
                    let dominantPattern = null;
                    
                    for (const pattern in patterns) {
                        if (patterns[pattern] > maxCount) {
                            maxCount = patterns[pattern];
                            dominantPattern = pattern;
                        }
                    }
                    
                    // If a dominant pattern exists and covers at least 70% of children, it's a pattern container
                    if (dominantPattern && (maxCount / container.children.length) >= 0.7) {
                        patternContainers.push({
                            container: getElementDetails(container, false),
                            childCount: container.children.length,
                            pattern: dominantPattern,
                            matchingChildren: maxCount,
                            consistency: maxCount / container.children.length,
                            sampleChild: getElementDetails(container.children[0], true)
                        });
                    }
                });
                
                // Sort by pattern consistency and child count
                return patternContainers.sort((a, b) => {
                    if (a.consistency === b.consistency) {
                        return b.childCount - a.childCount;
                    }
                    return b.consistency - a.consistency;
                });
            }
            
            return {
                url: window.location.href,
                viewport: {
                    width: viewportWidth,
                    height: viewportHeight
                 },
                documentHeight: documentHeight,
                structure: {
                    headers: findHeaderCandidates(),
                    footers: findFooterCandidates(),
                    navigation: findMainNavigation(),
                    mainContent: findMainContent(),
                    complementaryContent: findComplementaryContent(),
                    commonComponents: findCommonUIComponents(),
                    recurringElements: findRecurringElements(),
                    forms: findForms(),
                    commonContentBlocks: findCommonContentBlocks(),
                    repetitivePatterns: findRepetitivePatterns()
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
    
    # Header analysis
    headers = structure_data['structure']['headers']
    primary_header = headers.get('primary', None)
    secondary_headers = headers.get('secondary', [])
    all_headers = headers.get('all', [])
    
    # Footer analysis
    footers = structure_data['structure']['footers']
    primary_footer = footers.get('primary', None)
    secondary_footers = footers.get('secondary', [])
    all_footers = footers.get('all', [])
    
    # Process headers summary
    header_summary = {
        'found': primary_header is not None,
        'count': len(all_headers),
        'primaryType': primary_header['reason'] if primary_header else None,
        'hasSecondaryHeaders': len(secondary_headers) > 0,
        'secondaryHeaderCount': len(secondary_headers),
        'types': [item['reason'] for item in all_headers]
    }
    
    # Process footers summary
    footer_summary = {
        'found': primary_footer is not None,
        'count': len(all_footers),
        'primaryType': primary_footer['reason'] if primary_footer else None,
        'hasSecondaryFooters': len(secondary_footers) > 0,
        'secondaryFooterCount': len(secondary_footers),
        'types': [item['reason'] for item in all_footers]
    }
    
    # Process navigation summary
    navigation_summary = {
        'found': len(structure_data['structure']['navigation']) > 0,
        'count': len(structure_data['structure']['navigation']),
        'types': [item['reason'] for item in structure_data['structure']['navigation']]
    }
    
    # Process main content summary
    main_content_summary = {
        'found': len(structure_data['structure']['mainContent']) > 0,
        'count': len(structure_data['structure']['mainContent']),
        'types': [item['reason'] for item in structure_data['structure']['mainContent']]
    }
    
    # Process complementary content summary
    complementary_summary = {
        'found': len(structure_data['structure']['complementaryContent']) > 0,
        'count': len(structure_data['structure']['complementaryContent']),
        'types': [item['reason'] for item in structure_data['structure']['complementaryContent']]
    }
    
    # Process common content blocks
    content_blocks = structure_data['structure']['commonContentBlocks']
    content_blocks_summary = {
        'heroSections': len(content_blocks.get('heroSections', [])),
        'cardGrids': len(content_blocks.get('cardGrids', [])),
        'featureSections': len(content_blocks.get('featureSections', [])),
        'testimonials': len(content_blocks.get('testimonials', [])),
        'ctaSections': len(content_blocks.get('ctaSections', [])),
        'tabbedContent': len(content_blocks.get('tabbedContent', [])),
        'accordions': len(content_blocks.get('accordions', [])),
        'carousels': len(content_blocks.get('carousels', []))
    }
    
    # Process components summary
    components_summary = {
        'search': len(structure_data['structure']['commonComponents']['search']) > 0,
        'socialMedia': len(structure_data['structure']['commonComponents']['socialMedia']) > 0,
        'notices': len(structure_data['structure']['commonComponents']['notices']) > 0,
        'sidebars': len(structure_data['structure']['commonComponents']['sidebars']) > 0
    }
    
    # Process recurring elements summary
    recurring_elements_summary = {
        'chatbots': len(structure_data['structure']['recurringElements']['chatbots']) > 0,
        'cookieNotices': len(structure_data['structure']['recurringElements']['cookieNotices']) > 0,
        'newsletters': len(structure_data['structure']['recurringElements']['newsletters']) > 0,
        'popups': len(structure_data['structure']['recurringElements']['popups']) > 0,
        'forms': len(structure_data['structure']['recurringElements']['forms']) > 0
    }
    
    # Process repetitive patterns
    repetitive_patterns = structure_data['structure']['repetitivePatterns']
    repetitive_patterns_summary = {
        'count': len(repetitive_patterns),
        'highConsistencyPatterns': sum(1 for p in repetitive_patterns if p['consistency'] > 0.9),
        'patternsByChildCount': {}
    }
    
    # Group patterns by child count
    for pattern in repetitive_patterns:
        count_range = '3-5' if pattern['childCount'] <= 5 else '6-10' if pattern['childCount'] <= 10 else '10+'
        if count_range not in repetitive_patterns_summary['patternsByChildCount']:
            repetitive_patterns_summary['patternsByChildCount'][count_range] = 0
        repetitive_patterns_summary['patternsByChildCount'][count_range] += 1
    
    # Process forms summary
    forms_summary = {
        'count': len(structure_data['structure']['forms']),
        'types': {}
    }
    
    # Count form types
    for form in structure_data['structure']['forms']:
        form_type = form.get('formType', 'unknown')
        if form_type not in forms_summary['types']:
            forms_summary['types'][form_type] = 0
        forms_summary['types'][form_type] += 1
    
    # Extract key elements for easier analysis
    key_elements = {
        'primaryHeader': primary_header['details'] if primary_header else None,
        'primaryFooter': primary_footer['details'] if primary_footer else None,
        'navigation': structure_data['structure']['navigation'][0]['details'] if structure_data['structure']['navigation'] else None,
        'mainContent': structure_data['structure']['mainContent'][0]['details'] if structure_data['structure']['mainContent'] else None,
        'complementaryContent': structure_data['structure']['complementaryContent'][0]['details'] if structure_data['structure']['complementaryContent'] else None,
        'secondaryHeaders': [h['details'] for h in secondary_headers] if secondary_headers else [],
        'secondaryFooters': [f['details'] for f in secondary_footers] if secondary_footers else []
    }
    
    # Extract complexity data
    complexity_data = {
        'primaryHeader': primary_header.get('complexityScore', 0) if primary_header else 0,
        'primaryFooter': primary_footer.get('complexityScore', 0) if primary_footer else 0,
        'navigation': structure_data['structure']['navigation'][0].get('complexityScore', 0) if structure_data['structure']['navigation'] else 0,
        'mainContent': structure_data['structure']['mainContent'][0].get('complexityScore', 0) if structure_data['structure']['mainContent'] else 0,
        'complementaryContent': structure_data['structure']['complementaryContent'][0].get('complexityScore', 0) if structure_data['structure']['complementaryContent'] else 0
    }
    
    # Extract interactive elements data
    interactive_elements = {
        'primaryHeader': primary_header.get('interactiveElements', {}) if primary_header else {},
        'primaryFooter': primary_footer.get('interactiveElements', {}) if primary_footer else {},
        'navigation': structure_data['structure']['navigation'][0].get('interactiveElements', {}) if structure_data['structure']['navigation'] else {},
        'mainContent': structure_data['structure']['mainContent'][0].get('interactiveElements', {}) if structure_data['structure']['mainContent'] else {},
        'complementaryContent': structure_data['structure']['complementaryContent'][0].get('interactiveElements', {}) if structure_data['structure']['complementaryContent'] else {}
    }
    
    # Create page flags for key structural findings
    page_flags = {
        'hasHeader': header_summary['found'],
        'hasFooter': footer_summary['found'],
        'hasMainNavigation': navigation_summary['found'],
        'hasMainContent': main_content_summary['found'],
        'hasComplementaryContent': complementary_summary['found'],
        'hasMultipleHeaders': header_summary['count'] > 1,
        'hasMultipleFooters': footer_summary['count'] > 1,
        'hasSecondaryHeaders': header_summary['hasSecondaryHeaders'],
        'hasSecondaryFooters': footer_summary['hasSecondaryFooters'],
        'hasSearchComponent': components_summary['search'],
        'hasSocialMediaLinks': components_summary['socialMedia'],
        'hasCookieNotice': components_summary['notices'],
        'hasSidebars': components_summary['sidebars'],
        'hasChatbot': recurring_elements_summary['chatbots'],
        'hasNewsletterSignup': recurring_elements_summary['newsletters'],
        'hasPopups': recurring_elements_summary['popups'],
        'hasForms': recurring_elements_summary['forms'],
        'hasHeroSection': content_blocks_summary['heroSections'] > 0,
        'hasCardGrids': content_blocks_summary['cardGrids'] > 0,
        'hasFeatureSections': content_blocks_summary['featureSections'] > 0,
        'hasCarousels': content_blocks_summary['carousels'] > 0,
        'hasRepetitivePatterns': repetitive_patterns_summary['count'] > 0
    }
    
    # Return complete test results with documentation
    # Add section information to results

    data['results'] = add_section_info_to_test_results(page, data['results'])

    # Print violations with section information for debugging

    print_violations_with_sections(data['results']['violations'])

    return {
        'page_structure': {
            'timestamp': datetime.now().isoformat(),
            'url': structure_data['url'],
            'viewport': structure_data['viewport'],
            'documentHeight': structure_data.get('documentHeight', 0),
            'pageFlags': page_flags,
            'summary': {
                'header': header_summary,
                'footer': footer_summary,
                'navigation': navigation_summary,
                'mainContent': main_content_summary,
                'complementaryContent': complementary_summary,
                'contentBlocks': content_blocks_summary,
                'components': components_summary,
                'recurringElements': recurring_elements_summary,
                'repetitivePatterns': repetitive_patterns_summary,
                'forms': forms_summary
             },
            'keyElements': key_elements,
            'complexityData': complexity_data,
            'interactiveElements': interactive_elements,
            'fullStructure': structure_data['structure'],
            'documentation': TEST_DOCUMENTATION  # Include test documentation in results
        }
    }