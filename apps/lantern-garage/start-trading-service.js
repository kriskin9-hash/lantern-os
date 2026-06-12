#!/usr/bin/env node
/**
 * Start Trading Microservice (Port 5050)
 * Runs alongside main Lantern Garage server
 * Usage: node start-trading-service.js
 */

const path = require('path');

// Start the trading service
const tradingService = require('./lib/trading-service.js');

console.log('Trading Microservice started as child process');
