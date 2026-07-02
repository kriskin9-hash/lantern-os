// Dev entry shim — hooks server.js startup to FORCE the dev port (4178).
//
// server.js resolves its port as: LANTERN_GARAGE_PORT || PORT || 4177, and
// binds 0.0.0.0 whenever PORT is set. Some launchers (the preview tool,
// Railway, npm) inject their own PORT, which would otherwise drag the dev
// server onto the wrong port/host. We neutralize PORT here so dev always
// binds dev — deterministically, no matter who launches it.
const DEV_PORT = process.env.LANTERN_DEV_PORT || '4178';

delete process.env.PORT;                       // strip any launcher-injected PORT
process.env.LANTERN_GARAGE_PORT = DEV_PORT;    // force the dev port
process.env.LANTERN_GARAGE_HOST = '127.0.0.1'; // dev stays local-only

// Dev must NOT run the real-money AI trader — only stable (:4177) owns it. Both
// boots spawning start-ai-trader.js put two trading loops on the same Alpaca
// account, which place opposing orders and churn it to death on fees/slippage
// (observed 2026-07-02). Default dev to trading-disabled; opt back in explicitly
// with LANTERN_DISABLE_TRADING=0 (e.g. against a paper account).
if (process.env.LANTERN_DISABLE_TRADING === undefined) {
  process.env.LANTERN_DISABLE_TRADING = '1';
}

require(__dirname + '/server.js');
