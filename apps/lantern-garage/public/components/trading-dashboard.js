/**
 * Trading Dashboard Component
 */

class TradingDashboard {
  constructor(containerId = 'trading-panel') {
    this.container = document.getElementById(containerId);
    this.isHealthy = false;
    this.statusCache = {};
    if (!this.container) return;
    this.init();
  }

  async init() {
    await this.healthCheck();
    this.render();
    setInterval(() => this.refresh(), 5000);
  }

  async healthCheck() {
    try {
      const res = await fetch('/api/trading/ai-trader/health');
      this.isHealthy = res.ok;
    } catch (e) {
      this.isHealthy = false;
    }
  }

  async refresh() {
    try {
      const [status, positions, signals] = await Promise.all([
        fetch('/api/trading/ai-trader/status').then(r => r.json()).catch(() => ({})),
        fetch('/api/trading/ai-trader/positions').then(r => r.json()).catch(() => ({})),
        fetch('/api/trading/ai-trader/signals?limit=5').then(r => r.json()).catch(() => ({})),
      ]);
      this.render(status, positions, signals);
    } catch (e) {
      console.error('Refresh failed:', e);
    }
  }

  async pauseTrading() {
    if (!confirm('Pause trading?')) return;
    try {
      await fetch('/api/trading/ai-trader/pause', { method: 'POST' });
      this.refresh();
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  async resumeTrading() {
    if (!confirm('Resume trading?')) return;
    try {
      await fetch('/api/trading/ai-trader/resume', { method: 'POST' });
      this.refresh();
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  async closePosition(symbol) {
    if (!confirm(`Close ${symbol}?`)) return;
    try {
      await fetch(`/api/trading/ai-trader/close-position?symbol=${symbol}`, { method: 'POST' });
      this.refresh();
    } catch (e) {
      alert('Error: ' + e.message);
    }
  }

  render(status = {}, positions = {}, signals = {}) {
    if (!this.container) return;

    const paused = status.paused || false;
    let html = `
      <div style="border: 1px solid #ccc; padding: 12px; margin: 12px 0; border-radius: 4px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <h3 style="margin: 0;">📈 Trading</h3>
          <div>
            <button onclick="tradingDashboard.refresh()" style="padding: 4px 8px; margin-right: 4px;">Refresh</button>
            ${paused 
              ? '<button onclick="tradingDashboard.resumeTrading()" style="padding: 4px 8px;">Resume</button>'
              : '<button onclick="tradingDashboard.pauseTrading()" style="padding: 4px 8px;">Pause</button>'
            }
          </div>
        </div>
        <div style="font-size: 13px; color: #666; margin-bottom: 8px;">
          ${this.isHealthy ? '🟢' : '🔴'} 
          Market: ${status.market_open ? 'Open' : 'Closed'} | 
          Equity: $${(status.equity || 0).toFixed(0)} | 
          Positions: ${status.positions || 0}
          ${paused ? ' | 🛑 Paused' : ''}
        </div>
    `;

    if (positions.positions && positions.positions.length > 0) {
      html += '<div style="margin-bottom: 8px;"><strong>Positions:</strong> ';
      for (const pos of positions.positions.slice(0, 3)) {
        const pnl = pos.pnl_pct || 0;
        const color = pnl >= 0 ? '#2ecc71' : '#e74c3c';
        html += `<span style="color: ${color}; margin-right: 8px;">${pos.symbol} ${pnl.toFixed(1)}%</span>`;
      }
      html += '</div>';
    }

    if (signals.signals && signals.signals.length > 0) {
      html += '<div style="font-size: 12px;"><strong>Signals:</strong> ';
      for (const sig of signals.signals.slice(0, 2)) {
        html += `<span>${sig.agent} ${sig.direction} ${sig.ticker} ${sig.confidence}%</span> `;
      }
      html += '</div>';
    }

    html += '</div>';
    this.container.innerHTML = html;
  }
}

let tradingDashboard = null;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    tradingDashboard = new TradingDashboard('trading-panel');
  });
} else {
  tradingDashboard = new TradingDashboard('trading-panel');
}
