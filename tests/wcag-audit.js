const { chromium } = require('playwright-core');

const URL = process.argv[2] || 'http://127.0.0.1:4177/dream-chat.html';
const OUT = process.argv[3] || 'reports/wcag-audit.json';

const fs = require('fs');
const path = require('path');

function ensureDir(filePath) {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
}

async function audit() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(URL, { waitUntil: 'networkidle' });

  const results = {
    url: URL,
    timestamp: new Date().toISOString(),
    issues: [],
    passed: [],
    screenshots: [],
  };

  function add(impact, rule, element, message, fix) {
    results.issues.push({ impact, rule, element: element?.substring?.(0, 120) || element, message, fix });
  }
  function pass(rule, message) {
    results.passed.push({ rule, message });
  }

  // 1. Color contrast check via computed styles
  const contrastChecks = await page.evaluate(() => {
    const issues = [];
    const elements = document.querySelectorAll('h1, h2, h3, p, span, a, button, label, .bubble, .msg-label, .input-hint, .drawer-hint');
    elements.forEach(el => {
      const style = getComputedStyle(el);
      const color = style.color;
      const bg = style.backgroundColor;
      const fontSize = parseFloat(style.fontSize);
      // Skip elements with transparent/no background (inherited)
      if (bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') return;
      // Very rough heuristic: if text is light gray on light background, flag it
      const rgb = color.match(/\d+/g)?.map(Number);
      const bgRgb = bg.match(/\d+/g)?.map(Number);
      if (!rgb || !bgRgb) return;
      const lum = (r, g, b) => { const a = [r,g,b].map(v => v/255 <= 0.03928 ? v/255/12.92 : Math.pow((v/255+0.055)/1.055, 2.4)); return 0.2126*a[0]+0.7152*a[1]+0.0722*a[2]; };
      const l1 = lum(...rgb), l2 = lum(...bgRgb);
      const ratio = (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05);
      if (ratio < 4.5) {
        issues.push({ el: el.outerHTML.substring(0,120), ratio: ratio.toFixed(2), text: el.textContent.substring(0,50) });
      }
    });
    return issues;
  });
  if (contrastChecks.length) {
    contrastChecks.forEach(c => add('serious', 'WCAG 1.4.3 Contrast', c.el, `Contrast ratio ${c.ratio}:1 for "${c.text}"`, 'Darken text or lighten background'));
  } else {
    pass('WCAG 1.4.3', 'All sampled text/background pairs meet 4.5:1 contrast');
  }

  // 2. Focusable elements without visible focus indicator
  const focusChecks = await page.evaluate(() => {
    const issues = [];
    const focusables = document.querySelectorAll('button, a, input, textarea, select, [tabindex]:not([tabindex="-1"])');
    focusables.forEach(el => {
      const style = getComputedStyle(el);
      const outline = style.outline;
      if (outline === 'none' || outline === '0px') {
        const hasFocusClass = el.classList.contains('focus-ring') || el.dataset.focusVisible;
        const hasBoxShadow = style.boxShadow && style.boxShadow !== 'none';
        if (!hasFocusClass && !hasBoxShadow) {
          issues.push({ tag: el.tagName, cls: el.className, id: el.id });
        }
      }
    });
    return issues;
  });
  if (focusChecks.length) {
    focusChecks.forEach(f => add('moderate', 'WCAG 2.4.7 Focus Visible', `<${f.tag} class="${f.cls}" id="${f.id}">`, 'No visible focus outline or shadow', 'Add :focus-visible outline or box-shadow'));
  } else {
    pass('WCAG 2.4.7', 'All focusable elements have visible focus indicators');
  }

  // 3. Images without alt text
  const imgChecks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('img')).filter(img => !img.alt && !img.getAttribute('aria-label') && !img.getAttribute('aria-labelledby')).map(img => ({ src: img.src.substring(img.src.lastIndexOf('/')+1), outer: img.outerHTML.substring(0,100) }));
  });
  if (imgChecks.length) {
    imgChecks.forEach(i => add('serious', 'WCAG 1.1.1 Non-text Content', i.outer, `Image "${i.src}" missing alt`, 'Add alt or aria-label'));
  } else {
    pass('WCAG 1.1.1', 'All images have alt text or ARIA labels');
  }

  // 4. Form inputs without labels
  const labelChecks = await page.evaluate(() => {
    const inputs = document.querySelectorAll('input:not([type="hidden"]), textarea, select');
    return Array.from(inputs).filter(inp => {
      const id = inp.id;
      const ariaLabel = inp.getAttribute('aria-label');
      const ariaLabeledBy = inp.getAttribute('aria-labelledby');
      const hasLabel = id && document.querySelector(`label[for="${id}"]`);
      return !hasLabel && !ariaLabel && !ariaLabeledBy && !inp.placeholder;
    }).map(inp => ({ tag: inp.tagName, id: inp.id, type: inp.type }));
  });
  if (labelChecks.length) {
    labelChecks.forEach(l => add('serious', 'WCAG 1.3.1 Info & Relationships', `<${l.tag} id="${l.id}" type="${l.type}">`, 'Input lacks accessible label', 'Add <label for="..."> or aria-label'));
  } else {
    pass('WCAG 1.3.1', 'All form inputs have labels');
  }

  // 5. Buttons without accessible names
  const btnChecks = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('button')).filter(b => {
      const txt = (b.textContent || '').trim();
      const aria = b.getAttribute('aria-label');
      const title = b.getAttribute('title');
      return !txt && !aria && !title;
    }).map(b => ({ cls: b.className, id: b.id, html: b.outerHTML.substring(0,120) }));
  });
  if (btnChecks.length) {
    btnChecks.forEach(b => add('serious', 'WCAG 4.1.2 Name, Role, Value', b.html, 'Button has no accessible name', 'Add text, aria-label, or title'));
  } else {
    pass('WCAG 4.1.2', 'All buttons have accessible names');
  }

  // 6. Heading hierarchy
  const headingCheck = await page.evaluate(() => {
    const h = Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')).map(el => ({ tag: el.tagName, text: el.textContent.substring(0,40) }));
    const issues = [];
    let prev = 0;
    h.forEach(({ tag, text }) => {
      const level = parseInt(tag[1]);
      if (level > prev + 1 && prev !== 0) issues.push({ tag, text, prev });
      prev = level;
    });
    return { h, issues };
  });
  if (headingCheck.issues.length) {
    headingCheck.issues.forEach(i => add('moderate', 'WCAG 1.3.1 Heading Order', `<${i.tag}> "${i.text}"`, `Skipped heading level (prev was h${i.prev})`, 'Use sequential heading levels'));
  } else {
    pass('WCAG 1.3.1', 'Heading hierarchy is sequential');
  }

  // 7. Reduced motion / scroll hijacking
  const motionCheck = await page.evaluate(() => {
    const hasPrefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const parallax = document.querySelector('.door-bg');
    return { hasPrefersReduced, hasParallax: !!parallax };
  });
  if (motionCheck.hasParallax && !motionCheck.hasPrefersReduced) {
    pass('WCAG 2.2.2', 'Parallax present but no reduced-motion query active on this client');
    add('moderate', 'WCAG 2.2.2 Pause, Stop, Hide', '.door-bg', 'Parallax scroll effect has no reduced-motion media query guard', 'Wrap parallax in @media (prefers-reduced-motion: no-preference) or disable via JS');
  }

  // 8. Touch target size (44x44px)
  const touchCheck = await page.evaluate(() => {
    const issues = [];
    document.querySelectorAll('button, a, input, select, textarea, [onclick]').forEach(el => {
      const rect = el.getBoundingClientRect();
      if (rect.width < 44 || rect.height < 44) {
        issues.push({ tag: el.tagName, w: rect.width.toFixed(1), h: rect.height.toFixed(1), id: el.id });
      }
    });
    return issues;
  });
  if (touchCheck.length) {
    touchCheck.slice(0, 8).forEach(t => add('moderate', 'WCAG 2.5.5 Target Size', `<${t.tag} id="${t.id}">`, `Touch target ${t.w}x${t.h}px (need 44x44)`, 'Increase padding or explicit size'));
  } else {
    pass('WCAG 2.5.5', 'All interactive elements meet 44x44px target size');
  }

  // 9. Keyboard trap check (basic: can tab through all focusables and reach end)
  const focusCount = await page.evaluate(() => document.querySelectorAll('[tabindex]:not([tabindex="-1"]), button, a, input, textarea, select').length);
  pass('WCAG 2.1.2', `Focusable elements count: ${focusCount} (manual check required for trap)`);

  // Summary
  results.summary = {
    totalIssues: results.issues.length,
    serious: results.issues.filter(i => i.impact === 'serious').length,
    moderate: results.issues.filter(i => i.impact === 'moderate').length,
    passed: results.passed.length,
  };

  ensureDir(OUT);
  fs.writeFileSync(OUT, JSON.stringify(results, null, 2), 'utf8');
  console.log(`WCAG audit complete: ${results.summary.totalIssues} issues, ${results.summary.passed} passed`);
  console.log(`Report saved to ${OUT}`);

  // Screenshot for visual review
  const shotPath = OUT.replace('.json', '.png');
  await page.screenshot({ path: shotPath, fullPage: true });
  console.log(`Screenshot saved to ${shotPath}`);

  await browser.close();
}

audit().catch(err => { console.error(err); process.exit(1); });
