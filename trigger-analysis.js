/**
 * Analyze why "make changes to repo" fails to classify as code
 */

const { CAPABILITY_REGISTRY } = require('./apps/lantern-garage/lib/intent-router.js');

const testMessage = "make changes to repo";
console.log(`Testing message: "${testMessage}"\n`);

const keystone = CAPABILITY_REGISTRY.find(c => c.id === "keystone");
console.log(`Keystone triggers (${keystone.triggers.length} total):\n`);

keystone.triggers.forEach((trigger, idx) => {
  const matches = trigger.test(testMessage);
  console.log(`  [${idx}] ${trigger}`);
  console.log(`      Matches: ${matches ? 'YES' : 'NO'}`);
});

console.log('\n' + '='.repeat(80));
console.log('ANALYSIS:');
console.log('='.repeat(80));
console.log(`The word "changes" doesn't match any of the code-related keywords.`);
console.log(`The word "repo" doesn't match either (would need "repository" or code-specific term).`);
console.log(`\nProblematic keywords missing from Keystone triggers:`);
console.log(`  - "changes/change" (common in Git/coding context)`);
console.log(`  - "repo/repository" (Git source control)`);
console.log(`  - "modify/modification" (general code edit)`);
console.log(`  - "patch" (common in code reviews/fixes)`);
console.log(`  - "update" (deployed in many code contexts)`);
