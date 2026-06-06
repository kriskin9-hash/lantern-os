/**
 * UpdateChecker — polls local version vs GitHub master and shows update banner.
 * Works on both local dev server and GitHub Pages static deploys.
 */
(function () {
  const POLL_INTERVAL_MS = 60_000;
  const GITHUB_API = "https://api.github.com/repos/alex-place/lantern-os/commits/master";
  const LOCAL_API = (typeof serverBase !== "undefined" ? serverBase : "") + "/api/version";

  let localCommit = null;
  let remoteCommit = null;
  let dismissed = sessionStorage.getItem("lantern_update_dismissed");

  function createBanner() {
    if (document.getElementById("lantern-update-banner")) return;

    const banner = document.createElement("div");
    banner.id = "lantern-update-banner";
    banner.innerHTML = `
      <span class="lantern-update-text">Lantern OS update available on <code>master</code></span>
      <button class="lantern-update-btn" id="lantern-update-action" title="Update now">Update & Restart</button>
      <button class="lantern-update-dismiss" id="lantern-update-dismiss" title="Dismiss">&times;</button>
    `;
    document.body.prepend(banner);

    document.getElementById("lantern-update-action").addEventListener("click", async () => {
      const btn = document.getElementById("lantern-update-action");
      btn.disabled = true;
      btn.textContent = "Updating...";

      if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
        // Local dev — auto-update via POST to action endpoint
        try {
          const r = await fetch("/api/actions/update", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
          });
          const d = await r.json();
          if (d.ok && d.restart_scheduled) {
            banner.querySelector(".lantern-update-text").innerHTML =
              `<span style="color:#4caf82">Updated to <code>${d.version.tag}</code>. Restarting server...</span>`;
            btn.style.display = "none";
            document.getElementById("lantern-update-dismiss").style.display = "none";
            // Server will restart; wait 4s then reload
            setTimeout(() => window.location.reload(true), 4000);
          } else {
            const failed = d.steps.filter(s => !s.ok).map(s => s.step).join(", ");
            banner.querySelector(".lantern-update-text").innerHTML =
              `<span style="color:#ff6b6b">Update failed: ${failed}</span>`;
            btn.textContent = "Retry";
            btn.disabled = false;
          }
        } catch (e) {
          banner.querySelector(".lantern-update-text").innerHTML =
            `<span style="color:#ff6b6b">Network error: ${e.message}</span>`;
          btn.textContent = "Retry";
          btn.disabled = false;
        }
      } else {
        // GitHub Pages — hard refresh
        window.location.reload(true);
      }
    });

    document.getElementById("lantern-update-dismiss").addEventListener("click", () => {
      banner.remove();
      sessionStorage.setItem("lantern_update_dismissed", remoteCommit || "true");
    });
  }

  function removeBanner() {
    const banner = document.getElementById("lantern-update-banner");
    if (banner) banner.remove();
  }

  async function fetchLocalVersion() {
    try {
      const r = await fetch(LOCAL_API, { signal: AbortSignal.timeout(5000) });
      if (!r.ok) return null;
      const d = await r.json();
      return d.version?.commit || null;
    } catch {
      return null;
    }
  }

  async function fetchRemoteVersion() {
    try {
      const r = await fetch(GITHUB_API, { signal: AbortSignal.timeout(8000) });
      if (!r.ok) return null;
      const d = await r.json();
      return d.sha || null;
    } catch {
      return null;
    }
  }

  async function check() {
    [localCommit, remoteCommit] = await Promise.all([
      fetchLocalVersion(),
      fetchRemoteVersion()
    ]);

    if (!localCommit || !remoteCommit) {
      removeBanner();
      return;
    }

    if (localCommit === remoteCommit) {
      removeBanner();
      return;
    }

    if (dismissed === remoteCommit) {
      return;
    }

    createBanner();
  }

  // Inject styles once
  if (!document.getElementById("lantern-update-styles")) {
    const style = document.createElement("style");
    style.id = "lantern-update-styles";
    style.textContent = `
      #lantern-update-banner {
        position: fixed;
        top: 0; left: 0; right: 0;
        z-index: 99999;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 12px;
        padding: 10px 16px;
        background: linear-gradient(90deg, #1a1d2a, #2e2860 60%, #1a1d2a);
        border-bottom: 1px solid #7c6af7;
        color: #e8eaf6;
        font-family: "Segoe UI", system-ui, sans-serif;
        font-size: 0.9rem;
        box-shadow: 0 4px 24px rgba(0,0,0,0.4);
        animation: lanternBannerSlide 0.35s ease-out;
      }
      @keyframes lanternBannerSlide {
        from { transform: translateY(-100%); }
        to   { transform: translateY(0); }
      }
      #lantern-update-banner .lantern-update-text code {
        background: rgba(124,106,247,0.18);
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
        color: #f4c76b;
      }
      #lantern-update-banner .lantern-update-btn {
        background: #7c6af7;
        color: #fff;
        border: none;
        border-radius: 6px;
        padding: 6px 14px;
        font-size: 0.82rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.2s;
      }
      #lantern-update-banner .lantern-update-btn:hover {
        background: #9b8df9;
      }
      #lantern-update-banner .lantern-update-dismiss {
        background: transparent;
        color: #7880a4;
        border: none;
        font-size: 1.3rem;
        line-height: 1;
        cursor: pointer;
        margin-left: 4px;
        padding: 0 4px;
      }
      #lantern-update-banner .lantern-update-dismiss:hover {
        color: #e8eaf6;
      }
      /* Push page content down when banner is present */
      body:has(#lantern-update-banner) {
        padding-top: 44px;
      }
    `;
    document.head.appendChild(style);
  }

  // Initial check + periodic poll
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", check);
  } else {
    check();
  }
  setInterval(check, POLL_INTERVAL_MS);
})();
