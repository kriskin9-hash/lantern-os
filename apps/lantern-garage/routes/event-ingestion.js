/**
 * Event Ingestion API — PRL-1.1 Cloud Topology Fix
 *
 * Formal boundary between stateless AI trader and Lantern OS.
 * Python writes here (HTTP), Node owns the queue.
 *
 * This removes filesystem coupling and enables cloud deployment.
 */

"use strict";

async function eventIngestionRoutes(req, res, url, deps) {
  const { sendJson, collectRequestBody } = deps;
  const queue = deps.persistentEventQueue;
  const tracer = deps.systemAuditTracer;

  // POST /api/events/ingest — AI trader submits decisions
  if (url.pathname === "/api/events/ingest" && req.method === "POST") {
    try {
      const body = await collectRequestBody(req);
      const payload = body ? JSON.parse(body) : {};

      // Validate required fields
      const { ticker, action, confidence, source, timestamp } = payload;

      if (!ticker || !action) {
        sendJson(res, {
          status: "rejected",
          reason: "Missing required fields: ticker, action"
        }, 400);
        return true;
      }

      if (!source) {
        sendJson(res, {
          status: "rejected",
          reason: "Missing required field: source"
        }, 400);
        return true;
      }

      // Validate action
      if (!["BUY", "SELL", "NO_TRADE", "EXIT"].includes(action.toUpperCase())) {
        sendJson(res, {
          status: "rejected",
          reason: `Invalid action: ${action}`
        }, 400);
        return true;
      }

      // Validate confidence
      if (confidence !== undefined) {
        const conf = parseFloat(confidence);
        if (isNaN(conf) || conf < 0 || conf > 1) {
          sendJson(res, {
            status: "rejected",
            reason: "Confidence must be between 0 and 1"
          }, 400);
          return true;
        }
      }

      // Create trace ID for this decision
      const traceId = `trace-ingest-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

      // Enqueue the event
      // CRITICAL: Queue is Node-owned, Python has NO filesystem access
      const eventId = queue.enqueueEvent(traceId, source, {
        ticker: ticker.toUpperCase(),
        action: action.toUpperCase(),
        confidence: parseFloat(confidence) || 0.5,
        timestamp: timestamp || Date.now(),
        receivedAt: Date.now()
      });

      // Log ingestion event
      if (tracer) {
        tracer.recordEvent(
          "AI_DECISION_INGESTED",
          source,
          {
            ticker,
            action,
            confidence,
            eventId,
            traceId
          },
          null,
          traceId
        );
      }

      console.log(`[Ingestion] Accepted from ${source}: ${ticker} ${action} (confidence: ${confidence || 0.5})`);

      // Return success
      sendJson(res, {
        status: "accepted",
        eventId,
        traceId,
        message: `Decision enqueued: ${ticker} ${action}`
      }, 201);

      return true;

    } catch (e) {
      console.error("[Ingestion] Error:", e.message);
      sendJson(res, {
        status: "error",
        reason: "Failed to ingest event",
        details: e.message
      }, 500);
      return true;
    }
  }

  // GET /api/system/topology — Show deployment topology
  if (url.pathname === "/api/system/topology" && req.method === "GET") {
    const queue = deps.persistentEventQueue;
    const watchdog = deps.traderWatchdog;

    const topology = {
      deploymentMode: process.env.DEPLOYMENT_MODE || "cloud",
      services: {
        aiTrader: {
          type: "remote-stateless",
          role: "signal-generation",
          connectionMethod: "HTTP-ingestion",
          filesystemAccess: false
        },
        lanternOS: {
          type: "local-node",
          role: "execution-and-state",
          queueOwnership: true,
          filesystemAccess: true
        }
      },
      queue: {
        owner: "lantern-os-node",
        mode: "persistent-local",
        path: queue ? queue.queuePath : "N/A",
        pending: queue ? queue.getPendingEvents().length : 0
      },
      aiTraderStatus: watchdog ? {
        alive: watchdog.alive,
        restarts: watchdog.restartCount,
        lastHeartbeat: new Date(watchdog.lastHeartbeat).toISOString()
      } : null,
      architecture: {
        python: "stateless-signal-service",
        node: "stateful-execution-system",
        coupling: "http-only-no-filesystem"
      },
      constraints: {
        pythonAccess: {
          filesystem: false,
          queue: false,
          ingestionAPI: true
        },
        nodeOwned: {
          queue: true,
          stateEngine: true,
          auditLog: true
        }
      }
    };

    sendJson(res, topology, 200);
    return true;
  }

  // GET /api/events/status — Ingestion system status
  if (url.pathname === "/api/events/status" && req.method === "GET") {
    const queue = deps.persistentEventQueue;
    const consumer = deps.eventQueueConsumer;

    const status = {
      ingestionAPI: "healthy",
      queue: queue ? queue.getStats() : null,
      consumer: consumer ? consumer.getStatus() : null,
      timestamp: new Date().toISOString()
    };

    sendJson(res, status, 200);
    return true;
  }

  return false;
}

module.exports = eventIngestionRoutes;
