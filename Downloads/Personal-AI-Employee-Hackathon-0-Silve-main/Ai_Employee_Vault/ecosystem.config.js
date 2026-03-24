/**
 * PM2 Ecosystem Configuration for Watchers + Orchestrator
 * ========================================================
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only gmail_watcher
 *   pm2 stop ecosystem.config.js
 *   pm2 restart ecosystem.config.js
 *   pm2 delete ecosystem.config.js
 *
 * Watchers:
 *   - gmail_watcher: Monitors Gmail for important emails → saves to Inbox/
 *   - filesystem_watcher: Monitors Inbox folder for new files
 *   - whatsapp_watcher_simple: Monitors WhatsApp messages (file-based)
 *
 * Processors:
 *   - workflow_processor: Moves files Inbox → Needs_Action → Plans
 *   - orchestrator_agent: Auto-replies to approved emails
 *
 * Workflow:
 *   1. Gmail → Inbox/
 *   2. Workflow Processor → Needs_Action/ (if important)
 *   3. User reviews → Plans/
 *   4. User → Pending_Approval/
 *   5. User approves → Approved/
 *   6. Orchestrator sends reply → Done/
 *
 * NOTE:
 * - WhatsApp watcher (Playwright-based) requires Python 3.11/3.12
 * - Use whatsapp_watcher_simple.py as alternative for Python 3.14
 */

module.exports = {
  apps: [
    {
      name: 'gmail_watcher',
      script: 'Silver_Tier/watchers/gmail_watcher.py',
      interpreter: 'python',
      interpreter_args: '-u',  // Unbuffered output for real-time logs
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/gmail_watcher-error.log',
      out_file: './logs/pm2/gmail_watcher-out.log',
      log_file: './logs/pm2/gmail_watcher-combined.log',
      time: true,
      merge_logs: true,
    },
    {
      name: 'filesystem_watcher',
      script: 'Bronze_Tier/watchers/filesystem_watcher.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/filesystem_watcher-error.log',
      out_file: './logs/pm2/filesystem_watcher-out.log',
      log_file: './logs/pm2/filesystem_watcher-combined.log',
      time: true,
      merge_logs: true,
    },
    {
      name: 'whatsapp_watcher_simple',
      script: 'Silver_Tier/watchers/whatsapp_watcher_simple.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/whatsapp_watcher_simple-error.log',
      out_file: './logs/pm2/whatsapp_watcher_simple-out.log',
      log_file: './logs/pm2/whatsapp_watcher_simple-combined.log',
      time: true,
      merge_logs: true,
    },
    {
      name: 'workflow_processor',
      script: 'workflow_processor.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/workflow_processor-error.log',
      out_file: './logs/pm2/workflow_processor-out.log',
      log_file: './logs/pm2/workflow_processor-combined.log',
      time: true,
      merge_logs: true,
    },
    {
      name: 'orchestrator_agent',
      script: 'orchestrator_agent.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
      },
      error_file: './logs/pm2/orchestrator-error.log',
      out_file: './logs/pm2/orchestrator-out.log',
      log_file: './logs/pm2/orchestrator-combined.log',
      time: true,
      merge_logs: true,
    },
    // NOTE: Playwright-based watchers (whatsapp_watcher.py, linkedin_watcher.py)
    // require Python 3.11 or 3.12 due to greenlet compatibility issues.
    // Run manually with compatible Python version if needed.
  ]
};
