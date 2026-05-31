const PDFStatementParser = require('./pdf-statement-parser');
const fs = require('fs');
const path = require('path');

/**
 * Utility script to parse U.S. Bank statement PDFs and extract operational cost data
 * 
 * Usage:
 *   node parse-statements.js <path-to-pdf-or-directory>
 * 
 * Examples:
 *   node parse-statements.js "C:\Users\alexp\Downloads\2026-04-15 Statement - USB Alex Personal 5568.pdf"
 *   node parse-statements.js "C:\Users\alexp\Downloads"
 */

async function main() {
  const args = process.argv.slice(2);
  
  if (args.length === 0) {
    console.log('Usage: node parse-statements.js <path-to-pdf-or-directory>');
    console.log('Example: node parse-statements.js "C:\\Users\\alexp\\Downloads\\2026-04-15 Statement - USB Alex Personal 5568.pdf"');
    process.exit(1);
  }

  const inputPath = args[0];
  const parser = new PDFStatementParser();
  
  try {
    let results;
    
    if (fs.statSync(inputPath).isDirectory()) {
      // Parse all PDF files in directory
      const pdfFiles = fs.readdirSync(inputPath)
        .filter(file => file.toLowerCase().endsWith('.pdf'))
        .map(file => path.join(inputPath, file));
      
      if (pdfFiles.length === 0) {
        console.log('No PDF files found in directory');
        process.exit(1);
      }
      
      console.log(`Found ${pdfFiles.length} PDF file(s) to parse...`);
      results = await parser.parseMultipleStatements(pdfFiles);
    } else {
      // Parse single PDF file
      console.log(`Parsing ${inputPath}...`);
      const statement = await parser.parseStatement(inputPath);
      results = {
        statementCount: 1,
        statements: [statement.statementInfo],
        transactions: statement.transactions,
        summary: parser.calculateCostSummary(statement.transactions)
      };
    }

    // Display results
    console.log('\n=== STATEMENT PARSING RESULTS ===\n');
    
    console.log(`Statements Processed: ${results.statementCount}`);
    console.log('\nStatement Information:');
    results.statements.forEach((info, idx) => {
      console.log(`  Statement ${idx + 1}:`);
      console.log(`    Period: ${info.statementPeriod || 'N/A'}`);
      console.log(`    Account: ${info.accountNumber || 'N/A'}`);
      console.log(`    Opening Balance: ${info.openingBalance ? '$' + info.openingBalance.toFixed(2) : 'N/A'}`);
      console.log(`    Closing Balance: ${info.closingBalance ? '$' + info.closingBalance.toFixed(2) : 'N/A'}`);
    });

    console.log('\n=== OPERATIONAL COST SUMMARY ===\n');
    
    const summary = results.summary;
    console.log(`Total Transactions: ${summary.allTransactions.total}`);
    console.log(`Total Spending: $${summary.allTransactions.totalSpending.toFixed(2)}`);
    console.log(`Total Deposits: $${summary.allTransactions.totalDeposits.toFixed(2)}`);
    console.log(`Net Cash Flow: $${summary.netCashFlow.toFixed(2)}`);
    
    console.log('\n--- Infrastructure Costs ---');
    console.log(`Infrastructure Transactions: ${summary.infrastructureCosts.transactionCount}`);
    console.log(`Total Infrastructure Cost: $${summary.infrastructureCosts.total.toFixed(2)}`);
    
    if (summary.categoryBreakdown && Object.keys(summary.categoryBreakdown).length > 0) {
      console.log('\n--- Cost by Category ---');
      Object.entries(summary.categoryBreakdown).forEach(([category, data]) => {
        console.log(`  ${category}:`);
        console.log(`    Transactions: ${data.count}`);
        console.log(`    Total: $${data.total.toFixed(2)}`);
      });
    }

    if (summary.infrastructureCosts.transactions.length > 0) {
      console.log('\n--- Infrastructure Transaction Details ---');
      summary.infrastructureCosts.transactions.forEach((tx, idx) => {
        console.log(`  ${idx + 1}. ${tx.date} | ${tx.description} | $${Math.abs(tx.amount).toFixed(2)} | ${tx.category}`);
      });
    }

    // Save results to JSON file
    const outputPath = path.join(__dirname, 'statement-analysis-results.json');
    fs.writeFileSync(outputPath, JSON.stringify(results, null, 2));
    console.log(`\nResults saved to: ${outputPath}`);

    // Save infrastructure transactions to separate file for dashboard
    const dashboardData = {
      currentBalance: results.statements[results.statements.length - 1]?.closingBalance || 0,
      period: {
        startDate: results.transactions[0]?.date.toISOString().split('T')[0] || new Date().toISOString().split('T')[0],
        endDate: results.transactions[results.transactions.length - 1]?.date.toISOString().split('T')[0] || new Date().toISOString().split('T')[0],
        days: results.statatementCount * 30 || 30
      },
      infrastructureCosts: summary.infrastructureCosts,
      allTransactions: summary.allTransactions,
      categories: summary.categoryBreakdown,
      lastUpdated: new Date().toISOString(),
      source: 'PDF Statement Parser'
    };

    const dashboardPath = path.join(__dirname, 'cost-transparency-cache.json');
    fs.writeFileSync(dashboardPath, JSON.stringify({ data: dashboardData, cachedAt: new Date().toISOString() }, null, 2));
    console.log(`Dashboard data saved to: ${dashboardPath}`);

  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

// Run if executed directly
if (require.main === module) {
  main();
}

module.exports = { main };
