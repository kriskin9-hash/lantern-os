/**
 * Shadow Trading Engine
 *
 * Allows AI to generate trades without actual execution.
 * Used for backtesting and validation before live trading.
 *
 * Records performance metrics:
 * - Win rate
 * - Sharpe ratio
 * - Max drawdown
 * - Profit factor
 * - Expected value
 */

"use strict";

class ShadowTradingEngine {
  constructor(config = {}) {
    this.config = {
      initialCapital: config.initialCapital || 100000,
      ...config
    };

    this.trades = [];
    this.portfolio = {
      capital: this.config.initialCapital,
      positions: new Map(),
      pnl: 0,
      dailyPnL: 0,
      peakCapital: this.config.initialCapital,
      lowestCapital: this.config.initialCapital,
    };

    this.metrics = {
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      totalProfit: 0,
      totalLoss: 0,
    };

    this.mode = "shadow";  // Never executes live
  }

  /**
   * Simulate trade execution
   * Returns trade result without touching broker
   */
  simulateTrade(tradeRequest, marketPrice) {
    const tradeId = `SHADOW_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
    const entryTime = new Date().toISOString();

    const trade = {
      tradeId,
      ticker: tradeRequest.ticker,
      side: tradeRequest.side,
      entryPrice: marketPrice,
      quantity: tradeRequest.quantity,
      confidence: tradeRequest.confidence || 0.5,
      entryTime,
      exitPrice: null,
      exitTime: null,
      pnl: null,
      returnPercent: null,
      status: "OPEN",
    };

    this.trades.push(trade);
    this.metrics.totalTrades++;

    // Update position
    const posKey = tradeRequest.ticker;
    if (!this.portfolio.positions.has(posKey)) {
      this.portfolio.positions.set(posKey, {
        ticker: tradeRequest.ticker,
        quantity: 0,
        entryPrice: 0,
        currentPrice: marketPrice,
      });
    }

    const position = this.portfolio.positions.get(posKey);
    position.quantity += tradeRequest.side === "BUY" ? tradeRequest.quantity : -tradeRequest.quantity;
    position.entryPrice = marketPrice;
    position.currentPrice = marketPrice;

    console.log(
      `[ShadowTrading] Simulated ${tradeRequest.side} ${tradeRequest.quantity} ` +
      `${tradeRequest.ticker} @ ${marketPrice} (${tradeRequest.confidence.toFixed(2)})`
    );

    return {
      success: true,
      tradeId,
      trade,
    };
  }

  /**
   * Close simulated trade
   */
  closeTrade(tradeId, exitPrice) {
    const trade = this.trades.find(t => t.tradeId === tradeId);
    if (!trade || trade.status !== "OPEN") {
      return { success: false, reason: "Trade not found or already closed" };
    }

    trade.exitPrice = exitPrice;
    trade.exitTime = new Date().toISOString();
    trade.status = "CLOSED";

    // Calculate P&L
    if (trade.side === "BUY") {
      trade.pnl = (exitPrice - trade.entryPrice) * trade.quantity;
    } else {
      trade.pnl = (trade.entryPrice - exitPrice) * trade.quantity;
    }

    trade.returnPercent = (trade.pnl / (trade.entryPrice * trade.quantity)) * 100;

    // Update metrics
    if (trade.pnl > 0) {
      this.metrics.winningTrades++;
      this.metrics.totalProfit += trade.pnl;
    } else if (trade.pnl < 0) {
      this.metrics.losingTrades++;
      this.metrics.totalLoss += Math.abs(trade.pnl);
    }

    // Update portfolio
    this.portfolio.pnl += trade.pnl;
    this.portfolio.dailyPnL += trade.pnl;
    this.portfolio.capital += trade.pnl;

    this.portfolio.peakCapital = Math.max(this.portfolio.peakCapital, this.portfolio.capital);
    this.portfolio.lowestCapital = Math.min(this.portfolio.lowestCapital, this.portfolio.capital);

    return {
      success: true,
      trade,
      portfolioCapital: this.portfolio.capital,
      portfolioPnL: this.portfolio.pnl,
    };
  }

  /**
   * Update mark-to-market for open positions
   */
  updateMarketPrices(prices) {
    let mtmPnL = 0;

    for (const [ticker, price] of Object.entries(prices)) {
      const position = this.portfolio.positions.get(ticker);
      if (position) {
        position.currentPrice = price;
        const posPnL = (price - position.entryPrice) * position.quantity;
        mtmPnL += posPnL;
      }
    }

    return mtmPnL;
  }

  /**
   * Calculate performance metrics
   */
  getMetrics() {
    const winRate = this.metrics.totalTrades > 0
      ? (this.metrics.winningTrades / this.metrics.totalTrades) * 100
      : 0;

    const profitFactor = this.metrics.totalLoss > 0
      ? this.metrics.totalProfit / this.metrics.totalLoss
      : (this.metrics.totalProfit > 0 ? Infinity : 0);

    const expectationValue = this.metrics.totalTrades > 0
      ? (this.metrics.totalProfit - this.metrics.totalLoss) / this.metrics.totalTrades
      : 0;

    const maxDrawdown = this.calculateMaxDrawdown();
    const sharpeRatio = this.calculateSharpeRatio();

    return {
      portfolio: {
        initialCapital: this.config.initialCapital,
        currentCapital: this.portfolio.capital,
        totalPnL: this.portfolio.pnl,
        returnPercent: ((this.portfolio.pnl / this.config.initialCapital) * 100).toFixed(2),
        peakCapital: this.portfolio.peakCapital,
        lowestCapital: this.portfolio.lowestCapital,
      },
      trades: {
        total: this.metrics.totalTrades,
        winning: this.metrics.winningTrades,
        losing: this.metrics.losingTrades,
        winRate: winRate.toFixed(2),
      },
      performance: {
        totalProfit: this.metrics.totalProfit.toFixed(2),
        totalLoss: this.metrics.totalLoss.toFixed(2),
        profitFactor: profitFactor.toFixed(2),
        expectationValue: expectationValue.toFixed(2),
        maxDrawdown: (maxDrawdown * 100).toFixed(2),
        sharpeRatio: sharpeRatio.toFixed(2),
      },
    };
  }

  /**
   * Calculate maximum drawdown
   */
  calculateMaxDrawdown() {
    if (this.trades.length === 0) return 0;

    let maxDrawdown = 0;
    let peak = this.config.initialCapital;

    for (const trade of this.trades) {
      if (trade.status === "CLOSED" && trade.pnl) {
        const capital = this.config.initialCapital +
          this.trades.slice(0, this.trades.indexOf(trade) + 1)
            .filter(t => t.status === "CLOSED")
            .reduce((sum, t) => sum + (t.pnl || 0), 0);

        peak = Math.max(peak, capital);
        const drawdown = (peak - capital) / peak;
        maxDrawdown = Math.max(maxDrawdown, drawdown);
      }
    }

    return maxDrawdown;
  }

  /**
   * Calculate Sharpe ratio (simplified)
   */
  calculateSharpeRatio(riskFreeRate = 0.02) {
    if (this.trades.length === 0) return 0;

    const closedTrades = this.trades.filter(t => t.status === "CLOSED" && t.pnl !== null);
    if (closedTrades.length === 0) return 0;

    const returns = closedTrades.map(t => t.returnPercent / 100);
    const meanReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - meanReturn, 2), 0) / returns.length;
    const stdDev = Math.sqrt(variance);

    if (stdDev === 0) return 0;

    return (meanReturn - (riskFreeRate / 252)) / stdDev * Math.sqrt(252);
  }

  /**
   * Get trade history
   */
  getTradeHistory(limit = 100) {
    return this.trades
      .sort((a, b) => new Date(b.entryTime) - new Date(a.entryTime))
      .slice(0, limit);
  }

  /**
   * Reset for new session
   */
  reset() {
    this.trades = [];
    this.portfolio = {
      capital: this.config.initialCapital,
      positions: new Map(),
      pnl: 0,
      dailyPnL: 0,
      peakCapital: this.config.initialCapital,
      lowestCapital: this.config.initialCapital,
    };
    this.metrics = {
      totalTrades: 0,
      winningTrades: 0,
      losingTrades: 0,
      totalProfit: 0,
      totalLoss: 0,
    };

    console.log("[ShadowTrading] Reset complete");
  }

  /**
   * Report generation
   */
  generateReport() {
    return {
      timestamp: new Date().toISOString(),
      mode: this.mode,
      metrics: this.getMetrics(),
      trades: this.getTradeHistory(),
      summary: {
        message: "Shadow trading session report",
        note: "No real orders were executed",
      },
    };
  }
}

module.exports = ShadowTradingEngine;
