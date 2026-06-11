/**
 * Trading API Bridge
 * HTTP client for AI Trader microservice with retry logic and fallbacks
 */

const http = require('http');

class TradingAPIBridge {
  constructor(host = '127.0.0.1', port = 5555, apiKey = null, timeout = 10000) {
    this.host = host;
    this.port = port;
    this.apiKey = apiKey;
    this.timeout = timeout;
    this.maxRetries = 3;
    this.retryDelay = 500; // ms
    this.cache = {};
    this.lastHealthCheck = 0;
    this.isHealthy = false;
  }

  async _request(method, path, body = null, retries = 0) {
    return new Promise((resolve, reject) => {
      const options = {
        hostname: this.host,
        port: this.port,
        path,
        method,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        timeout: this.timeout,
      };

      if (this.apiKey && (method === 'POST' || method === 'PUT')) {
        options.headers['X-API-Key'] = this.apiKey;
      }

      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', chunk => data += chunk);
        res.on('end', () => {
          try {
            const parsed = data ? JSON.parse(data) : {};
            if (res.statusCode >= 200 && res.statusCode < 300) {
              resolve({ status: res.statusCode, data: parsed });
            } else {
              reject(new Error(`HTTP ${res.statusCode}: ${parsed.error || 'Unknown error'}`));
            }
          } catch (e) {
            reject(new Error(`Invalid JSON response: ${e.message}`));
          }
        });
      });

      req.on('error', (err) => {
        if (retries < this.maxRetries) {
          setTimeout(() => {
            this._request(method, path, body, retries + 1)
              .then(resolve)
              .catch(reject);
          }, this.retryDelay * (retries + 1));
        } else {
          reject(err);
        }
      });

      req.on('timeout', () => {
        req.destroy();
        if (retries < this.maxRetries) {
          setTimeout(() => {
            this._request(method, path, body, retries + 1)
              .then(resolve)
              .catch(reject);
          }, this.retryDelay * (retries + 1));
        } else {
          reject(new Error('Request timeout'));
        }
      });

      if (body) {
        req.write(JSON.stringify(body));
      }

      req.end();
    });
  }

  async healthCheck() {
    try {
      const result = await this._request('GET', '/health');
      this.isHealthy = true;
      this.lastHealthCheck = Date.now();
      return { healthy: true, data: result.data };
    } catch (error) {
      this.isHealthy = false;
      return { healthy: false, error: error.message };
    }
  }

  async getStatus() {
    try {
      const result = await this._request('GET', '/api/status');
      this.cache['status'] = result.data;
      return result.data;
    } catch (error) {
      return this.cache['status'] || { error: error.message, status: 'disconnected' };
    }
  }

  async getWatchlist() {
    try {
      const result = await this._request('GET', '/api/watchlist');
      this.cache['watchlist'] = result.data;
      return result.data;
    } catch (error) {
      return this.cache['watchlist'] || { error: error.message, watchlist: [] };
    }
  }

  async getZones() {
    try {
      const result = await this._request('GET', '/api/zones');
      this.cache['zones'] = result.data;
      return result.data;
    } catch (error) {
      return this.cache['zones'] || { error: error.message, zones: {} };
    }
  }

  async getSignals(limit = 10) {
    try {
      const result = await this._request('GET', `/api/signals?limit=${limit}`);
      this.cache['signals'] = result.data;
      return result.data;
    } catch (error) {
      return this.cache['signals'] || { error: error.message, signals: [] };
    }
  }

  async getPositions() {
    try {
      const result = await this._request('GET', '/api/positions');
      this.cache['positions'] = result.data;
      return result.data;
    } catch (error) {
      return this.cache['positions'] || { error: error.message, positions: [] };
    }
  }

  async getAlerts(limit = 20) {
    try {
      const result = await this._request('GET', `/api/alerts?limit=${limit}`);
      this.cache['alerts'] = result.data;
      return result.data;
    } catch (error) {
      return this.cache['alerts'] || { error: error.message, alerts: [] };
    }
  }

  async getDashboardData() {
    const [status, watchlist, zones, signals, positions, alerts] = await Promise.all([
      this.getStatus(),
      this.getWatchlist(),
      this.getZones(),
      this.getSignals(10),
      this.getPositions(),
      this.getAlerts(20),
    ]);

    return {
      status,
      watchlist,
      zones,
      signals,
      positions,
      alerts,
      health: { healthy: this.isHealthy, timestamp: new Date().toISOString() },
    };
  }

  async pauseTrading() {
    try {
      const result = await this._request('POST', '/api/control/pause');
      return { success: true, data: result.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async resumeTrading() {
    try {
      const result = await this._request('POST', '/api/control/resume');
      return { success: true, data: result.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }

  async closePosition(symbol) {
    try {
      const result = await this._request('POST', `/api/control/close-position?symbol=${symbol}`);
      return { success: true, data: result.data };
    } catch (error) {
      return { success: false, error: error.message };
    }
  }
}

module.exports = TradingAPIBridge;
