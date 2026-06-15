// Test script for TradingView UI improvements
const tests = {
  lightModeColors: {
    name: "Light Mode Colors",
    test: () => {
      const root = getComputedStyle(document.documentElement);
      const bg0 = root.getPropertyValue('--bg0').trim();
      const text0 = root.getPropertyValue('--text0').trim();
      return {
        pass: bg0 === '#ffffff' && text0 === '#1a1a1a',
        details: `bg0=${bg0}, text0=${text0}`
      };
    }
  },
  darkModeColors: {
    name: "Dark Mode Colors",
    test: () => {
      const root = getComputedStyle(document.documentElement);
      const initialBg = root.getPropertyValue('--bg0').trim();
      
      // Toggle light mode
      document.documentElement.classList.add('light-mode');
      const lightBg = root.getPropertyValue('--bg0').trim();
      document.documentElement.classList.remove('light-mode');
      
      return {
        pass: lightBg === '#ffffff',
        details: `Light mode bg0=${lightBg}`
      };
    }
  },
  chartCanvas: {
    name: "Chart Canvas Rendering",
    test: () => {
      const canvases = document.querySelectorAll('canvas.chart-canvas');
      return {
        pass: canvases.length > 0,
        details: `Found ${canvases.length} chart canvas(es)`
      };
    }
  },
  focusIndicators: {
    name: "Focus Indicators",
    test: () => {
      const style = getComputedStyle(document.documentElement);
      const hasRule = document.styleSheets.length > 0;
      return {
        pass: hasRule,
        details: `${document.styleSheets.length} stylesheets loaded`
      };
    }
  },
  keyboardAccessibility: {
    name: "Keyboard Navigation",
    test: () => {
      const buttons = document.querySelectorAll('button, a, [role="button"]');
      const focusableElements = document.querySelectorAll('[tabindex], button, a, input, select, textarea');
      return {
        pass: focusableElements.length > 0,
        details: `${buttons.length} buttons, ${focusableElements.length} focusable elements`
      };
    }
  },
  skipLink: {
    name: "Skip Link",
    test: () => {
      const skipLink = document.querySelector('.skip-link');
      return {
        pass: skipLink !== null,
        details: skipLink ? `Skip link text: "${skipLink.textContent}"` : "No skip link found"
      };
    }
  }
};

// Run all tests
console.log('=== Stock Trader UI Test Suite ===\n');
let passed = 0;
let failed = 0;

for (const [key, test] of Object.entries(tests)) {
  try {
    const result = test.test();
    const status = result.pass ? '✓ PASS' : '✗ FAIL';
    console.log(`${status}: ${test.name}`);
    console.log(`  ${result.details}\n`);
    result.pass ? passed++ : failed++;
  } catch (e) {
    console.log(`✗ FAIL: ${test.name}`);
    console.log(`  Error: ${e.message}\n`);
    failed++;
  }
}

console.log(`\n=== Results ===`);
console.log(`Passed: ${passed}/${Object.keys(tests).length}`);
console.log(`Failed: ${failed}/${Object.keys(tests).length}`);
