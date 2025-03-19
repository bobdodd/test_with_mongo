from datetime import datetime

async def test_title_attribute(page):
    """
    Test proper usage of title attribute - should only be used on iframes
    """
    try:
        title_data = await page.evaluate('''
            () => {
                function analyzeTitleAttributes() {
                    const elementsWithTitle = Array.from(document.querySelectorAll('[title]'))
                    const improperTitleUse = []
                    const properTitleUse = []

                    elementsWithTitle.forEach(element => {
                        const titleValue = element.getAttribute('title')
                        const elementInfo = {
                            element: element.tagName.toLowerCase(),
                            id: element.id || null,
                            class: element.className || null,
                            title: titleValue,
                            textContent: element.textContent.trim().substring(0, 100),
                            location: {
                                inHeader: element.closest('header') !== null,
                                inNav: element.closest('nav') !== null,
                                inMain: element.closest('main') !== null,
                                inFooter: element.closest('footer') !== null
                            }
                        }

                        if (element.tagName.toLowerCase() !== 'iframe') {
                            improperTitleUse.push(elementInfo)
                        } else {
                            properTitleUse.push(elementInfo)
                        }
                    })

                    return {
                        improperTitleUse,
                        properTitleUse,
                        summary: {
                            totalTitleAttributes: elementsWithTitle.length,
                            improperUseCount: improperTitleUse.length,
                            properUseCount: properTitleUse.length
                        }
                    }
                }

                const titleResults = analyzeTitleAttributes()

                return {
                    pageFlags: {
                        hasImproperTitleAttributes: titleResults.improperTitleUse.length > 0,
                        details: {
                            totalTitleAttributes: titleResults.summary.totalTitleAttributes,
                            improperUseCount: titleResults.summary.improperUseCount,
                            properUseCount: titleResults.summary.properUseCount
                        }
                    },
                    results: {
                        improperUse: titleResults.improperTitleUse,
                        properUse: titleResults.properTitleUse,
                        violations: titleResults.improperTitleUse.map(item => ({
                            issue: 'Improper use of title attribute',
                            element: item.element,
                            details: `Title attribute should only be used on iframes. Found on ${item.element}` +
                                   `${item.id ? ` with id "${item.id}"` : ''} with title "${item.title}"`
                        }))
                    }
                }
            }
        ''')

        return {
            'titleAttribute': {
                'pageFlags': title_data['pageFlags'],
                'details': title_data['results'],
                'timestamp': datetime.now().isoformat()
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'titleAttribute': {
                'pageFlags': {
                    'hasImproperTitleAttributes': False,
                    'details': {
                        'totalTitleAttributes': 0,
                        'improperUseCount': 0,
                        'properUseCount': 0
                    }
                },
                'details': {
                    'improperUse': [],
                    'properUse': [],
                    'violations': [{
                        'issue': 'Error evaluating title attributes',
                        'details': str(e)
                    }]
                }
            }
        }