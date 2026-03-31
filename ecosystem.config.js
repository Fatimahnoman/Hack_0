/**
 * PM2 Ecosystem Configuration for Watchers
 * ==========================================
 * Usage:
 *   pm2 start ecosystem.config.js
 *   pm2 start ecosystem.config.js --only gmail_watcher
 *   pm2 stop ecosystem.config.js
 *   pm2 restart ecosystem.config.js
 *   pm2 delete ecosystem.config.js
 *
 * NOTE: 
 * - WhatsApp and LinkedIn watchers (Playwright-based) require Python 3.11/3.12
 * - Use whatsapp_watcher_simple.py as alternative for Python 3.14
 */

module.exports = {
  apps: [
    {
      name: 'gmail_watcher',
      script: 'watchers/gmail_watcher.py',
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
      script: 'bronze/watchers/filesystem_watcher.py',
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
      script: 'watchers/whatsapp_watcher_simple.py',
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
    // NOTE: Playwright-based watchers (whatsapp_watcher.py, linkedin_watcher.py)
    // require Python 3.11 or 3.12 due to greenlet compatibility issues.
    // Run manually with compatible Python version if needed.
  ]
};
