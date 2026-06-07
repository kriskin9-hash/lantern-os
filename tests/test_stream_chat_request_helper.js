const assert = require("assert");
const { sanitizeHistory, parseStreamChatRequest } = require("../apps/lantern-garage/lib/stream-chat/request");

const history = sanitizeHistory([
  { role: "system", text: "ignored role becomes user" },
  { role: "assistant", text: "a".repeat(1200) },
  { role: "user", text: "hello" },
  { role: "assistant", text: "there" },
  { role: "user", text: "again" },
  { role: "assistant", text: "ok" },
  { role: "user", text: "tail" },
]);

assert.strictEqual(history.length, 6);
assert.strictEqual(history[0].role, "assistant");
assert.strictEqual(history[0].text.length, 1000);
assert.strictEqual(history[5].text, "tail");
assert.deepStrictEqual(sanitizeHistory(null), []);
assert.deepStrictEqual(sanitizeHistory([{ role: "user" }]), []);

(async () => {
  const getUrl = new URL("http://local/api/dream/chat/stream?message=%20hello%20&user=Alex&agent=keystone&provider=OpenAI");
  const parsedGet = await parseStreamChatRequest({ method: "GET" }, getUrl, {
    normalizeDreamerUser: (value) => String(value).toLowerCase(),
  });
  assert.deepStrictEqual(parsedGet, {
    message: "hello",
    user: "alex",
    requestedAgent: "keystone",
    requestedProvider: "openai",
    history: [],
    mcpFlag: false,
  });

  const postUrl = new URL("http://local/api/dream/chat/stream");
  const parsedPost = await parseStreamChatRequest({ method: "POST" }, postUrl, {
    normalizeDreamerUser: (value) => `u:${value}`,
    collectRequestBody: async () => JSON.stringify({
      message: "  hi  ",
      user: "dreamer-one",
      agent: "lantern",
      provider: "Gemini",
      mcp: true,
      history: [{ role: "assistant", text: "previous" }],
    }),
  });
  assert.strictEqual(parsedPost.message, "hi");
  assert.strictEqual(parsedPost.user, "u:dreamer-one");
  assert.strictEqual(parsedPost.requestedAgent, "lantern");
  assert.strictEqual(parsedPost.requestedProvider, "gemini");
  assert.strictEqual(parsedPost.mcpFlag, true);
  assert.deepStrictEqual(parsedPost.history, [{ role: "assistant", text: "previous" }]);

  const malformed = await parseStreamChatRequest({ method: "POST" }, postUrl, {
    collectRequestBody: async () => "not-json",
  });
  assert.strictEqual(malformed.message, "");
  assert.strictEqual(malformed.user, "dreamer");
  assert.deepStrictEqual(malformed.history, []);

  console.log("stream-chat request helper tests passed");
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
