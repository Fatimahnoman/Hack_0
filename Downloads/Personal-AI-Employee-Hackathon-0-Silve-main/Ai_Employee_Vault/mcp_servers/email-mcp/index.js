/**
 * Email MCP Server - Silver Tier
 * ===============================
 * MCP server for drafting and sending emails via Gmail API.
 * 
 * Features:
 * - Draft emails: Save drafts as .md files in /Plans
 * - Send emails: Only after HITL (Human-In-The-Loop) approval
 * - Gmail API integration with OAuth2
 * 
 * Install: npm install
 * Run: node mcp_servers/email-mcp/index.js
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
    CallToolRequestSchema,
    ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');
const { readFileSync, writeFileSync, mkdirSync, existsSync } = require('fs');
const { join, dirname } = require('path');
const { google } = require('googleapis');
const { authenticate } = require('@google-cloud/local-auth');

// Configuration
const PROJECT_ROOT = dirname(dirname(dirname(__dirname)));
const CREDENTIALS_FILE = join(PROJECT_ROOT, 'credentials.json');
const TOKEN_FILE = join(PROJECT_ROOT, 'token.json');
const PLANS_FOLDER = join(PROJECT_ROOT, 'Plans');
const PENDING_APPROVAL_FOLDER = join(PROJECT_ROOT, 'Pending_Approval');
const DONE_FOLDER = join(PROJECT_ROOT, 'Done');
const COMPANY_HANDBOOK = join(PROJECT_ROOT, 'Company_Handbook.md');

// Gmail API scopes
const SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.drafts'];

// Ensure directories exist
function ensureDirectories() {
    [PLANS_FOLDER, PENDING_APPROVAL_FOLDER, DONE_FOLDER].forEach(folder => {
        if (!existsSync(folder)) {
            mkdirSync(folder, { recursive: true });
        }
    });
}

// Load company rules
function loadCompanyRules() {
    let rules = { polite: true, approvalRequired: true };
    if (existsSync(COMPANY_HANDBOOK)) {
        const content = readFileSync(COMPANY_HANDBOOK, 'utf-8').toLowerCase();
        rules.polite = content.includes('polite');
        rules.approvalRequired = content.includes('approval');
    }
    return rules;
}

// Gmail API client
let gmailClient = null;

async function getGmailClient() {
    if (gmailClient) {
        return gmailClient;
    }

    if (!existsSync(CREDENTIALS_FILE)) {
        throw new Error(`credentials.json not found at ${CREDENTIALS_FILE}. Please download from Google Cloud Console.`);
    }

    try {
        const auth = await authenticate({
            keyfilePath: CREDENTIALS_FILE,
            scopes: SCOPES,
        });
        gmailClient = google.gmail({ version: 'v1', auth });
        return gmailClient;
    } catch (error) {
        throw new Error(`Gmail authentication failed: ${error.message}`);
    }
}

// Create email draft as .md file
function createEmailDraft(to, subject, body, cc = '', bcc = '') {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `email_draft_${timestamp}.md`;
    const filepath = join(PLANS_FOLDER, filename);

    const companyRules = loadCompanyRules();
    
    // Ensure polite language
    let politeBody = body;
    if (companyRules.polite) {
        // Add polite greeting if missing
        if (!politeBody.match(/^(dear|hello|hi|greetings|good morning|good afternoon)/i)) {
            politeBody = `Hello,\n\n${politeBody}`;
        }
        // Add polite closing if missing
        if (!politeBody.match(/(best regards|sincerely|thank you|thanks|kind regards)/i)) {
            politeBody = `${politeBody}\n\nBest regards`;
        }
    }

    const draftContent = `---
type: email_draft
to: ${to}
cc: ${cc}
bcc: ${bcc}
subject: ${subject}
created: ${new Date().toISOString()}
status: draft
hitl_approval: required
---

# Email Draft

## Recipients
- **To:** ${to}
- **CC:** ${cc || 'None'}
- **BCC:** ${bcc || 'None'}

## Subject
${subject}

## Body

${politeBody}

---

## Approval Status
- [ ] Draft reviewed
- [ ] Content verified
- [ ] HITL approval granted
- [ ] Ready to send

---
*Created by Email MCP Server - Requires HITL Approval Before Sending*
`;

    writeFileSync(filepath, draftContent, 'utf-8');
    return { filepath, filename };
}

// Move draft to pending approval
function moveToApproval(draftPath) {
    const filename = draftPath.split(/[\\/]/).pop();
    const approvalPath = join(PENDING_APPROVAL_FOLDER, filename);
    
    // Copy to pending approval
    const content = readFileSync(draftPath, 'utf-8');
    writeFileSync(approvalPath, content, 'utf-8');
    
    return approvalPath;
}

// Send email via Gmail API
async function sendEmail(to, subject, body, cc = '', bcc = '') {
    const gmail = await getGmailClient();
    
    // Create MIME message
    const mimeMessage = [
        `To: ${to}`,
        `From: me`,
        cc ? `Cc: ${cc}` : '',
        `Subject: ${subject}`,
        'MIME-Version: 1.0',
        'Content-Type: text/plain; charset=utf-8',
        '',
        body
    ].filter(line => line).join('\n');

    const encodedMessage = Buffer.from(mimeMessage)
        .toString('base64')
        .replace(/\+/g, '-')
        .replace(/\//g, '_')
        .replace(/=+$/, '');

    const response = await gmail.users.messages.send({
        userId: 'me',
        requestBody: {
            raw: encodedMessage
        }
    });

    return {
        messageId: response.data.id,
        threadId: response.data.threadId,
        sentAt: new Date().toISOString()
    };
}

// Create sent email record
function createSentRecord(to, subject, body, sendResult) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
    const filename = `email_sent_${timestamp}.md`;
    const filepath = join(DONE_FOLDER, filename);

    const recordContent = `---
type: email_sent
to: ${to}
subject: ${subject}
sent_at: ${sendResult.sentAt}
gmail_message_id: ${sendResult.messageId}
gmail_thread_id: ${sendResult.threadId}
status: sent
---

# Sent Email Record

## Recipients
- **To:** ${to}

## Subject
${subject}

## Body

${body}

---
*Sent by Email MCP Server on ${new Date(sendResult.sentAt).toLocaleString()}*
`;

    writeFileSync(filepath, recordContent, 'utf-8');
    return { filepath, filename };
}

// MCP Server instance
const server = new Server(
    {
        name: 'email-mcp-server',
        version: '1.0.0',
    },
    {
        capabilities: {
            tools: {},
        },
    }
);

// List available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
        tools: [
            {
                name: 'draft_email',
                description: 'Create an email draft and save as .md file in /Plans. Requires HITL approval before sending.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: {
                            type: 'string',
                            description: 'Recipient email address'
                        },
                        subject: {
                            type: 'string',
                            description: 'Email subject line'
                        },
                        body: {
                            type: 'string',
                            description: 'Email body content'
                        },
                        cc: {
                            type: 'string',
                            description: 'CC recipients (optional)',
                            default: ''
                        },
                        bcc: {
                            type: 'string',
                            description: 'BCC recipients (optional)',
                            default: ''
                        }
                    },
                    required: ['to', 'subject', 'body']
                }
            },
            {
                name: 'send_email',
                description: 'Send an email via Gmail API. Use only after HITL approval has been granted.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        to: {
                            type: 'string',
                            description: 'Recipient email address'
                        },
                        subject: {
                            type: 'string',
                            description: 'Email subject line'
                        },
                        body: {
                            type: 'string',
                            description: 'Email body content'
                        },
                        cc: {
                            type: 'string',
                            description: 'CC recipients (optional)',
                            default: ''
                        },
                        bcc: {
                            type: 'string',
                            description: 'BCC recipients (optional)',
                            default: ''
                        },
                        approval_confirmed: {
                            type: 'boolean',
                            description: 'Confirm that HITL approval has been granted'
                        }
                    },
                    required: ['to', 'subject', 'body', 'approval_confirmed']
                }
            },
            {
                name: 'approve_and_send',
                description: 'Approve a draft email and send it. Moves draft from Pending_Approval to Done.',
                inputSchema: {
                    type: 'object',
                    properties: {
                        draft_filename: {
                            type: 'string',
                            description: 'Name of the draft file in Pending_Approval'
                        }
                    },
                    required: ['draft_filename']
                }
            }
        ]
    };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
        ensureDirectories();

        switch (name) {
            case 'draft_email': {
                const { to, subject, body, cc = '', bcc = '' } = args;
                
                // Create draft
                const { filepath, filename } = createEmailDraft(to, subject, body, cc, bcc);
                
                // Move to pending approval
                const approvalPath = moveToApproval(filepath);
                
                return {
                    content: [
                        {
                            type: 'text',
                            text: `✅ Email draft created and moved to Pending_Approval\n\n` +
                                `📝 Draft: ${filepath}\n` +
                                `⚠️ Pending Approval: ${approvalPath}\n\n` +
                                `**Next Steps:**\n` +
                                `1. Review draft in Pending_Approval folder\n` +
                                `2. Edit if needed\n` +
                                `3. Use approve_and_send tool or send_email with approval_confirmed=true`
                        }
                    ]
                };
            }

            case 'send_email': {
                const { to, subject, body, cc = '', bcc = '', approval_confirmed } = args;
                
                if (!approval_confirmed) {
                    throw new Error('HITL approval not confirmed. Please review draft and set approval_confirmed=true');
                }
                
                // Send email
                const sendResult = await sendEmail(to, subject, body, cc, bcc);
                
                // Create sent record
                const { filepath, filename } = createSentRecord(to, subject, body, sendResult);
                
                return {
                    content: [
                        {
                            type: 'text',
                            text: `✅ Email sent successfully!\n\n` +
                                `📧 Message ID: ${sendResult.messageId}\n` +
                                `🔗 Thread ID: ${sendResult.threadId}\n` +
                                `📅 Sent: ${new Date(sendResult.sentAt).toLocaleString()}\n` +
                                `📁 Record: ${filepath}`
                        }
                    ]
                };
            }

            case 'approve_and_send': {
                const { draft_filename } = args;
                
                // Read draft file
                const draftPath = join(PENDING_APPROVAL_FOLDER, draft_filename);
                if (!existsSync(draftPath)) {
                    throw new Error(`Draft file not found: ${draftPath}`);
                }
                
                const draftContent = readFileSync(draftPath, 'utf-8');
                
                // Parse YAML frontmatter (simple parsing)
                const yamlMatch = draftContent.match(/^---\n([\s\S]*?)\n---/);
                if (!yamlMatch) {
                    throw new Error('Invalid draft format: missing YAML frontmatter');
                }
                
                const yamlContent = yamlMatch[1];
                const to = yamlContent.match(/to:\s*(.+)/)?.[1]?.trim();
                const subject = yamlContent.match(/subject:\s*(.+)/)?.[1]?.trim();
                
                // Extract body (after second ---)
                const bodyMatch = draftContent.match(/## Body\n\n([\s\S]*?)\n---\n## Approval/);
                const body = bodyMatch ? bodyMatch[1].trim() : 'Email body not found';
                
                if (!to || !subject) {
                    throw new Error('Could not parse recipient or subject from draft');
                }
                
                // Send email
                const sendResult = await sendEmail(to, subject, body);
                
                // Create sent record
                const { filepath, filename: sentFilename } = createSentRecord(to, subject, body, sendResult);
                
                return {
                    content: [
                        {
                            type: 'text',
                            text: `✅ Draft approved and email sent!\n\n` +
                                `📧 Message ID: ${sendResult.messageId}\n` +
                                `📁 Sent Record: ${filepath}\n` +
                                `📋 Original Draft: ${draftPath}`
                        }
                    ]
                };
            }

            default:
                throw new Error(`Unknown tool: ${name}`);
        }
    } catch (error) {
        return {
            content: [
                {
                    type: 'text',
                    text: `❌ Error: ${error.message}`
                }
            ],
            isError: true
        };
    }
});

// Start server
async function main() {
    console.error('Email MCP Server starting...');
    console.error(`Project Root: ${PROJECT_ROOT}`);
    console.error(`Credentials: ${CREDENTIALS_FILE}`);
    console.error(`Plans Folder: ${PLANS_FOLDER}`);
    console.error(`Pending Approval: ${PENDING_APPROVAL_FOLDER}`);
    console.error(`Done Folder: ${DONE_FOLDER}`);
    console.error('---');
    
    ensureDirectories();
    
    // Check for credentials
    if (!existsSync(CREDENTIALS_FILE)) {
        console.error(`⚠️  WARNING: credentials.json not found at ${CREDENTIALS_FILE}`);
        console.error('   Please download from Google Cloud Console and place in project root.');
        console.error('   Draft functionality will work, but sending requires authentication.');
    }
    
    const transport = new StdioServerTransport();
    await server.connect(transport);
    
    console.error('Email MCP Server running on stdio');
    console.error('Available tools: draft_email, send_email, approve_and_send');
}

main().catch((error) => {
    console.error('Fatal error:', error);
    process.exit(1);
});
