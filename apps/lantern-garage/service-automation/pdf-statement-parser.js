const fs = require('fs');
const pdfParse = require('pdf-parse');
const path = require('path');

/**
 * U.S. Bank Statement PDF Parser
 * Extracts transaction data from U.S. Bank PDF statements for cost transparency
 * 
 * This provides an alternative to live API integration by parsing downloaded statements
 */

class PDFStatementParser {
  constructor() {
    this.infrastructureKeywords = [
      'aws', 'amazon web services', 'amazonaws',
      'openai', 'open ai',
      'api', 'application programming interface',
      'token', 'tokens',
      'anthropic', 'claude',
      'google cloud', 'gcp',
      'azure', 'microsoft azure',
      'digitalocean', 'digital ocean',
      'heroku', 'vercel', 'netlify',
      'stripe', 'paypal',
      'infrastructure', 'hosting', 'server'
    ];
  }

  /**
   * Parse a U.S. Bank statement PDF file
   */
  async parseStatement(pdfPath) {
    try {
      const dataBuffer = fs.readFileSync(pdfPath);
      const data = await pdfParse(dataBuffer);
      
      const transactions = this.extractTransactions(data.text);
      const statementInfo = this.extractStatementInfo(data.text);
      
      return {
        statementInfo,
        transactions,
        rawText: data.text,
        pageCount: data.numpages
      };
    } catch (error) {
      throw new Error(`Failed to parse PDF: ${error.message}`);
    }
  }

  /**
   * Extract statement metadata (period, account info, etc.)
   */
  extractStatementInfo(text) {
    const info = {
      statementPeriod: null,
      accountNumber: null,
      accountType: null,
      openingBalance: null,
      closingBalance: null
    };

    // Extract statement period (various formats)
    const periodPatterns = [
      /Statement Period:\s*(.+?)(?:\n|$)/i,
      /Period:\s*(.+?)(?:\n|$)/i,
      /From\s*(.+?)\s*to\s*(.+?)(?:\n|$)/i,
      /(\d{1,2}\/\d{1,2}\/\d{2,4})\s*-\s*(\d{1,2}\/\d{1,2}\/\d{2,4})/
    ];

    for (const pattern of periodPatterns) {
      const match = text.match(pattern);
      if (match) {
        info.statementPeriod = match[0].trim();
        break;
      }
    }

    // Extract account number (last 4 digits common format)
    const accountMatch = text.match(/Account.*?(\*{0,4}\d{4})/i);
    if (accountMatch) {
      info.accountNumber = accountMatch[1];
    }

    // Extract balances
    const balancePatterns = [
      { pattern: /Opening Balance[:\s]*\$?([\d,]+\.?\d*)/gi, type: 'opening' },
      { pattern: /Beginning Balance[:\s]*\$?([\d,]+\.?\d*)/gi, type: 'opening' },
      { pattern: /Closing Balance[:\s]*\$?([\d,]+\.?\d*)/gi, type: 'closing' },
      { pattern: /Ending Balance[:\s]*\$?([\d,]+\.?\d*)/gi, type: 'closing' },
      { pattern: /Current Balance[:\s]*\$?([\d,]+\.?\d*)/gi, type: 'closing' }
    ];

    for (const { pattern, type } of balancePatterns) {
      const matches = text.matchAll(pattern);
      for (const match of matches) {
        const balance = parseFloat(match[1].replace(/,/g, ''));
        if (type === 'opening') {
          info.openingBalance = balance;
        } else if (type === 'closing') {
          info.closingBalance = balance;
        }
      }
    }

    return info;
  }

  /**
   * Extract transactions from statement text
   */
  extractTransactions(text) {
    const transactions = [];
    
    // Split text into lines
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    
    // U.S. Bank statement format: Multi-line transactions
    // Pattern: Date (Mar26) followed by transaction details on subsequent lines
    const datePattern = /^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(\d{1,2})/i;
    const amountPattern = /^-?\$?[\d,]+\.?\d*-?$/;
    
    let i = 0;
    while (i < lines.length) {
      const line = lines[i];
      const dateMatch = line.match(datePattern);
      
      if (dateMatch) {
        // Found a date line, start building transaction
        const monthStr = dateMatch[1];
        const dayStr = dateMatch[2];
        const transactionType = line.substring(dateMatch[0].length).trim();
        
        // Look ahead for description, reference, and amount
        let description = '';
        let amount = null;
        let j = i + 1;
        
        while (j < lines.length && j < i + 6) { // Look at next 6 lines max
          const nextLine = lines[j];
          
          // Check if this line is an amount (has decimal point, may have $, may end with -)
          // More specific: must be reasonable transaction amount (under $100,000)
          const amountMatch = nextLine.match(/^(-?\$?[\d,]+\.\d{2})(-?)$/);
          if (amountMatch) {
            const parsedAmount = this.parseAmount(amountMatch[1]);
            // Only accept if it's a reasonable transaction amount
            if (parsedAmount > 0 && parsedAmount < 100000) {
              amount = parsedAmount;
              // If amount ends with -, it's a withdrawal (negative)
              if (amountMatch[2] === '-' && amount > 0) {
                amount = -amount;
              }
              break;
            }
          }
          
          // Check if this line looks like a reference number (all digits, no decimal)
          if (/^\d+$/.test(nextLine)) {
            j++;
            continue;
          }
          
          // Check if this line starts with "On" (reference date format)
          if (nextLine.startsWith('On ')) {
            j++;
            continue;
          }
          
          // Otherwise, treat as description (if not already found)
          if (!description && nextLine.length > 3 && !amountMatch) {
            description = nextLine;
          }
          
          j++;
        }
        
        // If we found an amount, create the transaction
        if (amount !== null) {
          const transaction = {
            date: this.parseUSBankDate(monthStr, dayStr),
            description: description || transactionType,
            amount: amount,
            balance: null,
            isInfrastructure: this.isInfrastructureTransaction(description || transactionType),
            category: this.categorizeTransaction(description || transactionType)
          };
          
          transactions.push(transaction);
          i = j; // Skip to after the amount
        } else {
          i++;
        }
      } else {
        i++;
      }
    }

    // If U.S. Bank format didn't work, try standard table format
    if (transactions.length === 0) {
      return this.extractTransactionsTableFormat(text);
    }

    return transactions;
  }

  /**
   * Parse U.S. Bank date format (Mar26 -> March 26, current year)
   */
  parseUSBankDate(monthStr, dayStr) {
    const months = {
      'Jan': 0, 'Feb': 1, 'Mar': 2, 'Apr': 3, 'May': 4, 'Jun': 5,
      'Jul': 6, 'Aug': 7, 'Sep': 8, 'Oct': 9, 'Nov': 10, 'Dec': 11
    };
    
    const month = months[monthStr.charAt(0).toUpperCase() + monthStr.slice(1).toLowerCase()];
    const day = parseInt(dayStr);
    const year = new Date().getFullYear(); // Assume current year
    
    return new Date(year, month, day);
  }

  /**
   * Extract transactions in standard table format (fallback)
   */
  extractTransactionsTableFormat(text) {
    const transactions = [];
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    
    // Standard format: Date | Description | Amount | Balance
    const transactionPattern = /^(\d{1,2}\/\d{1,2}\/\d{2,4})\s+(.+?)\s+(-?\$?[\d,]+\.?\d*)\s*(\$?[\d,]+\.?\d*)?$/;
    
    for (const line of lines) {
      const match = line.match(transactionPattern);
      if (match) {
        transactions.push({
          date: this.parseDate(match[1]),
          description: match[2].trim(),
          amount: this.parseAmount(match[3]),
          balance: match[4] ? this.parseAmount(match[4]) : null,
          isInfrastructure: this.isInfrastructureTransaction(match[2]),
          category: this.categorizeTransaction(match[2])
        });
      }
    }

    return transactions;
  }

  /**
   * Alternative transaction extraction for different statement formats
   */
  extractTransactionsAlternative(text) {
    const transactions = [];
    
    // Look for lines with dates and dollar amounts
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    
    for (const line of lines) {
      // Check if line contains a date and an amount
      const dateMatch = line.match(/\d{1,2}\/\d{1,2}\/\d{2,4}/);
      const amountMatch = line.match(/-?\$?[\d,]+\.?\d*/);
      
      if (dateMatch && amountMatch) {
        const description = line
          .replace(dateMatch[0], '')
          .replace(amountMatch[0], '')
          .trim();
        
        if (description.length > 0) {
          transactions.push({
            date: this.parseDate(dateMatch[0]),
            description: description,
            amount: this.parseAmount(amountMatch[0]),
            balance: null,
            isInfrastructure: this.isInfrastructureTransaction(description),
            category: this.categorizeTransaction(description)
          });
        }
      }
    }

    return transactions;
  }

  /**
   * Parse date string to Date object
   */
  parseDate(dateStr) {
    // Handle various date formats
    const formats = [
      /(\d{1,2})\/(\d{1,2})\/(\d{2,4})/,  // MM/DD/YYYY or MM/DD/YY
      /(\d{4})-(\d{1,2})-(\d{1,2})/,      // YYYY-MM-DD
      /(\d{1,2})-(\d{1,2})-(\d{4})/       // DD-MM-YYYY
    ];

    for (const format of formats) {
      const match = dateStr.match(format);
      if (match) {
        let year, month, day;
        
        if (format.toString().includes('YYYY-MM-DD')) {
          year = parseInt(match[1]);
          month = parseInt(match[2]) - 1;
          day = parseInt(match[3]);
        } else if (format.toString().includes('DD-MM-YYYY')) {
          day = parseInt(match[1]);
          month = parseInt(match[2]) - 1;
          year = parseInt(match[3]);
        } else {
          month = parseInt(match[1]) - 1;
          day = parseInt(match[2]);
          year = parseInt(match[3]);
          
          // Handle 2-digit years
          if (year < 100) {
            year += year < 50 ? 2000 : 1900;
          }
        }

        return new Date(year, month, day);
      }
    }

    return new Date(); // Fallback to today
  }

  /**
   * Parse amount string to number
   */
  parseAmount(amountStr) {
    if (!amountStr) return 0;
    
    const cleaned = amountStr
      .replace(/[$,]/g, '')
      .trim();
    
    const parsed = parseFloat(cleaned);
    return isNaN(parsed) ? 0 : parsed;
  }

  /**
   * Check if transaction is infrastructure-related
   */
  isInfrastructureTransaction(description) {
    const lowerDesc = description.toLowerCase();
    return this.infrastructureKeywords.some(keyword => 
      lowerDesc.includes(keyword)
    );
  }

  /**
   * Categorize transaction based on description
   */
  categorizeTransaction(description) {
    const lowerDesc = description.toLowerCase();
    
    if (lowerDesc.includes('aws') || lowerDesc.includes('amazon')) return 'Cloud/AWS';
    if (lowerDesc.includes('openai') || lowerDesc.includes('open ai')) return 'AI/OpenAI';
    if (lowerDesc.includes('anthropic') || lowerDesc.includes('claude')) return 'AI/Anthropic';
    if (lowerDesc.includes('google') || lowerDesc.includes('gcp')) return 'Cloud/Google';
    if (lowerDesc.includes('azure')) return 'Cloud/Azure';
    if (lowerDesc.includes('stripe') || lowerDesc.includes('paypal')) return 'Payment Processing';
    if (lowerDesc.includes('github')) return 'Development Tools';
    if (lowerDesc.includes('domain') || lowerDesc.includes('hosting')) return 'Infrastructure';
    if (lowerDesc.includes('software') || lowerDesc.includes('subscription')) return 'Software';
    
    return 'Other';
  }

  /**
   * Calculate operational cost summary from parsed transactions
   */
  calculateCostSummary(transactions) {
    const infrastructureTransactions = transactions.filter(t => t.isInfrastructure);
    
    const totalInfrastructureCost = infrastructureTransactions.reduce(
      (sum, t) => sum + Math.abs(t.amount), 0
    );
    
    const totalSpending = transactions
      .filter(t => t.amount < 0)
      .reduce((sum, t) => sum + Math.abs(t.amount), 0);
    
    const totalDeposits = transactions
      .filter(t => t.amount > 0)
      .reduce((sum, t) => sum + t.amount, 0);

    // Group by category
    const categoryBreakdown = {};
    infrastructureTransactions.forEach(t => {
      const category = t.category || 'Uncategorized';
      if (!categoryBreakdown[category]) {
        categoryBreakdown[category] = { count: 0, total: 0 };
      }
      categoryBreakdown[category].count++;
      categoryBreakdown[category].total += Math.abs(t.amount);
    });

    return {
      infrastructureCosts: {
        total: totalInfrastructureCost,
        transactionCount: infrastructureTransactions.length,
        transactions: infrastructureTransactions.map(t => ({
          date: t.date.toISOString().split('T')[0],
          description: t.description,
          amount: t.amount,
          category: t.category
        }))
      },
      allTransactions: {
        total: transactions.length,
        totalSpending: totalSpending,
        totalDeposits: totalDeposits
      },
      categoryBreakdown,
      netCashFlow: totalDeposits - totalSpending
    };
  }

  /**
   * Parse multiple statement files and combine results
   */
  async parseMultipleStatements(filePaths) {
    const allTransactions = [];
    const statementSummaries = [];

    for (const filePath of filePaths) {
      try {
        const statement = await this.parseStatement(filePath);
        statementSummaries.push(statement.statementInfo);
        allTransactions.push(...statement.transactions);
      } catch (error) {
        console.error(`Failed to parse ${filePath}:`, error.message);
      }
    }

    // Sort all transactions by date
    allTransactions.sort((a, b) => a.date - b.date);

    return {
      statementCount: statementSummaries.length,
      statements: statementSummaries,
      transactions: allTransactions,
      summary: this.calculateCostSummary(allTransactions)
    };
  }
}

module.exports = PDFStatementParser;
