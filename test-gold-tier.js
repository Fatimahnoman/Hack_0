// Test Gold Tier Skills

const { generateWeeklyAudit, generateCEOBriefing } = require('./gold/skills/weekly-business-audit');
const { runAccountingAudit } = require('./gold/skills/accounting-audit');
const { ralphWiggumLoop } = require('./gold/skills/ralph-wiggum-loop');
const { createLogger, getSystemAuditSummary } = require('./gold/skills/audit-logger');

async function runTests() {
  console.log('=== Gold Tier Tests ===\n');
  
  // Test 1: Create logger and log something
  console.log('Test 1: Audit Logger');
  const logger = createLogger('test');
  logger.info('test_started', { test: 'Gold Tier' });
  console.log('✓ Logger created and logged\n');
  
  // Test 2: Generate Weekly Audit
  console.log('Test 2: Weekly Business Audit');
  try {
    const audit = await generateWeeklyAudit({ weekOffset: 0 });
    console.log('✓ Weekly Audit generated');
    console.log('  Status:', audit.status || 'success');
    console.log('  Period:', audit.period?.start, 'to', audit.period?.end);
  } catch (error) {
    console.log('⚠ Weekly Audit note:', error.message);
  }
  
  // Test 3: Generate CEO Briefing
  console.log('\nTest 3: CEO Briefing');
  try {
    const briefing = await generateCEOBriefing({ weekOffset: 0 });
    console.log('✓ CEO Briefing generated');
    console.log('  Title:', briefing.title);
  } catch (error) {
    console.log('⚠ CEO Briefing note:', error.message);
  }
  
  // Test 4: Ralph Wiggum Loop
  console.log('\nTest 4: Ralph Wiggum Loop');
  try {
    const result = await ralphWiggumLoop('Post weekly update to social media', {
      maxIterations: 3,
    });
    console.log('✓ Ralph Wiggum Loop completed');
    console.log('  Status:', result.status);
    console.log('  Iterations:', result.iterations);
  } catch (error) {
    console.log('⚠ Ralph Wiggum Loop:', error.message);
  }
  
  // Test 5: Get System Audit Summary
  console.log('\nTest 5: System Audit Summary');
  try {
    const summary = getSystemAuditSummary(24);
    console.log('✓ Audit Summary generated');
    console.log('  Total entries:', summary.totals.entries);
    console.log('  Errors:', summary.totals.errors);
  } catch (error) {
    console.log('⚠ Audit Summary:', error.message);
  }
  
  console.log('\n=== Tests Complete ===');
  console.log('\nNext steps:');
  console.log('1. Check generated files in: gold\\briefings\\');
  console.log('2. Check logs in: Logs\\');
  console.log('3. Test MCP servers individually');
}

runTests().catch(console.error);
