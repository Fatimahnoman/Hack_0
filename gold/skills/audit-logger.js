/**
 * Comprehensive Audit Logging System
 * 
 * Centralized logging for all system activities
 * Features: structured logging, log rotation, search, analytics
 */

const fs = require('fs');
const path = require('path');

const LOGS_DIR = path.join(__dirname, '../../Logs');
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_LOG_FILES = 10;

// Ensure logs directory exists
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

// Log levels
const LOG_LEVELS = {
  DEBUG: 0,
  INFO: 1,
  WARN: 2,
  ERROR: 3,
  CRITICAL: 4,
};

// Current log level
let currentLogLevel = LOG_LEVELS.INFO;

/**
 * Main Audit Logger Class
 */
class AuditLogger {
  constructor(service) {
    this.service = service;
    this.logFile = path.join(LOGS_DIR, `${service}-audit.jsonl`);
    this.errorLogFile = path.join(LOGS_DIR, `${service}-errors.jsonl`);
  }

  /**
   * Log an event
   */
  log(level, event, details = {}) {
    if (LOG_LEVELS[level] < currentLogLevel) {
      return;
    }

    const entry = {
      timestamp: new Date().toISOString(),
      level,
      service: this.service,
      event,
      details,
    };

    // Write to main log
    this._writeLog(this.logFile, entry);

    // Write errors to separate file
    if (LOG_LEVELS[level] >= LOG_LEVELS.ERROR) {
      this._writeLog(this.errorLogFile, entry);
    }

    // Check for rotation
    this._checkRotation();
  }

  /**
   * Convenience methods
   */
  debug(event, details) { this.log('DEBUG', event, details); }
  info(event, details) { this.log('INFO', event, details); }
  warn(event, details) { this.log('WARN', event, details); }
  error(event, details) { this.log('ERROR', event, details); }
  critical(event, details) { this.log('CRITICAL', event, details); }

  /**
   * Log API call
   */
  logApiCall(method, endpoint, statusCode, duration, details = {}) {
    this.log('INFO', 'api_call', {
      method,
      endpoint,
      statusCode,
      duration_ms: duration,
      ...details,
    });
  }

  /**
   * Log user action
   */
  logUserAction(userId, action, resource, details = {}) {
    this.log('INFO', 'user_action', {
      user_id: userId,
      action,
      resource,
      ...details,
    });
  }

  /**
   * Log system event
   */
  logSystemEvent(category, event, details = {}) {
    this.log('INFO', 'system_event', {
      category,
      event,
      ...details,
    });
  }

  /**
   * Log security event
   */
  logSecurityEvent(type, severity, details = {}) {
    this.log(severity === 'high' ? 'CRITICAL' : 'WARN', 'security_event', {
      type,
      severity,
      ...details,
    });
  }

  /**
   * Write log entry to file
   */
  _writeLog(filePath, entry) {
    try {
      fs.appendFileSync(filePath, JSON.stringify(entry) + '\n');
    } catch (e) {
      console.error('[AuditLogger] Failed to write log:', e.message);
    }
  }

  /**
   * Check and perform log rotation
   */
  _checkRotation() {
    try {
      const stats = fs.statSync(this.logFile);
      if (stats.size > MAX_LOG_SIZE) {
        this._rotateLogs();
      }
    } catch (e) {
      // File doesn't exist yet
    }
  }

  /**
   * Rotate log files
   */
  _rotateLogs() {
    const baseName = path.basename(this.logFile, '.jsonl');
    
    // Delete oldest log
    const oldestLog = path.join(LOGS_DIR, `${baseName}-${MAX_LOG_FILES}.jsonl`);
    if (fs.existsSync(oldestLog)) {
      fs.unlinkSync(oldestLog);
    }

    // Rotate existing logs
    for (let i = MAX_LOG_FILES - 1; i >= 1; i--) {
      const oldPath = path.join(LOGS_DIR, `${baseName}-${i}.jsonl`);
      const newPath = path.join(LOGS_DIR, `${baseName}-${i + 1}.jsonl`);
      if (fs.existsSync(oldPath)) {
        fs.renameSync(oldPath, newPath);
      }
    }

    // Rotate current log
    const newLogPath = path.join(LOGS_DIR, `${baseName}-1.jsonl`);
    if (fs.existsSync(this.logFile)) {
      fs.renameSync(this.logFile, newLogPath);
    }
  }
}

/**
 * Search logs
 */
function searchLogs(service, options = {}) {
  const {
    startTime,
    endTime,
    level,
    event,
    limit = 100,
    offset = 0,
  } = options;

  const logFile = path.join(LOGS_DIR, `${service}-audit.jsonl`);
  
  if (!fs.existsSync(logFile)) {
    return { results: [], total: 0 };
  }

  const content = fs.readFileSync(logFile, 'utf-8');
  const lines = content.split('\n').filter(line => line.trim());
  const results = [];

  for (const line of lines) {
    try {
      const entry = JSON.parse(line);

      // Apply filters
      if (startTime && entry.timestamp < startTime) continue;
      if (endTime && entry.timestamp > endTime) continue;
      if (level && entry.level !== level) continue;
      if (event && entry.event !== event) continue;

      results.push(entry);
    } catch (e) {
      // Skip malformed lines
    }
  }

  // Sort by timestamp descending
  results.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  // Apply pagination
  const total = results.length;
  const paginated = results.slice(offset, offset + limit);

  return { results: paginated, total };
}

/**
 * Get log statistics
 */
function getLogStats(service, hours = 24) {
  const since = new Date(Date.now() - hours * 60 * 60 * 1000);
  const stats = {
    service,
    period: {
      hours,
      since: since.toISOString(),
      to: new Date().toISOString(),
    },
    total: 0,
    byLevel: {},
    byEvent: {},
    errors: [],
  };

  const logFile = path.join(LOGS_DIR, `${service}-audit.jsonl`);
  
  if (!fs.existsSync(logFile)) {
    return stats;
  }

  const content = fs.readFileSync(logFile, 'utf-8');
  const lines = content.split('\n').filter(line => line.trim());

  for (const line of lines) {
    try {
      const entry = JSON.parse(line);
      
      if (new Date(entry.timestamp) < since) continue;

      stats.total++;

      // Count by level
      stats.byLevel[entry.level] = (stats.byLevel[entry.level] || 0) + 1;

      // Count by event
      stats.byEvent[entry.event] = (stats.byEvent[entry.event] || 0) + 1;

      // Collect errors
      if (LOG_LEVELS[entry.level] >= LOG_LEVELS.ERROR) {
        stats.errors.push({
          timestamp: entry.timestamp,
          event: entry.event,
          details: entry.details,
        });
      }
    } catch (e) {
      // Skip malformed lines
    }
  }

  return stats;
}

/**
 * Get system-wide audit summary
 */
function getSystemAuditSummary(hours = 24) {
  const services = [
    'odoo-accounting',
    'facebook-instagram',
    'twitter',
    'email',
    'linkedin',
    'weekly-audit',
    'accounting-audit',
    'error_recovery',
    'ralph-wiggum-loop',
  ];

  const summary = {
    generated_at: new Date().toISOString(),
    period: { hours },
    services: {},
    totals: {
      entries: 0,
      errors: 0,
      warnings: 0,
    },
  };

  services.forEach(service => {
    const stats = getLogStats(service, hours);
    summary.services[service] = stats;
    summary.totals.entries += stats.total;
    summary.totals.errors += (stats.byLevel['ERROR'] || 0) + (stats.byLevel['CRITICAL'] || 0);
    summary.totals.warnings += stats.byLevel['WARN'] || 0;
  });

  return summary;
}

/**
 * Export logs to JSON
 */
function exportLogs(service, options = {}) {
  const { startTime, endTime, format = 'json' } = options;
  
  const searchResult = searchLogs(service, {
    startTime,
    endTime,
    limit: 10000,
  });

  if (format === 'json') {
    return JSON.stringify(searchResult.results, null, 2);
  }

  if (format === 'csv') {
    const headers = ['timestamp', 'level', 'service', 'event', 'details'];
    const rows = searchResult.results.map(entry => [
      entry.timestamp,
      entry.level,
      entry.service,
      entry.event,
      JSON.stringify(entry.details),
    ]);
    return [headers, ...rows].map(row => row.join(',')).join('\n');
  }

  return JSON.stringify(searchResult.results, null, 2);
}

/**
 * Create logger factory
 */
function createLogger(service) {
  return new AuditLogger(service);
}

/**
 * Set global log level
 */
function setLogLevel(level) {
  if (LOG_LEVELS[level] !== undefined) {
    currentLogLevel = LOG_LEVELS[level];
  }
}

// ============================================================================
// Pre-configured Loggers for Gold Tier Services
// ============================================================================

const loggers = {
  odoo: new AuditLogger('odoo-accounting'),
  facebook: new AuditLogger('facebook-instagram'),
  twitter: new AuditLogger('twitter'),
  email: new AuditLogger('email'),
  linkedin: new AuditLogger('linkedin'),
  weeklyAudit: new AuditLogger('weekly-audit'),
  accountingAudit: new AuditLogger('accounting-audit'),
  errorRecovery: new AuditLogger('error_recovery'),
  ralphWiggum: new AuditLogger('ralph-wiggum-loop'),
};

// ============================================================================
// Exports
// ============================================================================

module.exports = {
  // Factory
  createLogger,
  
  // Pre-configured loggers
  loggers,
  
  // Search and analytics
  searchLogs,
  getLogStats,
  getSystemAuditSummary,
  exportLogs,
  
  // Configuration
  setLogLevel,
  LOG_LEVELS,
  
  // Direct class access
  AuditLogger,
};
