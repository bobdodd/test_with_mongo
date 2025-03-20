from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "HTML Structure Analysis",
    "description": "Evaluates fundamental HTML document structure and metadata elements required for accessibility and proper browser rendering. This test checks for proper DOCTYPE declaration, language attributes, and page title elements.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "tests": "Boolean flags for each specific HTML structure test",
        "details.doctype": "Information about the document's DOCTYPE declaration",
        "details.language": "Information about language attributes",
        "details.title": "Information about the document title element",
        "violations": "List of HTML structure violations"
    },
    "tests": [
        {
            "id": "doctype-presence",
            "name": "DOCTYPE Declaration",
            "description": "Checks if the HTML document has a proper DOCTYPE declaration at the beginning of the document.",
            "impact": "medium",
            "wcagCriteria": ["4.1.1"],
            "howToFix": "Add a proper DOCTYPE declaration at the beginning of the HTML document. For HTML5, use <!DOCTYPE html>.",
            "resultsFields": {
                "tests.hasDoctype": "Boolean indicating if the document has a DOCTYPE declaration",
                "details.doctype.exists": "Boolean indicating if DOCTYPE exists",
                "details.doctype.info": "Details about the DOCTYPE declaration"
            }
        },
        {
            "id": "language-declaration",
            "name": "Language Declaration",
            "description": "Verifies that the HTML document specifies a valid language using the lang attribute.",
            "impact": "high",
            "wcagCriteria": ["3.1.1"],
            "howToFix": "Add a valid lang attribute to the <html> element that reflects the primary language of the document (e.g., lang='en' for English).",
            "resultsFields": {
                "tests.hasValidLang": "Boolean indicating if the document has a valid lang attribute",
                "details.language.lang": "Value of the lang attribute",
                "details.language.langValid": "Boolean indicating if the lang value is valid"
            }
        },
        {
            "id": "matching-language-attributes",
            "name": "Matching Language Attributes",
            "description": "Checks if lang and xml:lang attributes match when both are present.",
            "impact": "medium",
            "wcagCriteria": ["3.1.1"],
            "howToFix": "Ensure that lang and xml:lang attributes (if both are present) have matching values.",
            "resultsFields": {
                "tests.hasMatchingLangs": "Boolean indicating if lang and xml:lang attributes match",
                "details.language.langsMatch": "Boolean indicating if both language attributes match"
            }
        },
        {
            "id": "title-presence",
            "name": "Page Title Presence",
            "description": "Checks if the page has a descriptive title element.",
            "impact": "high",
            "wcagCriteria": ["2.4.2"],
            "howToFix": "Add a descriptive <title> element within the document <head> that clearly identifies the page content.",
            "resultsFields": {
                "tests.hasValidTitle": "Boolean indicating if the document has a valid title",
                "details.title.exists": "Boolean indicating if title element exists",
                "details.title.analysis": "Analysis of the title content"
            }
        },
        {
            "id": "title-pattern",
            "name": "Title Pattern Consistency",
            "description": "Verifies that non-homepage titles follow a consistent pattern, typically 'Page Name - Site Name'.",
            "impact": "medium",
            "wcagCriteria": ["2.4.2"],
            "howToFix": "Format page titles consistently with a delimiter between the page-specific title and the site name (e.g., 'About Us - Company Name').",
            "resultsFields": {
                "details.title.analysis.followsPattern": "Boolean indicating if title follows consistent pattern"
            }
        }
    ]
}

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
            'html_structure': {
                'tests': results['tests'],
                'details': results['details'],
                'violations': results['violations'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
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
                }],
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }