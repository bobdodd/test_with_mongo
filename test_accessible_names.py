from datetime import datetime

async def test_accessible_names(page):
    """
    Test accessible names for all visible elements, ensuring they have appropriate labels.
    Uses the W3C accessible name computation algorithm.
    """
    try:
        names_data = await page.evaluate(r'''
            () => {
                // Default context initialization
                function getDefaultContext() {
                    return {
                        inherited: {
                            visitedNodes: [],
                            nodesUsed: new Set(),
                            rulesApplied: new Set(),
                        },
                    };
                }

                // Constants for role determination
                const ALWAYS_NAME_FROM_CONTENT = {
                    roles: [
                        'button', 'cell', 'checkbox', 'columnheader', 'gridcell',
                        'heading', 'link', 'menuitem', 'menuitemcheckbox', 
                        'menuitemradio', 'option', 'radio', 'row', 'rowgroup',
                        'rowheader', 'switch', 'tab', 'tooltip', 'tree', 'treeitem'
                    ],
                    tags: [
                        'button', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                        'summary', 'tbody', 'tfoot', 'thead'
                    ]
                };

                const NEVER_NAME_FROM_CONTENT = {
                    roles: [
                        'alert', 'alertdialog', 'application', 'article', 'banner',
                        'complementary', 'contentinfo', 'definition', 'dialog',
                        'directory', 'document', 'feed', 'figure', 'form', 'grid',
                        'group', 'img', 'list', 'listbox', 'log', 'main', 'marquee',
                        'math', 'menu', 'menubar', 'navigation', 'note', 'radiogroup',
                        'region', 'row', 'rowgroup', 'scrollbar', 'search', 'searchbox',
                        'separator', 'slider', 'spinbutton', 'status', 'table',
                        'tablist', 'tabpanel', 'term', 'textbox', 'timer', 'toolbar',
                        'tree', 'treegrid'
                    ],
                    tags: [
                        'article', 'aside', 'body', 'datalist', 'dialog', 'fieldset',
                        'figure', 'footer', 'form', 'header', 'hr', 'img', 'input',
                        'main', 'math', 'menu', 'nav', 'optgroup', 'section', 'select',
                        'textarea'
                    ]
                };

                const SOMETIMES_NAME_FROM_CONTENT = {
                    roles: [
                        'contentinfo', 'definition', 'directory', 'list', 'note',
                        'status', 'table', 'term'
                    ],
                    tags: ['dd', 'details', 'dl', 'ol', 'output', 'table', 'ul']
                };

                // Helper functions
                function closest(element, selector) {
                    if (element.closest) {
                        return element.closest(selector);
                    }
                }
                                         
                function resolveValidAriaLabelledbyIdrefs(elem) {
                    const idrefs = elem.getAttribute('aria-labelledby')?.split(' ') ?? [];
                    const validElems = [];
                    for (const id of idrefs) {
                        const elem = document.getElementById(id);
                        if (elem) {
                            validElems.push(elem);
                        }
                    }
                    return validElems;
                }

                function isFocusable(elem) {
                    if ((elem instanceof HTMLAnchorElement ||
                        elem instanceof HTMLAreaElement ||
                        elem instanceof HTMLLinkElement) &&
                        elem.hasAttribute('href')) {
                        return true;
                    }
                    if ((elem instanceof HTMLInputElement ||
                        elem instanceof HTMLSelectElement ||
                        elem instanceof HTMLTextAreaElement ||
                        elem instanceof HTMLButtonElement) &&
                        !elem.hasAttribute('disabled')) {
                        return true;
                    }
                    return elem.hasAttribute('tabindex') || elem.isContentEditable;
                }

                function isHidden(node, context) {
                    if (!(node instanceof HTMLElement)) {
                        return false;
                    }
                    if (node instanceof HTMLOptionElement &&
                        closest(node, 'select') !== null &&
                        context.inherited.partOfName) {
                        return false;
                    }
                    const notDisplayed = node.offsetHeight === 0 && node.offsetWidth === 0;
                    if (notDisplayed && !isFocusable(node)) {
                        return true;
                    }
                    const visibility = window.getComputedStyle(node).visibility;
                    if (visibility === 'hidden') {
                        return true;
                    }
                    const hiddenAncestor = closest(node, '[hidden],[aria-hidden="true"]');
                    if (hiddenAncestor !== null) {
                        return true;
                    }
                    return false;
                }

                // XPath generation
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

                // Accessible name computation rules
                function rule2A(node, context) {
                    let result = null;
                    if (isHidden(node, context)) {
                        result = '';
                    }
                    return result;
                }

                function rule2B(node, context = getDefaultContext()) {
                    if (!(node instanceof HTMLElement)) {
                        return null;
                    }
                    if (context.directLabelReference) {
                        return null;
                    }
                    const labelElems = resolveValidAriaLabelledbyIdrefs(node);
                    if (labelElems.length === 0) {
                        return null;
                    }
                    return labelElems
                        .map(labelElem => {
                            context.inherited.partOfName = true;
                            return computeTextAlternative(labelElem, {
                                directLabelReference: true,
                                inherited: context.inherited,
                            }).name;
                        })
                        .join(' ')
                        .trim();
                }

                function rule2C(node, context = getDefaultContext()) {
                    if (!(node instanceof HTMLElement)) {
                        return null;
                    }
                    const ariaLabel = node.getAttribute('aria-label');
                    if (!ariaLabel || ariaLabel.trim() === '') {
                        return null;
                    }
                    return ariaLabel.trim();
                }

                function resolveValidAriaLabelledbyIdrefs(elem) {
                    const idrefs = elem.getAttribute('aria-labelledby')?.split(' ') ?? [];
                    const validElems = [];
                    for (const id of idrefs) {
                        const elem = document.getElementById(id);
                        if (elem) {
                            validElems.push(elem);
                        }
                    }
                    return validElems;
                }

                function allowsNameFromContent(elem, context) {
                    // Check if element matches any of the roles in a given RoleType
                    function matchesRole(elem, roleType) {
                        // Explicit roles: specified using 'role' attribute
                        const explicitRole = elem.getAttribute('role')?.trim().toLowerCase() ?? '';
                        if (roleType.roles.includes(explicitRole)) {
                            return true;
                        }
                        // Implicit roles: implied by current node tag name
                        const elemNodeName = elem.nodeName.toLowerCase();
                        if (roleType.tags.includes(elemNodeName)) {
                            return true;
                        }
                        return false;
                    }

                    // List 3 roles (sometimes name from content)
                    if (context.inherited.partOfName && elem.parentElement) {
                        const parent = elem.parentElement;
                        if (matchesRole(parent, ALWAYS_NAME_FROM_CONTENT) &&
                            matchesRole(elem, SOMETIMES_NAME_FROM_CONTENT)) {
                            return true;
                        }
                    }

                    // List 2 roles (name from content if focusable)
                    if (matchesRole(elem, NEVER_NAME_FROM_CONTENT)) {
                        // Special case: role=menu should not allow name from content even if focusable
                        if (elem.getAttribute('role')?.toLowerCase() === 'menu') {
                            return false;
                        }
                        return isFocusable(elem);
                    }

                    // List 1 roles (always name from content)
                    if (matchesRole(elem, ALWAYS_NAME_FROM_CONTENT)) {
                        return true;
                    }

                    // Elements that conditionally have an implicit role that matches ALWAYS_NAME_FROM_CONTENT
                    const elemNodeName = elem.nodeName.toLowerCase();
                    
                    // Handle special cases for specific elements
                    switch (elemNodeName) {
                        case 'a':
                            return elem.hasAttribute('href');
                        case 'area':
                            return elem.hasAttribute('href');
                        case 'link':
                            return elem.hasAttribute('href');
                        case 'td':
                            return closest(elem, 'table') !== null;
                        case 'th':
                            return closest(elem, 'table') !== null;
                        case 'option':
                            return closest(elem, 'select,datalist') !== null;
                    }

                    // Allow name from content if part of a label or referenced by aria-labelledby
                    if (context.directLabelReference) {
                        return true;
                    }

                    // Allow name from content if part of computing a name
                    if (context.inherited.partOfName) {
                        return true;
                    }

                    return false;
                }
                                         
                function rule2D(node, context = getDefaultContext()) {
                    // Handle SVG title
                    if (node instanceof SVGElement) {
                        for (const child of node.childNodes) {
                            if (child instanceof SVGTitleElement) {
                                return child.textContent;
                            }
                        }
                    }

                    if (!(node instanceof HTMLElement)) {
                        return null;
                    }

                    const roleAttribute = node.getAttribute('role');
                    if (roleAttribute === 'presentation' || roleAttribute === 'none') {
                        return null;
                    }

                    // Handle input elements first
                    if (node instanceof HTMLInputElement) {
                        const inputType = node.getAttribute('type')?.toLowerCase();
                        
                        // Handle buttons
                        if (inputType === 'submit' || inputType === 'button' || inputType === 'reset') {
                            if (node.hasAttribute('value')) {
                                return node.value;
                            }
                            // Default values if no value attribute
                            if (inputType === 'submit') return 'Submit';
                            if (inputType === 'reset') return 'Reset';
                        }

                        // Handle image inputs
                        if (inputType === 'image') {
                            const alt = node.getAttribute('alt');
                            if (alt !== null) {
                                return alt;
                            }
                            if (!node.hasAttribute('title')) {
                                return 'Submit Query'; // Default value for input[type=image]
                            }
                        }

                        // Check for labels (for all other input types)
                        // First check for a wrapping label
                        const parentLabel = closest(node, 'label');
                        if (parentLabel) {
                            const clone = parentLabel.cloneNode(true);
                            const inputInClone = clone.querySelector('input, textarea, select');
                            if (inputInClone) {
                                inputInClone.remove();
                            }
                            const labelText = clone.textContent.trim();
                            if (labelText) {
                                return labelText;
                            }
                        }

                        // Then check for associated label via 'for' attribute
                        if (node.id) {
                            const labelElement = document.querySelector(`label[for="${node.id}"]`);
                            if (labelElement) {
                                return labelElement.textContent.trim();
                            }
                        }
                    }

                    // Handle other form controls (textarea, select)
                    if (node instanceof HTMLTextAreaElement || 
                        node instanceof HTMLSelectElement) {
                        
                        // Check for wrapping label
                        const parentLabel = closest(node, 'label');
                        if (parentLabel) {
                            const clone = parentLabel.cloneNode(true);
                            const controlInClone = clone.querySelector('textarea, select');
                            if (controlInClone) {
                                controlInClone.remove();
                            }
                            const labelText = clone.textContent.trim();
                            if (labelText) {
                                return labelText;
                            }
                        }

                        // Check for associated label
                        if (node.id) {
                            const labelElement = document.querySelector(`label[for="${node.id}"]`);
                            if (labelElement) {
                                return labelElement.textContent.trim();
                            }
                        }
                    }

                    // Handle images and areas
                    if (node instanceof HTMLImageElement || 
                        node instanceof HTMLAreaElement) {
                        const alt = node.getAttribute('alt');
                        if (alt !== null) {
                            return alt;
                        }
                    }

                    // Handle tables
                    if (node instanceof HTMLTableElement) {
                        const captionElem = node.querySelector('caption');
                        if (captionElem) {
                            context.inherited.partOfName = true;
                            return computeTextAlternative(captionElem, {
                                inherited: context.inherited,
                            }).name;
                        }
                    }

                    // Handle figures
                    if (node.tagName === 'FIGURE') {
                        const figcaptionElem = node.querySelector('figcaption');
                        if (figcaptionElem) {
                            context.inherited.partOfName = true;
                            return computeTextAlternative(figcaptionElem, {
                                inherited: context.inherited,
                            }).name;
                        }
                    }

                    // Handle fieldsets
                    if (node instanceof HTMLFieldSetElement) {
                        const legendElem = node.querySelector('legend');
                        if (legendElem) {
                            context.inherited.partOfName = true;
                            return computeTextAlternative(legendElem, {
                                inherited: context.inherited,
                            }).name;
                        }
                    }

                    return null;
                }

                function rule2E(node, context = getDefaultContext()) {
                    if (!(node instanceof HTMLElement)) {
                        return null;
                    }
                    if (!context.inherited.partOfName) {
                        return null;
                    }
                    // ... [Rest of rule2E implementation]
                    return null;
                }

                const inlineTags = [
                    'a', 'abbr', 'acronym', 'b', 'bdi', 'bdo', 'big', 'button',
                    'canvas', 'cite', 'code', 'data', 'datalist', 'del', 'dfn',
                    'em', 'embed', 'i', 'iframe', 'img', 'ins', 'kbd', 'label',
                    'map', 'mark', 'meter', 'noscript', 'object', 'output',
                    'picture', 'progress', 'q', 'ruby', 's', 'samp', 'script',
                    'select', 'slot', 'small', 'span', 'strong', 'sub', 'sup',
                    'template', 'textarea', 'time', 'tt', 'u', 'var', 'video', 'wbr'
                ];
                                         
                function getCssContent(elem, pseudoElementName) {
                    const computedStyle = window.getComputedStyle(elem, pseudoElementName);
                    const cssContent = computedStyle.content;
                    const isBlockDisplay = computedStyle.display === 'block';
                    
                    // <string> CSS content identified by surrounding quotes
                    if ((cssContent[0] === '"' && cssContent[cssContent.length - 1] === '"') ||
                        (cssContent[0] === "'" && cssContent[cssContent.length - 1] === "'")) {
                        return isBlockDisplay
                            ? ' ' + cssContent.slice(1, -1) + ' '
                            : cssContent.slice(1, -1);
                    }
                    
                    return '';
                }                                         

                function rule2F(node, context = getDefaultContext()) {
                    if (!(node instanceof HTMLElement)) {
                        return null;
                    }

                    if (!allowsNameFromContent(node, context)) {
                        return null;
                    }

                    const a11yChildNodes = Array.from(node.childNodes);
                    // Get aria-owned nodes if any
                    const ariaOwnedNodeIds = node.getAttribute('aria-owns');
                    if (ariaOwnedNodeIds) {
                        for (const idref of ariaOwnedNodeIds.split(' ')) {
                            const referencedNode = document.getElementById(idref);
                            if (referencedNode) {
                                a11yChildNodes.push(referencedNode);
                            }
                        }
                    }

                    const textAlternatives = [];
                    for (const childNode of a11yChildNodes) {
                        if (!context.inherited.visitedNodes.includes(childNode)) {
                            context.inherited.visitedNodes.push(childNode);
                            context.inherited.partOfName = true;
                            
                            const textAlternative = computeTextAlternative(childNode, {
                                inherited: context.inherited,
                            }).name;
                            
                            if (textAlternative) {
                                textAlternatives.push(textAlternative);
                            }
                        }
                    }

                    const accumulatedText = textAlternatives
                        .filter(text => text !== '')
                        .join('')
                        .replace(/\s+/g, ' ')
                        .trim();

                    const cssBeforeContent = getCssContent(node, ':before');
                    const cssAfterContent = getCssContent(node, ':after');

                    const result = (cssBeforeContent + accumulatedText + cssAfterContent).trim();
                    return result || null;
                }
                                         
                function rule2G(node) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        return node.textContent?.replace(/\s\s+/g, ' ') ?? '';
                    }
                    return null;
                }

                function rule2I(node) {
                    if (!(node instanceof HTMLElement)) {
                        return null;
                    }
                    return node.title || null;
                }

                // Main computation function
                function computeTextAlternative(node, context = getDefaultContext()) {
                    context.inherited.nodesUsed.add(node);
                    
                    const rules = {
                        '2A': rule2A,
                        '2B': rule2B,
                        '2C': rule2C,
                        '2D': rule2D,
                        '2E': rule2E,
                        '2F': rule2F,
                        '2G': rule2G,
                        '2I': rule2I
                    };

                    // Try each rule in order
                    for (const [rule, impl] of Object.entries(rules)) {
                        const result = impl(node, context);
                        if (result !== null && result !== "") {
                            context.inherited.rulesApplied.add(rule);
                            return {
                                name: result,
                                nodesUsed: context.inherited.nodesUsed,
                                rulesApplied: context.inherited.rulesApplied,
                            };
                        }
                    }

                    return {
                        name: '',
                        nodesUsed: context.inherited.nodesUsed,
                        rulesApplied: context.inherited.rulesApplied,
                    };
                }

                // Main evaluation code
                const results = {
                    elements: [],
                    violations: [],
                    summary: {
                        totalElements: 0,
                        elementsRequiringNames: 0,
                        missingNames: 0
                    }
                };

                function shouldHaveAccessibleName(element) {
                    const tag = element.tagName.toLowerCase();
                    
                    // Elements that can have empty accessible names
                    const canBeEmpty = ['div', 'span', 'br', 'p'];
                    if (canBeEmpty.includes(tag)) {
                        return false;
                    }

                    // Special case for anchors - only need names if they're interactive (have href)
                    if (tag === 'a') {
                        return element.hasAttribute('href');
                    }

                    // Elements that must have non-empty accessible names
                    const requiresName = [
                        'button', 'input', 'textarea', 'select', 'img',
                        'iframe', 'area', 'dialog', 'form'
                    ];
                    
                    // Check for ARIA roles that require names
                    const role = element.getAttribute('role');
                    const requiresNameRoles = [
                        'button', 'checkbox', 'combobox', 'heading', 'link', 
                        'listbox', 'menu', 'menubar', 'menuitem', 'radio', 
                        'tab', 'tabpanel', 'textbox', 'toolbar', 'tree', 'treeitem'
                    ];

                    return requiresName.includes(tag) || 
                        (role && requiresNameRoles.includes(role));
                }

                const elements = Array.from(document.body.getElementsByTagName('*'))
                    .filter(element => {
                        const tag = element.tagName.toLowerCase();
                        const style = window.getComputedStyle(element);
                        const isHidden = element.getAttribute('aria-hidden') === 'true' ||
                                       style.display === 'none' ||
                                       style.visibility === 'hidden';
                        return !isHidden && tag !== 'script' && tag !== 'style';
                    });

                elements.forEach(element => {
                    const tag = element.tagName.toLowerCase();
                    const computationResult = computeTextAlternative(element);
                    const accessibleName = computationResult.name;
                    const needsName = shouldHaveAccessibleName(element);
                    const isNameValid = accessibleName.length > 0 || 
                                     (tag === 'img' && element.getAttribute('alt') === '') ||
                                     ['div', 'span', 'br', 'p'].includes(tag);

                    const elementInfo = {
                        tag: tag,
                        role: element.getAttribute('role') || null,
                        accessibleName: accessibleName,
                        needsAccessibleName: needsName,
                        hasValidName: isNameValid,
                        xpath: needsName && !isNameValid ? getFullXPath(element) : null
                    };

                    results.elements.push(elementInfo);

                    if (needsName && !isNameValid) {
                        results.violations.push({
                            element: tag,
                            role: elementInfo.role,
                            issue: 'Missing accessible name',
                            currentName: accessibleName,
                            xpath: getFullXPath(element)
                        });
                    }
                });

                results.summary.totalElements = elements.length;
                results.summary.elementsRequiringNames = results.elements
                    .filter(e => e.needsAccessibleName).length;
                results.summary.missingNames = results.violations.length;

                return {
                    pageFlags: {
                        hasMissingAccessibleNames: results.violations.length > 0,
                        details: {
                            elementsRequiringNames: results.summary.elementsRequiringNames,
                            elementsMissingNames: results.summary.missingNames
                        }
                    },
                    results: results
                };
            }
        ''')

        # Print violations with XPaths for debug purposes
        if names_data['results']['violations']:
            print("\nAccessibility Violations Found:")
            for violation in names_data['results']['violations']:
                print(f"\nElement: {violation['element']}")
                print(f"Role: {violation['role']}")
                print(f"Issue: {violation['issue']}")
                print(f"XPath: {violation['xpath']}")
                if 'currentName' in violation:
                    print(f"Current Name: {violation['currentName']}")
                print("-" * 50)

        return {
            'accessible_names': {
                'pageFlags': names_data['pageFlags'],
                'details': names_data['results'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'accessible_names': {
                'pageFlags': {
                    'hasMissingAccessibleNames': False,
                    'details': {
                        'elementsRequiringNames': 0,
                        'elementsMissingNames': 0
                    }
                },
                'details': {
                    'elements': [],
                    'violations': [{
                        'issue': 'Error evaluating accessible names',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalElements': 0,
                        'elementsRequiringNames': 0,
                        'missingNames': 0
                    }
                }
            }
        }