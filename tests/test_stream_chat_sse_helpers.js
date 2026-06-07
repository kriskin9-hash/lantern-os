const assert = require("assert");
const { writeStreamHeaders, writeData, sendToken, sendError, sendDone } = require("../apps/lantern-garage/lib/stream-chat/sse");

function fakeRes() {
  return {
    status: null,
    headers: null,
    chunks: [],
    ended: false,
    writeHead(status, headers) {
      this.status = status;
      this.headers = headers;
    },
    write(chunk) {
      this.chunks.push(String(chunk));
    },
    end() {
      this.ended = true;
    },
  };
}

function parseChunk(chunk) {
  assert.ok(chunk.startsWith("data: "), "chunk should be an SSE data line");
  return JSON.parse(chunk.slice(6).trim());
}

const res = fakeRes();
writeStreamHeaders(res);
assert.strictEqual(res.status, 200);
assert.strictEqual(res.headers["Content-Type"], "text/event-stream; charset=utf-8");
assert.strictEqual(res.headers["Cache-Control"], "no-cache");

writeData(res, { type: "custom", ok: true });
assert.deepStrictEqual(parseChunk(res.chunks[0]), { type: "custom", ok: true });

sendToken(res, "hello");
assert.deepStrictEqual(parseChunk(res.chunks[1]), { type: "token", text: "hello" });

sendError(res, "bad");
assert.deepStrictEqual(parseChunk(res.chunks[2]), { type: "error", text: "bad" });

sendDone(res, "unit", { online: false });
assert.deepStrictEqual(parseChunk(res.chunks[3]), { type: "done", source: "unit", online: false });
assert.strictEqual(res.ended, true);

console.log("stream-chat sse helper tests passed");
