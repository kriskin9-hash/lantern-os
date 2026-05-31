"use strict";

const $ = (id) => document.getElementById(id);
const transcript = $("transcript");

function bubble(text, cls) {
  const el = document.createElement("div");
  el.className = "bubble " + (cls || "bot");
  el.textContent = text;
  transcript.appendChild(el);
  transcript.scrollTop = transcript.scrollHeight;
  return el;
}

function setStat(id, text, state) {
  const el = $(id);
  el.textContent = text;
  el.className = "v" + (state ? " " + state : "");
}

async function getJSON(url, opts) {
  const resp = await fetch(url, opts);
  if (!resp.ok) {
    let detail = resp.statusText;
    try { detail = (await resp.json()).detail || detail; } catch (_) {}
    throw new Error(detail);
  }
  return resp.json();
}

async function refreshHealth() {
  try {
    const h = await getJSON("/api/health");
    setStat("envVal", h.environment, h.environment === "prod" ? "held" : "ok");
    setStat("liveVal", h.liveEnabled ? "ARMED" : "disabled", h.liveEnabled ? "held" : "ok");
    setStat("killVal", h.killSwitchActive ? "ACTIVE" : "clear", h.killSwitchActive ? "off" : "ok");
  } catch (_) {}
}

async function refreshSession() {
  const me = await getJSON("/api/me");
  const session = $("session");
  if (me.authenticated) {
    session.innerHTML =
      `<span class="who">@${me.user.login}</span> <a class="btn" href="/logout">Sign out</a>`;
    await refreshBalance();
    return true;
  }
  session.innerHTML = `<a class="btn" id="loginBtn" href="/login">Sign in with GitHub</a>`;
  return false;
}

async function refreshBalance() {
  try {
    const b = await getJSON("/api/balance");
    setStat("balVal", `$${b.balanceUsd.toFixed(2)}`, "ok");
    setStat("todayVal", `${b.tradesToday}/${b.caps.maxTradesPerDay} · $${b.riskTodayUsd.toFixed(2)}`);
  } catch (e) {
    setStat("balVal", "n/a");
    setStat("todayVal", "—");
  }
}

function renderOrder(data) {
  const cls = data.blockers && data.blockers.length ? "blocked" : "bot";
  const el = bubble(data.reply, cls);
  if (data.intent === "order" && (!data.blockers || !data.blockers.length)) {
    const btn = document.createElement("button");
    btn.className = "btn primary confirm";
    btn.textContent = data.live ? "Confirm LIVE order (real money)" : "Submit dry-run";
    btn.onclick = () => submitOrder(data.plan, data.live, btn);
    el.appendChild(document.createElement("br"));
    el.appendChild(btn);
  }
}

async function submitOrder(plan, live, btn) {
  btn.disabled = true;
  btn.textContent = live ? "Submitting live…" : "Submitting dry-run…";
  try {
    const res = await getJSON("/api/order", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...plan, live }),
    });
    if (res.status === "submitted") {
      bubble(`LIVE order submitted ($${res.plan_cost_usd.toFixed(2)}).`, "bot");
      await refreshBalance();
    } else if (res.status === "dry_run") {
      bubble(`Dry-run recorded ($${res.plan_cost_usd.toFixed(2)}). No real order placed.`, "bot");
    } else if (res.status === "blocked") {
      bubble("BLOCKED: " + res.blockers.join("; "), "blocked");
    }
  } catch (e) {
    bubble("Error: " + e.message, "error");
  }
}

async function send(message) {
  bubble(message, "user");
  try {
    const data = await getJSON("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    if (data.intent === "order") renderOrder(data);
    else bubble(data.reply, "bot");
    if (data.intent === "balance") await refreshBalance();
  } catch (e) {
    if (String(e.message).toLowerCase().includes("login")) {
      bubble("Please sign in with GitHub first.", "blocked");
    } else {
      bubble("Error: " + e.message, "error");
    }
  }
}

$("composer").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const input = $("msg");
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  send(text);
});

(async function init() {
  await refreshHealth();
  const authed = await refreshSession();
  bubble(
    authed
      ? "Signed in. Type 'help' for commands, or e.g. 'buy 1 yes on TICKER at 40c'."
      : "Welcome to Lantern Trade Chat. Sign in with GitHub to trade. Type 'help' to see commands.",
    "bot"
  );
})();
