from datetime import datetime
import re

async def test_images(page):
    """
    Test images for proper alt text and role attributes according to accessibility requirements
    """
    try:
        images_data = await page.evaluate('''
            () => {
                function validateAltText(alt, src) {
                    if (alt === null) return { valid: false, reason: 'Missing alt attribute' };
                    
                    // Check for HTML tags
                    if (/<[^>]*>/g.test(alt)) {
                        return { valid: false, reason: 'Contains HTML elements' };
                    }

                    // Trim the alt text
                    const trimmedAlt = alt.trim();

                    // Check for empty string (which is valid in some cases)
                    if (trimmedAlt === '') {
                        return { valid: true, isDecorative: true };
                    }

                    // Check for whitespace only
                    if (!trimmedAlt) {
                        return { valid: false, reason: 'Contains only whitespace' };
                    }

                    // Check for punctuation only
                    if (/^[.,/#!$%^&*;:{}=\-_`~()]+$/.test(trimmedAlt)) {
                        return { valid: false, reason: 'Contains only punctuation' };
                    }

                    // Check if it's just a URL or filename
                    const urlPattern = /^(https?:\/\/|www\.|\/|\w+\.[a-zA-Z]{3,4}$)/i;
                    if (urlPattern.test(trimmedAlt) || 
                        trimmedAlt.toLowerCase() === src.toLowerCase() ||
                        src.toLowerCase().includes(trimmedAlt.toLowerCase())) {
                        return { valid: false, reason: 'Appears to be URL or filename' };
                    }

                    // Check length
                    if (trimmedAlt.length > 200) {
                        return { valid: false, reason: 'Exceeds 200 characters' };
                    }

                    return { valid: true, isDecorative: false };
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
                        altValidation: altValidation
                    };

                    results.images.push(imageInfo);

                    // Check for violations
                    if (alt === null) {
                        results.violations.push({
                            element: imageInfo.tag,
                            src: src,
                            issue: 'Missing alt attribute'
                        });
                        results.summary.missingAlt++;
                    } else if (!altValidation.valid) {
                        results.violations.push({
                            element: imageInfo.tag,
                            src: src,
                            issue: `Invalid alt text: ${altValidation.reason}`,
                            alt: alt
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
                            issue: 'Non-interactive SVG missing role="img"'
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

        return {
            'images': {
                'pageFlags': images_data['pageFlags'],
                'details': images_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }