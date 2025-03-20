from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Electronic Document Link Analysis",
    "description": "Identifies links to electronic documents like PDFs, Word documents, spreadsheets, etc., and evaluates whether they have appropriate accessibility information. This test helps ensure that users are properly informed about document format before downloading, as different formats may require specific software or have accessibility limitations.",
    "version": "1.0.0",
    "date": "2025-03-19",
    "dataSchema": {
        "document_links": "Collection of document links and their properties",
        "document_links.total_documents": "Total number of document links found",
        "document_links.by_type": "Count of documents by file type",
        "document_links.documents": "Array of document link objects with properties",
        "timestamp": "ISO timestamp when the test was run"
    },
    "tests": [
        {
            "id": "document-link-identification",
            "name": "Document Link Detection",
            "description": "Identifies links to electronic documents such as PDFs, Word files, Excel spreadsheets, etc. This helps ensure that users are aware of what content they're accessing.",
            "impact": "medium",
            "wcagCriteria": ["2.4.4", "2.4.9"],
            "howToFix": "Ensure all document links are properly identified with text that includes the document type, size, and purpose. For example: 'Annual Report (PDF, 3.5MB)'.",
            "resultsFields": {
                "document_links.total_documents": "Count of document links found",
                "document_links.by_type": "Breakdown of document types"
            }
        },
        {
            "id": "document-link-labeling",
            "name": "Document Link Labeling",
            "description": "Checks if document links have accessible names that include the document type. Users should know when a link will open a document and what format it will be in.",
            "impact": "high",
            "wcagCriteria": ["2.4.4", "3.2.4"],
            "howToFix": "Include the document type in the link text or use aria-label to provide this information. Example: 'Annual Report (PDF)' or add an icon with appropriate alt text.",
            "resultsFields": {
                "document_links.documents[].text": "The visible text of the document link",
                "document_links.documents[].ariaLabel": "Any aria-label attribute on the document link"
            }
        },
        {
            "id": "document-metadata",
            "name": "Document Metadata",
            "description": "Evaluates if document links provide supplementary information like file size, modification date, or version. This helps users make informed decisions before downloading.",
            "impact": "medium",
            "wcagCriteria": ["3.3.2"],
            "howToFix": "Add file metadata near the link, such as size and date. Example: 'Annual Report (PDF, 3.5MB, updated Jan 2025)'.",
            "resultsFields": {
                "document_links.documents[].title": "The title attribute on the document link which may contain additional metadata"
            }
        }
    ]
}
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
            'timestamp': datetime.now().isoformat(),
            'documentation': TEST_DOCUMENTATION  # Include test documentation in results
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
            'timestamp': datetime.now().isoformat(),
            'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
        }