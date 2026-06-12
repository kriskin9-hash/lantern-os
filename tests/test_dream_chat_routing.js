/**
 * Dream Chat Routing Tests
 * Verify intent classification and agent routing
 */

const assert = require("assert");
const { classifyIntent, CAPABILITY_REGISTRY, getAgent } = require("../apps/lantern-garage/lib/intent-router");

describe("Intent Router", () => {
  describe("classifyIntent()", () => {
    it("should route 'make changes' to code/keystone", () => {
      const route = classifyIntent("make changes to the repo");
      assert.strictEqual(route.intent, "code");
      assert.strictEqual(route.agent, "keystone");
      assert.strictEqual(route.surface, "convergence");
      assert.strictEqual(route.requires_convergence, true);
    });

    it("should route 'code review' to code/keystone", () => {
      const route = classifyIntent("code review: check the PR for bugs");
      assert.strictEqual(route.intent, "code");
      assert.strictEqual(route.agent, "keystone");
    });

    it("should route 'implement' to code/keystone", () => {
      const route = classifyIntent("implement the trading agent");
      assert.strictEqual(route.intent, "code");
      assert.strictEqual(route.agent, "keystone");
    });

    it("should route 'play three doors' to rp_game", () => {
      const route = classifyIntent("let's play three doors");
      assert.strictEqual(route.intent, "rp_game");
      assert.strictEqual(route.agent, "three-doors");
      assert.strictEqual(route.surface, "three_doors");
      assert.strictEqual(route.requires_convergence, false);
    });

    it("should route 'three doors' to rp_game", () => {
      const route = classifyIntent("start three doors game");
      assert.strictEqual(route.intent, "rp_game");
      assert.strictEqual(route.agent, "three-doors");
    });

    it("should route 'export dreams' to memory_export", () => {
      const route = classifyIntent("export dreams to archive");
      assert.strictEqual(route.intent, "memory_export");
      assert.strictEqual(route.agent, "csf");
      assert.strictEqual(route.requires_convergence, true);
    });

    it("should route 'what do dreams mean' to dream_analysis", () => {
      const route = classifyIntent("what do my dreams mean?");
      assert.strictEqual(route.intent, "dream_analysis");
      assert.strictEqual(route.agent, "lantern");
      assert.strictEqual(route.surface, "dream_chat");
      assert.strictEqual(route.requires_convergence, false);
    });

    it("should route 'help me think' to strategy/founder", () => {
      const route = classifyIntent("help me think through this strategy");
      assert.strictEqual(route.intent, "strategy");
      assert.strictEqual(route.agent, "founder");
      assert.strictEqual(route.requires_convergence, true);
    });

    it("should route 'trading signals' to trading", () => {
      const route = classifyIntent("check my trading signals");
      assert.strictEqual(route.intent, "trading");
      assert.strictEqual(route.agent, "trading");
      assert.strictEqual(route.requires_convergence, true);
    });

    it("should default unknown to lantern/dream_chat", () => {
      const route = classifyIntent("hey, what's up?");
      assert.strictEqual(route.intent, "unknown");
      assert.strictEqual(route.agent, "lantern");
      assert.strictEqual(route.surface, "dream_chat");
      assert.strictEqual(route.requires_convergence, false);
    });

    it("should be case-insensitive", () => {
      const route1 = classifyIntent("MAKE CHANGES");
      const route2 = classifyIntent("Make Changes");
      assert.strictEqual(route1.agent, "keystone");
      assert.strictEqual(route2.agent, "keystone");
    });

    it("should match trigger anywhere in message", () => {
      const route = classifyIntent(
        "I want to integrate this feature into the repo"
      );
      assert.strictEqual(route.agent, "keystone");
    });
  });

  describe("CAPABILITY_REGISTRY", () => {
    it("should have all required agents", () => {
      const agentIds = CAPABILITY_REGISTRY.map((a) => a.id);
      assert(agentIds.includes("keystone"));
      assert(agentIds.includes("three-doors"));
      assert(agentIds.includes("founder"));
      assert(agentIds.includes("lantern"));
      assert(agentIds.includes("csf"));
      assert(agentIds.includes("trading"));
    });

    it("should have intents and triggers for each agent", () => {
      for (const agent of CAPABILITY_REGISTRY) {
        assert(Array.isArray(agent.intents));
        assert(agent.intents.length > 0);
        assert(Array.isArray(agent.triggers));
        assert(agent.triggers.length > 0);
      }
    });

    it("should mark convergence agents correctly", () => {
      const keystoneAgent = CAPABILITY_REGISTRY.find(
        (a) => a.id === "keystone"
      );
      const threeDoorsAgent = CAPABILITY_REGISTRY.find(
        (a) => a.id === "three-doors"
      );
      assert.strictEqual(keystoneAgent.canConverge, true);
      assert.strictEqual(threeDoorsAgent.canConverge, false);
    });
  });

  describe("getAgent()", () => {
    it("should return agent by id", () => {
      const agent = getAgent("keystone");
      assert.strictEqual(agent.id, "keystone");
      assert.strictEqual(agent.name, "Keystone (Code Coordinator)");
    });

    it("should return null for unknown agent", () => {
      const agent = getAgent("unknown-agent");
      assert.strictEqual(agent, null);
    });
  });
});
