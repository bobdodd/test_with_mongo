from datetime import datetime

# Test metadata for documentation and reporting
TEST_DOCUMENTATION = {
    "testName": "Table Accessibility Analysis",
    "description": "Evaluates HTML tables for proper semantic structure and accessibility features essential for screen reader users. This test checks for captions, headers, proper table structure, and scope attributes to ensure data tables are navigable and understandable.",
    "version": "1.1.0",
    "date": "2025-03-19",
    "dataSchema": {
        "timestamp": "ISO timestamp when the test was run",
        "pageFlags": "Boolean flags indicating presence of key issues",
        "details.tables": "List of all tables with their properties and analysis",
        "details.summary": "Aggregated statistics about table accessibility"
    },
    "tests": [
        {
            "id": "table-caption",
            "name": "Table Caption Presence",
            "description": "Checks whether tables have captions that provide a title or summary of the table content.",
            "impact": "high",
            "wcagCriteria": ["1.3.1", "2.4.6"],
            "howToFix": "Add a <caption> element as the first child of the <table> element that provides a concise title or description of the table content.",
            "resultsFields": {
                "pageFlags.hasTableViolations": "Indicates if any tables have accessibility violations",
                "details.summary.violationTypes.missingCaptions": "Count of tables missing captions",
                "details.tables[].analysis.hasCaption": "Boolean indicating if a specific table has a caption"
            }
        },
        {
            "id": "table-structure",
            "name": "Table Structure",
            "description": "Evaluates if tables use proper structural elements like thead, tbody, and tfoot.",
            "impact": "medium",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Use proper table structure with <thead>, <tbody>, and if applicable <tfoot> elements to organize the table content semantically.",
            "resultsFields": {
                "details.summary.violationTypes.missingTheadSection": "Count of tables missing thead sections",
                "details.tables[].analysis.hasTheadSection": "Boolean indicating if a specific table has a thead section",
                "details.tables[].analysis.hasTbodySection": "Boolean indicating if a specific table has a tbody section"
            }
        },
        {
            "id": "table-headers",
            "name": "Table Headers",
            "description": "Checks if tables have proper column and row headers.",
            "impact": "high",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Use <th> elements for all table headers and include the scope attribute (scope='col' for column headers, scope='row' for row headers).",
            "resultsFields": {
                "details.summary.violationTypes.missingHeaders": "Count of tables with missing header cells",
                "details.tables[].analysis.colHeaders": "List of column headers in a specific table",
                "details.tables[].analysis.rowHeaders": "List of row headers in a specific table"
            }
        },
        {
            "id": "table-scope",
            "name": "Header Cell Scope Attributes",
            "description": "Verifies that header cells have appropriate scope attributes to associate them with data cells.",
            "impact": "high",
            "wcagCriteria": ["1.3.1"],
            "howToFix": "Add scope='col' to all column header cells and scope='row' to all row header cells.",
            "resultsFields": {
                "details.summary.violationTypes.missingScopes": "Count of tables with header cells missing scope attributes",
                "details.tables[].analysis.violations": "List of violations including missing scope attributes in specific tables"
            }
        }
    ]
}

async def test_tables(page):
    """
    Test HTML tables for accessibility requirements
    """
    try:
        tables_data = await page.evaluate('''
            () => {
                function analyzeTable(table) {
                    const info = {
                        hasCaption: false,
                        caption: null,
                        hasTheadSection: false,
                        hasTbodySection: false,
                        totalRows: 0,
                        totalCols: 0,
                        colHeaders: [],
                        rowHeaders: [],
                        violations: [],
                        structure: {
                            thead: null,
                            tbody: null,
                            tfoot: null
                        }
                    }

                    // Check caption
                    const caption = table.querySelector('caption')
                    info.hasCaption = !!caption
                    info.caption = caption ? caption.textContent.trim() : null
                    if (!caption) {
                        info.violations.push({
                            type: 'missing-caption',
                            message: 'Table lacks a caption element'
                        })
                    }

                    // Check table sections
                    info.hasTheadSection = !!table.querySelector('thead')
                    info.hasTbodySection = !!table.querySelector('tbody')
                    
                    if (!info.hasTheadSection) {
                        info.violations.push({
                            type: 'missing-thead',
                            message: 'Table lacks a thead section'
                        })
                    }

                    // Analyze headers
                    const thElements = table.querySelectorAll('th')
                    thElements.forEach(th => {
                        const scope = th.getAttribute('scope')
                        if (!scope) {
                            info.violations.push({
                                type: 'missing-scope',
                                text: th.textContent.trim(),
                                message: 'Header cell lacks scope attribute'
                            })
                        } else if (scope === 'col') {
                            info.colHeaders.push({
                                text: th.textContent.trim(),
                                scope: scope
                            })
                        } else if (scope === 'row') {
                            info.rowHeaders.push({
                                text: th.textContent.trim(),
                                scope: scope
                            })
                        }
                    })

                    // Get table dimensions
                    const rows = table.rows
                    info.totalRows = rows.length
                    info.totalCols = rows.length > 0 ? rows[0].cells.length : 0

                    // Check if all rows have headers
                    const firstRow = rows[0]
                    if (firstRow) {
                        const firstRowHeaders = firstRow.querySelectorAll('th[scope="col"]')
                        if (firstRowHeaders.length === 0) {
                            info.violations.push({
                                type: 'no-column-headers',
                                message: 'First row contains no column headers'
                            })
                        } else if (firstRowHeaders.length !== info.totalCols) {
                            info.violations.push({
                                type: 'incomplete-headers',
                                message: `Not all columns have headers (${firstRowHeaders.length}/${info.totalCols})`
                            })
                        }
                    }

                    // Check for row headers in data rows
                    for (let i = 1; i < rows.length; i++) {
                        const row = rows[i]
                        const rowHeader = row.querySelector('th[scope="row"]')
                        if (!rowHeader) {
                            info.violations.push({
                                type: 'missing-row-header',
                                message: `Row ${i + 1} lacks a row header`
                            })
                        }
                    }

                    return info
                }

                const results = {
                    tables: [],
                    summary: {
                        totalTables: 0,
                        tablesWithViolations: 0,
                        violationTypes: {
                            missingCaptions: 0,
                            missingHeaders: 0,
                            missingScopes: 0,
                            missingTheadSection: 0
                        }
                    }
                }

                // Find all tables
                const tables = document.querySelectorAll('table')
                results.summary.totalTables = tables.length

                tables.forEach((table, index) => {
                    const analysis = analyzeTable(table)
                    
                    const tableInfo = {
                        index: index + 1,
                        id: table.id || null,
                        analysis: analysis,
                        hasViolations: analysis.violations.length > 0
                    }

                    results.tables.push(tableInfo)

                    if (analysis.violations.length > 0) {
                        results.summary.tablesWithViolations++
                    }

                    // Update violation type counts
                    analysis.violations.forEach(violation => {
                        switch(violation.type) {
                            case 'missing-caption':
                                results.summary.violationTypes.missingCaptions++
                                break
                            case 'no-column-headers':
                            case 'missing-row-header':
                                results.summary.violationTypes.missingHeaders++
                                break
                            case 'missing-scope':
                                results.summary.violationTypes.missingScopes++
                                break
                            case 'missing-thead':
                                results.summary.violationTypes.missingTheadSection++
                                break
                        }
                    })
                })

                return {
                    pageFlags: {
                        hasTables: results.summary.totalTables > 0,
                        hasTableViolations: results.summary.tablesWithViolations > 0,
                        details: {
                            totalTables: results.summary.totalTables,
                            tablesWithViolations: results.summary.tablesWithViolations,
                            violationTypes: results.summary.violationTypes
                        }
                    },
                    results: results
                }
            }
        ''')

        return {
            'tables': {
                'pageFlags': tables_data['pageFlags'],
                'details': tables_data['results'],
                'timestamp': datetime.now().isoformat(),
                'documentation': TEST_DOCUMENTATION  # Include test documentation in results
            }
        }

    except Exception as e:
        return {
            'error': str(e),
            'timestamp': datetime.now().isoformat(),
            'tables': {
                'pageFlags': {
                    'hasTables': False,
                    'hasTableViolations': False,
                    'details': {
                        'totalTables': 0,
                        'tablesWithViolations': 0,
                        'violationTypes': {
                            'missingCaptions': 0,
                            'missingHeaders': 0,
                            'missingScopes': 0,
                            'missingTheadSection': 0
                        }
                    }
                },
                'details': {
                    'tables': [],
                    'violations': [{
                        'issue': 'Error evaluating tables',
                        'details': str(e)
                    }]
                },
                'documentation': TEST_DOCUMENTATION  # Include test documentation even in error case
            }
        }