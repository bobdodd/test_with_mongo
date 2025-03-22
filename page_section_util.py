"""
Utility functions for detecting which page section (header, footer, content area, etc.) 
an element belongs to based on page structure analysis.
"""

def categorize_element_by_section(element_xpath, page_structure_data):
    """
    Determine which section of the page an element belongs to
    based on the page structure analysis.
    
    Args:
        element_xpath (str): The XPath of the element to categorize
        page_structure_data (dict): The result of test_page_structure
        
    Returns:
        dict: Information about the section where the element is located
            {
                'section_type': One of ('header', 'footer', 'navigation', 'mainContent', 
                                      'complementaryContent', 'unknown'),
                'section_name': Human-readable name of the section,
                'primary': Boolean indicating if it's a primary section (vs secondary)
            }
    """
    if not page_structure_data or not element_xpath:
        return {
            'section_type': 'unknown',
            'section_name': 'Unknown Section',
            'primary': False
        }
    
    # Extract key elements from page structure
    key_elements = page_structure_data.get('keyElements', {})
    
    # Check if the page structure has xpath values for key elements
    def is_element_within_section(element_xpath, section_data):
        if not section_data:
            return False
            
        section_xpath = section_data.get('xpath', '')
        if not section_xpath:
            return False
            
        # Check if element xpath starts with the section xpath (indicating containment)
        return element_xpath.startswith(section_xpath)
    
    # Check element against all key sections
    sections_to_check = [
        ('header', 'primaryHeader', 'Header', True),
        ('footer', 'primaryFooter', 'Footer', True),
        ('navigation', 'navigation', 'Navigation Menu', True),
        ('mainContent', 'mainContent', 'Main Content Area', True),
        ('complementaryContent', 'complementaryContent', 'Sidebar/Complementary Content', True)
    ]
    
    for section_type, section_key, section_name, is_primary in sections_to_check:
        section_data = key_elements.get(section_key, {})
        if is_element_within_section(element_xpath, section_data):
            return {
                'section_type': section_type,
                'section_name': section_name,
                'primary': is_primary
            }
    
    # Check secondary sections if available
    secondary_headers = page_structure_data.get('secondaryElements', {}).get('headers', [])
    for idx, header in enumerate(secondary_headers):
        if is_element_within_section(element_xpath, header):
            return {
                'section_type': 'header',
                'section_name': f'Secondary Header {idx + 1}',
                'primary': False
            }
            
    secondary_footers = page_structure_data.get('secondaryElements', {}).get('footers', [])
    for idx, footer in enumerate(secondary_footers):
        if is_element_within_section(element_xpath, footer):
            return {
                'section_type': 'footer',
                'section_name': f'Secondary Footer {idx + 1}',
                'primary': False
            }
    
    # Check if element is within special components
    special_components = [
        ('search', 'searchComponent', 'Search Section'),
        ('cookie', 'cookieNotice', 'Cookie Notice'),
        ('heroSection', 'heroSection', 'Hero Section'),
        ('form', 'form', 'Form Section')
    ]
    
    for comp_type, comp_key, comp_name in special_components:
        component = page_structure_data.get('components', {}).get(comp_key, {})
        if component and is_element_within_section(element_xpath, component):
            return {
                'section_type': comp_type,
                'section_name': comp_name,
                'primary': False
            }
    
    # If no section matched, determine if it might be in content area based on position
    if 'viewport' in page_structure_data:
        viewport_height = page_structure_data.get('viewport', {}).get('height', 0)
        
        # Try to extract element position from xpath attributes if available
        element_position = extract_position_from_xpath(element_xpath)
        
        if element_position:
            # Rough heuristic: divide page into thirds
            if element_position['y'] < viewport_height / 3:
                return {
                    'section_type': 'topArea',
                    'section_name': 'Top of Page',
                    'primary': False
                }
            elif element_position['y'] > (viewport_height * 2 / 3):
                return {
                    'section_type': 'bottomArea',
                    'section_name': 'Bottom of Page',
                    'primary': False
                }
            else:
                return {
                    'section_type': 'middleArea',
                    'section_name': 'Middle of Page',
                    'primary': False
                }
    
    # Default if no section is identified
    return {
        'section_type': 'unknown',
        'section_name': 'Unknown Section',
        'primary': False
    }

def extract_position_from_xpath(xpath):
    """
    Try to extract positional information from an xpath if it contains
    position attributes (sometimes added by test scripts).
    
    Args:
        xpath (str): The xpath to analyze
        
    Returns:
        dict: Position information if available, otherwise None
    """
    # This is a simple implementation - would need to be enhanced
    # based on how position data is actually encoded in your XPaths
    try:
        if 'position(' in xpath:
            # Extract position attributes if available in format position(x,y,width,height)
            pos_start = xpath.find('position(')
            if pos_start > 0:
                pos_end = xpath.find(')', pos_start)
                pos_str = xpath[pos_start + 9:pos_end]
                parts = [int(p.strip()) for p in pos_str.split(',')]
                if len(parts) >= 4:
                    return {
                        'x': parts[0],
                        'y': parts[1],
                        'width': parts[2],
                        'height': parts[3]
                    }
    except:
        pass
    
    return None

def enrich_violations_with_section_info(violations, page_structure_data):
    """
    Takes a list of violations and adds section information to each one.
    
    Args:
        violations (list): List of violation dictionaries, each should have an 'xpath' field
        page_structure_data (dict): The result of test_page_structure
        
    Returns:
        list: The same violations with added 'section' field
    """
    enriched_violations = []
    
    for violation in violations:
        if 'xpath' in violation:
            section = categorize_element_by_section(violation['xpath'], page_structure_data)
            # Create a copy of the violation with section info added
            enriched_violation = violation.copy()
            enriched_violation['section'] = section
            enriched_violations.append(enriched_violation)
        else:
            # If no xpath, can't determine section
            violation['section'] = {
                'section_type': 'unknown',
                'section_name': 'Unknown Section',
                'primary': False
            }
            enriched_violations.append(violation)
    
    return enriched_violations