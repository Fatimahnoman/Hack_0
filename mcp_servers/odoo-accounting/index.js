/**
 * Odoo Accounting MCP Server
 * 
 * Integrates with Odoo 19 Community Edition via JSON-RPC API
 * Provides accounting operations: invoices, bills, payments, reports
 */

const http = require('http');

// Odoo Configuration
const ODOO_CONFIG = {
  url: process.env.ODOO_URL || 'http://localhost:8069',
  db: process.env.ODOO_DB || 'odoo',
  username: process.env.ODOO_USERNAME || 'admin',
  password: process.env.ODOO_PASSWORD || 'admin',
};

// MCP Server Configuration
const MCP_CONFIG = {
  name: 'odoo-accounting',
  version: '1.0.0',
  description: 'Odoo Accounting Integration via JSON-RPC API',
};

// Store for Odoo session
let odooSession = {
  uid: null,
  userContext: null,
};

/**
 * Make JSON-RPC call to Odoo
 */
async function callOdoo(method, params) {
  return new Promise((resolve, reject) => {
    const payload = {
      jsonrpc: '2.0',
      method: 'call',
      params: params,
      id: Math.floor(Math.random() * 1000000),
    };

    const url = new URL(ODOO_CONFIG.url);
    const options = {
      hostname: url.hostname,
      port: url.port || 8069,
      path: '/jsonrpc',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.error) {
            reject(new Error(response.error.data.message));
          } else {
            resolve(response.result);
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    req.write(JSON.stringify(payload));
    req.end();
  });
}

/**
 * Authenticate with Odoo
 */
async function authenticate() {
  try {
    const result = await callOdoo('call', {
      service: 'common',
      method: 'authenticate',
      args: [
        ODOO_CONFIG.db,
        ODOO_CONFIG.username,
        ODOO_CONFIG.password,
        {},
      ],
    });
    
    odooSession.uid = result.uid;
    odooSession.userContext = result.user_context;
    return result;
  } catch (error) {
    console.error('Odoo authentication failed:', error.message);
    throw error;
  }
}

/**
 * Execute Odoo model method
 */
async function execute(model, method, args = [], kwargs = {}) {
  if (!odooSession.uid) {
    await authenticate();
  }

  return callOdoo('call', {
    service: 'object',
    method: 'execute_kwargs',
    args: [
      ODOO_CONFIG.db,
      odooSession.uid,
      ODOO_CONFIG.password,
      model,
      method,
      args,
      kwargs,
    ],
  });
}

// ============================================================================
// MCP Tool Handlers
// ============================================================================

/**
 * Create a new customer invoice
 */
async function createInvoice(invoiceData) {
  const invoice = {
    move_type: 'out_invoice',
    partner_id: invoiceData.partner_id,
    invoice_date: invoiceData.invoice_date || new Date().toISOString().split('T')[0],
    invoice_line_ids: [],
  };

  if (invoiceData.lines) {
    invoice.invoice_line_ids = invoiceData.lines.map((line, index) => [
      0,
      index,
      {
        product_id: line.product_id,
        name: line.name || 'Product',
        quantity: line.quantity || 1,
        price_unit: line.price_unit || 0,
      },
    ]);
  }

  const invoiceId = await execute('account.move', 'create', [invoice]);
  return { success: true, invoice_id: invoiceId, message: 'Invoice created successfully' };
}

/**
 * Get invoice by ID
 */
async function getInvoice(invoiceId) {
  const invoices = await execute('account.move', 'search_read', [
    [['id', '=', invoiceId]],
    ['name', 'partner_id', 'invoice_date', 'amount_total', 'amount_due', 'state'],
  ]);
  return invoices[0] || null;
}

/**
 * List all invoices with optional filters
 */
async function listInvoices(filters = {}) {
  const domain = [['move_type', 'in', ['out_invoice', 'out_refund']]];
  
  if (filters.partner_id) {
    domain.push(['partner_id', '=', filters.partner_id]);
  }
  if (filters.state) {
    domain.push(['state', '=', filters.state]);
  }
  if (filters.date_from) {
    domain.push(['invoice_date', '>=', filters.date_from]);
  }
  if (filters.date_to) {
    domain.push(['invoice_date', '<=', filters.date_to]);
  }

  const invoices = await execute('account.move', 'search_read', [
    domain,
    ['name', 'partner_id', 'invoice_date', 'amount_total', 'amount_due', 'state', 'payment_state'],
  ], {
    limit: filters.limit || 50,
    offset: filters.offset || 0,
  });

  return invoices;
}

/**
 * Confirm/post an invoice
 */
async function confirmInvoice(invoiceId) {
  await execute('account.move', 'action_post', [[invoiceId]]);
  return { success: true, message: 'Invoice confirmed' };
}

/**
 * Register payment for an invoice
 */
async function registerPayment(invoiceId, paymentData) {
  const payment = {
    move_id: invoiceId,
    payment_type: 'inbound',
    partner_type: 'customer',
    amount: paymentData.amount,
    date: paymentData.date || new Date().toISOString().split('T')[0],
  };

  const paymentId = await execute('account.payment', 'create', [payment]);
  await execute('account.payment', 'action_post', [[paymentId]]);
  
  return { success: true, payment_id: paymentId, message: 'Payment registered' };
}

/**
 * Create vendor bill
 */
async function createBill(billData) {
  const bill = {
    move_type: 'in_invoice',
    partner_id: billData.partner_id,
    invoice_date: billData.invoice_date || new Date().toISOString().split('T')[0],
    invoice_line_ids: [],
  };

  if (billData.lines) {
    bill.invoice_line_ids = billData.lines.map((line, index) => [
      0,
      index,
      {
        product_id: line.product_id,
        name: line.name || 'Product',
        quantity: line.quantity || 1,
        price_unit: line.price_unit || 0,
      },
    ]);
  }

  const billId = await execute('account.move', 'create', [bill]);
  return { success: true, bill_id: billId, message: 'Vendor bill created successfully' };
}

/**
 * List vendor bills
 */
async function listBills(filters = {}) {
  const domain = [['move_type', '=', 'in_invoice']];
  
  if (filters.partner_id) {
    domain.push(['partner_id', '=', filters.partner_id]);
  }
  if (filters.state) {
    domain.push(['state', '=', filters.state]);
  }

  const bills = await execute('account.move', 'search_read', [
    domain,
    ['name', 'partner_id', 'invoice_date', 'amount_total', 'amount_due', 'state'],
  ], {
    limit: filters.limit || 50,
  });

  return bills;
}

/**
 * Get accounting dashboard summary
 */
async function getDashboardSummary() {
  // Get total receivables
  const receivables = await execute('account.move', 'search_read', [
    [['move_type', '=', 'out_invoice'], ['payment_state', '!=', 'paid']],
    ['amount_total', 'amount_due'],
  ]);

  // Get total payables
  const payables = await execute('account.move', 'search_read', [
    [['move_type', '=', 'in_invoice'], ['payment_state', '!=', 'paid']],
    ['amount_total', 'amount_due'],
  ]);

  const totalReceivables = receivables.reduce((sum, inv) => sum + (inv.amount_due || 0), 0);
  const totalPayables = payables.reduce((sum, bill) => sum + (bill.amount_due || 0), 0);

  // Get recent invoices
  const recentInvoices = await execute('account.move', 'search_read', [
    [['move_type', '=', 'out_invoice']],
    ['name', 'partner_id', 'invoice_date', 'amount_total', 'state'],
  ], {
    limit: 10,
    order: 'invoice_date DESC',
  });

  return {
    total_receivables: totalReceivables,
    total_payables: totalPayables,
    cash_flow: totalReceivables - totalPayables,
    recent_invoices: recentInvoices,
    currency: 'USD',
  };
}

/**
 * Get partner (customer/vendor) list
 */
async function listPartners(filters = {}) {
  const domain = [];
  
  if (filters.customer) {
    domain.push(['customer_rank', '>', 0]);
  }
  if (filters.supplier) {
    domain.push(['supplier_rank', '>', 0]);
  }

  const partners = await execute('res.partner', 'search_read', [
    domain,
    ['name', 'email', 'phone', 'customer_rank', 'supplier_rank'],
  ], {
    limit: filters.limit || 50,
  });

  return partners;
}

/**
 * Create a new partner
 */
async function createPartner(partnerData) {
  const partner = {
    name: partnerData.name,
    email: partnerData.email,
    phone: partnerData.phone,
    customer_rank: partnerData.is_customer ? 1 : 0,
    supplier_rank: partnerData.is_supplier ? 1 : 0,
  };

  const partnerId = await execute('res.partner', 'create', [partner]);
  return { success: true, partner_id: partnerId, message: 'Partner created successfully' };
}

/**
 * Get product list
 */
async function listProducts(filters = {}) {
  const products = await execute('product.template', 'search_read', [
    [],
    ['name', 'list_price', 'standard_price', 'type'],
  ], {
    limit: filters.limit || 50,
  });

  return products;
}

/**
 * Create accounting report
 */
async function generateReport(reportType, filters = {}) {
  const dateFrom = filters.date_from || new Date(new Date().getFullYear(), 0, 1).toISOString().split('T')[0];
  const dateTo = filters.date_to || new Date().toISOString().split('T')[0];

  switch (reportType) {
    case 'aged_receivable':
      return await generateAgedReceivable(dateFrom, dateTo);
    case 'aged_payable':
      return await generateAgedPayable(dateFrom, dateTo);
    case 'income_statement':
      return await generateIncomeStatement(dateFrom, dateTo);
    default:
      throw new Error(`Unknown report type: ${reportType}`);
  }
}

async function generateAgedReceivable(dateFrom, dateTo) {
  const invoices = await execute('account.move', 'search_read', [
    [['move_type', '=', 'out_invoice'], ['state', '=', 'posted']],
    ['partner_id', 'amount_total', 'amount_due', 'invoice_date'],
  ]);

  const aged = {};
  const now = new Date();

  invoices.forEach(inv => {
    const partner = inv.partner_id[1];
    if (!aged[partner]) {
      aged[partner] = { current: 0, '30_days': 0, '60_days': 0, '90_days': 0, 'over_90': 0 };
    }

    const invoiceDate = new Date(inv.invoice_date);
    const daysOverdue = Math.floor((now - invoiceDate) / (1000 * 60 * 60 * 24));
    const amount = inv.amount_due || 0;

    if (daysOverdue < 0) {
      aged[partner].current += amount;
    } else if (daysOverdue < 30) {
      aged[partner]['30_days'] += amount;
    } else if (daysOverdue < 60) {
      aged[partner]['60_days'] += amount;
    } else if (daysOverdue < 90) {
      aged[partner]['90_days'] += amount;
    } else {
      aged[partner]['over_90'] += amount;
    }
  });

  return { report_type: 'aged_receivable', data: aged, generated_at: new Date().toISOString() };
}

async function generateAgedPayable(dateFrom, dateTo) {
  const bills = await execute('account.move', 'search_read', [
    [['move_type', '=', 'in_invoice'], ['state', '=', 'posted']],
    ['partner_id', 'amount_total', 'amount_due', 'invoice_date'],
  ]);

  const aged = {};
  const now = new Date();

  bills.forEach(bill => {
    const partner = bill.partner_id[1];
    if (!aged[partner]) {
      aged[partner] = { current: 0, '30_days': 0, '60_days': 0, '90_days': 0, 'over_90': 0 };
    }

    const billDate = new Date(bill.invoice_date);
    const daysOverdue = Math.floor((now - billDate) / (1000 * 60 * 60 * 24));
    const amount = bill.amount_due || 0;

    if (daysOverdue < 0) {
      aged[partner].current += amount;
    } else if (daysOverdue < 30) {
      aged[partner]['30_days'] += amount;
    } else if (daysOverdue < 60) {
      aged[partner]['60_days'] += amount;
    } else if (daysOverdue < 90) {
      aged[partner]['90_days'] += amount;
    } else {
      aged[partner]['over_90'] += amount;
    }
  });

  return { report_type: 'aged_payable', data: aged, generated_at: new Date().toISOString() };
}

async function generateIncomeStatement(dateFrom, dateTo) {
  // Simplified income statement
  const income = await execute('account.move', 'search_read', [
    [['move_type', '=', 'out_invoice'], ['state', '=', 'posted'], ['invoice_date', '>=', dateFrom], ['invoice_date', '<=', dateTo]],
    ['amount_total'],
  ]);

  const expenses = await execute('account.move', 'search_read', [
    [['move_type', '=', 'in_invoice'], ['state', '=', 'posted'], ['invoice_date', '>=', dateFrom], ['invoice_date', '<=', dateTo]],
    ['amount_total'],
  ]);

  const totalIncome = income.reduce((sum, inv) => sum + (inv.amount_total || 0), 0);
  const totalExpenses = expenses.reduce((sum, bill) => sum + (bill.amount_total || 0), 0);

  return {
    report_type: 'income_statement',
    period: { from: dateFrom, to: dateTo },
    total_income: totalIncome,
    total_expenses: totalExpenses,
    net_income: totalIncome - totalExpenses,
    generated_at: new Date().toISOString(),
  };
}

// ============================================================================
// MCP Server Implementation
// ============================================================================

const TOOLS = [
  {
    name: 'odoo_create_invoice',
    description: 'Create a new customer invoice in Odoo',
    inputSchema: {
      type: 'object',
      properties: {
        partner_id: { type: 'integer', description: 'Customer ID' },
        invoice_date: { type: 'string', description: 'Invoice date (YYYY-MM-DD)' },
        lines: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              product_id: { type: 'integer' },
              name: { type: 'string' },
              quantity: { type: 'number' },
              price_unit: { type: 'number' },
            },
          },
        },
      },
      required: ['partner_id'],
    },
  },
  {
    name: 'odoo_get_invoice',
    description: 'Get invoice details by ID',
    inputSchema: {
      type: 'object',
      properties: {
        invoice_id: { type: 'integer', description: 'Invoice ID' },
      },
      required: ['invoice_id'],
    },
  },
  {
    name: 'odoo_list_invoices',
    description: 'List invoices with optional filters',
    inputSchema: {
      type: 'object',
      properties: {
        partner_id: { type: 'integer' },
        state: { type: 'string' },
        date_from: { type: 'string' },
        date_to: { type: 'string' },
        limit: { type: 'integer' },
      },
    },
  },
  {
    name: 'odoo_confirm_invoice',
    description: 'Confirm/post an invoice',
    inputSchema: {
      type: 'object',
      properties: {
        invoice_id: { type: 'integer', description: 'Invoice ID' },
      },
      required: ['invoice_id'],
    },
  },
  {
    name: 'odoo_register_payment',
    description: 'Register payment for an invoice',
    inputSchema: {
      type: 'object',
      properties: {
        invoice_id: { type: 'integer', description: 'Invoice ID' },
        amount: { type: 'number', description: 'Payment amount' },
        date: { type: 'string', description: 'Payment date (YYYY-MM-DD)' },
      },
      required: ['invoice_id', 'amount'],
    },
  },
  {
    name: 'odoo_create_bill',
    description: 'Create a new vendor bill',
    inputSchema: {
      type: 'object',
      properties: {
        partner_id: { type: 'integer', description: 'Vendor ID' },
        invoice_date: { type: 'string' },
        lines: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              product_id: { type: 'integer' },
              name: { type: 'string' },
              quantity: { type: 'number' },
              price_unit: { type: 'number' },
            },
          },
        },
      },
      required: ['partner_id'],
    },
  },
  {
    name: 'odoo_list_bills',
    description: 'List vendor bills',
    inputSchema: {
      type: 'object',
      properties: {
        partner_id: { type: 'integer' },
        state: { type: 'string' },
        limit: { type: 'integer' },
      },
    },
  },
  {
    name: 'odoo_dashboard',
    description: 'Get accounting dashboard summary',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'odoo_list_partners',
    description: 'List customers and vendors',
    inputSchema: {
      type: 'object',
      properties: {
        customer: { type: 'boolean' },
        supplier: { type: 'boolean' },
        limit: { type: 'integer' },
      },
    },
  },
  {
    name: 'odoo_create_partner',
    description: 'Create a new customer or vendor',
    inputSchema: {
      type: 'object',
      properties: {
        name: { type: 'string', description: 'Partner name' },
        email: { type: 'string' },
        phone: { type: 'string' },
        is_customer: { type: 'boolean' },
        is_supplier: { type: 'boolean' },
      },
      required: ['name'],
    },
  },
  {
    name: 'odoo_list_products',
    description: 'List products',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer' },
      },
    },
  },
  {
    name: 'odoo_generate_report',
    description: 'Generate accounting report',
    inputSchema: {
      type: 'object',
      properties: {
        report_type: { type: 'string', enum: ['aged_receivable', 'aged_payable', 'income_statement'] },
        date_from: { type: 'string' },
        date_to: { type: 'string' },
      },
      required: ['report_type'],
    },
  },
];

async function handleToolCall(name, args) {
  try {
    console.log(`[Odoo MCP] Calling tool: ${name}`, args);

    switch (name) {
      case 'odoo_create_invoice':
        return await createInvoice(args);
      case 'odoo_get_invoice':
        return await getInvoice(args.invoice_id);
      case 'odoo_list_invoices':
        return await listInvoices(args);
      case 'odoo_confirm_invoice':
        return await confirmInvoice(args.invoice_id);
      case 'odoo_register_payment':
        return await registerPayment(args.invoice_id, args);
      case 'odoo_create_bill':
        return await createBill(args);
      case 'odoo_list_bills':
        return await listBills(args);
      case 'odoo_dashboard':
        return await getDashboardSummary();
      case 'odoo_list_partners':
        return await listPartners(args);
      case 'odoo_create_partner':
        return await createPartner(args);
      case 'odoo_list_products':
        return await listProducts(args);
      case 'odoo_generate_report':
        return await generateReport(args.report_type, args);
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error) {
    console.error(`[Odoo MCP] Error in ${name}:`, error.message);
    throw error;
  }
}

// MCP Protocol Handler
async function handleRequest(request) {
  const { method, params, id } = request;

  try {
    if (method === 'initialize') {
      return {
        jsonrpc: '2.0',
        id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: {
            tools: {},
          },
          serverInfo: MCP_CONFIG,
        },
      };
    }

    if (method === 'tools/list') {
      return {
        jsonrpc: '2.0',
        id,
        result: { tools: TOOLS },
      };
    }

    if (method === 'tools/call') {
      const result = await handleToolCall(params.name, params.arguments || {});
      return {
        jsonrpc: '2.0',
        id,
        result: {
          content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
        },
      };
    }

    if (method === 'ping') {
      return { jsonrpc: '2.0', id, result: {} };
    }

    return {
      jsonrpc: '2.0',
      id,
      error: { code: -32601, message: 'Method not found' },
    };
  } catch (error) {
    return {
      jsonrpc: '2.0',
      id,
      error: { code: -32603, message: error.message },
    };
  }
}

// Main server loop
async function main() {
  console.log('[Odoo Accounting MCP] Starting server...');
  console.log('[Odoo Accounting MCP] Odoo URL:', ODOO_CONFIG.url);

  // Test connection
  try {
    await authenticate();
    console.log('[Odoo Accounting MCP] Connected to Odoo successfully');
    console.log('[Odoo Accounting MCP] User ID:', odooSession.uid);
  } catch (error) {
    console.warn('[Odoo Accounting MCP] Initial connection failed, will retry on first request:', error.message);
  }

  // Read from stdin for MCP protocol
  process.stdin.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    
    for (const line of lines) {
      try {
        const request = JSON.parse(line);
        handleRequest(request).then((response) => {
          process.stdout.write(JSON.stringify(response) + '\n');
        });
      } catch (error) {
        console.error('[Odoo MCP] Error parsing request:', error.message);
      }
    }
  });

  console.log('[Odoo Accounting MCP] Server ready');
}

main().catch(console.error);
