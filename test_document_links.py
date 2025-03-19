from datetime import datetime  # Add this import
async def test_document_links(page):
    """
    Test for links to electronic documents (PDF, DOC, DOCX, XLS, XLSX, etc.)
    """
    try:
        documents = await page.evaluate('''
            () => {
                const documentExtensions = [
                    '.pdf', '.doc', '.docx', '.xls', '.xlsx',
                    '.ppt', '.pptx', '.rtf', '.odt', '.ods',
                    '.odp', '.txt', '.csv'
                ];
                
                const links = Array.from(document.getElementsByTagName('a'));
                const documentLinks = links
                    .filter(link => {
                        const href = link.href.toLowerCase();
                        return documentExtensions.some(ext => href.endsWith(ext));
                    })
                    .map(link => ({
                        url: link.href,
                        text: link.textContent.trim(),
                        type: link.href.split('.').pop().toLowerCase(),
                        ariaLabel: link.getAttribute('aria-label'),
                        title: link.getAttribute('title')
                    }));
                
                return {
                    total_documents: documentLinks.length,
                    by_type: documentLinks.reduce((acc, doc) => {
                        acc[doc.type] = (acc[doc.type] || 0) + 1;
                        return acc;
                    }, {}),
                    documents: documentLinks
                };
            }
        ''')
        return {
            'document_links': documents,
            'timestamp': datetime.now().isoformat()
        }
    except Exception as e:
        # Return empty structure on error
        return {
            'document_links': {
                'total_documents': 0,
                'by_type': {},
                'documents': []
            },
            'document_links_error': str(e),
            'timestamp': datetime.now().isoformat()
        }