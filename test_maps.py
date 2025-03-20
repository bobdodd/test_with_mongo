from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Digital Maps Accessibility Analysis",
    "description": "Evaluates embedded digital maps for proper accessibility attributes and alternative content. This test identifies common map implementations including Google Maps, Mapbox, and Leaflet, and checks that they are properly labeled and accessible to screen reader users.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.maps": "List of all map elements with their properties",
        "details.violations": "List of map accessibility violations",
        "details.summary": "Aggregated statistics about maps usage"
    },
    "tests": [
        {
            "id": "map-title",
            "name": "Map Title Attribute",
            "description": "Checks if embedded map iframes have descriptive title attributes to identify their purpose.",
            "impact": "high",
            "wcagCriteria": ["2.4.1", "4.1.2"],
            "howToFix": "Add a descriptive title attribute to all map iframes that clearly explains the map's purpose and content (e.g., 'Map showing our office locations in North America').",
            "resultsFields": {
                "pageFlags.hasMapsWithoutTitle": "Indicates if any maps are missing title attributes",
                "pageFlags.details.mapsWithoutTitle": "Count of maps missing title attributes",
                "details.violations": "List of violations including maps without titles"
            }
        },
        {
            "id": "map-aria-hidden",
            "name": "Maps with aria-hidden",
            "description": "Identifies maps that have been hidden from screen readers with aria-hidden attribute.",
            "impact": "high",
            "wcagCriteria": ["1.1.1"],
            "howToFix": "Remove aria-hidden='true' from map elements unless you provide an alternative text description or representation of the map content elsewhere on the page.",
            "resultsFields": {
                "pageFlags.hasMapsWithAriaHidden": "Indicates if any maps have aria-hidden='true'",
                "pageFlags.details.mapsWithAriaHidden": "Count of maps with aria-hidden='true'",
                "details.violations": "List of violations including maps with aria-hidden='true'"
            }
        },
        {
            "id": "div-map-accessibility",
            "name": "Div-based Map Accessibility",
            "description": "Checks if div-based maps (like Leaflet or Mapbox) have proper ARIA attributes for accessibility.",
            "impact": "high",
            "wcagCriteria": ["1.1.1", "4.1.2"],
            "howToFix": "For div-based maps, add appropriate aria attributes like aria-label and role='application' or role='img', along with textual alternatives that describe the map's purpose and key information.",
            "resultsFields": {
                "details.violations": "List of violations including div maps missing accessibility attributes"
            }
        },
        {
            "id": "map-identification",
            "name": "Map Provider Identification",
            "description": "Identifies the map providers used on the page for informational purposes.",
            "impact": "informational",
            "wcagCriteria": [],
            "howToFix": "This is an informational test only. No remediation required.",
            "resultsFields": {
                "pageFlags.hasMaps": "Indicates if maps are present on the page",
                "pageFlags.details.totalMaps": "Count of maps found on the page",
                "pageFlags.details.mapsByProvider": "Breakdown of maps by provider",
                "details.maps": "List of all maps with their properties"
            }
        }
    ]
}

async def test_maps(page):
    """
    Test for embedded digital maps and their accessibility attributes
    """
    try:
        maps_data = await page.evaluate('''
            () => {
                function identifyMapProvider(src) {
                    const srcLower = src.toLowerCase();
                    if (srcLower.includes('google.com/maps')) return 'Google Maps';
                    if (srcLower.includes('bing.com/maps')) return 'Bing Maps';
                    if (srcLower.includes('openstreetmap.org')) return 'OpenStreetMap';
                    if (srcLower.includes('waze.com')) return 'Waze';
                    if (srcLower.includes('mapbox.com')) return 'Mapbox';
                    if (srcLower.includes('leafletjs.com') || srcLower.includes('leaflet')) return 'Leaflet';
                    if (srcLower.includes('arcgis.com')) return 'ArcGIS';
                    if (srcLower.includes('here.com')) return 'HERE Maps';
                    if (srcLower.includes('tomtom.com')) return 'TomTom';
                    if (srcLower.includes('maps.apple.com')) return 'Apple Maps';
                    return 'Unknown Map Provider';
                }

                const results = {
                    maps: [],
                    violations: [],
                    summary: {
                        totalMaps: 0,
                        mapsByProvider: {},
                        mapsWithoutTitle: 0,
                        mapsWithAriaHidden: 0
                    }
                };

                // Find map iframes
                const mapIframes = Array.from(document.querySelectorAll('iframe')).filter(iframe => {
                    const src = iframe.src || '';
                    return src.includes('map') || 
                           src.includes('maps.google') ||
                           src.includes('maps.bing') ||
                           src.includes('openstreetmap') ||
                           src.includes('waze') ||
                           src.includes('mapbox') ||
                           src.includes('arcgis') ||
                           src.includes('here.com') ||
                           src.includes('tomtom');
                });

                // Process each map
                mapIframes.forEach(iframe => {
                    const provider = identifyMapProvider(iframe.src);
                    const title = iframe.getAttribute('title');
                    const ariaHidden = iframe.getAttribute('aria-hidden');

                    const mapInfo = {
                        provider: provider,
                        src: iframe.src,
                        title: title,
                        hasTitle: !!title,
                        ariaHidden: ariaHidden === 'true',
                        dimensions: {
                            width: iframe.getAttribute('width'),
                            height: iframe.getAttribute('height')
                        },
                        attributes: {
                            id: iframe.id || null,
                            class: iframe.className || null,
                            title: title,
                            ariaHidden: ariaHidden
                        }
                    };

                    results.maps.push(mapInfo);

                    // Update summary
                    results.summary.mapsByProvider[provider] = 
                        (results.summary.mapsByProvider[provider] || 0) + 1;

                    // Check for violations
                    if (!title) {
                        results.summary.mapsWithoutTitle++;
                        results.violations.push({
                            type: 'missing-title',
                            provider: provider,
                            src: iframe.src
                        });
                    }

                    if (ariaHidden === 'true') {
                        results.summary.mapsWithAriaHidden++;
                        results.violations.push({
                            type: 'aria-hidden',
                            provider: provider,
                            src: iframe.src,
                            title: title
                        });
                    }
                });

                // Also check for map div elements (some providers use divs)
                const mapDivs = Array.from(document.querySelectorAll('div[class*="map"], div[id*="map"]'))
                    .filter(div => {
                        const classAndId = (div.className + ' ' + (div.id || '')).toLowerCase();
                        return classAndId.includes('map') && 
                               !classAndId.includes('sitemap') && // Exclude sitemaps
                               !classAndId.includes('heatmap'); // Exclude heatmaps
                    });

                mapDivs.forEach(div => {
                    // Look for known map provider scripts or styles
                    const hasMapboxGL = document.querySelector('script[src*="mapbox-gl"]');
                    const hasLeaflet = document.querySelector('link[href*="leaflet"]');
                    const hasGoogleMaps = document.querySelector('script[src*="maps.google"]');
                    
                    let provider = 'Unknown Map Provider';
                    if (hasMapboxGL) provider = 'Mapbox';
                    if (hasLeaflet) provider = 'Leaflet';
                    if (hasGoogleMaps) provider = 'Google Maps';

                    const mapInfo = {
                        provider: provider,
                        type: 'div',
                        id: div.id || null,
                        class: div.className,
                        ariaLabel: div.getAttribute('aria-label'),
                        role: div.getAttribute('role')
                    };

                    results.maps.push(mapInfo);
                    results.summary.mapsByProvider[provider] = 
                        (results.summary.mapsByProvider[provider] || 0) + 1;

                    // Check for accessibility attributes on div-based maps
                    if (!div.getAttribute('aria-label') && !div.getAttribute('role')) {
                        results.violations.push({
                            type: 'div-map-missing-attributes',
                            provider: provider,
                            element: `div#${div.id || ''}.${div.className}`
                        });
                    }
                });

                results.summary.totalMaps = results.maps.length;

                return {
                    pageFlags: {
                        hasMaps: results.maps.length > 0,
                        hasMapsWithoutTitle: results.summary.mapsWithoutTitle > 0,
                        hasMapsWithAriaHidden: results.summary.mapsWithAriaHidden > 0,
                        details: {
                            totalMaps: results.summary.totalMaps,
                            mapsByProvider: results.summary.mapsByProvider,
                            mapsWithoutTitle: results.summary.mapsWithoutTitle,
                            mapsWithAriaHidden: results.summary.mapsWithAriaHidden
                        }
                    },
                    results: results
                };
            }
        ''')

        return {
            'maps': {
                'pageFlags': maps_data['pageFlags'],
                'details': maps_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'maps': {
                'pageFlags': {
                    'hasMaps': False,
                    'hasMapsWithoutTitle': False,
                    'hasMapsWithAriaHidden': False,
                    'details': {
                        'totalMaps': 0,
                        'mapsByProvider': {},
                        'mapsWithoutTitle': 0,
                        'mapsWithAriaHidden': 0
                    }
                },
                'details': {
                    'maps': [],
                    'violations': [{
                        'issue': 'Error evaluating maps',
                        'details': str(e)
                    }],
                    'summary': {
                        'totalMaps': 0,
                        'mapsByProvider': {},
                        'mapsWithoutTitle': 0,
                        'mapsWithAriaHidden': 0
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }