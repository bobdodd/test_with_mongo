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
    "testName": "Video Accessibility Analysis",
    "description": "Evaluates the presence and accessibility of video elements on the page, including native HTML5 videos and embedded players from services like YouTube and Vimeo. This test specifically checks for required title attributes on iframe-embedded videos.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.videos": "List of all videos with their properties",
        "details.violations": "List of video accessibility violations",
        "details.summary": "Aggregated statistics about videos"
    },
    "tests": [
        {
            "id": "iframe-title",
            "name": "Iframe Title Attribute",
            "description": "Checks if embedded videos using iframes have title attributes that describe their content.",
            "impact": "high",
            "wcagCriteria": ["2.4.1", "4.1.2"],
            "howToFix": "Add a descriptive title attribute to all iframe elements that embed videos, clearly describing the video content (e.g., title='Introduction to Our Company').",
            "resultsFields": {
                "pageFlags.hasIframesWithoutTitles": "Indicates if any video iframes are missing title attributes",
                "pageFlags.details.iframesWithoutTitles": "Count of iframes missing title attributes",
                "details.violations": "List of violations including iframes without titles"
            }
        },
        {
            "id": "video-identification",
            "name": "Video Identification",
            "description": "Identifies all video content on the page, including native HTML5 videos and common embedded players.",
            "impact": "informational",
            "wcagCriteria": ["1.2.1", "1.2.2", "1.2.3", "1.2.5"],
            "howToFix": "This test is informational only and identifies videos that may need captions, audio descriptions, or transcripts to meet accessibility requirements.",
            "resultsFields": {
                "pageFlags.hasVideos": "Indicates if the page contains videos",
                "pageFlags.details.totalVideos": "Count of videos found on the page",
                "pageFlags.details.videoTypes": "Breakdown of video types (YouTube, Vimeo, native, etc.)",
                "details.videos": "List of all videos with their properties"
            }
        },
        {
            "id": "native-video-controls",
            "name": "Native Video Controls",
            "description": "Checks if native HTML5 video elements have controls attribute enabled.",
            "impact": "high",
            "wcagCriteria": ["2.1.1"],
            "howToFix": "Add the 'controls' attribute to all <video> elements to ensure keyboard users can operate the video player.",
            "resultsFields": {
                "details.videos": "List of videos including information about controls"
            }
        },
        {
            "id": "video-player-accessibility",
            "name": "Video Player Accessibility",
            "description": "Evaluates if video players have accessible controls and attributes.",
            "impact": "high",
            "wcagCriteria": ["1.2.1", "1.2.2", "2.1.1"],
            "howToFix": "Ensure video players have proper ARIA labels, keyboard-accessible controls, and support for captions and transcripts.",
            "resultsFields": {
                "details.videos": "List of videos with their attribute information"
            }
        }
    ]
}

async def test_videos(page):
    """
    Test for presence of videos, including native video elements and embedded players.
    Specifically checks for titles on iframe-embedded videos.
    """
    try:
        video_data = await page.evaluate('''
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
        
        {
                // ... (previous helper functions remain the same) ...

                function getVideoName(element, type) {
                    if (element.tagName.toLowerCase() === 'iframe') {
                        // For iframes, title attribute is required
                        const iframeTitle = element.getAttribute('title');
                        if (!iframeTitle) {
                            return null; // Indicates missing required title
                        }
                        return iframeTitle;
                    }

                    // For non-iframes, try various attributes
                    const possibleNames = [
                        element.getAttribute('title'),
                        element.getAttribute('aria-label'),
                        element.getAttribute('alt'),
                        element.getAttribute('data-title')
                    ].filter(Boolean);

                    // For YouTube, try to extract video ID if no other name found
                    if (type === 'YouTube' && !possibleNames.length) {
                        const src = element.src || '';
                        const videoId = src.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})/i);
                        if (videoId) {
                            return `YouTube video ID: ${videoId[1]}`;
                        }
                    }

                    // For Vimeo, try to extract video ID if no other name found
                    if (type === 'Vimeo' && !possibleNames.length) {
                        const src = element.src || '';
                        const videoId = src.match(/vimeo\.com\/(?:video\/)?([0-9]+)/i);
                        if (videoId) {
                            return `Vimeo video ID: ${videoId[1]}`;
                        }
                    }

                    return possibleNames[0] || 'Untitled video';
                }

                const results = {
                    videos: [],
                    violations: [],
                    summary: {
                        totalVideos: 0,
                        byType: {},
                        iframesWithoutTitles: 0
                    }
                };

                // Find native video elements
                const nativeVideos = Array.from(document.getElementsByTagName('video'));
                
                // Find iframes that might contain videos
                const iframeVideos = Array.from(document.getElementsByTagName('iframe'))
                    .filter(iframe => {
                        const src = iframe.src || '';
                        return src.includes('youtube.com') || 
                               src.includes('youtu.be') ||
                               src.includes('vimeo.com') ||
                               src.includes('dailymotion.com') ||
                               src.includes('facebook.com/plugins/video') ||
                               src.includes('brightcove') ||
                               src.includes('kaltura');
                    });

                // Find other potential video players
                const otherPlayers = Array.from(document.querySelectorAll(
                    '.video-js, .jwplayer, .plyr, [data-player-type="video"]'
                ));

                // Process all video elements
                [...nativeVideos, ...iframeVideos, ...otherPlayers].forEach(element => {
                    const type = getVideoType(element);
                    const isIframe = element.tagName.toLowerCase() === 'iframe';
                    const name = getVideoName(element, type);
                    
                    const videoInfo = {
                        type: type,
                        name: name,
                        url: getVideoUrl(element, type),
                        element: {
                            tag: element.tagName.toLowerCase(),
                            id: element.id || null,
                            class: element.className || null
                        },
                        attributes: {
                            title: element.getAttribute('title'),
                            ariaLabel: element.getAttribute('aria-label'),
                            width: element.getAttribute('width'),
                            height: element.getAttribute('height')
                        },
                        isIframe: isIframe,
                        hasMissingTitle: isIframe && !element.getAttribute('title')
                    };

                    results.videos.push(videoInfo);
                    results.summary.byType[type] = (results.summary.byType[type] || 0) + 1;

                    // Check for iframe title violations
                    if (isIframe && !element.getAttribute('title')) {
                        results.summary.iframesWithoutTitles++;
                        results.violations.push({

                            xpath: getFullXPath(element),
                            type: 'missing-iframe-title',
                            element: 'iframe',
                            videoType: type,
                            url: element.src
                        });
                    }
                });

                results.summary.totalVideos = results.videos.length;

                return {
                    pageFlags: {
                        hasVideos: results.videos.length > 0,
                        hasIframesWithoutTitles: results.summary.iframesWithoutTitles > 0,
                        details: {
                            totalVideos: results.summary.totalVideos,
                            videoTypes: results.summary.byType,
                            iframesWithoutTitles: results.summary.iframesWithoutTitles
                         }
                    },
                    results: results
                };
            }
        ''')

        # Add section information to results

        data['results'] = add_section_info_to_test_results(page, data['results'])

        # Print violations with section information for debugging

        print_violations_with_sections(data['results']['violations'])

        return {
            'videos': {
                'pageFlags': video_data['pageFlags'],
                'details': video_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
             }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'videos': {
                'pageFlags': {
                    'hasVideos': False,
                    'hasIframesWithoutTitles': False,
                    'details': {
                        'totalVideos': 0,
                        'videoTypes': {},
                        'iframesWithoutTitles': 0
                    }
                },
                'details': {
                    'videos': [],
                    'violations': [],
                    'summary': {
                        'totalVideos': 0,
                        'byType': {},
                        'iframesWithoutTitles': 0
                    }
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }