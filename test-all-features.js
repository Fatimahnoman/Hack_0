// Complete Gold Tier Feature Test Suite

console.log('===========================================');
console.log('   GOLD TIER - COMPLETE FEATURE TEST');
console.log('===========================================\n');

const tests = [];

// Feature 1: Audit Logger
console.log('[1/10] Testing Audit Logger...');
try {
  const { createLogger } = require('./gold/skills/audit-logger');
  const logger = createLogger('test-suite');
  logger.info('test_suite_started', { timestamp: new Date().toISOString() });
  console.log('       ✓ Audit Logger - PASS\n');
  tests.push({ name: 'Audit Logger', status: 'PASS' });
} catch (e) {
  console.log('       ✗ Audit Logger - FAIL:', e.message, '\n');
  tests.push({ name: 'Audit Logger', status: 'FAIL', error: e.message });
}

// Feature 2: Weekly Business Audit
console.log('[2/10] Testing Weekly Business Audit...');
const { generateWeeklyAudit, generateCEOBriefing } = require('./gold/skills/weekly-business-audit');
generateWeeklyAudit({ weekOffset: 0 })
  .then(audit => {
    console.log('       ✓ Weekly Business Audit - PASS');
    console.log('         Status:', audit.status || 'success');
    console.log('         Period:', audit.period?.start, 'to', audit.period?.end, '\n');
    tests.push({ name: 'Weekly Business Audit', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ Weekly Business Audit - FAIL:', e.message, '\n');
    tests.push({ name: 'Weekly Business Audit', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 3: CEO Briefing
    console.log('[3/10] Testing CEO Briefing...');
    return generateCEOBriefing({ weekOffset: 0 });
  })
  .then(briefing => {
    console.log('       ✓ CEO Briefing - PASS');
    console.log('         Title:', briefing.title);
    console.log('         Priority:', briefing.priority, '\n');
    tests.push({ name: 'CEO Briefing', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ CEO Briefing - FAIL:', e.message, '\n');
    tests.push({ name: 'CEO Briefing', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 4: Ralph Wiggum Loop
    console.log('[4/10] Testing Ralph Wiggum Loop...');
    const { ralphWiggumLoop } = require('./gold/skills/ralph-wiggum-loop');
    return ralphWiggumLoop('Test autonomous task', { maxIterations: 3 });
  })
  .then(result => {
    console.log('       ✓ Ralph Wiggum Loop - PASS');
    console.log('         Status:', result.status);
    console.log('         Iterations:', result.iterations, '\n');
    tests.push({ name: 'Ralph Wiggum Loop', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ Ralph Wiggum Loop - FAIL:', e.message, '\n');
    tests.push({ name: 'Ralph Wiggum Loop', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 5: Error Recovery
    console.log('[5/10] Testing Error Recovery...');
    const { classifyError, executeWithRetry } = require('./gold/skills/error-recovery');
    const err = new Error('Connection timeout');
    const classification = classifyError(err);
    console.log('       ✓ Error Recovery - PASS');
    console.log('         Category:', classification.category);
    console.log('         Retryable:', classification.isRetryable, '\n');
    tests.push({ name: 'Error Recovery', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ Error Recovery - FAIL:', e.message, '\n');
    tests.push({ name: 'Error Recovery', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 6: System Audit Summary
    console.log('[6/10] Testing System Audit Summary...');
    const { getSystemAuditSummary } = require('./gold/skills/audit-logger');
    const summary = getSystemAuditSummary(24);
    console.log('       ✓ System Audit Summary - PASS');
    console.log('         Total Entries:', summary.totals.entries);
    console.log('         Errors:', summary.totals.errors, '\n');
    tests.push({ name: 'System Audit Summary', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ System Audit Summary - FAIL:', e.message, '\n');
    tests.push({ name: 'System Audit Summary', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 7: Cross-Domain Integration
    console.log('[7/10] Testing Cross-Domain Integration...');
    const { analyzeTaskDomain } = require('./gold/skills/cross-domain-integration');
    const analysis = analyzeTaskDomain('Post accounting summary to LinkedIn');
    console.log('       ✓ Cross-Domain Integration - PASS');
    console.log('         Domain:', analysis.domain);
    console.log('         Subtasks:', analysis.subtasks.length, '\n');
    tests.push({ name: 'Cross-Domain Integration', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ Cross-Domain Integration - FAIL:', e.message, '\n');
    tests.push({ name: 'Cross-Domain Integration', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 8: Accounting Audit
    console.log('[8/10] Testing Accounting Audit...');
    const { runAccountingAudit } = require('./gold/skills/accounting-audit');
    return runAccountingAudit({ period: 'monthly' });
  })
  .then(audit => {
    console.log('       ✓ Accounting Audit - PASS');
    console.log('         Type:', audit.report_type);
    console.log('         Status:', audit.status || 'completed', '\n');
    tests.push({ name: 'Accounting Audit', status: 'PASS' });
  })
  .catch(e => {
    console.log('       ✗ Accounting Audit - FAIL:', e.message, '\n');
    tests.push({ name: 'Accounting Audit', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 9: Odoo MCP Server Check
    console.log('[9/10] Checking Odoo MCP Server...');
    const fs = require('fs');
    const odooMcpExists = fs.existsSync('./mcp_servers/odoo-accounting/index.js');
    if (odooMcpExists) {
      console.log('       ✓ Odoo MCP Server - PASS');
      console.log('         File: mcp_servers/odoo-accounting/index.js exists\n');
      tests.push({ name: 'Odoo MCP Server', status: 'PASS' });
    } else {
      console.log('       ✗ Odoo MCP Server - FAIL: File not found\n');
      tests.push({ name: 'Odoo MCP Server', status: 'FAIL' });
    }
  })
  .catch(e => {
    console.log('       ✗ Odoo MCP Server - FAIL:', e.message, '\n');
    tests.push({ name: 'Odoo MCP Server', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Feature 10: Social Media MCP Servers Check
    console.log('[10/10] Checking Social Media MCP Servers...');
    const fs = require('fs');
    const fbExists = fs.existsSync('./mcp_servers/facebook-instagram/index.js');
    const twitterExists = fs.existsSync('./mcp_servers/twitter/index.js');
    if (fbExists && twitterExists) {
      console.log('       ✓ Social Media MCP Servers - PASS');
      console.log('         Facebook/Instagram: ✓');
      console.log('         Twitter: ✓\n');
      tests.push({ name: 'Social Media MCP Servers', status: 'PASS' });
    } else {
      console.log('       ✗ Social Media MCP Servers - FAIL\n');
      tests.push({ name: 'Social Media MCP Servers', status: 'FAIL' });
    }
  })
  .catch(e => {
    console.log('       ✗ Social Media MCP Servers - FAIL:', e.message, '\n');
    tests.push({ name: 'Social Media MCP Servers', status: 'FAIL', error: e.message });
  })
  .then(() => {
    // Final Summary
    setTimeout(() => {
      console.log('===========================================');
      console.log('              TEST SUMMARY');
      console.log('===========================================');
      const passed = tests.filter(t => t.status === 'PASS').length;
      const failed = tests.filter(t => t.status === 'FAIL').length;
      console.log(`Total Tests: ${tests.length}`);
      console.log(`Passed: ${passed}`);
      console.log(`Failed: ${failed}`);
      console.log('\nResults:');
      tests.forEach(t => {
        console.log(`  ${t.status === 'PASS' ? '✓' : '✗'} ${t.name}`);
      });
      console.log('\n===========================================');
      console.log(passed === tests.length ? '   ALL TESTS PASSED! 🎉' : '   SOME TESTS FAILED');
      console.log('===========================================\n');
    }, 2000);
  });
