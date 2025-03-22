from datetime import datetime
import re



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
    "testName": "Image Accessibility Analysis",
    "description": "Evaluates images on the page for proper alternative text and ARIA roles to ensure they are accessible to screen reader users. This test checks for missing alt attributes, invalid alt text content, and proper role attributes for SVG elements.",
    "version": "1.1.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.images": "List of all images with their properties",
        "details.violations": "List of images with accessibility violations",
        "details.summary": "Aggregated statistics about image accessibility"
    },
    "tests": [
        {
            "id": "image-alt-presence",
            "name": "Alternative Text Presence",
            "description": "Checks whether all non-decorative images have an alt attribute providing a text alternative.",
            "impact": "high",
            "wcagCriteria": ["1.1.1"],
            "howToFix": "Add an alt attribute to all meaningful images. For decorative images, use an empty alt attribute (alt='').",
            "resultsFields": {
                "pageFlags.hasImagesWithoutAlt": "Indicates if any images are missing alt attributes",
                "details.summary.missingAlt": "Count of images missing alt attributes",
                "details.violations": "List of images with missing alt attributes"
            }
        },
        {
            "id": "image-alt-quality",
            "name": "Alternative Text Quality",
            "description": "Evaluates the quality of alternative text to ensure it's meaningful and not just a filename or URL.",
            "impact": "high",
            "wcagCriteria": ["1.1.1"],
            "howToFix": "Ensure alt text is concise, descriptive, and conveys the purpose or content of the image. Avoid using filenames, URLs, or generic text like 'image'.",
            "resultsFields": {
                "pageFlags.hasImagesWithInvalidAlt": "Indicates if any images have invalid alt text",
                "details.summary.invalidAlt": "Count of images with invalid alt text",
                "details.violations": "List of images with invalid alt text"
            }
        },
        {
            "id": "svg-role",
            "name": "SVG Role Attributes",
            "description": "Checks if SVG elements have proper role attributes for accessibility.",
            "impact": "medium",
            "wcagCriteria": ["1.1.1", "4.1.2"],
            "howToFix": "Add role='img' to non-interactive SVG elements, and provide appropriate text alternatives using aria-label or aria-labelledby.",
            "resultsFields": {
                "pageFlags.hasSVGWithoutRole": "Indicates if any SVG elements are missing role attributes",
                "details.summary.missingRole": "Count of SVG elements missing role attributes",
                "details.violations": "List of SVG elements with missing role attributes"
            }
        },
        {
            "id": "decorative-images",
            "name": "Decorative Image Identification",
            "description": "Identifies decorative images that use empty alt text to be properly ignored by screen readers.",
            "impact": "low",
            "wcagCriteria": ["1.1.1"],
            "howToFix": "For purely decorative images, use an empty alt attribute (alt='') rather than omitting the attribute entirely.",
            "resultsFields": {
                "details.summary.decorativeImages": "Count of decorative images with empty alt text",
                "details.images": "List of all images with isDecorative property indicating decorative status"
            }
        }
    ]
}

async def test_images(page):
    """
    Test images for proper alt text and role attributes according to accessibility requirements
    """
    try:
        images_data = await page.evaluate('''
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
                
                function validateAltText(alt, src) {
                    if (alt === null) return { valid: false, reason: 'Missing alt attribute'  };
                    
                    // Check for HTML tags
                    if (/<[^>]*>/g.test(alt)) {
                        return { valid: false, reason: 'Contains HTML elements'  };
                    }

                    // Trim the alt text
                    const trimmedAlt = alt.trim();

                    // Check for empty string (which is valid in some cases)
                    if (trimmedAlt === '') {
                        return { valid: true, isDecorative: true  };
                    }

                    // Check for whitespace only
                    if (!trimmedAlt) {
                        return { valid: false, reason: 'Contains only whitespace'  };
                    }

                    // Check for punctuation only
                    if (/^[.,/#!$%^&*;:{}=\-_`~()]+$/.test(trimmedAlt)) {
                        return { valid: false, reason: 'Contains only punctuation'  };
                    }

                    // Check if it's just a URL or filename
                    const urlPattern = /^(https?:\/\/|www\.|\/|\w+\.[a-zA-Z]{3,4}$)/i;
                    if (urlPattern.test(trimmedAlt) || 
                        trimmedAlt.toLowerCase() === src.toLowerCase() ||
                        src.toLowerCase().includes(trimmedAlt.toLowerCase())) {
                        return { valid: false, reason: 'Appears to be URL or filename'  };
                    }

                    // Check length
                    if (trimmedAlt.length > 200) {
                        return { valid: false, reason: 'Exceeds 200 characters'  };
                    }

                    return { valid: true, isDecorative: false  };
                }

                const results = {
                    images: [],
                    violations: [],
                    summary: {
                        totalImages: 0,
                        missingAlt: 0,
                        invalidAlt: 0,
                        missingRole: 0,
                        decorativeImages: 0
                    }
                };

                // Get all images, including SVG
                const images = [
                    ...Array.from(document.getElementsByTagName('img')),
                    ...Array.from(document.getElementsByTagName('svg'))
                ];

                images.forEach(img => {
                    const isInteractiveSVG = img.tagName.toLowerCase() === 'svg' && 
                                          (img.closest('button') || img.closest('a'));
                    
                    const parentAnchor = img.closest('a');
                    const src = img.tagName.toLowerCase() === 'img' ? 
                              (img.getAttribute('src') || '') : '';
                    const alt = img.getAttribute('alt');
                    const role = img.getAttribute('role');
                    
                    // Validate alt text
                    const altValidation = validateAltText(alt, src);
                    
                    const imageInfo = {
                        tag: img.tagName.toLowerCase(),
                        src: src,
                        alt: alt,
                        role: role,
                        isInLink: !!parentAnchor,
                        linkHref: parentAnchor ? parentAnchor.href : null,
                        linkText: parentAnchor ? parentAnchor.textContent.trim() : null,
                        isDecorative: altValidation.isDecorative,
                        altValidation: altValidation,
                        xpath: getFullXPath(img) // Add XPath for section identification
                    };

                    results.images.push(imageInfo);

                    // Check for violations
                    if (alt === null) {
                        results.violations.push({
                            element: imageInfo.tag,
                            src: src,
                            issue: 'Missing alt attribute',
                            xpath: imageInfo.xpath,
                            description: 'Image is missing an alt attribute, which is required for screen reader users'
                        });
                        results.summary.missingAlt++;
                    } else if (!altValidation.valid) {
                        results.violations.push({
                            element: imageInfo.tag,
                            src: src,
                            issue: `Invalid alt text: ${altValidation.reason}`,
                            alt: alt,
                            xpath: imageInfo.xpath,
                            description: `Image has invalid alt text (${alt}): ${altValidation.reason}`
                        });
                        results.summary.invalidAlt++;
                    }

                    // Check role
                    if (!isInteractiveSVG && 
                        img.tagName.toLowerCase() === 'svg' && 
                        role !== 'img') {
                        results.violations.push({
                            element: 'svg',
                            src: src,
                            issue: 'Non-interactive SVG missing role="img"',
                            xpath: imageInfo.xpath,
                            description: 'SVG element should have role="img" to be properly announced by screen readers'
                        });
                        results.summary.missingRole++;
                    }

                    // Track decorative images
                    if (altValidation.isDecorative) {
                        results.summary.decorativeImages++;
                    }
                });

                results.summary.totalImages = images.length;

                return {
                    pageFlags: {
                        hasImagesWithoutAlt: results.summary.missingAlt > 0,
                        hasImagesWithInvalidAlt: results.summary.invalidAlt > 0,
                        hasSVGWithoutRole: results.summary.missingRole > 0,
                        details: {
                            totalImages: results.summary.totalImages,
                            missingAlt: results.summary.missingAlt,
                            invalidAlt: results.summary.invalidAlt,
                            missingRole: results.summary.missingRole,
                            decorativeImages: results.summary.decorativeImages
                         }
                    },
                    results: results
                };
            }
        ''')

        # Add section information to results
        images_data['results'] = add_section_info_to_test_results(page, images_data['results'])
        
        # Print violations with section information for debugging
        print_violations_with_sections(images_data['results']['violations'])

        return {
            'images': {
                'pageFlags': images_data['pageFlags'],
                'details': images_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'images': {
                'pageFlags': {
                    'hasImagesWithoutAlt': False,
                    'hasImagesWithInvalidAlt': False,
                    'hasSVGWithoutRole': False,
                    'details': {
                        'totalImages': 0,
                        'missingAlt': 0,
                        'invalidAlt': 0,
                        'missingRole': 0,
                        'decorativeImages': 0
                     }
                },
                'details': {
                    'images': [],
                    'violations': [{
                        'issue': 'Error evaluating images',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalImages': 0,
                        'missingAlt': 0,
                        'invalidAlt': 0,
                        'missingRole': 0,
                        'decorativeImages': 0
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }