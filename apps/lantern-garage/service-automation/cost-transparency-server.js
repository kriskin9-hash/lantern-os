const express = require('express');
const USBankApiClient = require('./usbank-api-client');
const BankAuthFlow = require('./bank-auth-flow');
const path = require('path');
const fs = require('fs');

/**
 * Cost Transparency Server
 * Serves operational cost data from U.S. Bank API for outreach program transparency
 */

class CostTransparencyServer {
  constructor(port = 3000) {
    this.port = port;
    this.app = express();
    this.apiClient = new USBankApiClient();
    this.authFlow = new BankAuthFlow();
    this.dataCachePath = path.join(__dirname, 'cost-transparency-cache.json');
    
    this.setupMiddleware();
    this.setupRoutes();
  }

  setupMiddleware() {
    this.app.use(express.json());
    this.app.use(express.static(path.join(__dirname, '../public')));
  }

  setupRoutes() {
    // Health check
    this.app.get('/api/health', (req, res) => {
      res.json({ status: 'healthy', timestamp: new Date().toISOString() });
    });

    // OAuth initiation
    this.app.get('/api/auth/start', (req, res) => {
      try {
        const authInfo = this.authFlow.initiateAuthorization();
        res.json(authInfo);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // OAuth callback
    this.app.get('/api/auth/callback', async (req, res) => {
      try {
        const { code, state } = req.query;
        if (!code || !state) {
          return res.status(400).json({ error: 'Missing code or state parameter' });
        }

        const result = await this.authFlow.handleCallback(code, state);
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Verify account
    this.app.post('/api/auth/verify', async (req, res) => {
      try {
        const { accountId } = req.body;
        if (!accountId) {
          return res.status(400).json({ error: 'accountId is required' });
        }

        const result = await this.authFlow.completeFlow(accountId);
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Test connection
    this.app.get('/api/auth/test', async (req, res) => {
      try {
        const result = await this.authFlow.testConnection();
        res.json(result);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get operational cost summary
    this.app.get('/api/costs/summary', async (req, res) => {
      try {
        const days = parseInt(req.query.days) || 30;
        const accountId = this.apiClient.config.accountId;

        if (!accountId) {
          return res.status(400).json({ 
            error: 'No account configured. Complete auth flow first.',
            cached: this.loadCachedData()
          });
        }

        const summary = await this.apiClient.getOperationalCostSummary(accountId, days);
        
        // Cache the data
        this.cacheData(summary);
        
        res.json(summary);
      } catch (error) {
        res.status(500).json({ 
          error: error.message,
          cached: this.loadCachedData()
        });
      }
    });

    // Get cached cost data (fallback)
    this.app.get('/api/costs/cached', (req, res) => {
      const cached = this.loadCachedData();
      if (cached) {
        res.json(cached);
      } else {
        res.status(404).json({ error: 'No cached data available' });
      }
    });

    // Parse PDF statements endpoint
    this.app.post('/api/statements/parse', async (req, res) => {
      try {
        const PDFStatementParser = require('./pdf-statement-parser');
        const parser = new PDFStatementParser();
        
        const { filePaths } = req.body;
        if (!filePaths || !Array.isArray(filePaths)) {
          return res.status(400).json({ error: 'filePaths array is required' });
        }

        const results = await parser.parseMultipleStatements(filePaths);
        
        // Cache the results
        const dashboardData = {
          currentBalance: results.statements[results.statements.length - 1]?.closingBalance || 0,
          period: {
            startDate: results.transactions[0]?.date.toISOString().split('T')[0] || new Date().toISOString().split('T')[0],
            endDate: results.transactions[results.transactions.length - 1]?.date.toISOString().split('T')[0] || new Date().toISOString().split('T')[0],
            days: results.statementCount * 30 || 30
          },
          infrastructureCosts: results.summary.infrastructureCosts,
          allTransactions: results.summary.allTransactions,
          categories: results.summary.categoryBreakdown,
          lastUpdated: new Date().toISOString(),
          source: 'PDF Statement Parser'
        };

        this.cacheData(dashboardData);
        
        res.json({
          success: true,
          statementCount: results.statementCount,
          summary: results.summary,
          dashboardData: dashboardData
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Manual infrastructure cost entry endpoint
    this.app.post('/api/costs/manual', (req, res) => {
      try {
        const { currentBalance, infrastructureCosts, period } = req.body;
        
        if (!currentBalance || !infrastructureCosts) {
          return res.status(400).json({ error: 'currentBalance and infrastructureCosts are required' });
        }

        const dashboardData = {
          currentBalance: currentBalance,
          period: period || {
            startDate: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
            endDate: new Date().toISOString().split('T')[0],
            days: 30
          },
          infrastructureCosts: {
            total: infrastructureCosts.total || 0,
            transactionCount: infrastructureCosts.transactions?.length || 0,
            transactions: infrastructureCosts.transactions || []
          },
          allTransactions: {
            total: infrastructureCosts.transactions?.length || 0,
            totalSpending: infrastructureCosts.total || 0,
            totalDeposits: 0
          },
          categories: infrastructureCosts.categories || {},
          lastUpdated: new Date().toISOString(),
          source: 'Manual Entry'
        };

        this.cacheData(dashboardData);
        
        res.json({
          success: true,
          dashboardData: dashboardData
        });
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Get transactions
    this.app.get('/api/transactions', async (req, res) => {
      try {
        const accountId = this.apiClient.config.accountId;
        if (!accountId) {
          return res.status(400).json({ error: 'No account configured' });
        }

        const days = parseInt(req.query.days) || 30;
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - days);

        const transactions = await this.apiClient.getTransactions(accountId, startDate, endDate);
        res.json(transactions);
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    });

    // Serve outreach page with cost dashboard
    this.app.get('/outreach-dashboard', (req, res) => {
      res.sendFile(path.join(__dirname, '../public/outreach-cost-dashboard.html'));
    });
  }

  cacheData(data) {
    try {
      const cacheEntry = {
        data: data,
        cachedAt: new Date().toISOString()
      };
      fs.writeFileSync(this.dataCachePath, JSON.stringify(cacheEntry, null, 2));
    } catch (error) {
      console.error('Failed to cache data:', error.message);
    }
  }

  loadCachedData() {
    try {
      if (fs.existsSync(this.dataCachePath)) {
        const content = fs.readFileSync(this.dataCachePath, 'utf8');
        const cacheEntry = JSON.parse(content);
        
        // Return cache if less than 24 hours old
        const cacheAge = Date.now() - new Date(cacheEntry.cachedAt).getTime();
        if (cacheAge < 24 * 60 * 60 * 1000) {
          return cacheEntry;
        }
      }
      return null;
    } catch (error) {
      console.error('Failed to load cached data:', error.message);
      return null;
    }
  }

  start() {
    this.app.listen(this.port, () => {
      console.log(`Cost Transparency Server running on port ${this.port}`);
      console.log(`Dashboard available at http://localhost:${this.port}/outreach-dashboard`);
      console.log(`API endpoints available at http://localhost:${this.port}/api/`);
    });
  }
}

// Start server if run directly
if (require.main === module) {
  const server = new CostTransparencyServer(3000);
  server.start();
}

module.exports = CostTransparencyServer;
