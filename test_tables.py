from datetime import datetime

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
                'timestamp': datetime.now().isoformat()
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
                }
            }
        }