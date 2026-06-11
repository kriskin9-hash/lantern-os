// Stub: Web search client
// Enables dream-chat to load without MCP server

function webSearchMcp(query) {
  return Promise.resolve([]);
}

function formatGroundingContext(results) {
  return "";
}

function needsGrounding(message) {
  return false;
}

function extractSearchQuery(message) {
  return null;
}

module.exports = {
  webSearchMcp,
  formatGroundingContext,
  needsGrounding,
  extractSearchQuery,
};
