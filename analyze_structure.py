# analyze_structure.py - Analyzes common structural elements across sites

from pymongo import MongoClient
from collections import defaultdict, Counter
import json
from bson import ObjectId
from datetime import datetime
import pprint

class AccessibilityDB:
    def __init__(self):
        try:
            self.client = MongoClient('mongodb://localhost:27017/')
            self.db = self.client['accessibility_tests']
            self.test_runs = self.db['test_runs']
            self.page_results = self.db['page_results']
            self.structure_analysis = self.db['structure_analysis']
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise

    def get_page_results(self, test_run_ids=None):
        """Get all page results for specific test runs"""
        query = {}
        if test_run_ids:
            if isinstance(test_run_ids, list):
                query['test_run_id'] = {'$in': test_run_ids}
            else:
                query['test_run_id'] = test_run_ids
        return list(self.page_results.find(query))

    def get_most_recent_test_run_id(self):
        """Get the most recent test run ID"""
        latest_run = self.test_runs.find_one(
            sort=[('timestamp_start', -1)]
        )
        return str(latest_run['_id']) if latest_run else None

    def save_structure_analysis(self, analysis_data):
        """Save structure analysis results to a separate collection"""
        return self.structure_analysis.insert_one(analysis_data)

    def __del__(self):
        if hasattr(self, 'client'):
            self.client.close()

def analyze_common_structure():
    """
    Analyze common structural elements by site, then provide an overall summary.
    """
    db = AccessibilityDB()
    
    # Get the most recent test run ID
    test_run_id = db.get_most_recent_test_run_id()
    print(f"Analyzing structure for test run: {test_run_id}")
    
    # Get all page results for this test run
    page_results = db.get_page_results(test_run_id)
    print(f"Found {len(page_results)} pages to analyze")
    
    # Group results by domain
    pages_by_domain = {}
    all_accessible_names = {}
    all_structure_data = {}
    
    for result in page_results:
        url = result['url']
        domain = url.replace('http://', '').replace('https://', '').split('/')[0]
        
        # Initialize domain entry if needed
        if domain not in pages_by_domain:
            pages_by_domain[domain] = []
            all_accessible_names[domain] = {}
            all_structure_data[domain] = {}
        
        # Add page to domain list
        pages_by_domain[domain].append(url)
        
        # Extract accessible_names data
        elements = []
        if 'results' in result and 'accessibility' in result['results']:
            accessibility = result['results']['accessibility']
            
            # Try the accessible_names test
            if 'tests' in accessibility and 'accessible_names' in accessibility['tests']:
                accessible_names = accessibility['tests']['accessible_names']
                if 'accessible_names' in accessible_names:
                    details = accessible_names['accessible_names'].get('details', {})
                    elements = details.get('elements', [])
        
        if elements:
            all_accessible_names[domain][url] = elements
        
        # Extract structure data if available
        if 'results' in result and 'accessibility' in result['results']:
            accessibility = result['results']['accessibility']
            
            if 'tests' in accessibility and 'page_structure' in accessibility['tests']:
                structure_data = accessibility['tests']['page_structure'].get('page_structure', {})
                
                if structure_data:
                    all_structure_data[domain][url] = structure_data
    
    print(f"Grouped pages into {len(pages_by_domain)} domains")
    
    # Analyze each domain separately
    domain_analyses = {}
    
    for domain, urls in pages_by_domain.items():
        print(f"Analyzing domain: {domain} ({len(urls)} pages)")
        
        # Use structure data if available, otherwise fall back to accessible_names
        if domain in all_structure_data and all_structure_data[domain]:
            analysis = analyze_domain_structure(domain, all_structure_data[domain])
        elif domain in all_accessible_names and all_accessible_names[domain]:
            analysis = analyze_domain_accessible_names(domain, all_accessible_names[domain])
        else:
            analysis = None
            
        if analysis:
            domain_analyses[domain] = analysis
    
    # Calculate overall cross-site consistency
    overall_analysis = {
        'test_run_id': test_run_id,
        'timestamp': datetime.now().isoformat(),
        'total_pages': len(page_results),
        'total_domains': len(pages_by_domain),
        'domains_analyzed': list(domain_analyses.keys()),
        'domain_analyses': domain_analyses,
        'overall_summary': calculate_overall_summary(domain_analyses)
    }
    
    # Save the analysis to MongoDB
    result = db.save_structure_analysis(overall_analysis)
    
    print(f"Structure analysis completed and saved with ID: {result.inserted_id}")
    
    # Print summary
    print_analysis_summary(overall_analysis)
    
    return overall_analysis

def analyze_domain_structure(domain, structure_data_by_url):
    """Analyze page structure for a specific domain using dedicated structure data"""
    
    # Analyze primary header consistency
    header_analysis = analyze_component_consistency(
        structure_data_by_url, 
        lambda data: data.get('keyElements', {}).get('primaryHeader', {})
    )
    
    # Analyze primary footer consistency
    footer_analysis = analyze_component_consistency(
        structure_data_by_url, 
        lambda data: data.get('keyElements', {}).get('primaryFooter', {})
    )
    
    # Analyze secondary headers
    secondary_headers_count = sum(1 for data in structure_data_by_url.values() 
                               if data.get('pageFlags', {}).get('hasSecondaryHeaders', False))
    
    # Analyze secondary footers
    secondary_footers_count = sum(1 for data in structure_data_by_url.values() 
                               if data.get('pageFlags', {}).get('hasSecondaryFooters', False))
    
    # Analyze navigation consistency
    navigation_analysis = analyze_component_consistency(
        structure_data_by_url, 
        lambda data: data.get('keyElements', {}).get('navigation', {})
    )
    
    # Analyze main content consistency
    main_content_analysis = analyze_component_consistency(
        structure_data_by_url, 
        lambda data: data.get('keyElements', {}).get('mainContent', {})
    )
    
    # Analyze complementary content consistency
    complementary_analysis = analyze_component_consistency(
        structure_data_by_url, 
        lambda data: data.get('keyElements', {}).get('complementaryContent', {})
    )
    
    # Analyze component presence
    component_presence = {
        'search': sum(1 for data in structure_data_by_url.values() if data.get('pageFlags', {}).get('hasSearchComponent', False)),
        'socialMedia': sum(1 for data in structure_data_by_url.values() if data.get('pageFlags', {}).get('hasSocialMediaLinks', False)),
        'cookieNotice': sum(1 for data in structure_data_by_url.values() if data.get('pageFlags', {}).get('hasCookieNotice', False)),
        'sidebars': sum(1 for data in structure_data_by_url.values() if data.get('pageFlags', {}).get('hasSidebars', False))
    }
    
    # Analyze recurring elements presence
    recurring_elements = {
        'chatbots': sum(1 for data in structure_data_by_url.values() 
                      if data.get('pageFlags', {}).get('hasChatbot', False)),
        'cookieNotices': sum(1 for data in structure_data_by_url.values() 
                           if data.get('pageFlags', {}).get('hasCookieNotice', False)),
        'newsletters': sum(1 for data in structure_data_by_url.values() 
                         if data.get('pageFlags', {}).get('hasNewsletterSignup', False)),
        'popups': sum(1 for data in structure_data_by_url.values() 
                     if data.get('pageFlags', {}).get('hasPopups', False)),
        'forms': sum(1 for data in structure_data_by_url.values() 
                   if data.get('pageFlags', {}).get('hasForms', False))
    }
    
    # Analyze forms data for this domain
    forms_analysis = analyze_forms_for_domain(domain, structure_data_by_url)
    
    # Extract complexity data
    complexity_data = {
        'header': {},
        'footer': {},
        'navigation': {},
        'mainContent': {},
        'complementaryContent': {}
    }
    
    for url, data in structure_data_by_url.items():
        complexity = data.get('complexityData', {})
        for component in complexity_data.keys():
            if component in complexity:
                complexity_data[component][url] = complexity[component]
    
    # Extract interactive elements summary
    interactive_elements = {
        'header': {},
        'footer': {},
        'navigation': {},
        'mainContent': {},
        'complementaryContent': {}
    }
    
    for url, data in structure_data_by_url.items():
        interactive = data.get('interactiveElements', {})
        for component in interactive_elements.keys():
            if component in interactive:
                interactive_elements[component][url] = interactive[component]
    
    # Sample pages for detailed analysis
    sample_pages = {}
    if structure_data_by_url:
        # Get a representative sample page
        url = next(iter(structure_data_by_url.keys()))
        sample_pages[url] = structure_data_by_url[url]
    
    # Calculate overall consistency score for this domain
    scores = [
        header_analysis.get('consistency_score', 0),
        footer_analysis.get('consistency_score', 0),
        navigation_analysis.get('consistency_score', 0),
        main_content_analysis.get('consistency_score', 0) if main_content_analysis else 0,
        complementary_analysis.get('consistency_score', 0) if complementary_analysis else 0
    ]
    # Filter out zero scores (components that might not be present)
    scores = [score for score in scores if score > 0]
    overall_score = sum(scores) / len(scores) if scores else 0
    
    return {
        'domain': domain,
        'page_count': len(structure_data_by_url),
        'header_analysis': header_analysis,
        'footer_analysis': footer_analysis,
        'secondary_headers': {
            'count': secondary_headers_count,
            'presence_ratio': secondary_headers_count / len(structure_data_by_url) if structure_data_by_url else 0
        },
        'secondary_footers': {
            'count': secondary_footers_count,
            'presence_ratio': secondary_footers_count / len(structure_data_by_url) if structure_data_by_url else 0
        },
        'navigation_analysis': navigation_analysis,
        'main_content_analysis': main_content_analysis,
        'complementary_analysis': complementary_analysis,
        'component_presence': component_presence,
        'recurring_elements': recurring_elements,
        'forms_analysis': forms_analysis,
        'complexity_data': complexity_data,
        'interactive_elements': interactive_elements,
        'content_blocks': {
            'heroSections': sum(1 for data in structure_data_by_url.values() 
                             if data.get('pageFlags', {}).get('hasHeroSection', False)),
            'cardGrids': sum(1 for data in structure_data_by_url.values() 
                          if data.get('pageFlags', {}).get('hasCardGrids', False)),
            'featureSections': sum(1 for data in structure_data_by_url.values() 
                                if data.get('pageFlags', {}).get('hasFeatureSections', False)),
            'carousels': sum(1 for data in structure_data_by_url.values() 
                          if data.get('pageFlags', {}).get('hasCarousels', False))
        },
        'repetitive_patterns': {
            'found': sum(1 for data in structure_data_by_url.values() 
                      if data.get('pageFlags', {}).get('hasRepetitivePatterns', False))
        },
        'overall_consistency_score': overall_score,
        'sample_pages': sample_pages,
        'analysis_method': 'page_structure'
    }

def analyze_forms_for_domain(domain, structure_data_by_url):
    """
    Analyze forms for a specific domain
    """
    forms_by_url = {}
    form_types = {}
    form_locations = {}
    unique_forms = {}
    
    for url, data in structure_data_by_url.items():
        forms = data.get('fullStructure', {}).get('forms', [])
        if forms:
            forms_by_url[url] = []
            
            for form in forms:
                form_type = form.get('formType', 'unknown')
                form_location = form.get('location', 'unknown')
                has_submit = form.get('hasSubmit', False)
                
                # Track form type counts
                if form_type not in form_types:
                    form_types[form_type] = 0
                form_types[form_type] += 1
                
                # Track form location counts
                if form_location not in form_locations:
                    form_locations[form_location] = 0
                form_locations[form_location] += 1
                
                # Create a form record
                form_record = {
                    'url': url,
                    'type': form_type,
                    'location': form_location,
                    'has_submit': has_submit,
                    'inputs': form.get('inputs', []),
                    'buttons': form.get('buttons', []),
                    'fingerprint': form.get('fingerprint', '')
                }
                
                # Add to unique forms using fingerprint for deduplication
                fingerprint = form.get('fingerprint', '')
                if fingerprint and fingerprint not in unique_forms:
                    unique_forms[fingerprint] = form_record
                
                # Add to forms for this URL
                forms_by_url[url].append(form_record)
    
    return {
        'forms_by_url': forms_by_url,
        'form_types': form_types,
        'form_locations': form_locations,
        'total_forms': sum(len(forms) for forms in forms_by_url.values()),
        'unique_forms': unique_forms,
        'total_unique_forms': len(unique_forms)
    }

def analyze_forms_across_sites(domain_analyses):
    """
    Analyze forms across all domains and pages, organizing by type and deduplicate.
    """
    all_forms = {}
    unique_forms = {}
    forms_by_page = {}
    forms_by_domain = {}
    
    # First pass: collect all forms
    for domain, domain_data in domain_analyses.items():
        forms_analysis = domain_data.get('forms_analysis', {})
        if not forms_analysis:
            continue
            
        forms_by_url = forms_analysis.get('forms_by_url', {})
        
        for page_url, forms in forms_by_url.items():
            # Track by page
            if page_url not in forms_by_page:
                forms_by_page[page_url] = []
            
            # Track by domain
            if domain not in forms_by_domain:
                forms_by_domain[domain] = []
            
            for form in forms:
                # Create a form record
                form_record = {
                    'domain': domain,
                    'page_url': page_url,
                    'form_type': form.get('type', 'unknown'),
                    'location': form.get('location', 'unknown'),
                    'has_submit': form.get('has_submit', False),
                    'input_count': len(form.get('inputs', [])),
                    'button_count': len(form.get('buttons', [])),
                    'fingerprint': form.get('fingerprint', '')
                }
                
                # Add to collections
                fingerprint = form.get('fingerprint', '')
                if fingerprint and fingerprint not in unique_forms:
                    unique_forms[fingerprint] = form_record
                
                forms_by_page[page_url].append(form_record)
                forms_by_domain[domain].append(form_record)
    
    # Group forms by type
    forms_by_type = {}
    for fingerprint, form in unique_forms.items():
        form_type = form['form_type']
        if form_type not in forms_by_type:
            forms_by_type[form_type] = []
        forms_by_type[form_type].append(form)
    
    return {
        'forms_by_type': forms_by_type,
        'forms_by_page': forms_by_page,
        'forms_by_domain': forms_by_domain,
        'unique_forms': unique_forms
    }

def analyze_domain_accessible_names(domain, accessible_names_by_url):
    """
    Analyze page structure for a specific domain using accessible_names data as fallback
    This is a fallback method that tries to identify headers, footers, etc. from element properties
    """
    
    # Helper function to categorize elements
    def categorize_element(element):
        tag = str(element.get('tag', '')).lower()
        role = str(element.get('role', '')).lower() if element.get('role') is not None else ''
        name = str(element.get('accessibleName', '')).lower() if element.get('accessibleName') is not None else ''
        
        categories = []
        
        # Header detection
        if (tag == 'header' or 
            'header' in name or 
            (tag == 'nav' and 'main' in name) or
            (tag == 'a' and ('home' in name or 'logo' in name))):
            categories.append('header')
        
        # Footer detection
        if (tag == 'footer' or 
            'footer' in name or 
            'copyright' in name or
            'contentinfo' in role):
            categories.append('footer')
        
        # Navigation detection
        if (tag == 'nav' or
            role == 'navigation' or
            (tag == 'ul' and name and ('menu' in name or 'nav' in name))):
            categories.append('navigation')
        
        # Main content detection
        if (tag == 'main' or
            role == 'main' or
            'content' in name or
            'article' in tag):
            categories.append('mainContent')
        
        # Complementary content detection
        if (tag == 'aside' or
            role == 'complementary' or
            'sidebar' in name or
            'related' in name):
            categories.append('complementaryContent')
        
        # Search component detection
        if ('search' in name or 
            'search' in role or 
            (tag == 'input' and 'search' in name)):
            categories.append('search')
        
        return categories
    
    # Prepare element categorization by URL
    categorized_elements = {}
    
    for url, elements in accessible_names_by_url.items():
        categorized_elements[url] = {
            'header': [],
            'footer': [],
            'navigation': [],
            'mainContent': [],
            'complementaryContent': [],
            'search': []
        }
        
        for element in elements:
            categories = categorize_element(element)
            for category in categories:
                if category in categorized_elements[url]:
                    categorized_elements[url][category].append(element)
    
    # Count how many pages have each component
    pages_with_header = sum(1 for url in categorized_elements if categorized_elements[url]['header'])
    pages_with_footer = sum(1 for url in categorized_elements if categorized_elements[url]['footer'])
    pages_with_navigation = sum(1 for url in categorized_elements if categorized_elements[url]['navigation'])
    pages_with_main = sum(1 for url in categorized_elements if categorized_elements[url]['mainContent'])
    pages_with_complementary = sum(1 for url in categorized_elements if categorized_elements[url]['complementaryContent'])
    pages_with_search = sum(1 for url in categorized_elements if categorized_elements[url]['search'])
    
    # Calculate consistency scores
    def calculate_tag_consistency(category):
        tag_counts = Counter()
        for url in categorized_elements:
            elements = categorized_elements[url][category]
            if elements:
                # Count unique tags for this URL's category
                url_tags = Counter(element.get('tag', '') for element in elements)
                # Add the most common tag for this URL
                if url_tags:
                    most_common = url_tags.most_common(1)[0][0]
                    tag_counts[most_common] += 1
        
        # Return consistency score
        total_pages_with_category = sum(1 for url in categorized_elements if categorized_elements[url][category])
        if total_pages_with_category > 0:
            most_common_tag = tag_counts.most_common(1)[0] if tag_counts else ('', 0)
            return {
                'tag': most_common_tag[0],
                'count': most_common_tag[1],
                'score': most_common_tag[1] / total_pages_with_category if total_pages_with_category > 0 else 0
            }
        return {'tag': '', 'count': 0, 'score': 0}
    
    # Calculate consistency scores
    header_consistency = calculate_tag_consistency('header')
    footer_consistency = calculate_tag_consistency('footer')
    navigation_consistency = calculate_tag_consistency('navigation')
    main_consistency = calculate_tag_consistency('mainContent')
    complementary_consistency = calculate_tag_consistency('complementaryContent')
    
    # Prepare the analysis results
    total_pages = len(accessible_names_by_url)
    
    header_analysis = {
        'presence_ratio': pages_with_header / total_pages if total_pages > 0 else 0,
        'consistency_score': header_consistency['score'],
        'common_patterns': {
            'tag': header_consistency['tag'],
            'tag_frequency': header_consistency['score'],
            'common_classes': [],  # Not available from accessible_names
            'typical_children_count': 0  # Not available from accessible_names
        },
        'page_count': total_pages,
        'pages_with_component': pages_with_header
    }
    
    footer_analysis = {
        'presence_ratio': pages_with_footer / total_pages if total_pages > 0 else 0,
        'consistency_score': footer_consistency['score'],
        'common_patterns': {
            'tag': footer_consistency['tag'],
            'tag_frequency': footer_consistency['score'],
            'common_classes': [],  # Not available from accessible_names
            'typical_children_count': 0  # Not available from accessible_names
        },
        'page_count': total_pages,
        'pages_with_component': pages_with_footer
    }
    
    navigation_analysis = {
        'presence_ratio': pages_with_navigation / total_pages if total_pages > 0 else 0,
        'consistency_score': navigation_consistency['score'],
        'common_patterns': {
            'tag': navigation_consistency['tag'],
            'tag_frequency': navigation_consistency['score'],
            'common_classes': [],  # Not available from accessible_names
            'typical_children_count': 0  # Not available from accessible_names
        },
        'page_count': total_pages,
        'pages_with_component': pages_with_navigation
    }
    
    main_content_analysis = {
        'presence_ratio': pages_with_main / total_pages if total_pages > 0 else 0,
        'consistency_score': main_consistency['score'],
        'common_patterns': {
            'tag': main_consistency['tag'],
            'tag_frequency': main_consistency['score'],
            'common_classes': [],  # Not available from accessible_names
            'typical_children_count': 0  # Not available from accessible_names
        },
        'page_count': total_pages,
        'pages_with_component': pages_with_main
    }
    
    complementary_analysis = {
        'presence_ratio': pages_with_complementary / total_pages if total_pages > 0 else 0,
        'consistency_score': complementary_consistency['score'],
        'common_patterns': {
            'tag': complementary_consistency['tag'],
            'tag_frequency': complementary_consistency['score'],
            'common_classes': [],  # Not available from accessible_names
            'typical_children_count': 0  # Not available from accessible_names
        },
        'page_count': total_pages,
        'pages_with_component': pages_with_complementary
    }
    
    # Prepare the component presence data
    component_presence = {
        'search': pages_with_search,
        'socialMedia': 0,  # Not easily detectable from accessible_names
        'cookieNotice': 0,  # Not easily detectable from accessible_names
        'sidebars': 0       # Not easily detectable from accessible_names
    }
    
    # Recurring elements - placeholder for accessible_names method
    recurring_elements = {
        'chatbots': 0,
        'cookieNotices': 0,
        'newsletters': 0,
        'popups': 0,
        'forms': 0
    }
    
    # Forms analysis - placeholder for accessible_names method
    forms_analysis = {
        'forms_by_url': {},
        'form_types': {},
        'form_locations': {},
        'total_forms': 0,
        'unique_forms': {},
        'total_unique_forms': 0
    }
    
    # Sample pages for detailed analysis - select a representative page
    sample_pages = {}
    if accessible_names_by_url:
        # Get a representative sample page
        sample_url = next(iter(accessible_names_by_url.keys()))
        # Create a simple structure representation from accessible names data
        sample_data = {
            'pageFlags': {
                'hasHeader': bool(categorized_elements[sample_url]['header']),
                'hasFooter': bool(categorized_elements[sample_url]['footer']),
                'hasMainNavigation': bool(categorized_elements[sample_url]['navigation']),
                'hasMainContent': bool(categorized_elements[sample_url]['mainContent']),
                'hasComplementaryContent': bool(categorized_elements[sample_url]['complementaryContent']),
                'hasSearchComponent': bool(categorized_elements[sample_url]['search'])
            },
            'keyElements': {
                'header': categorized_elements[sample_url]['header'][0] if categorized_elements[sample_url]['header'] else None,
                'footer': categorized_elements[sample_url]['footer'][0] if categorized_elements[sample_url]['footer'] else None,
                'navigation': categorized_elements[sample_url]['navigation'][0] if categorized_elements[sample_url]['navigation'] else None,
                'mainContent': categorized_elements[sample_url]['mainContent'][0] if categorized_elements[sample_url]['mainContent'] else None,
                'complementaryContent': categorized_elements[sample_url]['complementaryContent'][0] if categorized_elements[sample_url]['complementaryContent'] else None
            }
        }
        sample_pages[sample_url] = sample_data
    
    # Calculate overall consistency score for this domain - only include components that are present
    scores = [
        header_analysis.get('consistency_score', 0) if pages_with_header > 0 else 0,
        footer_analysis.get('consistency_score', 0) if pages_with_footer > 0 else 0,
        navigation_analysis.get('consistency_score', 0) if pages_with_navigation > 0 else 0,
        main_content_analysis.get('consistency_score', 0) if pages_with_main > 0 else 0,
        complementary_analysis.get('consistency_score', 0) if pages_with_complementary > 0 else 0
    ]
    # Filter out zero scores
    scores = [score for score in scores if score > 0]
    overall_score = sum(scores) / len(scores) if scores else 0
    
    return {
        'domain': domain,
        'page_count': total_pages,
        'header_analysis': header_analysis,
        'footer_analysis': footer_analysis,
        'navigation_analysis': navigation_analysis,
        'main_content_analysis': main_content_analysis,
        'complementary_analysis': complementary_analysis,
        'component_presence': component_presence,
        'recurring_elements': recurring_elements,
        'forms_analysis': forms_analysis,
        'overall_consistency_score': overall_score,
        'sample_pages': sample_pages,
        'analysis_method': 'accessible_names'
    }

def calculate_overall_summary(domain_analyses):
    """Calculate overall summary statistics across all domains"""
    
    if not domain_analyses:
        return {
            'average_consistency_score': 0,
            'domains_with_consistent_header': 0,
            'domains_with_consistent_footer': 0,
            'domains_with_consistent_navigation': 0,
            'domains_with_consistent_main': 0,
            'domains_with_consistent_complementary': 0,
            'total_domains': 0
        }
    
    # Calculate average consistency scores across domains
    total_domains = len(domain_analyses)
    overall_scores = []
    header_scores = []
    footer_scores = []
    navigation_scores = []
    main_content_scores = []
    complementary_scores = []
    
    for domain, analysis in domain_analyses.items():
        overall_scores.append(analysis.get('overall_consistency_score', 0))
        header_scores.append(analysis.get('header_analysis', {}).get('consistency_score', 0))
        footer_scores.append(analysis.get('footer_analysis', {}).get('consistency_score', 0))
        navigation_scores.append(analysis.get('navigation_analysis', {}).get('consistency_score', 0))
        
        # Add main content and complementary content scores
        if 'main_content_analysis' in analysis and analysis['main_content_analysis']:
            main_content_scores.append(analysis['main_content_analysis'].get('consistency_score', 0))
        
        if 'complementary_analysis' in analysis and analysis['complementary_analysis']:
            complementary_scores.append(analysis['complementary_analysis'].get('consistency_score', 0))
    
    # Count domains with good consistency (score >= 0.8)
    domains_with_consistent_header = sum(1 for score in header_scores if score >= 0.8)
    domains_with_consistent_footer = sum(1 for score in footer_scores if score >= 0.8)
    domains_with_consistent_navigation = sum(1 for score in navigation_scores if score >= 0.8)
    domains_with_consistent_main = sum(1 for score in main_content_scores if score >= 0.8)
    domains_with_consistent_complementary = sum(1 for score in complementary_scores if score >= 0.8)
    
    # Analyze forms across all domains
    forms_analysis = analyze_forms_across_sites(domain_analyses)
    
    # Analyze content blocks across all domains
    content_blocks_analysis = analyze_content_blocks_across_sites(domain_analyses)
    
    return {
        'average_consistency_score': sum(overall_scores) / total_domains if overall_scores else 0,
        'average_header_score': sum(header_scores) / total_domains if header_scores else 0,
        'average_footer_score': sum(footer_scores) / total_domains if footer_scores else 0,
        'average_navigation_score': sum(navigation_scores) / total_domains if navigation_scores else 0,
        'average_main_content_score': sum(main_content_scores) / len(main_content_scores) if main_content_scores else 0,
        'average_complementary_score': sum(complementary_scores) / len(complementary_scores) if complementary_scores else 0,
        'domains_with_consistent_header': domains_with_consistent_header,
        'domains_with_consistent_footer': domains_with_consistent_footer,
        'domains_with_consistent_navigation': domains_with_consistent_navigation,
        'domains_with_consistent_main': domains_with_consistent_main,
        'domains_with_consistent_complementary': domains_with_consistent_complementary,
        'forms_analysis': forms_analysis,
        'content_blocks_analysis': content_blocks_analysis,
        'total_domains': total_domains
    }

def analyze_component_consistency(structure_data_by_url, component_extractor):
    """
    Analyze consistency of a component (header, footer, navigation) across pages
    
    Args:
        structure_data_by_url: Dictionary mapping URLs to structure data
        component_extractor: Function that extracts the component from structure data
        
    Returns:
        Analysis results for the component
    """
    # Extract components from all pages
    components = {url: component_extractor(data) for url, data in structure_data_by_url.items()}
    
    # Filter out pages where the component was not found
    valid_components = {url: comp for url, comp in components.items() if comp}
    
    if not valid_components:
        return {
            'presence_ratio': 0.0,
            'consistency_score': 0.0,
            'common_patterns': {
                'tag': None,
                'tag_frequency': 0,
                'common_classes': [],
                'typical_children_count': 0
            },
            'page_count': len(structure_data_by_url),
            'pages_with_component': 0
        }
    
    # Analyze tag consistency
    tags = Counter(comp.get('tag', '').lower() for comp in valid_components.values())
    most_common_tag = tags.most_common(1)[0] if tags else (None, 0)
    
    # Analyze class/id pattern consistency
    class_patterns = Counter()
    for comp in valid_components.values():
        classes = comp.get('className', '').lower().split() if comp.get('className') else []
        for cls in classes:
            class_patterns[cls] += 1
    
    common_classes = [cls for cls, count in class_patterns.most_common(5) if count > len(valid_components) * 0.3]
    
    # Analyze structural consistency (children count, etc.)
    children_counts = Counter(len(comp.get('children', [])) for comp in valid_components.values())
    most_common_children_count = children_counts.most_common(1)[0] if children_counts else (0, 0)
    
    # Calculate overall consistency score based on multiple factors
    tag_consistency = most_common_tag[1] / len(valid_components) if len(valid_components) > 0 else 0
    class_consistency = len(common_classes) / 5  # Normalize to [0,1]
    children_consistency = most_common_children_count[1] / len(valid_components) if len(valid_components) > 0 else 0
    
    consistency_score = (tag_consistency * 0.5) + (class_consistency * 0.3) + (children_consistency * 0.2)
    
    return {
        'presence_ratio': len(valid_components) / len(structure_data_by_url),
        'consistency_score': consistency_score,
        'common_patterns': {
            'tag': most_common_tag[0],
            'tag_frequency': most_common_tag[1] / len(valid_components) if len(valid_components) > 0 else 0,
            'common_classes': common_classes,
            'typical_children_count': most_common_children_count[0]
        },
        'page_count': len(structure_data_by_url),
        'pages_with_component': len(valid_components)
    }

def print_analysis_summary(analysis):
    """Print a summary of the structure analysis"""
    print("\n=== STRUCTURE ANALYSIS SUMMARY ===")
    
    # Overall statistics
    print(f"Total domains analyzed: {analysis.get('total_domains', 0)}")
    print(f"Total pages analyzed: {analysis.get('total_pages', 0)}")
    
    # Get overall summary
    summary = analysis.get('overall_summary', {})
    overall_score = summary.get('average_consistency_score', 0) * 100
    
    print(f"\nOverall Structure Consistency Score: {overall_score:.1f}%")
    print(f"Domains with consistent headers: {summary.get('domains_with_consistent_header', 0)} of {summary.get('total_domains', 0)}")
    print(f"Domains with consistent footers: {summary.get('domains_with_consistent_footer', 0)} of {summary.get('total_domains', 0)}")
    print(f"Domains with consistent navigation: {summary.get('domains_with_consistent_navigation', 0)} of {summary.get('total_domains', 0)}")
    print(f"Domains with consistent main content: {summary.get('domains_with_consistent_main', 0)} of {summary.get('total_domains', 0)}")
    print(f"Domains with consistent complementary content: {summary.get('domains_with_consistent_complementary', 0)} of {summary.get('total_domains', 0)}")
    
    # Check for multi-header/footer patterns
    domains_with_secondary_headers = sum(1 for domain_data in analysis['domain_analyses'].values() 
                                       if domain_data.get('secondary_headers', {}).get('count', 0) > 0)
    domains_with_secondary_footers = sum(1 for domain_data in analysis['domain_analyses'].values() 
                                       if domain_data.get('secondary_footers', {}).get('count', 0) > 0)
    
    if domains_with_secondary_headers > 0:
        print(f"\nSecondary Headers: Found in {domains_with_secondary_headers} domains")
    
    if domains_with_secondary_footers > 0:
        print(f"Secondary Footers: Found in {domains_with_secondary_footers} domains")
    
    # Forms summary
    forms_analysis = summary.get('forms_analysis', {})
    unique_forms = forms_analysis.get('unique_forms', {})
    if unique_forms:
        print(f"\nFound {len(unique_forms)} unique forms across all sites")
        
        forms_by_type = forms_analysis.get('forms_by_type', {})
        print("Forms by type:")
        for form_type, forms in sorted(forms_by_type.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {form_type.title()}: {len(forms)}")
    
    # Content blocks summary
    content_blocks_analysis = summary.get('content_blocks_analysis', {})
    domains_with_blocks = content_blocks_analysis.get('domains_with_content_blocks', {})
    
    if sum(domains_with_blocks.values()) > 0:
        print("\nCommon content blocks:")
        if domains_with_blocks.get('heroSections', 0) > 0:
            print(f"  Hero sections: Found in {domains_with_blocks.get('heroSections', 0)} domains")
        if domains_with_blocks.get('cardGrids', 0) > 0:
            print(f"  Card grids: Found in {domains_with_blocks.get('cardGrids', 0)} domains")
        if domains_with_blocks.get('featureSections', 0) > 0:
            print(f"  Feature sections: Found in {domains_with_blocks.get('featureSections', 0)} domains")
        if domains_with_blocks.get('carousels', 0) > 0:
            print(f"  Carousels/sliders: Found in {domains_with_blocks.get('carousels', 0)} domains")
        
        repetitive_patterns = content_blocks_analysis.get('domains_with_repetitive_patterns', 0)
        if repetitive_patterns > 0:
            print(f"  Repetitive patterns: Found in {repetitive_patterns} domains")
    
    # Domain breakdown
    print("\nConsistency scores by domain:")
    domain_analyses = analysis.get('domain_analyses', {})
    
    for domain, domain_analysis in domain_analyses.items():
        score = domain_analysis.get('overall_consistency_score', 0) * 100
        method = domain_analysis.get('analysis_method', 'unknown')
        pages = domain_analysis.get('page_count', 0)
        print(f"{domain}: {score:.1f}% consistency ({pages} pages, {method} analysis)")

def analyze_content_blocks_across_sites(domain_analyses):
    """
    Analyze common content blocks across all domains and pages.
    """
    domains_with_content_blocks = {
        'heroSections': 0,
        'cardGrids': 0,
        'featureSections': 0,
        'carousels': 0
    }
    
    domains_with_repetitive_patterns = 0
    
    # First pass: count domains with each type of content block
    for domain, domain_data in domain_analyses.items():
        content_blocks = domain_data.get('content_blocks', {})
        if content_blocks:
            if content_blocks.get('heroSections', 0) > 0:
                domains_with_content_blocks['heroSections'] += 1
            if content_blocks.get('cardGrids', 0) > 0:
                domains_with_content_blocks['cardGrids'] += 1
            if content_blocks.get('featureSections', 0) > 0:
                domains_with_content_blocks['featureSections'] += 1
            if content_blocks.get('carousels', 0) > 0:
                domains_with_content_blocks['carousels'] += 1
        
        # Check for repetitive patterns
        if domain_data.get('repetitive_patterns', {}).get('found', 0) > 0:
            domains_with_repetitive_patterns += 1
    
    # Calculate percentages
    total_domains = len(domain_analyses)
    percentages = {}
    
    if total_domains > 0:
        percentages = {
            'heroSections': domains_with_content_blocks['heroSections'] / total_domains,
            'cardGrids': domains_with_content_blocks['cardGrids'] / total_domains,
            'featureSections': domains_with_content_blocks['featureSections'] / total_domains,
            'carousels': domains_with_content_blocks['carousels'] / total_domains,
            'repetitivePatterns': domains_with_repetitive_patterns / total_domains
        }
    
    return {
        'domains_with_content_blocks': domains_with_content_blocks,
        'domains_with_repetitive_patterns': domains_with_repetitive_patterns,
        'percentages': percentages,
        'total_domains': total_domains
    }

if __name__ == "__main__":
    analyze_common_structure()