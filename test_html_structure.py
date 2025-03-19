from datetime import datetime

async def test_html_structure(page, is_homepage=False):
    """
    Test HTML structure requirements including doctype, lang attribute, and title
    """
    try:
        structure_data = await page.evaluate('''
            (isHomepage) => {
                function isValidLanguageTag(lang) {
                    return /^[a-zA-Z]{2,3}(-[a-zA-Z]{2,4})?$/i.test(lang);
                }

                function analyzeTitle(title, isHomepage) {
                    const titleText = title.trim();
                    const hasWords = /[a-zA-Z]+/.test(titleText);
                    const parts = titleText.split(/[-–—|]/); // Common title delimiters
                    
                    return {
                        text: titleText,
                        hasWords: hasWords,
                        length: titleText.length,
                        parts: parts.map(p => p.trim()).filter(p => p),
                        isValid: hasWords && titleText.length > 0,
                        followsPattern: !isHomepage && parts.length > 1
                    };
                }

                // Get doctype
                const doctype = document.doctype;
                const doctypeInfo = doctype ? {
                    name: doctype.name,
                    publicId: doctype.publicId,
                    systemId: doctype.systemId
                } : null;

                // Get html element attributes
                const htmlElement = document.documentElement;
                const lang = htmlElement.getAttribute('lang');
                const xmlLang = htmlElement.getAttribute('xml:lang');
                const dir = htmlElement.getAttribute('dir');

                // Get title
                const titleElement = document.querySelector('title');
                const titleAnalysis = titleElement ? 
                    analyzeTitle(titleElement.textContent, isHomepage) : null;

                return {
                    doctype: {
                        exists: !!doctype,
                        info: doctypeInfo
                    },
                    language: {
                        lang: lang,
                        xmlLang: xmlLang,
                        langValid: lang ? isValidLanguageTag(lang) : false,
                        xmlLangValid: xmlLang ? isValidLanguageTag(xmlLang) : false,
                        langsMatch: lang && xmlLang ? lang.toLowerCase() === xmlLang.toLowerCase() : true,
                        dir: dir
                    },
                    title: {
                        exists: !!titleElement,
                        analysis: titleAnalysis
                    }
                };
            }
        ''', is_homepage)

        # Process results and add test outcomes
        results = {
            'tests': {
                'hasDoctype': structure_data['doctype']['exists'],
                'hasValidLang': structure_data['language']['langValid'],
                'hasValidTitle': structure_data['title']['exists'] and 
                                structure_data['title']['analysis']['isValid'],
                'hasMatchingLangs': structure_data['language']['langsMatch']
            },
            'details': structure_data,
            'violations': []
        }

        # Collect violations
        if not structure_data['doctype']['exists']:
            results['violations'].append({
                'type': 'doctype',
                'message': 'Document is missing DOCTYPE declaration'
            })

        if not structure_data['language']['lang']:
            results['violations'].append({
                'type': 'language',
                'message': 'Missing lang attribute in <html> tag'
            })
        elif not structure_data['language']['langValid']:
            results['violations'].append({
                'type': 'language',
                'message': f'Invalid lang attribute value: {structure_data["language"]["lang"]}'
            })

        if structure_data['language']['xmlLang'] and not structure_data['language']['langsMatch']:
            results['violations'].append({
                'type': 'language',
                'message': 'lang and xml:lang attributes do not match'
            })

        if not structure_data['title']['exists']:
            results['violations'].append({
                'type': 'title',
                'message': 'Missing <title> element'
            })
        elif not structure_data['title']['analysis']['isValid']:
            results['violations'].append({
                'type': 'title',
                'message': 'Title is empty or contains no words'
            })
        elif not is_homepage and not structure_data['title']['analysis']['followsPattern']:
            results['violations'].append({
                'type': 'title',
                'message': 'Title does not follow pattern: page title <delimiter> site name'
            })

        return {
            'html_structure': results,
            'timestamp': datetime.now().isoformat()
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'html_structure': {
                'tests': {
                    'hasDoctype': False,
                    'hasValidLang': False,
                    'hasValidTitle': False,
                    'hasMatchingLangs': False
                },
                'details': None,
                'violations': [{
                    'type': 'error',
                    'message': str(e)
                }]
            }
        }