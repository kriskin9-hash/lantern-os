// Kingdome of Hearts game integration for Dream Chat
// Detects !threedoors, !three-doors, !kingdome, "play three doors", "door game" etc.
// Calls the shared Python engine via POST /api/dream/doors

const THREE_DOORS_TRIGGERS = [
  "!threedoors", "!three-doors", "!three doors",
  "!kingdome", "!kingdome-of-hearts", "!kingdome of hearts",
  "play three doors", "start three doors", "three doors game",
  "door game", "!doors", "!door game",
  "play kingdome", "start kingdome", "kingdome game",
];

function isThreeDoorsTrigger(text) {
  const lower = text.toLowerCase().trim();
  return THREE_DOORS_TRIGGERS.some(t => lower.includes(t));
}

function isDoorChoice(text) {
  const lower = text.toLowerCase().trim();
  // Matches "door A", "choose B", "pick the burrow door", "A", "B", "C"
  if (/^[abc]$/.test(lower)) return lower;
  const m = lower.match(/(?:door|choose|pick)\s+([abc])/);
  if (m) return m[1];
  const nameMatch = lower.match(/(?:the\s+)?(burrow|sunken bell|little crown|root|ember|stream|deep|echo|surface|throne|hollow|star|storybook|cloverfield|fog|lucky|today|tomorrow)\s+door/);
  if (nameMatch) return nameMatch[1];
  return null;
}

async function handleThreeDoorsChat(message, userId = "web-anon") {
  const choice = isDoorChoice(message);
  if (choice) {
    // Player is choosing a door
    return await callDoorsApi({ userId, action: "choose", choice });
  }
  // Start or resume game
  return await callDoorsApi({ userId, action: "start" });
}

async function callDoorsApi(body) {
  try {
    const serverBase = window?.serverBase || "";
    const r = await fetch(`${serverBase}/api/dream/doors`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await r.json();
  } catch (e) {
    return { error: e.message };
  }
}

function formatThreeDoorsResponse(data) {
  if (data.error) return { type: "text", content: `Kingdome of Hearts error: ${data.error}` };

  const lines = [data.text];
  lines.push("");
  if (data.fox_present) lines.push("🦊 The fox is with you.");
  lines.push("");
  lines.push("**Choose a door:**");
  for (const d of data.doors) {
    lines.push(`**${d.label}.** ${d.name} — ${d.description}`);
  }

  const content = lines.join("\n");

  // If image generation is available, include prompts
  const imagePrompts = data.image_available ? [{ prompt: data.image_prompt, label: "scene" }] : [];

<<<<<<< HEAD
  // Breadcrumb/stage tracking
  const breadcrumbs = [];
  if (data.loop && data.stage !== undefined) {
    breadcrumbs.push(`Loop ${data.loop}`);
    breadcrumbs.push(`Stage ${data.stage + 1}/7`);
    if (data.stage_name) breadcrumbs.push(data.stage_name);
  }

=======
>>>>>>> pr-340
  return {
    type: "doors",
    content,
    doors: data.doors,
    scene_key: data.scene_key,
    imagePrompts,
<<<<<<< HEAD
    breadcrumbs,
    loop: data.loop,
    stage: data.stage,
    stage_name: data.stage_name,
=======
>>>>>>> pr-340
    raw: data,
  };
}

// Server-side version (for Node.js route usage)
function handleThreeDoorsServer(message, userId = "web-anon") {
  // Returns a plain object that dream-chat.js can consume
  if (isThreeDoorsTrigger(message)) {
    return { type: "three_doors", userId, message };
  }
  return null;
}

module.exports = {
  isThreeDoorsTrigger,
  isDoorChoice,
  handleThreeDoorsChat,
  callDoorsApi,
  formatThreeDoorsResponse,
  handleThreeDoorsServer,
  THREE_DOORS_TRIGGERS,
};
