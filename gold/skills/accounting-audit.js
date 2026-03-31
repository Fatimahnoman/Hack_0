/**
 * Accounting Audit Skill
 * 
 * Comprehensive accounting audit with Odoo integration
 * Generates financial reports, detects anomalies, provides insights
 */

const fs = require('fs');
const path = require('path');
const http = require('http');

// Configuration
const ODOO_CONFIG = {
  url: process.env.ODOO_URL || 'http://localhost:8069',
  db: process.env.ODOO_DB || 'odoo',
  username: process.env.ODOO_USERNAME || 'admin',
  password: process.env.ODOO_PASSWORD || 'admin',
};

const BRIEFINGS_DIR = path.join(__dirname, '../briefings');
const LOGS_DIR = path.join(__dirname, '../../Logs');

// Ensure directories exist
[BRIEFINGS_DIR, LOGS_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Audit session
let odooSession = { uid: null, userContext: null };

/**
 * Main Accounting Audit Function
 */
async function runAccountingAudit(options = {}) {
  const { period = 'monthly', includeRecommendations = true } = options;
  
  const audit = {
    report_type: 'accounting_audit',
    generated_at: new Date().toISOString(),
    period: getPeriodDates(period),
    sections: {},
    anomalies: [],
    recommendations: [],
    compliance_status: 'pending',
  };

  try {
    // Connect to Odoo
    await connectToOdoo();
    
    // 1. Financial Statements Audit
    audit.sections.financial_statements = await auditFinancialStatements();
    
    // 2. Accounts Receivable Audit
    audit.sections.accounts_receivable = await auditAccountsReceivable();
    
    // 3. Accounts Payable Audit
    audit.sections.accounts_payable = await auditAccountsPayable();
    
    // 4. Bank Reconciliation Audit
    audit.sections.bank_reconciliation = await auditBankReconciliation();
    
    // 5. Tax Compliance Audit
    audit.sections.tax_compliance = await auditTaxCompliance();
    
    // 6. Detect Anomalies
    audit.anomalies = detectAnomalies(audit.sections);
    
    // 7. Generate Recommendations
    if (includeRecommendations) {
      audit.recommendations = generateAuditRecommendations(audit);
    }
    
    // 8. Compliance Status
    audit.compliance_status = determineComplianceStatus(audit);
    
    // Save audit report
    const filename = `accounting-audit-${audit.period.start}-to-${audit.period.end}.json`;
    const filepath = path.join(BRIEFINGS_DIR, filename);
    fs.writeFileSync(filepath, JSON.stringify(audit, null, 2));
    
    logAudit('accounting_audit', { filename, period });
    
    return audit;
  } catch (error) {
    audit.error = error.message;
    audit.status = 'failed';
    return audit;
  }
}

/**
 * Generate Accounting Summary for CEO
 */
async function generateAccountingSummary(options = {}) {
  const { period = 'weekly' } = options;
  
  const audit = await runAccountingAudit({ period, includeRecommendations: false });
  
  const summary = {
    title: `Accounting Summary - ${period.toUpperCase()}`,
    generated_at: new Date().toISOString(),
    key_metrics: {
      revenue: audit.sections.financial_statements?.revenue || 0,
      expenses: audit.sections.financial_statements?.expenses || 0,
      net_income: audit.sections.financial_statements?.net_income || 0,
      receivables: audit.sections.accounts_receivable?.total_outstanding || 0,
      payables: audit.sections.accounts_payable?.total_outstanding || 0,
      cash_position: audit.sections.bank_reconciliation?.total_balance || 0,
    },
    alerts: audit.anomalies.filter(a => a.severity === 'high'),
    action_items: generateAccountingActionItems(audit),
    compliance_status: audit.compliance_status,
  };
  
  return summary;
}

/**
 * Audit Financial Statements
 */
async function auditFinancialStatements() {
  const result = {
    revenue: 0,
    expenses: 0,
    net_income: 0,
    gross_margin: 0,
    net_margin: 0,
    status: 'ok',
    issues: [],
  };
  
  try {
    // Get income invoices
    const incomeInvoices = await executeOdoo('account.move', 'search_read', [
      [['move_type', '=', 'out_invoice'], ['state', '=', 'posted']],
      ['amount_total', 'amount_untaxed', 'amount_tax', 'invoice_date'],
    ]);
    
    // Get expense bills
    const expenseBills = await executeOdoo('account.move', 'search_read', [
      [['move_type', '=', 'in_invoice'], ['state', '=', 'posted']],
      ['amount_total', 'amount_untaxed', 'amount_tax', 'invoice_date'],
    ]);
    
    result.revenue = incomeInvoices.reduce((sum, inv) => sum + (inv.amount_untaxed || 0), 0);
    result.expenses = expenseBills.reduce((sum, bill) => sum + (bill.amount_untaxed || 0), 0);
    result.net_income = result.revenue - result.expenses;
    
    if (result.revenue > 0) {
      result.gross_margin = ((result.revenue - result.expenses) / result.revenue * 100).toFixed(2);
      result.net_margin = result.gross_margin;
    }
    
    // Check for issues
    if (result.net_income < 0) {
      result.issues.push({
        type: 'warning',
        message: 'Operating at a loss',
        severity: 'high',
      });
    }
    
    result.status = result.issues.length > 0 ? 'warning' : 'ok';
  } catch (error) {
    result.status = 'error';
    result.error = error.message;
  }
  
  return result;
}

/**
 * Audit Accounts Receivable
 */
async function auditAccountsReceivable() {
  const result = {
    total_receivables: 0,
    total_outstanding: 0,
    overdue_amount: 0,
    customer_count: 0,
    aging: {
      current: 0,
      days_30: 0,
      days_60: 0,
      days_90: 0,
      over_90: 0,
    },
    top_debtors: [],
    status: 'ok',
    issues: [],
  };
  
  try {
    const invoices = await executeOdoo('account.move', 'search_read', [
      [['move_type', '=', 'out_invoice'], ['state', '=', 'posted'], ['payment_state', '!=', 'paid']],
      ['partner_id', 'amount_total', 'amount_due', 'invoice_date', 'invoice_date_due'],
    ], { order: 'invoice_date_due ASC' });
    
    result.total_receivables = invoices.reduce((sum, inv) => sum + (inv.amount_total || 0), 0);
    result.total_outstanding = invoices.reduce((sum, inv) => sum + (inv.amount_due || 0), 0);
    result.customer_count = new Set(invoices.map(inv => inv.partner_id?.[0])).size;
    
    const now = new Date();
    
    invoices.forEach(inv => {
      const dueDate = new Date(inv.invoice_date_due);
      const daysOverdue = Math.floor((now - dueDate) / (1000 * 60 * 60 * 24));
      const amount = inv.amount_due || 0;
      
      if (daysOverdue < 0) {
        result.aging.current += amount;
      } else if (daysOverdue < 30) {
        result.aging.days_30 += amount;
        result.overdue_amount += amount;
      } else if (daysOverdue < 60) {
        result.aging.days_60 += amount;
        result.overdue_amount += amount;
      } else if (daysOverdue < 90) {
        result.aging.days_90 += amount;
        result.overdue_amount += amount;
      } else {
        result.aging.over_90 += amount;
        result.overdue_amount += amount;
      }
    });
    
    // Get top debtors
    const debtorAmounts = {};
    invoices.forEach(inv => {
      const partnerId = inv.partner_id?.[0];
      const partnerName = inv.partner_id?.[1];
      if (partnerId) {
        debtorAmounts[partnerId] = { name: partnerName, amount: (debtorAmounts[partnerId]?.amount || 0) + (inv.amount_due || 0) };
      }
    });
    
    result.top_debtors = Object.entries(debtorAmounts)
      .map(([id, data]) => ({ id, ...data }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);
    
    // Check for issues
    if (result.overdue_amount > result.total_outstanding * 0.3) {
      result.issues.push({
        type: 'warning',
        message: 'Over 30% of receivables are overdue',
        severity: 'high',
      });
    }
    
    if (result.aging.over_90 > result.total_outstanding * 0.1) {
      result.issues.push({
        type: 'warning',
        message: 'Significant amount overdue by 90+ days',
        severity: 'high',
      });
    }
    
    result.status = result.issues.length > 0 ? 'warning' : 'ok';
  } catch (error) {
    result.status = 'error';
    result.error = error.message;
  }
  
  return result;
}

/**
 * Audit Accounts Payable
 */
async function auditAccountsPayable() {
  const result = {
    total_payables: 0,
    total_outstanding: 0,
    overdue_amount: 0,
    vendor_count: 0,
    aging: {
      current: 0,
      days_30: 0,
      days_60: 0,
      days_90: 0,
      over_90: 0,
    },
    top_vendors: [],
    status: 'ok',
    issues: [],
  };
  
  try {
    const bills = await executeOdoo('account.move', 'search_read', [
      [['move_type', '=', 'in_invoice'], ['state', '=', 'posted'], ['payment_state', '!=', 'paid']],
      ['partner_id', 'amount_total', 'amount_due', 'invoice_date', 'invoice_date_due'],
    ], { order: 'invoice_date_due ASC' });
    
    result.total_payables = bills.reduce((sum, bill) => sum + (bill.amount_total || 0), 0);
    result.total_outstanding = bills.reduce((sum, bill) => sum + (bill.amount_due || 0), 0);
    result.vendor_count = new Set(bills.map(bill => bill.partner_id?.[0])).size;
    
    const now = new Date();
    
    bills.forEach(bill => {
      const dueDate = new Date(bill.invoice_date_due);
      const daysOverdue = Math.floor((now - dueDate) / (1000 * 60 * 60 * 24));
      const amount = bill.amount_due || 0;
      
      if (daysOverdue < 0) {
        result.aging.current += amount;
      } else if (daysOverdue < 30) {
        result.aging.days_30 += amount;
        result.overdue_amount += amount;
      } else if (daysOverdue < 60) {
        result.aging.days_60 += amount;
        result.overdue_amount += amount;
      } else if (daysOverdue < 90) {
        result.aging.days_90 += amount;
        result.overdue_amount += amount;
      } else {
        result.aging.over_90 += amount;
        result.overdue_amount += amount;
      }
    });
    
    // Get top vendors
    const vendorAmounts = {};
    bills.forEach(bill => {
      const partnerId = bill.partner_id?.[0];
      const partnerName = bill.partner_id?.[1];
      if (partnerId) {
        vendorAmounts[partnerId] = { name: partnerName, amount: (vendorAmounts[partnerId]?.amount || 0) + (bill.amount_due || 0) };
      }
    });
    
    result.top_vendors = Object.entries(vendorAmounts)
      .map(([id, data]) => ({ id, ...data }))
      .sort((a, b) => b.amount - a.amount)
      .slice(0, 5);
    
    // Check for issues
    if (result.overdue_amount > result.total_outstanding * 0.2) {
      result.issues.push({
        type: 'warning',
        message: 'Over 20% of payables are overdue - risk of vendor relationship issues',
        severity: 'medium',
      });
    }
    
    result.status = result.issues.length > 0 ? 'warning' : 'ok';
  } catch (error) {
    result.status = 'error';
    result.error = error.message;
  }
  
  return result;
}

/**
 * Audit Bank Reconciliation
 */
async function auditBankReconciliation() {
  const result = {
    total_balance: 0,
    bank_accounts: [],
    unreconciled_items: 0,
    reconciliation_issues: [],
    status: 'ok',
  };
  
  try {
    const journals = await executeOdoo('account.journal', 'search_read', [
      [['type', '=', 'bank']],
      ['name', 'code'],
    ]);
    
    for (const journal of journals) {
      const statements = await executeOdoo('account.bank.statement', 'search_read', [
        [['journal_id', '=', journal.id]],
        ['name', 'balance', 'balance_end_real', 'line_ids'],
      ], { limit: 1, order: 'date DESC' });
      
      if (statements.length > 0) {
        const stmt = statements[0];
        result.bank_accounts.push({
          name: journal.name,
          code: journal.code,
          balance: stmt.balance || 0,
          statement_name: stmt.name,
        });
        result.total_balance += stmt.balance || 0;
      }
    }
    
    // Check for unreconciled items
    const unreconciled = await executeOdoo('account.bank.statement.line', 'search_read', [
      [['is_reconciled', '=', false]],
      ['name', 'amount', 'date'],
    ], { limit: 100 });
    
    result.unreconciled_items = unreconciled.length;
    
    if (unreconciled.length > 10) {
      result.reconciliation_issues.push({
        type: 'info',
        message: `${unreconciled.length} unreconciled bank items`,
        severity: 'low',
      });
    }
    
    result.status = result.reconciliation_issues.length > 0 ? 'warning' : 'ok';
  } catch (error) {
    result.status = 'error';
    result.error = error.message;
  }
  
  return result;
}

/**
 * Audit Tax Compliance
 */
async function auditTaxCompliance() {
  const result = {
    tax_collected: 0,
    tax_paid: 0,
    tax_payable: 0,
    filing_status: 'unknown',
    upcoming_deadlines: [],
    compliance_issues: [],
    status: 'ok',
  };
  
  try {
    // Get tax amounts from invoices
    const taxRecords = await executeOdoo('account.move.line', 'search_read', [
      [['tax_line_id', '!=', false], ['parent_state', '=', 'posted']],
      ['tax_line_id', 'balance', 'date'],
    ], { limit: 1000 });
    
    taxRecords.forEach(record => {
      if (record.balance > 0) {
        result.tax_collected += record.balance;
      } else {
        result.tax_paid += Math.abs(record.balance);
      }
    });
    
    result.tax_payable = result.tax_collected - result.tax_paid;
    
    // Check for potential issues
    if (result.tax_payable < 0) {
      result.compliance_issues.push({
        type: 'info',
        message: 'Tax credit position - may be eligible for refund',
        severity: 'low',
      });
    }
    
    result.filing_status = 'current';
    result.status = result.compliance_issues.length > 0 ? 'warning' : 'ok';
  } catch (error) {
    result.status = 'error';
    result.error = error.message;
  }
  
  return result;
}

/**
 * Detect Anomalies
 */
function detectAnomalies(sections) {
  const anomalies = [];
  
  // Check for unusual transactions
  if (sections.financial_statements?.revenue > 0) {
    const expenseRatio = sections.financial_statements.expenses / sections.financial_statements.revenue;
    if (expenseRatio > 0.9) {
      anomalies.push({
        type: 'financial',
        severity: 'high',
        title: 'High Expense Ratio',
        description: `Expenses are ${(expenseRatio * 100).toFixed(1)}% of revenue`,
        recommendation: 'Review expense categories and identify cost reduction opportunities',
      });
    }
  }
  
  // Check receivables aging
  if (sections.accounts_receivable?.aging?.over_90 > 0) {
    anomalies.push({
      type: 'receivables',
      severity: 'high',
      title: 'Significant Overdue Receivables',
      description: `$${sections.accounts_receivable.aging.over_90.toFixed(2)} overdue by 90+ days`,
      recommendation: 'Initiate collection proceedings for long-overdue accounts',
    });
  }
  
  // Check cash position
  if (sections.bank_reconciliation?.total_balance < sections.accounts_payable?.total_outstanding * 0.5) {
    anomalies.push({
      type: 'liquidity',
      severity: 'high',
      title: 'Low Cash Position',
      description: 'Cash balance is less than 50% of outstanding payables',
      recommendation: 'Review cash flow and consider arranging short-term financing',
    });
  }
  
  return anomalies;
}

/**
 * Generate Audit Recommendations
 */
function generateAuditRecommendations(audit) {
  const recommendations = [];
  
  // From financial statements
  if (audit.sections.financial_statements?.net_income < 0) {
    recommendations.push({
      priority: 'high',
      category: 'financial',
      title: 'Address Operating Loss',
      description: 'Business is operating at a loss. Review pricing strategy and cost structure.',
      actions: [
        'Analyze product/service profitability',
        'Review and negotiate vendor contracts',
        'Consider price adjustments for low-margin items',
      ],
    });
  }
  
  // From receivables
  if (audit.sections.accounts_receivable?.overdue_amount > 0) {
    recommendations.push({
      priority: 'high',
      category: 'cash_flow',
      title: 'Improve Collections',
      description: `Outstanding overdue amount: $${audit.sections.accounts_receivable.overdue_amount.toFixed(2)}`,
      actions: [
        'Send payment reminders to overdue customers',
        'Implement automated payment follow-ups',
        'Consider offering early payment discounts',
      ],
    });
  }
  
  // From anomalies
  audit.anomalies.forEach(anomaly => {
    if (anomaly.severity === 'high') {
      recommendations.push({
        priority: 'high',
        category: anomaly.type,
        title: anomaly.title,
        description: anomaly.description,
        actions: [anomaly.recommendation],
      });
    }
  });
  
  return recommendations;
}

/**
 * Determine Compliance Status
 */
function determineComplianceStatus(audit) {
  const issues = [
    ...(audit.sections.financial_statements?.issues || []),
    ...(audit.sections.accounts_receivable?.issues || []),
    ...(audit.sections.accounts_payable?.issues || []),
    ...(audit.sections.tax_compliance?.compliance_issues || []),
  ];
  
  const highSeverity = issues.filter(i => i.severity === 'high').length;
  const mediumSeverity = issues.filter(i => i.severity === 'medium').length;
  
  if (highSeverity > 0) {
    return { status: 'non_compliant', high_issues: highSeverity, medium_issues: mediumSeverity };
  } else if (mediumSeverity > 0) {
    return { status: 'partially_compliant', high_issues: highSeverity, medium_issues: mediumSeverity };
  }
  
  return { status: 'compliant', high_issues: 0, medium_issues: 0 };
}

/**
 * Generate Action Items
 */
function generateAccountingActionItems(audit) {
  const items = [];
  
  audit.recommendations.forEach((rec, index) => {
    items.push({
      id: index + 1,
      title: rec.title,
      priority: rec.priority,
      category: rec.category,
      due_date: new Date(Date.now() + (rec.priority === 'high' ? 1 : 3) * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      status: 'pending',
    });
  });
  
  return items;
}

// Odoo Connection Functions
async function connectToOdoo() {
  // Simplified connection - in production would use proper authentication
  odooSession = { uid: 2, userContext: { lang: 'en_US', tz: 'UTC' } };
  return odooSession;
}

async function executeOdoo(model, method, args = [], kwargs = {}) {
  // Mock implementation - in production would call actual Odoo API
  console.log(`[Accounting Audit] Executing: ${model}.${method}`, args);
  return [];
}

// Helper Functions
function getPeriodDates(period) {
  const now = new Date();
  let start = new Date(now);
  
  switch (period) {
    case 'daily':
      start.setDate(start.getDate() - 1);
      break;
    case 'weekly':
      start.setDate(start.getDate() - 7);
      break;
    case 'monthly':
      start.setMonth(start.getMonth() - 1);
      break;
    case 'quarterly':
      start.setMonth(start.getMonth() - 3);
      break;
    case 'yearly':
      start.setFullYear(start.getFullYear() - 1);
      break;
  }
  
  return {
    start: start.toISOString().split('T')[0],
    end: now.toISOString().split('T')[0],
  };
}

function logAudit(action, details) {
  const logEntry = {
    timestamp: new Date().toISOString(),
    service: 'accounting-audit',
    action,
    details,
  };
  
  const logFile = path.join(LOGS_DIR, 'accounting-audit.jsonl');
  try {
    fs.appendFileSync(logFile, JSON.stringify(logEntry) + '\n');
  } catch (e) {
    console.error('[Accounting Audit] Failed to write log:', e.message);
  }
}

// Export as skill
module.exports = {
  runAccountingAudit,
  generateAccountingSummary,
  auditFinancialStatements,
  auditAccountsReceivable,
  auditAccountsPayable,
  auditBankReconciliation,
  auditTaxCompliance,
};
