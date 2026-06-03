with open('apps/lantern-garage/server.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix Anthropic streaming to check status code and fall through on error
old_anthropic = '''          const https = require("https");
          const req2 = https.request(opts, (upstream) => {
            let buf = "";
            upstream.on("data", (chunk) => {
              buf += chunk.toString();
              const lines = buf.split("\\n");
              buf = lines.pop(); // keep incomplete line
              for (const line of lines) {
                if (!line.startsWith("data:")) continue;
                const raw = line.slice(5).trim();
                if (raw === "[DONE]" || raw === "") continue;
                try {
                  const evt = JSON.parse(raw);
                  if (evt.type === "content_block_delta" && evt.delta?.text) {
                    fullReply += evt.delta.text;
                    sendToken(evt.delta.text);
                  }
                } catch { /* skip malformed */ }
              }
            });
            upstream.on("end", () => resolve());
            upstream.on("error", reject);
          });'''

new_anthropic = '''          const https = require("https");
          const req2 = https.request(opts, (upstream) => {
            if (upstream.statusCode !== 200) {
              upstream.resume();
              reject(new Error(`anthropic_status_${upstream.statusCode}`));
              return;
            }
            let buf = "";
            upstream.on("data", (chunk) => {
              buf += chunk.toString();
              const lines = buf.split("\\n");
              buf = lines.pop(); // keep incomplete line
              for (const line of lines) {
                if (!line.startsWith("data:")) continue;
                const raw = line.slice(5).trim();
                if (raw === "[DONE]" || raw === "") continue;
                try {
                  const evt = JSON.parse(raw);
                  if (evt.type === "content_block_delta" && evt.delta?.text) {
                    fullReply += evt.delta.text;
                    sendToken(evt.delta.text);
                  }
                } catch { /* skip malformed */ }
              }
            });
            upstream.on("end", () => resolve());
            upstream.on("error", reject);
          });'''

js = js.replace(old_anthropic, new_anthropic)

with open('apps/lantern-garage/server.js', 'w', encoding='utf-8') as f:
    f.write(js)

print('patched anthropic status check')
