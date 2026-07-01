### Kalshi terminal reskin — global chrome, two-button game, device polish, account HUD

The Kalshi swipe deck is restyled to match home + chat and read as a polished device:

- **Global header + footer.** Replaces the page's ad-hoc nav (which crammed status chips
  into the nav bar) with the shared `.site-nav` (unisona.ai brand + Chat/Trader/Kalshi/
  Create/Explore/Help links + profile/theme/screenshot actions) and the shared
  `.site-footer`. Drops the custom palette override so the page inherits the canonical
  `site.css` tokens and adapts correctly in **both light and dark** (theme via the shared
  bootstrap + `theme-toggle.js`).
- **Two-button game.** Minimized to the card + one prominent **Pass / Take** pair (the
  in-card duplicate buttons are hidden). Green Take uses dark-on-green text and the danger
  Pass uses an outline — both WCAG-AA at large/bold sizes — with visible focus rings and
  keyboard (←/→) support.
- **Polished device frame** (fallout-radio-inspired, theme-adaptive): the deck sits in a
  beveled "console" with corner-screw detail, the card area is a recessed "screen" with
  faint scanlines and a soft accent glow behind the live card, and the controls read as
  tactile transport. No green-CRT takeover — trading red/green semantics are preserved.
- **Account · profile · positions HUD.** A new panel below the deck, **collapsed by default
  to a slim bar** (user · balance · N positions · env · council verdict) and expanding to
  four sections: Profile (name/tier + link), Kalshi account (balance/env/connection +
  kill-switch reason), Positions held (live `/positions`), and the Σ₀ Council (graded,
  win-rate, net-after-fee, verdict). The old busy status chips + image gallery are removed.
- **A11y:** `kalshi-terminal.html` is added to `scripts/test-a11y.js` and passes (27
  checks, 0 issues) — semantic landmarks, labelled controls, skip link, `aria-current`.
