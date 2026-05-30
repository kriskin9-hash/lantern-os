const https = require('https');
const fs = require('fs');
const path = require('path');

/**
 * U.S. Bank Data Toolbox API Client
 * Integrates with U.S. Bank retail banking APIs for transparent operational cost reporting
 * 
 * API Documentation: https://developer.usbank.com/
 * Data Toolbox: Access authorized consumer banking account, transaction and tax data
 */

class USBankApiClient {
  constructor(configPath) {
    this.configPath = configPath || path.join(__dirname, 'usbank-config.json');
    this.config = this.loadConfig();
    this.baseUrl = 'api.usbank.com';
    this.apiVersion = 'v1';
  }

  /**
   * Load API configuration from secure config file
   */
  loadConfig() {
    try {
      const content = fs.readFileSync(this.configPath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      console.error('Failed to load U.S. Bank API config:', error.message);
      return {
        clientId: null,
        clientSecret: null,
        redirectUri: null,
        environment: 'sandbox',
        accessToken: null,
        refreshToken: null
      };
    }
  }

  /**
   * Save API configuration
   */
  saveConfig() {
    try {
      fs.writeFileSync(this.configPath, JSON.stringify(this.config, null, 2));
      return true;
    } catch (error) {
      console.error('Failed to save U.S. Bank API config:', error.message);
      return false;
    }
  }

  /**
   * Step 1: Verify - Account Validation
   * Validate account information to verify identity and enhance security
   */
  async validateAccount(accountNumber, routingNumber) {
    const endpoint = `/account-validation/${this.apiVersion}/accounts`;
    const payload = {
      accountNumber: this.maskSensitive(accountNumber),
      routingNumber: routingNumber
    };

    return this.makeRequest('POST', endpoint, payload);
  }

  /**
   * Step 2: Access - Get Account Balance
   * Get current balance of savings/checking account
   */
  async getAccountBalance(accountId) {
    const endpoint = `/accounts/${this.apiVersion}/${accountId}/balances`;
    return this.makeRequest('GET', endpoint);
  }

  /**
   * Step 2: Access - Get Account Details
   * Access account details including account type and status
   */
  async getAccountDetails(accountId) {
    const endpoint = `/accounts/${this.apiVersion}/${accountId}`;
    return this.makeRequest('GET', endpoint);
  }

  /**
   * Step 2: Access - Get Documents (Spending Habits)
   * Use Documents feature to obtain spending habits and statements
   */
  async getAccountDocuments(accountId, documentType = 'statement') {
    const endpoint = `/accounts/${this.apiVersion}/${accountId}/documents`;
    const params = new URLSearchParams({ documentType });
    return this.makeRequest('GET', `${endpoint}?${params}`);
  }

  /**
   * Step 3: Compare - Get Transactions
   * Compare savings balance against income and spend
   */
  async getTransactions(accountId, startDate, endDate, limit = 100) {
    const endpoint = `/accounts/${this.apiVersion}/${accountId}/transactions`;
    const params = new URLSearchParams({
      startDate: startDate.toISOString().split('T')[0],
      endDate: endDate.toISOString().split('T')[0],
      limit: limit.toString()
    });
    return this.makeRequest('GET', `${endpoint}?${params}`);
  }

  /**
   * Step 4: Analyze - Transaction Categories
   * Analyze deposits and payment frequency with Transactions feature
   */
  async getTransactionCategories(accountId) {
    const endpoint = `/accounts/${this.apiVersion}/${accountId}/transactions/categories`;
    return this.makeRequest('GET', endpoint);
  }

  /**
   * Step 5: Enrich - Get Tax Data
   * Access authorized tax data for comprehensive financial picture
   */
  async getTaxData(accountId, taxYear) {
    const endpoint = `/accounts/${this.apiVersion}/${accountId}/tax/${taxYear}`;
    return this.makeRequest('GET', endpoint);
  }

  /**
   * OAuth 2.0 Authorization Code Flow
   * Initiate the authorization process
   */
  getAuthorizationUrl(scopes = ['accounts', 'transactions', 'documents']) {
    const authUrl = `https://${this.baseUrl}/oauth2/authorize`;
    const params = new URLSearchParams({
      response_type: 'code',
      client_id: this.config.clientId,
      redirect_uri: this.config.redirectUri,
      scope: scopes.join(' '),
      state: this.generateState()
    });
    return `${authUrl}?${params}`;
  }

  /**
   * Exchange authorization code for access token
   */
  async exchangeCodeForToken(code, state) {
    const endpoint = '/oauth2/token';
    const payload = {
      grant_type: 'authorization_code',
      code: code,
      redirect_uri: this.config.redirectUri,
      client_id: this.config.clientId,
      client_secret: this.config.clientSecret
    };
    
    const response = await this.makeRequest('POST', endpoint, payload, true);
    
    if (response.access_token) {
      this.config.accessToken = response.access_token;
      this.config.refreshToken = response.refresh_token;
      this.saveConfig();
    }
    
    return response;
  }

  /**
   * Refresh access token
   */
  async refreshAccessToken() {
    const endpoint = '/oauth2/token';
    const payload = {
      grant_type: 'refresh_token',
      refresh_token: this.config.refreshToken,
      client_id: this.config.clientId,
      client_secret: this.config.clientSecret
    };
    
    const response = await this.makeRequest('POST', endpoint, payload, true);
    
    if (response.access_token) {
      this.config.accessToken = response.access_token;
      if (response.refresh_token) {
        this.config.refreshToken = response.refresh_token;
      }
      this.saveConfig();
    }
    
    return response;
  }

  /**
   * Make authenticated API request
   */
  async makeRequest(method, endpoint, payload = null, isAuth = false) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.baseUrl,
        path: endpoint,
        method: method,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        }
      };

      if (!isAuth && this.config.accessToken) {
        options.headers['Authorization'] = `Bearer ${this.config.accessToken}`;
      }

      const req = https.request(options, (res) => {
        let data = '';
        
        res.on('data', (chunk) => {
          data += chunk;
        });
        
        res.on('end', () => {
          try {
            const jsonData = JSON.parse(data);
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve(jsonData);
            } else {
              reject(new Error(`API Error ${res.statusCode}: ${jsonData.message || data}`));
            }
          } catch (error) {
            reject(new Error(`Failed to parse response: ${error.message}`));
          }
        });
      });

      req.on('error', (error) => {
        reject(error);
      });

      if (payload) {
        req.write(JSON.stringify(payload));
      }

      req.end();
    });
  }

  /**
   * Generate random state parameter for OAuth security
   */
  generateState() {
    return Math.random().toString(36).substring(2, 15) + 
           Math.random().toString(36).substring(2, 15);
  }

  /**
   * Mask sensitive data for logging
   */
  maskSensitive(data) {
    if (!data || typeof data !== 'string') return data;
    if (data.length <= 4) return '****';
    return data.substring(0, 2) + '****' + data.substring(data.length - 2);
  }

  /**
   * Get operational cost summary for transparency dashboard
   * Aggregates transaction data to show infrastructure costs
   */
  async getOperationalCostSummary(accountId, days = 30) {
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);

    try {
      const [transactions, balance, categories] = await Promise.all([
        this.getTransactions(accountId, startDate, endDate),
        this.getAccountBalance(accountId),
        this.getTransactionCategories(accountId)
      ]);

      // Filter for infrastructure-related transactions
      const infrastructureTransactions = transactions.filter(t => 
        t.description && (
          t.description.toLowerCase().includes('aws') ||
          t.description.toLowerCase().includes('openai') ||
          t.description.toLowerCase().includes('api') ||
          t.description.toLowerCase().includes('token') ||
          t.category && t.category.toLowerCase().includes('technology')
        )
      );

      const totalInfrastructureCost = infrastructureTransactions.reduce(
        (sum, t) => sum + Math.abs(t.amount), 0
      );

      return {
        currentBalance: balance.available || balance.current,
        period: { startDate, endDate, days },
        infrastructureCosts: {
          total: totalInfrastructureCost,
          transactionCount: infrastructureTransactions.length,
          transactions: infrastructureTransactions.map(t => ({
            date: t.date,
            description: t.description,
            amount: t.amount,
            category: t.category
          }))
        },
        allTransactions: {
          total: transactions.length,
          totalSpending: transactions.filter(t => t.amount < 0).reduce((sum, t) => sum + Math.abs(t.amount), 0),
          totalDeposits: transactions.filter(t => t.amount > 0).reduce((sum, t) => sum + t.amount, 0)
        },
        categories: categories,
        lastUpdated: new Date().toISOString()
      };
    } catch (error) {
      console.error('Failed to get operational cost summary:', error.message);
      throw error;
    }
  }
}

module.exports = USBankApiClient;
