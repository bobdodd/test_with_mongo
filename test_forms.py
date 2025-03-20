from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Form Accessibility Analysis",
    "description": "Evaluates web forms for accessibility requirements including proper labeling, structure, layout, and contrast. This test helps ensure that forms can be completed by all users, regardless of their abilities or assistive technologies.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "pageFlags": "Boolean flags indicating key form accessibility issues",
        "details": "Full form data including structure, inputs, and violations",
        "timestamp": "ISO timestamp when the test was run"
    },
    "tests": [
        {
            "id": "form-landmark-context",
            "name": "Form Landmark Context",
            "description": "Checks if forms are properly placed within appropriate landmark regions. Forms should typically be within main content areas and not directly in header or footer unless they are simple search or subscription forms.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1", "2.4.1"],
            "howToFix": "Place forms within the appropriate landmark regions:\n1. Use <main> for primary content forms\n2. Use appropriate ARIA landmarks for specialized forms\n3. Only place search forms in <header> or forms directly related to footer content in <footer>",
            "resultsFields": {
                "pageFlags.hasFormsOutsideLandmarks": "Indicates if any forms are outside appropriate landmarks",
                "pageFlags.details.formsOutsideLandmarks": "Count of forms outside landmarks",
                "details.forms[].location": "Details of each form's landmark context"
            }
        },
        {
            "id": "form-headings",
            "name": "Form Headings and Identification",
            "description": "Checks if forms are properly identified with headings and ARIA labeling to make their purpose clear to all users.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.6"],
            "howToFix": "Add proper headings to forms:\n1. Include a heading (h2-h6) that describes the form's purpose\n2. Connect the heading to the form using aria-labelledby\n3. Ensure the heading text clearly describes the form's purpose",
            "resultsFields": {
                "pageFlags.hasFormsWithoutHeadings": "Indicates if forms lack proper headings",
                "pageFlags.details.formsWithoutHeadings": "Count of forms without proper headings",
                "details.forms[].heading": "Details of each form's heading information"
            }
        },
        {
            "id": "form-input-labels",
            "name": "Input Field Labeling",
            "description": "Verifies that all form inputs have properly associated labels that clearly describe the purpose of each field.",
            "impact": "critical",
            "wcagCriteria": ["1.3.1", "3.3.2", "4.1.2"],
            "howToFix": "Implement proper labels for all form fields:\n1. Use <label> elements with a 'for' attribute that matches the input's 'id'\n2. Ensure labels are visible and descriptive\n3. For complex controls, use aria-labelledby or aria-label if needed\n4. Never rely on placeholders alone for labeling",
            "resultsFields": {
                "pageFlags.hasInputsWithoutLabels": "Indicates if any inputs lack proper labels",
                "pageFlags.details.inputsWithoutLabels": "Count of inputs without labels",
                "details.forms[].inputs[].label": "Details of each input's label"
            }
        },
        {
            "id": "form-placeholder-misuse",
            "name": "Placeholder Text Misuse",
            "description": "Identifies form fields that use placeholder text as a substitute for proper labels, which creates accessibility barriers.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "3.3.2"],
            "howToFix": "Address placeholder-only fields:\n1. Add proper labels for all inputs\n2. Use placeholders only for format examples, not as instruction text\n3. Ensure placeholder text has sufficient contrast\n4. Keep placeholder text concise and helpful",
            "resultsFields": {
                "pageFlags.hasPlaceholderOnlyInputs": "Indicates if any inputs use placeholders as labels",
                "pageFlags.details.inputsWithPlaceholderOnly": "Count of inputs with placeholder-only labeling",
                "details.violations": "List of inputs with placeholder misuse"
            }
        },
        {
            "id": "form-layout-issues",
            "name": "Form Layout and Structure",
            "description": "Examines the layout of form elements to ensure fields are properly positioned for logical completion and navigation.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1", "1.3.2", "3.3.2"],
            "howToFix": "Improve form layout:\n1. Position labels above or to the left of their fields\n2. Left-align labels with their fields\n3. Avoid multiple fields on the same line (except for related fields like city/state/zip)\n4. Group related fields with fieldset and legend elements\n5. Arrange fields in a logical sequence",
            "resultsFields": {
                "pageFlags.hasLayoutIssues": "Indicates if forms have layout problems",
                "pageFlags.details.inputsWithLayoutIssues": "Count of inputs with layout issues",
                "details.forms[].layoutIssues": "Details of layout problems in each form"
            }
        },
        {
            "id": "form-input-contrast",
            "name": "Form Control Contrast",
            "description": "Checks that form controls, labels, and placeholder text have sufficient contrast against their backgrounds.",
            "impact": "high",
            "wcagCriteria": ["1.4.3", "1.4.11"],
            "howToFix": "Improve form control contrast:\n1. Ensure form input text has at least 4.5:1 contrast ratio\n2. Ensure form borders have at least 3:1 contrast ratio\n3. Ensure placeholder text has at least 4.5:1 contrast ratio\n4. Use visual indicators for focus states with 3:1 contrast ratio",
            "resultsFields": {
                "pageFlags.hasContrastIssues": "Indicates if form controls have contrast issues",
                "pageFlags.details.inputsWithContrastIssues": "Count of inputs with contrast problems",
                "details.forms[].inputs[].contrast": "Contrast measurements for each input"
            }
        }
    ]
}

async def test_forms(page):
    """
    Test forms for accessibility requirements including:
    - Form location and landmark context
    - Proper labeling and heading relationships
    - Input field requirements (excluding single input + button combinations from layout rules)
    - Layout and positioning
    - Contrast requirements
    """
    try:
        forms_data = await page.evaluate('''
            () => {
                function getLuminance(r, g, b) {
                    const [rs, gs, bs] = [r, g, b].map(c => {
                        c = c / 255;
                        return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
                    });
                    return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
                }

                function getContrastRatio(l1, l2) {
                    const lighter = Math.max(l1, l2);
                    const darker = Math.min(l1, l2);
                    return (lighter + 0.05) / (darker + 0.05);
                }

                function getRGBFromColor(color) {
                    const temp = document.createElement('div');
                    temp.style.color = color;
                    temp.style.display = 'none';
                    document.body.appendChild(temp);
                    const style = window.getComputedStyle(temp);
                    const rgb = style.color.match(/\\d+/g).map(Number);
                    document.body.removeChild(temp);
                    return rgb;
                }

                function isInLandmark(element, landmarkRole) {
                    let current = element;
                    while (current && current !== document.body) {
                        if (current.getAttribute('role') === landmarkRole ||
                            (landmarkRole === 'contentinfo' && current.tagName.toLowerCase() === 'footer') ||
                            (landmarkRole === 'banner' && current.tagName.toLowerCase() === 'header')) {
                            return true;
                        }
                        current = current.parentElement;
                    }
                    return false;
                }

                function checkLabelPosition(label, input) {
                    const labelRect = label.getBoundingClientRect();
                    const inputRect = input.getBoundingClientRect();
                    
                    return {
                        isAbove: labelRect.bottom <= inputRect.top,
                        isLeftAligned: Math.abs(labelRect.left - inputRect.left) < 5
                    };
                }

                function isVisible(element) {
                    const style = window.getComputedStyle(element);
                    return style.display !== 'none' && 
                           style.visibility !== 'hidden' && 
                           style.opacity !== '0';
                }

                function checkFieldsOnSameLine(input1, input2) {
                    const rect1 = input1.getBoundingClientRect();
                    const rect2 = input2.getBoundingClientRect();
                    return Math.abs(rect1.top - rect2.top) < 10;
                }

                function isSubmitButton(element) {
                    if (element.tagName.toLowerCase() === 'button') {
                        return element.type === 'submit' || !element.type;
                    }
                    return element.type === 'submit';
                }

                function getAutoCompleteType(input) {
                    const type = input.getAttribute('type') || 'text';
                    const name = input.name.toLowerCase();
                    
                    const autoCompleteMap = {
                        'name': ['name', 'fname', 'firstname', 'lastname'],
                        'email': ['email'],
                        'tel': ['phone', 'telephone', 'mobile'],
                        'street-address': ['address', 'street'],
                        'postal-code': ['zip', 'zipcode', 'postal'],
                        'country': ['country'],
                        'username': ['username', 'user'],
                        'current-password': ['password', 'pwd']
                    };

                    for (const [autoComplete, patterns] of Object.entries(autoCompleteMap)) {
                        if (patterns.some(pattern => name.includes(pattern))) {
                            return autoComplete;
                        }
                    }

                    return null;
                }

                const results = {
                    forms: [],
                    violations: [],
                    summary: {
                        totalForms: 0,
                        formsOutsideLandmarks: 0,
                        formsWithoutHeadings: 0,
                        inputsWithoutLabels: 0,
                        inputsWithPlaceholderOnly: 0,
                        inputsWithLayoutIssues: 0,
                        inputsWithContrastIssues: 0
                    }
                };

                document.querySelectorAll('form').forEach(form => {
                    const isInHeader = isInLandmark(form, 'banner');
                    const isInFooter = isInLandmark(form, 'contentinfo');
                    
                    const formHeading = form.querySelector('h1, h2, h3, h4, h5, h6');
                    const headingId = formHeading?.id;
                    const isLabelledByHeading = headingId && 
                                              form.getAttribute('aria-labelledby') === headingId;

                    const formInfo = {
                        id: form.id || null,
                        location: {
                            inHeader: isInHeader,
                            inFooter: isInFooter,
                            outsideLandmarks: !isInHeader && !isInFooter
                        },
                        heading: {
                            exists: !!formHeading,
                            text: formHeading?.textContent.trim() || null,
                            properlyLinked: isLabelledByHeading
                        },
                        inputs: [],
                        submitButton: null,
                        layoutIssues: []
                    };

                    // Get all form controls
                    const formControls = Array.from(form.querySelectorAll(
                        'input:not([type="hidden"]), textarea, select, button'
                    ));

                    // Count actual input fields (excluding buttons)
                    const inputFields = formControls.filter(
                        control => !isSubmitButton(control) && 
                                 control.tagName.toLowerCase() !== 'button'
                    );

                    let previousControl = null;

                    formControls.forEach(control => {
                        if (previousControl) {
                            const isCurrentSubmit = isSubmitButton(control);
                            const isPreviousSubmit = isSubmitButton(previousControl);
                            
                            // Only check for same-line issue if it's not a single input + button combination
                            // or if we have more than one input field
                            if (checkFieldsOnSameLine(previousControl, control) && 
                                !(inputFields.length === 1 && 
                                  ((isCurrentSubmit && !isPreviousSubmit) || 
                                   (!isCurrentSubmit && isPreviousSubmit)))) {
                                
                                formInfo.layoutIssues.push({
                                    type: 'fields-on-same-line',
                                    fields: [
                                        {
                                            id: previousControl.id || null,
                                            name: previousControl.name || null,
                                            type: previousControl.type || previousControl.tagName.toLowerCase()
                                        },
                                        {
                                            id: control.id || null,
                                            name: control.name || null,
                                            type: control.type || control.tagName.toLowerCase()
                                        }
                                    ]
                                });
                            }
                        }
                        previousControl = control;

                        // Skip further checks for submit buttons
                        if (isSubmitButton(control)) return;

                        const labelElement = document.querySelector(`label[for="${control.id}"]`);
                        const placeholder = control.getAttribute('placeholder');
                        
                        let labelPosition = null;
                        if (labelElement && isVisible(labelElement)) {
                            labelPosition = checkLabelPosition(labelElement, control);
                        }

                        // Check contrast
                        const style = window.getComputedStyle(control);
                        const textColor = getRGBFromColor(style.color);
                        const bgColor = getRGBFromColor(style.backgroundColor);
                        const textContrast = getContrastRatio(
                            getLuminance(...textColor),
                            getLuminance(...bgColor)
                        );

                        let placeholderContrast = null;
                        if (placeholder) {
                            const placeholderColor = getRGBFromColor(style.color)
                                .map(c => Math.min(c + 40, 255));
                            placeholderContrast = getContrastRatio(
                                getLuminance(...placeholderColor),
                                getLuminance(...bgColor)
                            );
                        }

                        const inputInfo = {
                            type: control.type || control.tagName.toLowerCase(),
                            id: control.id || null,
                            name: control.name || null,
                            label: {
                                exists: !!labelElement,
                                visible: labelElement ? isVisible(labelElement) : false,
                                text: labelElement?.textContent.trim() || null,
                                position: labelPosition
                            },
                            placeholder: {
                                exists: !!placeholder,
                                text: placeholder || null,
                                contrast: placeholderContrast
                            },
                            autoComplete: {
                                attribute: control.getAttribute('autocomplete'),
                                suggestedType: getAutoCompleteType(control)
                            },
                            contrast: {
                                textContrast: textContrast,
                                meetsRequirement: textContrast >= 4.5
                            }
                        };

                        formInfo.inputs.push(inputInfo);

                        // Check for violations
                        if (!labelElement) {
                            results.violations.push({
                                type: 'missing-label',
                                form: form.id || 'unnamed-form',
                                input: control.id || control.name || 'unnamed-input'
                            });
                            results.summary.inputsWithoutLabels++;
                        }

                        if (!labelElement && placeholder) {
                            results.violations.push({
                                type: 'placeholder-as-label',
                                form: form.id || 'unnamed-form',
                                input: control.id || control.name || 'unnamed-input'
                            });
                            results.summary.inputsWithPlaceholderOnly++;
                        }

                        if (labelPosition && (!labelPosition.isAbove || !labelPosition.isLeftAligned)) {
                            results.violations.push({
                                type: 'improper-label-position',
                                form: form.id || 'unnamed-form',
                                input: control.id || control.name || 'unnamed-input'
                            });
                            results.summary.inputsWithLayoutIssues++;
                        }

                        if (textContrast < 4.5 || (placeholder && placeholderContrast < 4.5)) {
                            results.violations.push({
                                type: 'insufficient-contrast',
                                form: form.id || 'unnamed-form',
                                input: control.id || control.name || 'unnamed-input',
                                contrast: {
                                    text: textContrast,
                                    placeholder: placeholderContrast
                                }
                            });
                            results.summary.inputsWithContrastIssues++;
                        }
                    });

                    // Check submit button
                    const submitButton = form.querySelector('button[type="submit"], input[type="submit"]');
                    if (submitButton) {
                        formInfo.submitButton = {
                            exists: true,
                            visible: isVisible(submitButton),
                            text: submitButton.textContent || submitButton.value
                        };
                    }

                    results.forms.push(formInfo);

                    // Update summary
                    results.summary.totalForms++;
                    if (!isInHeader && !isInFooter) {
                        results.summary.formsOutsideLandmarks++;
                    }
                    if (!isLabelledByHeading) {
                        results.summary.formsWithoutHeadings++;
                    }
                });

                return {
                    pageFlags: {
                        hasFormsOutsideLandmarks: results.summary.formsOutsideLandmarks > 0,
                        hasFormsWithoutHeadings: results.summary.formsWithoutHeadings > 0,
                        hasInputsWithoutLabels: results.summary.inputsWithoutLabels > 0,
                        hasPlaceholderOnlyInputs: results.summary.inputsWithPlaceholderOnly > 0,
                        hasLayoutIssues: results.summary.inputsWithLayoutIssues > 0,
                        hasContrastIssues: results.summary.inputsWithContrastIssues > 0,
                        details: {
                            totalForms: results.summary.totalForms,
                            formsOutsideLandmarks: results.summary.formsOutsideLandmarks,
                            inputsWithoutLabels: results.summary.inputsWithoutLabels,
                            inputsWithPlaceholderOnly: results.summary.inputsWithPlaceholderOnly,
                            inputsWithLayoutIssues: results.summary.inputsWithLayoutIssues,
                            inputsWithContrastIssues: results.summary.inputsWithContrastIssues
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'forms': {
                'pageFlags': forms_data['pageFlags'],
                'details': forms_data['results'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'forms': {
                'pageFlags': {
                    'hasFormsOutsideLandmarks': False,
                    'hasFormsWithoutHeadings': False,
                    'hasInputsWithoutLabels': False,
                    'hasPlaceholderOnlyInputs': False,
                    'hasLayoutIssues': False,
                    'hasContrastIssues': False,
                    'details': {
                        'totalForms': 0,
                        'formsOutsideLandmarks': 0,
                        'inputsWithoutLabels': 0,
                        'inputsWithPlaceholderOnly': 0,
                        'inputsWithLayoutIssues': 0,
                        'inputsWithContrastIssues': 0
                    }
                },
                'details': {
                    'forms': [],
                    'violations': [{
                        'issue': 'Error evaluating forms',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalForms': 0,
                        'formsOutsideLandmarks': 0,
                        'formsWithoutHeadings': 0,
                        'inputsWithoutLabels': 0,
                        'inputsWithPlaceholderOnly': 0,
                        'inputsWithLayoutIssues': 0,
                        'inputsWithContrastIssues': 0
                    }
                }
            }
        }