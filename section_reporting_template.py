"""
Template for adding section reporting to test modules
"""
from datetime import datetime
# Handle import errors gracefully - allows both package and direct imports
try:
    # Try direct import first (for when run as a script)
    from src.test_with_mongo.page_section_util import enrich_violations_with_section_info
except ImportError:
    try:
        # Then try relative import (for when imported as a module)
        from .page_section_util import enrich_violations_with_section_info
    except ImportError:
        # Fallback to non-relative import 
        from page_section_util import enrich_violations_with_section_info


def add_section_info_to_test_results(page, test_results):
    """
    Helper function to add section information to test results.
    
    Args:
        page: The Puppeteer page object with _accessibility_context
        test_results: The test results containing violations
        
    Returns:
        The updated test results with section information added
    """
    # Get page structure data from the context
    page_structure_data = {}
    if hasattr(page, '_accessibility_context') and page._accessibility_context:
        page_structure_data = page._accessibility_context.get('page_structure', {})
    
    # Get violations from test results
    if 'violations' in test_results:
        # Direct violations list
        violations = test_results['violations']
        enriched_violations = enrich_violations_with_section_info(violations, page_structure_data)
        test_results['violations'] = enriched_violations
        test_results['section_statistics'] = calculate_section_statistics(enriched_violations)
    elif 'details' in test_results and 'violations' in test_results['details']:
        # Nested violations list
        violations = test_results['details']['violations']
        enriched_violations = enrich_violations_with_section_info(violations, page_structure_data)
        test_results['details']['violations'] = enriched_violations
        test_results['details']['section_statistics'] = calculate_section_statistics(enriched_violations)
    
    return test_results

def calculate_section_statistics(violations):
    """
    Calculate statistics about which sections have violations
    
    Args:
        violations: List of violations with section information
        
    Returns:
        Dictionary with section statistics
    """
    section_stats = {}
    for violation in violations:
        section = violation.get('section', {}).get('section_type', 'unknown')
        if section not in section_stats:
            section_stats[section] = 0
        section_stats[section] += 1
    
    return section_stats

def print_violations_with_sections(violations):
    """
    Print violations with section information for debugging
    
    Args:
        violations: List of violations with section information
    """
    if not violations:
        return
        
    print("\nViolations by Page Section:")
    for violation in violations:
        section_info = violation.get('section', {})
        section_name = section_info.get('section_name', 'Unknown Section')
        
        print(f"\nElement: {violation.get('element', 'Unknown Element')}")
        if 'issue' in violation:
            print(f"Issue: {violation['issue']}")
        if 'description' in violation:
            print(f"Description: {violation['description']}")
        if 'role' in violation:
            print(f"Role: {violation['role']}")
        print(f"Section: {section_name}")
        if 'xpath' in violation:
            print(f"XPath: {violation['xpath']}")
        print("-" * 50)

"""
Example usage in a test module:

from section_reporting_template import add_section_info_to_test_results, print_violations_with_sections

async def test_example(page):
    try:
        # Run your test evaluation
        test_data = await page.evaluate('''() => {
            // Your test logic
            return {
                violations: [
                    {
                        element: 'button',
                        issue: 'Missing label',
                        xpath: '/html/body/div[1]/button[2]'
                    }
                ]
            };
        }''')
        
        # Add section information to the results
        test_data = add_section_info_to_test_results(page, test_data)
        
        # Print violations for debugging
        print_violations_with_sections(test_data['violations'])
        
        return {
            'example_test': {
                'details': test_data,
                'timestamp': datetime.now().isoformat()
            }
        }
    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
"""