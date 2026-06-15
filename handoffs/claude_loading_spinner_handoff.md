# Claude Code One-Click Handoff — Loading Spinner + Dashboard UX Refactor

## Objective
Refactor the Trader Dashboard loading experience into a reusable, component-based system so all future dashboards use a consistent loading state instead of ad-hoc DOM spinners.

---

## Current State
- Loading spinner exists inline in `stock-trader.html`
- Uses `#cardsGrid` replacement trick on first render
- Uses Lantern OS mandala SVG animation
- Works, but is not reusable or scalable

---

## Problem
Current implementation is:
- Hardcoded into a single file
- Not reusable across other dashboards (kalshi, news, etc.)
- Tightly coupled to grid rendering lifecycle

---

## Target Architecture
Create a reusable loading system:

### 1. Loading Overlay Component
Create a reusable overlay:

```html
<div id="loadingOverlay" class="loading-overlay hidden">
  <img src="/mandala.svg" class="loading-spinner" />
  <div class="loading-text">LOADING MARKET DATA…</div>
</div>
```

### 2. Global Utility
Add to a shared JS file (or top-level dashboard script):

```js
export function showLoading(targetId = "cardsGrid") {
  document.getElementById("loadingOverlay").classList.remove("hidden");
  document.getElementById(targetId).style.opacity = "0.4";
}

export function hideLoading(targetId = "cardsGrid") {
  document.getElementById("loadingOverlay").classList.add("hidden");
  document.getElementById(targetId).style.opacity = "1";
}
```

---

## 3. CSS Standardization

```css
.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10,10,15,0.6);
  backdrop-filter: blur(6px);
  z-index: 999;
}

.loading-spinner {
  width: 80px;
  height: 80px;
  animation: spin 1.8s linear infinite;
}

.loading-text {
  margin-top: 12px;
  font-size: 12px;
  letter-spacing: 2px;
  color: #9aa4b2;
}

.hidden {
  display: none;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

---

## 4. Integration Changes

### Replace current stock-trader behavior:

**REMOVE:**
- grid innerHTML loading placeholder logic

**REPLACE WITH:**

```js
showLoading();

await fullRefresh();
await renderCards();

hideLoading();
```

---

## 5. Extension Requirement
Apply same system to:
- `/kalshi-terminal.html`
- `/news.html`
- Any future dashboard modules

---

## 6. Acceptance Criteria
- No dashboard should appear “frozen” on load
- Spinner must appear instantly on page entry
- Spinner must be reusable across all dashboards
- No inline grid replacement hacks remain

---

## Notes
This is a UX infrastructure upgrade, not just a UI tweak. It standardizes loading behavior across Lantern OS dashboards and prevents future fragmentation between trading modules.
