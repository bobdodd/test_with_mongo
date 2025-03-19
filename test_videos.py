from datetime import datetime
import re

async def test_videos(page):
    """
    Test for presence of videos, including native video elements and embedded players.
    Specifically checks for titles on iframe-embedded videos.
    """
    try:
        video_data = await page.evaluate('''
            () => {
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

        return {
            'videos': {
                'pageFlags': video_data['pageFlags'],
                'details': video_data['results'],
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }