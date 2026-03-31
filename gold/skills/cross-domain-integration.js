/**
 * Cross-Domain Integration Skill
 * 
 * Unifies Personal and Business domains
 * Provides seamless integration across all MCP servers and services
 */

const fs = require('fs');
const path = require('path');

const LOGS_DIR = path.join(__dirname, '../../Logs');
const BRIEFINGS_DIR = path.join(__dirname, '../briefings');

// Ensure directories exist
if (!fs.existsSync(BRIEFINGS_DIR)) {
  fs.mkdirSync(BRIEFINGS_DIR, { recursive: true });
}

/**
 * Unified Task Executor
 * Routes tasks to appropriate domain (Personal/Business)
 */
async function executeCrossDomainTask(task, context = {}) {
  const analysis = analyzeTaskDomain(task);
  
  const result = {
    taskId: `cross_${Date.now()}`,
    originalTask: task,
    domain: analysis.domain,
    subtasks: [],
    results: {},
    timestamp: new Date().toISOString(),
  };
  
  // Execute based on domain
  if (analysis.domain === 'business') {
    result.results = await executeBusinessTasks(analysis.subtasks, context);
  } else if (analysis.domain === 'personal') {
    result.results = await executePersonalTasks(analysis.subtasks, context);
  } else {
    result.results = await executeMixedTasks(analysis.subtasks, context);
  }
  
  // Log execution
  logCrossDomainExecution(result);
  
  return result;
}

/**
 * Analyze task domain
 */
function analyzeTaskDomain(task) {
  const businessKeywords = [
    'accounting', 'invoice', 'bill', 'financial', 'audit', 'report',
    'facebook', 'instagram', 'twitter', 'linkedin', 'post', 'social',
    'business', 'company', 'client', 'customer', 'vendor', 'revenue',
  ];
  
  const personalKeywords = [
    'personal', 'family', 'home', 'personal email', 'my account',
    'vacation', 'holiday', 'personal finance', 'my bills',
  ];
  
  const taskLower = task.toLowerCase();
  
  const hasBusiness = businessKeywords.some(kw => taskLower.includes(kw));
  const hasPersonal = personalKeywords.some(kw => taskLower.includes(kw));
  
  let domain = 'mixed';
  if (hasBusiness && !hasPersonal) domain = 'business';
  if (hasPersonal && !hasBusiness) domain = 'personal';
  
  // Decompose into subtasks
  const subtasks = decomposeCrossDomainTask(task, domain);
  
  return { domain, subtasks, hasBusiness, hasPersonal };
}

/**
 * Decompose cross-domain task
 */
function decomposeCrossDomainTask(task, domain) {
  const subtasks = [];
  
  if (domain === 'business') {
    // Business task decomposition
    if (/weekly.*audit|audit.*weekly/i.test(task)) {
      subtasks.push(
        { service: 'odoo', action: 'getFinancialSummary' },
        { service: 'social', action: 'getSocialSummary' },
        { service: 'audit', action: 'generateWeeklyReport' },
        { service: 'briefing', action: 'createCEOBriefing' },
      );
    } else if (/accounting.*audit|audit.*accounting/i.test(task)) {
      subtasks.push(
        { service: 'odoo', action: 'connect' },
        { service: 'odoo', action: 'runFullAudit' },
        { service: 'audit', action: 'generateReport' },
        { service: 'briefing', action: 'saveReport' },
      );
    } else if (/post.*social|social.*post/i.test(task)) {
      subtasks.push(
        { service: 'content', action: 'analyzeContent' },
        { service: 'facebook', action: 'post' },
        { service: 'instagram', action: 'post' },
        { service: 'twitter', action: 'post' },
        { service: 'linkedin', action: 'post' },
        { service: 'analytics', action: 'trackPosts' },
      );
    }
  } else if (domain === 'personal') {
    // Personal task decomposition
    subtasks.push(
      { service: 'personal', action: 'identifyTask' },
      { service: 'personal', action: 'executeTask' },
      { service: 'personal', action: 'confirmCompletion' },
    );
  } else {
    // Mixed domain - coordinate across both
    subtasks.push(
      { service: 'coordinator', action: 'analyzeDomains' },
      { service: 'business', action: 'executeBusinessPart' },
      { service: 'personal', action: 'executePersonalPart' },
      { service: 'coordinator', action: 'consolidateResults' },
    );
  }
  
  return subtasks;
}

/**
 * Execute business tasks
 */
async function executeBusinessTasks(subtasks, context) {
  const results = {};
  
  for (const subtask of subtasks) {
    try {
      results[subtask.service] = await executeServiceAction(subtask.service, subtask.action, context);
      results[subtask.service].status = 'success';
    } catch (error) {
      results[subtask.service] = {
        status: 'error',
        error: error.message,
      };
    }
  }
  
  return results;
}

/**
 * Execute personal tasks
 */
async function executePersonalTasks(subtasks, context) {
  // Placeholder for personal task execution
  return {
    personal: {
      status: 'success',
      message: 'Personal tasks executed',
    },
  };
}

/**
 * Execute mixed domain tasks
 */
async function executeMixedTasks(subtasks, context) {
  const results = {};
  
  for (const subtask of subtasks) {
    try {
      if (subtask.service === 'coordinator') {
        results[subtask.service] = await coordinatorAction(subtask.action, context);
      } else {
        results[subtask.service] = await executeServiceAction(subtask.service, subtask.action, context);
      }
      results[subtask.service].status = 'success';
    } catch (error) {
      results[subtask.service] = {
        status: 'error',
        error: error.message,
      };
    }
  }
  
  return results;
}

/**
 * Execute service action
 */
async function executeServiceAction(service, action, context) {
  // Route to appropriate MCP server or skill
  switch (service) {
    case 'odoo':
      return await executeOdooAction(action, context);
    case 'facebook':
      return await executeFacebookAction(action, context);
    case 'instagram':
      return await executeInstagramAction(action, context);
    case 'twitter':
      return await executeTwitterAction(action, context);
    case 'linkedin':
      return await executeLinkedinAction(action, context);
    case 'social':
      return await executeSocialAction(action, context);
    case 'audit':
      return await executeAuditAction(action, context);
    case 'briefing':
      return await executeBriefingAction(action, context);
    case 'content':
      return await executeContentAction(action, context);
    case 'analytics':
      return await executeAnalyticsAction(action, context);
    default:
      return { message: `Unknown service: ${service}` };
  }
}

/**
 * Coordinator actions for mixed domain tasks
 */
async function coordinatorAction(action, context) {
  switch (action) {
    case 'analyzeDomains':
      return {
        message: 'Analyzing task domains',
        domains: ['business', 'personal'],
      };
    case 'consolidateResults':
      return {
        message: 'Consolidating results from all domains',
        consolidated: true,
      };
    default:
      return { message: `Unknown coordinator action: ${action}` };
  }
}

// Service-specific action handlers (placeholders)
async function executeOdooAction(action, context) {
  return { service: 'odoo', action, executed: true };
}

async function executeFacebookAction(action, context) {
  return { service: 'facebook', action, executed: true };
}

async function executeInstagramAction(action, context) {
  return { service: 'instagram', action, executed: true };
}

async function executeTwitterAction(action, context) {
  return { service: 'twitter', action, executed: true };
}

async function executeLinkedinAction(action, context) {
  return { service: 'linkedin', action, executed: true };
}

async function executeSocialAction(action, context) {
  return { service: 'social', action, executed: true };
}

async function executeAuditAction(action, context) {
  return { service: 'audit', action, executed: true };
}

async function executeBriefingAction(action, context) {
  return { service: 'briefing', action, executed: true };
}

async function executeContentAction(action, context) {
  return { service: 'content', action, executed: true };
}

async function executeAnalyticsAction(action, context) {
  return { service: 'analytics', action, executed: true };
}

/**
 * Generate Unified Dashboard Data
 */
async function generateUnifiedDashboard() {
  const dashboard = {
    generated_at: new Date().toISOString(),
    business: {
      accounting: await getBusinessAccountingSummary(),
      social_media: await getBusinessSocialSummary(),
      operations: await getBusinessOperationsSummary(),
    },
    personal: {
      tasks: await getPersonalTasksSummary(),
      calendar: await getPersonalCalendarSummary(),
    },
    integration: {
      cross_domain_tasks: await getCrossDomainTasksSummary(),
      pending_approvals: await getPendingApprovalsSummary(),
    },
  };
  
  return dashboard;
}

async function getBusinessAccountingSummary() {
  return { status: 'connected', last_sync: new Date().toISOString() };
}

async function getBusinessSocialSummary() {
  return { platforms: ['facebook', 'instagram', 'twitter', 'linkedin'], status: 'active' };
}

async function getBusinessOperationsSummary() {
  return { automation_status: 'running', uptime: '99.9%' };
}

async function getPersonalTasksSummary() {
  return { pending: 0, completed: 0 };
}

async function getPersonalCalendarSummary() {
  return { events_today: 0, upcoming: 0 };
}

async function getCrossDomainTasksSummary() {
  return { total: 0, business: 0, personal: 0, mixed: 0 };
}

async function getPendingApprovalsSummary() {
  return { pending: 0, requires_attention: false };
}

/**
 * Log cross-domain execution
 */
function logCrossDomainExecution(result) {
  const logEntry = {
    timestamp: result.timestamp,
    service: 'cross-domain',
    taskId: result.taskId,
    domain: result.domain,
    originalTask: result.originalTask,
    results: result.results,
  };
  
  const logFile = path.join(LOGS_DIR, 'cross-domain-audit.jsonl');
  try {
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
  } catch (e) {
    console.error('[Cross-Domain] Failed to write log:', e.message);
  }
}

/**
 * Generate Integration Report
 */
async function generateIntegrationReport(period = 'weekly') {
  const report = {
    report_type: 'cross_domain_integration',
    generated_at: new Date().toISOString(),
    period,
    summary: {
      total_tasks: 0,
      business_tasks: 0,
      personal_tasks: 0,
      mixed_tasks: 0,
      success_rate: 0,
    },
    services_used: [],
    recommendations: [],
  };
  
  // Read logs and generate report
  const logFile = path.join(LOGS_DIR, 'cross-domain-audit.jsonl');
  if (fs.existsSync(logFile)) {
    const content = fs.readFileSync(logFile, 'utf-8');
    const entries = content.split('\n').filter(line => line.trim()).map(line => JSON.parse(line));
    
    report.summary.total_tasks = entries.length;
    report.summary.business_tasks = entries.filter(e => e.domain === 'business').length;
    report.summary.personal_tasks = entries.filter(e => e.domain === 'personal').length;
    report.summary.mixed_tasks = entries.filter(e => e.domain === 'mixed').length;
    
    const successful = entries.filter(e => 
      Object.values(e.results).every(r => r.status === 'success')
    ).length;
    
    report.summary.success_rate = entries.length > 0 
      ? ((successful / entries.length) * 100).toFixed(2)
      : 0;
    
    // Get unique services
    const services = new Set();
    entries.forEach(entry => {
      Object.keys(entry.results).forEach(service => services.add(service));
    });
    report.services_used = Array.from(services);
  }
  
  // Save report
  const filename = `integration-report-${period}-${new Date().toISOString().split('T')[0]}.json`;
  const filepath = path.join(BRIEFINGS_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(report, null, 2));
  
  return report;
}

// ============================================================================
// Exports
// ============================================================================

module.exports = {
  executeCrossDomainTask,
  analyzeTaskDomain,
  generateUnifiedDashboard,
  generateIntegrationReport,
  executeServiceAction,
};
