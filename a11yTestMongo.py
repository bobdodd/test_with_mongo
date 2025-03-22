import asyncio
import click
from pyppeteer import launch
import platform
import sys
import os
import re
import importlib
import inspect
from urllib.parse import urlparse
import json
from datetime import datetime
from database import AccessibilityDB
from analyze_structure import analyze_common_structure


# Your existing test imports
from test_media_queries import test_media_queries, TEST_DOCUMENTATION as MEDIA_QUERIES_DOCS
from test_document_links import test_document_links
from test_fonts import test_fonts
from test_html_structure import test_html_structure
from test_focus_management import test_focus_management, TEST_DOCUMENTATION as FOCUS_MANAGEMENT_DOCS
from test_accessible_names import test_accessible_names, TEST_DOCUMENTATION as ACCESSIBLE_NAMES_DOCS
from test_images import test_images, TEST_DOCUMENTATION as IMAGES_DOCS
from test_videos import test_videos
from test_landmarks import test_landmarks
from test_forms import test_forms
from test_headings import test_headings, TEST_DOCUMENTATION as HEADINGS_DOCS
from test_read_more_links import test_read_more_links
from test_tabindex import test_tabindex
from test_timers import test_timers
from test_animations import test_animations
from test_maps import test_maps
from test_colors import test_colors
from test_tables import test_tables, TEST_DOCUMENTATION as TABLES_DOCS
from test_modals import test_modals
from test_event_handlers import test_event_handlers
from test_title_attribute import test_title_attribute
from test_lists import test_lists
from test_menus import test_menus
from test_floating_dialogs import test_floating_dialogs
from test_text_resize import test_text_resize
from test_page_structure import test_page_structure, TEST_DOCUMENTATION as PAGE_STRUCTURE_DOCS
from test_responsive_accessibility import test_responsive_accessibility, consolidate_responsive_results, TEST_DOCUMENTATION as RESPONSIVE_DOCS

def clean_filename(url):
    """
    Convert URL to a clean filename
    """
    parsed = urlparse(url)
    path = parsed.hostname + parsed.path
    path = path.rstrip('/')
    clean = re.sub(r'[^a-zA-Z0-9]', '_', path)
    clean = re.sub(r'_+', '_', clean)
    return f"{clean}.png"

async def test_page_accessibility(page):
    """
    Test accessibility features of the page
    """
    try:
        print(f"Testing accessibility for: {page.url}")
        results = {
            'url': page.url,
            'tests': {}
        }
        
        # Test for media queries first
        print("Testing for CSS media queries and responsive breakpoints...")
        media_queries_results = await test_media_queries(page)
        results['tests']['media_queries'] = media_queries_results

        # Get responsive breakpoints for later viewport testing
        responsive_breakpoints = []
        
        # Extract breakpoints from the media queries results
        try:
            # First try the direct 'breakpoints' property that's in the new data structure
            if 'breakpoints' in media_queries_results:
                all_breakpoints = media_queries_results['breakpoints']
                if all_breakpoints:
                    print(f"Found {len(all_breakpoints)} responsive breakpoints: {all_breakpoints}")
                    responsive_breakpoints = sorted([int(bp) for bp in all_breakpoints])
                else:
                    print("No responsive breakpoints found in direct breakpoints")
            
            # Backward compatibility check for older structure
            elif 'media_queries' in media_queries_results and 'responsiveBreakpoints' in media_queries_results['media_queries']:
                all_breakpoints = media_queries_results['media_queries']['responsiveBreakpoints'].get('allBreakpoints', [])
                if all_breakpoints:
                    print(f"Found {len(all_breakpoints)} responsive breakpoints (legacy format): {all_breakpoints}")
                    responsive_breakpoints = sorted([int(bp) for bp in all_breakpoints])
                else:
                    print("No responsive breakpoints found in media queries results")
            
            # If no breakpoints were found, log it but don't add default ones
            if not responsive_breakpoints:
                print("No responsive breakpoints found in CSS media queries. Responsive accessibility tests will be skipped.")
                # No default breakpoints, as we only want to test actual responsive breakpoints
        except Exception as bp_error:
            print(f"Error extracting breakpoints: {str(bp_error)}")
            # No default breakpoints on error - only want to test actual responsive breakpoints
            
        # Store the original viewport to restore later
        original_viewport = page.viewport
        print(f"Original viewport: {original_viewport}")
        
        # Test for document links
        print("Testing for electronic documents...")
        document_results = await test_document_links(page)
        results['tests']['documents'] = document_results

        # Add summary of documents found
        if 'document_links' in document_results:
            docs = document_results['document_links']
            print(f"Found {docs['total_documents']} electronic documents:")
            for doc_type, count in docs['by_type'].items():
                print(f"  - {doc_type.upper()}: {count}")

        try:
            # Add font testing
            print("Testing fonts and text styles...")
            font_results = await test_fonts(page)
            results['tests']['fonts'] = font_results

            if font_results and 'font_analysis' in font_results:
                analysis = font_results['font_analysis']
                if 'summary' in analysis:
                    print(f"\nFont Analysis Summary:")
                    print(f"Total text elements: {analysis['summary'].get('totalTextElements', 0)}")
                    print(f"Unique fonts found: {len(analysis['summary'].get('uniqueFonts', []))}")
        except Exception as font_error:
            print(f"Error in font testing: {str(font_error)}")
            results['tests']['fonts'] = {
                'error': str(font_error),
                'timestamp': datetime.now().isoformat()
            }

        # Determine if this is the homepage
        url = page.url
        is_homepage = url.endswith('/') or url.endswith('.com') or url.endswith('.ca') or \
                     not any(x in url.split('?')[0].split('/')[-1] for x in ['.', '_', '-'])

        # Run all other tests
        print("Testing page structure for comment elements...")
        page_structure_results = await test_page_structure(page)
        results['tests']['page_structure'] = page_structure_results

        print("Testing HTML structure...")
        html_results = await test_html_structure(page, is_homepage)
        results['tests']['html_structure'] = html_results

        print("Testing focus management...")
        focus_results = await test_focus_management(page)
        results['tests']['focus_management'] = focus_results

        print("Testing accessible names...")
        names_results = await test_accessible_names(page)
        results['tests']['accessible_names'] = names_results

        print("Testing images...")
        images_results = await test_images(page)
        results['tests']['images'] = images_results

        print("Testing for videos...")
        video_results = await test_videos(page)
        results['tests']['videos'] = video_results

        print("Testing landmarks...")
        landmarks_results = await test_landmarks(page)
        results['tests']['landmarks'] = landmarks_results

        print("Testing forms...")
        forms_results = await test_forms(page)
        results['tests']['forms'] = forms_results

        print("Testing headings...")
        headings_results = await test_headings(page)
        results['tests']['headings'] = headings_results

        print("Testing read more links...")
        read_more_results = await test_read_more_links(page)
        results['tests']['read_more_links'] = read_more_results

        print("Testing tabindex attributes...")
        tabindex_results = await test_tabindex(page)
        results['tests']['tabindex'] = tabindex_results

        print("Testing timers...")
        timer_results = await test_timers(page)
        results['tests']['timers'] = timer_results

        print("Testing CSS animations...")
        animation_results = await test_animations(page)
        results['tests']['animations'] = animation_results

        print("Testing for digital maps...")
        maps_results = await test_maps(page)
        results['tests']['maps'] = maps_results

        print("Testing colors...")
        color_results = await test_colors(page)
        results['tests']['colors'] = color_results

        print("Testing tables...")
        tables_results = await test_tables(page)
        results['tests']['tables'] = tables_results

        print("Testing modal dialogs...")
        modals_results = await test_modals(page)
        results['tests']['modals'] = modals_results

        print("Testing event handlers...")
        event_results = await test_event_handlers(page)
        results['tests']['events'] = event_results

        print("Testing title attribute...")
        title_results = await test_title_attribute(page)
        results['tests']['title'] = title_results

        print("Testing lists...")
        lists_results = await test_lists(page)
        results['tests']['lists'] = lists_results

        print("Testing menus...")
        menus_results = await test_menus(page)
        results['tests']['menus'] = menus_results

        # Test floating dialogs which handles its own breakpoint iteration
        print("Testing floating dialogs...")
        floating_results = await test_floating_dialogs(page)
        results['tests']['floating_dialogs'] = floating_results

        '''
        print("Testing text resize...")
        resize_results = await test_text_resize(page)
        results['tests']['text_resize'] = resize_results
        '''
        
        # Add responsive breakpoint testing structure
        # Using our comprehensive responsive accessibility tests
        results['responsive_testing'] = {
            'breakpoints': responsive_breakpoints,
            'breakpoint_results': {}
        }
        
        # Only proceed with responsive testing if breakpoints were found
        if responsive_breakpoints:
            print("\n=== STARTING RESPONSIVE BREAKPOINT TESTING ===")
            print(f"Testing {len(responsive_breakpoints)} breakpoints: {responsive_breakpoints}")
            
            # Test at each breakpoint
            for i, breakpoint in enumerate(responsive_breakpoints):
                print(f"\n--- Testing breakpoint {i+1}/{len(responsive_breakpoints)}: {breakpoint}px ---")
                
                try:
                    # Set viewport width to the breakpoint
                    print(f"  Setting viewport width to {breakpoint}px")
                    await page.setViewport({
                        'width': breakpoint,
                        'height': original_viewport['height'] 
                    })
                    
                    # Wait for layout to stabilize
                    await asyncio.sleep(0.5)  # 500ms pause
                    
                    # Initialize results for this breakpoint
                    breakpoint_results = {
                        'breakpoint': breakpoint,
                        'viewport': {
                            'width': breakpoint,
                            'height': original_viewport['height']
                        },
                        'tests': {}
                    }
                    
                    # Run comprehensive responsive accessibility tests at this breakpoint
                    print("  Running responsive accessibility tests at this breakpoint...")
                    responsive_results = await test_responsive_accessibility(page, breakpoint)
                    
                    # Ensure consistent data structure - responsive_results should contain a 'tests' dictionary
                    if isinstance(responsive_results, dict):
                        # Store the responsive results in the correct structure
                        breakpoint_results['tests'] = responsive_results
                    else:
                        # Create a proper structure if something went wrong
                        print(f"  Warning: Unexpected responsive results type: {type(responsive_results)}")
                        breakpoint_results['tests'] = {
                            'error': 'Invalid results structure',
                            'timestamp': datetime.now().isoformat()
                        }
                    
                    # Store results for this breakpoint
                    results['responsive_testing']['breakpoint_results'][str(breakpoint)] = breakpoint_results
                    
                    # Add a short pause between breakpoints
                    await asyncio.sleep(0.1)
                    
                except Exception as bp_error:
                    print(f"  ERROR at breakpoint {breakpoint}px: {str(bp_error)}")
                    results['responsive_testing']['breakpoint_results'][str(breakpoint)] = {
                        'breakpoint': breakpoint,
                        'error': str(bp_error)
                    }
            
            # Consolidate results across all breakpoints
            print("\n--- Consolidating responsive testing results ---")
            try:
                consolidated_results = consolidate_responsive_results(results['responsive_testing']['breakpoint_results'])
                results['responsive_testing']['consolidated'] = consolidated_results
                
                # Add summary to main results
                print(f"  Found {consolidated_results.get('summary', {}).get('totalIssues', 0)} responsive accessibility issues across {consolidated_results.get('summary', {}).get('affectedBreakpoints', 0)} breakpoints")
                
            except Exception as consolidation_error:
                print(f"  ERROR consolidating results: {str(consolidation_error)}")
                results['responsive_testing']['consolidated'] = {
                    'error': str(consolidation_error),
                    'timestamp': datetime.now().isoformat()
                }
        else:
            # No breakpoints found, add information to results but skip testing
            print("\n=== SKIPPING RESPONSIVE BREAKPOINT TESTING (NO BREAKPOINTS FOUND) ===")
            results['responsive_testing']['status'] = 'skipped'
            results['responsive_testing']['reason'] = 'No CSS media query breakpoints found'
            results['responsive_testing']['timestamp'] = datetime.now().isoformat()
        
        # Restore original viewport
        print("\n--- Restoring original viewport ---")
        await page.setViewport(original_viewport)
        await asyncio.sleep(0.5)  # Wait for layout to stabilize
        
        return results

    except Exception as e:
        return {
            'url': page.url,
            'error': str(e),
            'tests': {}
        }
    
def collect_test_documentation():
    """
    Collects TEST_DOCUMENTATION objects from all test modules.
    
    Returns:
        dict: A dictionary mapping test names to their documentation objects
    """
    print("Collecting test documentation from all test modules...")
    documentation = {}
    
    # Add the manually imported documentation
    documentation['media_queries'] = MEDIA_QUERIES_DOCS
    documentation['page_structure'] = PAGE_STRUCTURE_DOCS
    documentation['accessible_names'] = ACCESSIBLE_NAMES_DOCS
    documentation['focus_management'] = FOCUS_MANAGEMENT_DOCS
    documentation['images'] = IMAGES_DOCS
    documentation['tables'] = TABLES_DOCS
    documentation['headings'] = HEADINGS_DOCS
    documentation['responsive_accessibility'] = RESPONSIVE_DOCS
    
    # Just return what we've manually imported to simplify the testing process
    print(f"Collected documentation for {len(documentation)} tests")
    return documentation

async def process_urls(file_path, screenshots_dir, results_file, max_pages, clear_db, delay, db_name, auto_create_db):
    """
    Process URLs from the input file one at a time using Puppeteer
    """
    # Initialize database with the specified name
    db = AccessibilityDB(db_name=db_name, create_if_not_exists=auto_create_db)
    
    # Clear database if requested
    if clear_db:
        print(f"Clearing database '{db.db_name}'...")
        db.clear_database()
    
    # Collect test documentation from all modules
    test_documentation = collect_test_documentation()
    
    # Create settings dictionary
    settings = {
        'screenshots_dir': screenshots_dir,
        'input_file': file_path,
        'results_file': results_file,
        'max_pages': max_pages,
        'database_cleared': clear_db,
        'delay_between_pages': delay
    }
    
    # Start new test run with documentation included
    test_run_id = db.start_new_test_run(settings, documentation=test_documentation)
    
    # Create screenshots directory if it doesn't exist
    os.makedirs(screenshots_dir, exist_ok=True)

    launch_options = {
        'headless': False,
        'args': [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--window-size=1920,1080',
        '--ignore-certificate-errors',
        '--disable-web-security',
        '--disable-quic',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-features=BlockInsecurePrivateNetworkRequests',
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'  # Updated user agent
        ],
        'ignoreHTTPSErrors': True,
        'defaultViewport': {
            'width': 1920,
            'height': 1080
        }
    }

    try:
        # Read URLs from file
        with open(file_path, 'r') as file:
            urls = [line.strip() for line in file if line.strip()]

        # Limit the number of URLs if max_pages is specified
        if max_pages:
            urls = urls[:max_pages]
            print(f"\nLimiting test to first {max_pages} pages")
        
        print(f"Total pages to process: {len(urls)}")
        print(f"Delay between pages: {delay} seconds")

        for index, url in enumerate(urls, 1):
            print(f"\nProcessing page {index} of {len(urls)}: {url}")
            
            # Initialize page result
            page_result = {
                'status': 'started',
                'screenshot': None,
                'errors': [],
                'timestamp_start': datetime.now().isoformat(),
                'index': index
            }

            # Save initial status
            db.save_page_result(test_run_id, url, page_result)

            browser = await launch(launch_options)
            
            try:
                page = await browser.newPage()
                page.setDefaultNavigationTimeout(60000)

                try:
                    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

                    response = await page.goto(url, {
                        'waitUntil': ['load', 'networkidle0', 'domcontentloaded'],
                        'timeout': 60000
                    })

                    if response is None:
                        error_msg = f"Failed to load {url}: No response received"
                        print(error_msg)
                        page_result['errors'].append(error_msg)
                        page_result['status'] = 'failed'
                        db.save_page_result(test_run_id, url, page_result)
                        continue

                    await page.waitForSelector('body', {'timeout': 30000})

                    screenshot_filename = clean_filename(url)
                    screenshot_path = os.path.join(screenshots_dir, screenshot_filename)
                    await page.screenshot({
                        'path': screenshot_path,
                        'fullPage': True
                    })
                    print(f"Screenshot saved: {screenshot_path}")

                    # Update results with screenshot info
                    page_result['screenshot'] = screenshot_filename
                    page_result['status'] = 'in_progress'

                    # Run accessibility tests
                    accessibility_results = await test_page_accessibility(page)
                    page_result['accessibility'] = accessibility_results
                    page_result['status'] = 'completed'
                    page_result['timestamp_end'] = datetime.now().isoformat()

                    # Save completed page result
                    db.save_page_result(test_run_id, url, page_result)

                except Exception as e:
                    error_message = f"Error processing {url}: {str(e)}"
                    print(error_message)
                    page_result['errors'].append(error_message)
                    page_result['status'] = 'error'
                    db.save_page_result(test_run_id, url, page_result)

                finally:
                    try:
                        await asyncio.wait_for(page.close(), timeout=5.0)
                    except asyncio.TimeoutError:
                        print("Warning: Page close operation timed out")
            except Exception as e:
                error_message = f"Error creating page for {url}: {str(e)}"
                print(error_message)
                page_result['errors'].append(error_message)
                page_result['status'] = 'error'
                db.save_page_result(test_run_id, url, page_result)

            finally:
                await browser.close()
                print(f"Waiting {delay} seconds before next page...")
                await asyncio.sleep(delay)

    except Exception as e:
        print(f"Error reading file or processing URLs: {str(e)}")
        
    finally:
        # Complete the test run
        summary = {
            'total_urls': len(urls),
            'completed_at': datetime.now().isoformat()
        }
        db.complete_test_run(test_run_id, summary)
        
        # Export to JSON if needed
        if results_file:
            db.export_to_json(results_file, test_run_id)
            print(f"\nFinal results saved to: {results_file}")

@click.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('--screenshots-dir', '-s', default='screenshots',
              help='Directory to save screenshots (default: screenshots)')
@click.option('--results-file', '-r', default='results.json',
              help='JSON file to save results (default: results.json)')
@click.option('--max-pages', '-m', type=int, default=None,
              help='Maximum number of pages to test (default: no limit)')
@click.option('--clear-db', '-c', is_flag=True,
              help='Clear specified database before starting new test run')
@click.option('--delay', '-d', type=float, default=2.0,
              help='Delay in seconds between page tests (default: 2.0)')
@click.option('--database', '-db', default=None,
              help='MongoDB database name to use (default: accessibility_tests)')
@click.option('--auto-create-db', '-a', is_flag=True,
              help='Automatically create the database if it does not exist')
def main(input_file, screenshots_dir, results_file, max_pages, clear_db, delay, database, auto_create_db):
    """
    Process URLs from INPUT_FILE one at a time and test for accessibility.
    Screenshots will be saved in the specified directory.
    Results will be saved to both MongoDB and the specified JSON file.
    Optional limit on number of pages to test.
    Optional database clearing before starting.
    Optional delay between page tests.
    Optional database name to use.
    Optional automatic creation of database if it does not exist.
    """
    try:
        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(process_urls(input_file, screenshots_dir, results_file, max_pages, clear_db, delay, database, auto_create_db))
        loop.close()

        print("\nAnalyzing common page structure across the site...")
        structure_analysis = analyze_common_structure(db_name=database)
        print("Structure analysis complete.")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()