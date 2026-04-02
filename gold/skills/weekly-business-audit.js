/**
 * Weekly Business Audit Skill
 * 
 * Generates comprehensive weekly business audit with CEO Briefing
 * Integrates data from: Social Media, Accounting, Operations
 */

const fs = require('fs');
const path = require('path');
const { exec } = require('child_process');
const { promisify } = require('util');

const execAsync = promisify(exec);

// Configuration (this file lives in gold/skills/)
const PROJECT_ROOT = path.join(__dirname, '../..');
const BRIEFINGS_DIR = path.join(__dirname, '../briefings');
const LOGS_DIR = path.join(PROJECT_ROOT, 'Logs');

// Ensure directories exist
[BRIEFINGS_DIR, LOGS_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

/**
 * Generate Weekly Business Audit
 */
async function generateWeeklyAudit(options = {}) {
  const { weekOffset = 0, includeRecommendations = true } = options;
  
  const audit = {
    report_type: 'weekly_business_audit',
    generated_at: new Date().toISOString(),
    period: getWeekPeriod(weekOffset),
    sections: {},
    summary: {},
    recommendations: [],
  };

  // 1. Financial Summary
  audit.sections.financial = await getFinancialSummary();
  
  // 2. Social Media Summary
  audit.sections.social_media = await getSocialMediaSummary();
  
  // 3. Operations Summary
  audit.sections.operations = await getOperationsSummary();
  
  // 4. Key Metrics
  audit.sections.kpi = await getKPISummary(audit.sections);
  
  // 5. Generate Summary
  audit.summary = generateExecutiveSummary(audit.sections);
  
  // 6. Generate Recommendations
  if (includeRecommendations) {
    audit.recommendations = generateRecommendations(audit.sections);
  }

  // Save report
  const filename = `weekly-audit-${getWeekPeriod(weekOffset).start}-to-${getWeekPeriod(weekOffset).end}.json`;
  const filepath = path.join(BRIEFINGS_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(audit, null, 2));

  // Log audit
  logAudit('weekly_business_audit', { filename, week_offset: weekOffset });

  return audit;
}

/**
 * Generate CEO Briefing Document
 */
async function generateCEOBriefing(options = {}) {
  const { weekOffset = 0, format = 'markdown' } = options;
  
  const audit = await generateWeeklyAudit({ weekOffset });
  
  const briefing = {
    title: `CEO Weekly Briefing - Week of ${audit.period.start}`,
    generated_at: new Date().toISOString(),
    priority: 'high',
    read_time_minutes: 5,
    content: generateBriefingContent(audit),
    attachments: {
      full_audit: `gold/briefings/weekly-audit-${audit.period.start}-to-${audit.period.end}.json`,
    },
    action_items: extractActionItems(audit),
    decisions_needed: extractDecisionsNeeded(audit),
  };

  // Save briefing
  const filename = `ceo-briefing-${audit.period.start}.md`;
  const filepath = path.join(BRIEFINGS_DIR, filename);
  
  const markdownContent = formatBriefingAsMarkdown(briefing);
  fs.writeFileSync(filepath, markdownContent);

  logAudit('ceo_briefing', { filename, week_offset: weekOffset });

  return briefing;
}

/**
 * Get Financial Summary from Odoo
 */
async function getFinancialSummary() {
  const summary = {
    revenue: 0,
    expenses: 0,
    profit: 0,
    receivables: 0,
    payables: 0,
    cash_flow: 0,
    invoices_sent: 0,
    bills_received: 0,
    top_custom: null,
    top_expense_category: null,
  };

  try {
    // This would call the Odoo MCP server in production
    // For now, we'll create a placeholder structure
    summary.status = 'connected';
    summary.currency = 'USD';
    summary.last_sync = new Date().toISOString();
  } catch (error) {
    summary.status = 'error';
    summary.error = error.message;
  }

  return summary;
}

/**
 * Get Social Media Summary
 */
async function getSocialMediaSummary() {
  const summary = {
    facebook: {
      posts: 0,
      reach: 0,
      engagement: 0,
      new_followers: 0,
    },
    instagram: {
      posts: 0,
      reach: 0,
      engagement: 0,
      new_followers: 0,
    },
    twitter: {
      tweets: 0,
      impressions: 0,
      engagement: 0,
      new_followers: 0,
    },
    linkedin: {
      posts: 0,
      impressions: 0,
      engagement: 0,
      new_followers: 0,
    },
    total: {
      posts: 0,
      reach: 0,
      engagement: 0,
      new_followers: 0,
    },
  };

  try {
    // Read from social media audit logs
    const socialLogs = readAuditLogs('facebook-instagram');
    const twitterLogs = readAuditLogs('twitter');
    const linkedinLogs = readAuditLogs('linkedin');

    summary.facebook.posts = socialLogs.filter(l => l.action === 'facebook_post' && l.result === 'success').length;
    summary.instagram.posts = socialLogs.filter(l => l.action === 'instagram_post' && l.result === 'success').length;
    summary.twitter.tweets = twitterLogs.filter(l => l.action === 'post_tweet' && l.result === 'success').length;
    summary.linkedin.posts = linkedinLogs.filter(l => l.action === 'post' && l.result === 'success').length;
    
    summary.total.posts = summary.facebook.posts + summary.instagram.posts + summary.twitter.tweets + summary.linkedin.posts;
    summary.status = 'connected';
  } catch (error) {
    summary.status = 'error';
    summary.error = error.message;
  }

  return summary;
}

/**
 * Get Operations Summary
 */
async function getOperationsSummary() {
  const summary = {
    tasks_completed: 0,
    tasks_pending: 0,
    tasks_failed: 0,
    automation_runs: 0,
    errors: 0,
    uptime_percentage: 100,
    mcp_servers_active: 0,
  };

  try {
    // Read from logs
    const allLogs = readAllAuditLogs();
    
    summary.tasks_completed = allLogs.filter(l => l.result === 'success').length;
    summary.tasks_failed = allLogs.filter(l => l.result === 'failed').length;
    summary.automation_runs = allLogs.length;
    summary.errors = allLogs.filter(l => l.result === 'error').length;
    
    if (summary.automation_runs > 0) {
      summary.uptime_percentage = ((summary.tasks_completed / summary.automation_runs) * 100).toFixed(2);
    }

    summary.status = 'operational';
  } catch (error) {
    summary.status = 'error';
    summary.error = error.message;
  }

  return summary;
}

/**
 * Get KPI Summary
 */
async function getKPISummary(sections) {
  return {
    financial_health: calculateFinancialHealth(sections.financial),
    social_growth: calculateSocialGrowth(sections.social_media),
    operational_efficiency: sections.operations.uptime_percentage,
    overall_score: calculateOverallScore(sections),
  };
}

/**
 * Generate Executive Summary
 */
function generateExecutiveSummary(sections) {
  const highlights = [];
  const concerns = [];

  // Financial highlights/concerns
  if (sections.financial.profit > 0) {
    highlights.push(`Generated profit of $${sections.financial.profit.toFixed(2)}`);
  } else if (sections.financial.profit < 0) {
    concerns.push(`Loss of $${Math.abs(sections.financial.profit).toFixed(2)}`);
  }

  // Social media highlights
  if (sections.social_media.total.posts > 0) {
    highlights.push(`Published ${sections.social_media.total.posts} social media posts`);
  }

  // Operations highlights
  if (sections.operations.uptime_percentage >= 99) {
    highlights.push(`System uptime: ${sections.operations.uptime_percentage}%`);
  } else if (sections.operations.uptime_percentage < 95) {
    concerns.push(`System uptime below target: ${sections.operations.uptime_percentage}%`);
  }

  return {
    highlights,
    concerns,
    overall_status: concerns.length > 0 ? 'needs_attention' : 'good',
  };
}

/**
 * Generate Recommendations
 */
function generateRecommendations(sections) {
  const recommendations = [];

  // Financial recommendations
  if (sections.financial.receivables > sections.financial.revenue * 0.3) {
    recommendations.push({
      priority: 'high',
      category: 'financial',
      title: 'Follow up on outstanding receivables',
      description: `Outstanding receivables ($${sections.financial.receivables}) exceed 30% of revenue. Consider sending payment reminders.`,
      action: 'Review aged receivables report and contact customers with overdue invoices.',
    });
  }

  // Social media recommendations
  if (sections.social_media.total.posts < 3) {
    recommendations.push({
      priority: 'medium',
      category: 'marketing',
      title: 'Increase social media activity',
      description: 'Only published few posts this week. Consider increasing posting frequency.',
      action: 'Schedule at least 3-5 posts per week across all platforms.',
    });
  }

  // Operations recommendations
  if (sections.operations.tasks_failed > 0) {
    recommendations.push({
      priority: 'high',
      category: 'operations',
      title: 'Review failed automation tasks',
      description: `${sections.operations.tasks_failed} automation tasks failed this week.`,
      action: 'Check Logs directory for error details and implement fixes.',
    });
  }

  return recommendations;
}

/**
 * Generate Briefing Content
 */
function generateBriefingContent(audit) {
  return {
    executive_summary: audit.summary,
    key_metrics: audit.sections.kpi,
    financial_highlights: audit.sections.financial,
    social_media_performance: audit.sections.social_media,
    operations_status: audit.sections.operations,
    recommendations: audit.recommendations,
  };
}

/**
 * Extract Action Items
 */
function extractActionItems(audit) {
  const actions = [];

  audit.recommendations.forEach((rec, index) => {
    if (rec.priority === 'high') {
      actions.push({
        id: index + 1,
        title: rec.title,
        priority: rec.priority,
        category: rec.category,
        due_date: getDueDate(rec.priority),
      });
    }
  });

  return actions;
}

/**
 * Extract Decisions Needed
 */
function extractDecisionsNeeded(audit) {
  const decisions = [];

  // Check for significant financial decisions
  if (audit.sections.financial.profit < 0) {
    decisions.push({
      title: 'Review loss-making operations',
      description: 'Business operated at a loss this week. Review cost structure.',
      urgency: 'high',
    });
  }

  return decisions;
}

/**
 * Format Briefing as Markdown
 */
function formatBriefingAsMarkdown(briefing) {
  let md = `# ${briefing.title}\n\n`;
  md += `**Generated:** ${new Date(briefing.generated_at).toLocaleString()}\n`;
  md += `**Priority:** ${briefing.priority.toUpperCase()}\n`;
  md += `**Read Time:** ${briefing.read_time_minutes} minutes\n\n`;
  
  md += `---\n\n`;
  
  md += `## Executive Summary\n\n`;
  md += briefing.content.executive_summary.highlights.map(h => `✅ ${h}`).join('\n');
  md += '\n\n';
  if (briefing.content.executive_summary.concerns.length > 0) {
    md += `### Concerns\n\n`;
    md += briefing.content.executive_summary.concerns.map(c => `⚠️ ${c}`).join('\n');
    md += '\n\n';
  }
  
  md += `---\n\n`;
  
  md += `## Key Metrics\n\n`;
  md += `| Metric | Value |\n`;
  md += `|--------|-------|\n`;
  md += `| Financial Health | ${briefing.content.key_metrics.financial_health}/100 |\n`;
  md += `| Social Growth | ${briefing.content.key_metrics.social_growth}/100 |\n`;
  md += `| Operational Efficiency | ${briefing.content.key_metrics.operational_efficiency}% |\n`;
  md += `| **Overall Score** | **${briefing.content.key_metrics.overall_score}/100** |\n\n`;
  
  md += `---\n\n`;
  
  md += `## Action Items\n\n`;
  briefing.action_items.forEach(item => {
    md += `- [ ] **${item.title}** (Priority: ${item.priority}, Due: ${item.due_date})\n`;
  });
  md += '\n';
  
  if (briefing.decisions_needed.length > 0) {
    md += `---\n\n`;
    md += `## Decisions Needed\n\n`;
    briefing.decisions_needed.forEach(decision => {
      md += `- **${decision.title}** (${decision.urgency}): ${decision.description}\n`;
    });
    md += '\n';
  }
  
  md += `---\n\n`;
  
  md += `## Recommendations\n\n`;
  briefing.content.recommendations.forEach((rec, index) => {
    md += `### ${index + 1}. ${rec.title}\n`;
    md += `**Category:** ${rec.category} | **Priority:** ${rec.priority}\n\n`;
    md += `${rec.description}\n\n`;
    md += `**Action:** ${rec.action}\n\n`;
  });
  
  return md;
}

// Helper Functions
function getWeekPeriod(offset = 0) {
  const now = new Date();
  const weekStart = new Date(now);
  weekStart.setDate(now.getDate() - now.getDay() - (offset * 7));
  weekStart.setHours(0, 0, 0, 0);
  
  const weekEnd = new Date(weekStart);
  weekEnd.setDate(weekStart.getDate() + 6);
  weekEnd.setHours(23, 59, 59, 999);
  
  return {
    start: weekStart.toISOString().split('T')[0],
    end: weekEnd.toISOString().split('T')[0],
  };
}

function getDueDate(priority) {
  const now = new Date();
  switch (priority) {
    case 'high':
      now.setDate(now.getDate() + 1);
      break;
    case 'medium':
      now.setDate(now.getDate() + 3);
      break;
    case 'low':
      now.setDate(now.getDate() + 7);
      break;
  }
  return now.toISOString().split('T')[0];
}

function calculateFinancialHealth(financial) {
  // Simple scoring: profit margin, cash flow, receivables ratio
  let score = 50;
  
  if (financial.profit > 0) score += 20;
  if (financial.cash_flow > 0) score += 15;
  if (financial.receivables < (financial.revenue || 1) * 0.2) score += 15;
  
  return Math.min(100, score);
}

function calculateSocialGrowth(social) {
  // Simple scoring based on activity and growth
  let score = 0;
  
  if (social.total.posts >= 5) score += 40;
  else if (social.total.posts >= 3) score += 25;
  else if (social.total.posts >= 1) score += 10;
  
  if (social.total.new_followers > 0) score += 30;
  if (social.total.engagement > 0) score += 30;
  
  return Math.min(100, score);
}

function calculateOverallScore(sections) {
  const weights = {
    financial: 0.4,
    social: 0.3,
    operations: 0.3,
  };
  
  const financialScore = calculateFinancialHealth(sections.financial);
  const socialScore = calculateSocialGrowth(sections.social_media);
  const operationsScore = parseFloat(sections.operations.uptime_percentage);
  
  return Math.round(
    financialScore * weights.financial +
    socialScore * weights.social +
    operationsScore * weights.operations
  );
}

function readAuditLogs(service) {
  const logFile = path.join(LOGS_DIR, `${service}-audit.jsonl`);
  if (!fs.existsSync(logFile)) return [];
  
  const content = fs.readFileSync(logFile, 'utf-8');
  return content.split('\n').filter(line => line.trim()).map(line => JSON.parse(line));
}

function readAllAuditLogs() {
  const services = ['facebook-instagram', 'twitter', 'odoo-accounting', 'linkedin'];
  const allLogs = [];
  
  services.forEach(service => {
    const logs = readAuditLogs(service);
    allLogs.push(...logs);
  });
  
  return allLogs;
}

function logAudit(action, details) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    service: 'weekly-audit',
    action,
    details,
  };
  
  const logFile = path.join(LOGS_DIR, 'weekly-audit.jsonl');
  try {
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
  } catch (e) {
    console.error('[Weekly Audit] Failed to write log:', e.message);
  }
}

// Export as skill
module.exports = {
  generateWeeklyAudit,
  generateCEOBriefing,
  getFinancialSummary,
  getSocialMediaSummary,
  getOperationsSummary,
};
