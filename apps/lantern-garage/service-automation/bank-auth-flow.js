const USBankApiClient = require('./usbank-api-client');
const fs = require('fs');
const path = require('path');

/**
 * Bank Account Authentication and Verification Flow
 * Handles the complete OAuth flow and account verification for transparent cost reporting
 */

class BankAuthFlow {
  constructor(configPath) {
    this.apiClient = new USBankApiClient(configPath);
    this.authStatePath = path.join(path.dirname(configPath), 'auth-state.json');
  }

  /**
   * Step 1: Initiate OAuth Authorization
   * Generate authorization URL and redirect user to U.S. Bank consent screen
   */
  initiateAuthorization(scopes = ['accounts', 'transactions', 'documents']) {
    const authUrl = this.apiClient.getAuthorizationUrl(scopes);
    const state = this.extractStateFromUrl(authUrl);
    
    // Save state for verification
    this.saveAuthState({ state, timestamp: new Date().toISOString() });
    
    return {
      authUrl,
      state,
      instructions: 'Visit this URL to authorize U.S. Bank access. After authorization, you will be redirected to your redirect URI with an authorization code.'
    };
  }

  /**
   * Step 2: Handle OAuth Callback
   * Exchange authorization code for access token
   */
  async handleCallback(code, state) {
    // Verify state matches
    const savedState = this.loadAuthState();
    if (!savedState || savedState.state !== state) {
      throw new Error('Invalid state parameter. Possible CSRF attack.');
    }

    try {
      const tokenResponse = await this.apiClient.exchangeCodeForToken(code, state);
      
      // Clear auth state after successful exchange
      this.clearAuthState();
      
      return {
        success: true,
        accessToken: tokenResponse.access_token ? '***REDACTED***' : null,
        refreshToken: tokenResponse.refresh_token ? '***REDACTED***' : null,
        expiresIn: tokenResponse.expires_in,
        tokenType: tokenResponse.token_type
      };
    } catch (error) {
      throw new Error(`Token exchange failed: ${error.message}`);
    }
  }

  /**
   * Step 3: Verify Account
   * Validate account information and retrieve account details
   */
  async verifyAccount(accountId) {
    try {
      const [accountDetails, balance] = await Promise.all([
        this.apiClient.getAccountDetails(accountId),
        this.apiClient.getAccountBalance(accountId)
      ]);

      return {
        verified: true,
        accountId: accountId,
        accountType: accountDetails.accountType,
        accountStatus: accountDetails.status,
        currentBalance: balance.available || balance.current,
        currency: balance.currency,
        verifiedAt: new Date().toISOString()
      };
    } catch (error) {
      throw new Error(`Account verification failed: ${error.message}`);
    }
  }

  /**
   * Step 4: List Available Accounts
   * Get list of authorized accounts for user selection
   */
  async listAccounts() {
    try {
      // This would typically call an accounts list endpoint
      // For now, return a placeholder structure
      return {
        accounts: [],
        message: 'Account listing requires specific U.S. Bank endpoint. Please provide accountId manually or implement accounts list endpoint.'
      };
    } catch (error) {
      throw new Error(`Failed to list accounts: ${error.message}`);
    }
  }

  /**
   * Complete Authentication Flow
   * End-to-end flow from authorization to account verification
   */
  async completeFlow(accountId) {
    const verification = await this.verifyAccount(accountId);
    
    // Save verified account ID to config
    this.apiClient.config.accountId = accountId;
    this.apiClient.saveConfig();
    
    return {
      success: true,
      verification: verification,
      nextSteps: [
        'Account verified successfully',
        'You can now retrieve transaction data',
        'Use getOperationalCostSummary() to generate transparency report'
      ]
    };
  }

  /**
   * Test Connection
   * Verify that the API client is properly configured
   */
  async testConnection() {
    try {
      if (!this.apiClient.config.accessToken) {
        return {
          connected: false,
          message: 'No access token. Please complete OAuth flow first.'
        };
      }

      // Try to get account details to test connection
      if (this.apiClient.config.accountId) {
        await this.apiClient.getAccountDetails(this.apiClient.config.accountId);
        return {
          connected: true,
          message: 'Connection successful. API access verified.'
        };
      }

      return {
        connected: true,
        message: 'Access token present. Please verify an account ID.'
      };
    } catch (error) {
      return {
        connected: false,
        message: `Connection test failed: ${error.message}`
      };
    }
  }

  /**
   * Refresh Token if Needed
   * Check and refresh access token if expired
   */
  async ensureValidToken() {
    try {
      if (!this.apiClient.config.refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await this.apiClient.refreshAccessToken();
      return {
        success: true,
        message: 'Token refreshed successfully',
        expiresIn: response.expires_in
      };
    } catch (error) {
      throw new Error(`Token refresh failed: ${error.message}`);
    }
  }

  /**
   * Helper: Extract state from auth URL
   */
  extractStateFromUrl(url) {
    const match = url.match(/[?&]state=([^&]+)/);
    return match ? match[1] : null;
  }

  /**
   * Helper: Save auth state to file
   */
  saveAuthState(state) {
    try {
      fs.writeFileSync(this.authStatePath, JSON.stringify(state, null, 2));
    } catch (error) {
      console.error('Failed to save auth state:', error.message);
    }
  }

  /**
   * Helper: Load auth state from file
   */
  loadAuthState() {
    try {
      const content = fs.readFileSync(this.authStatePath, 'utf8');
      return JSON.parse(content);
    } catch (error) {
      return null;
    }
  }

  /**
   * Helper: Clear auth state
   */
  clearAuthState() {
    try {
      if (fs.existsSync(this.authStatePath)) {
        fs.unlinkSync(this.authStatePath);
      }
    } catch (error) {
      console.error('Failed to clear auth state:', error.message);
    }
  }
}

module.exports = BankAuthFlow;
