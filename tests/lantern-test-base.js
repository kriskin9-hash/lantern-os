const DEFAULT_BASE_URL = "http://127.0.0.1:4177";

function resolveBaseUrl() {
  if (process.env.LANTERN_GARAGE_TEST_BASE_URL) {
    return process.env.LANTERN_GARAGE_TEST_BASE_URL;
  }

  const port = process.env.LANTERN_GARAGE_TEST_PORT || process.env.LANTERN_GARAGE_PORT;
  if (port) {
    return `http://127.0.0.1:${port}`;
  }

  return DEFAULT_BASE_URL;
}

const baseUrl = resolveBaseUrl();
const parsed = new URL(baseUrl);

module.exports = {
  baseUrl,
  hostname: parsed.hostname,
  port: Number(parsed.port || (parsed.protocol === "https:" ? 443 : 80)),
};
