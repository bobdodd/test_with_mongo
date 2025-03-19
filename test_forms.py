from datetime import datetime

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