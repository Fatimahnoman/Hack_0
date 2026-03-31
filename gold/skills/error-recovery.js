/**
 * Error Recovery and Graceful Degradation System
 * 
 * Provides robust error handling, automatic recovery, and graceful fallbacks
 * Ensures system continues operating even when components fail
 */

const fs = require('fs');
const path = require('path');

const LOGS_DIR = path.join(__dirname, '../../Logs');
const CONFIG_DIR = path.join(__dirname, '../../mcp_servers');

// Ensure directories exist
if (!fs.existsSync(LOGS_DIR)) {
  fs.mkdirSync(LOGS_DIR, { recursive: true });
}

// Error Recovery Configuration
const RECOVERY_CONFIG = {
  maxRetries: 3,
  baseDelay: 1000, // 1 second
  maxDelay: 30000, // 30 seconds
  backoffMultiplier: 2,
  circuitBreakerThreshold: 5,
  circuitBreakerTimeout: 60000, // 1 minute
  healthCheckInterval: 30000, // 30 seconds
};

// Circuit Breaker State
const circuitBreakers = new Map();

// Service Health State
const serviceHealth = new Map();

/**
 * Execute function with automatic retry and exponential backoff
 */
async function executeWithRetry(fn, options = {}) {
  const config = { ...RECOVERY_CONFIG, ...options };
  let lastError;
  
  for (let attempt = 1; attempt <= config.maxRetries; attempt++) {
    try {
      const result = await fn();
      
      if (attempt > 1) {
        logRecovery('retry_success', { attempt, function: fn.name || 'anonymous' });
      }
      
      return result;
    } catch (error) {
      lastError = error;
      
      logRecovery('retry_attempt', {
        attempt,
        maxRetries: config.maxRetries,
        error: error.message,
        function: fn.name || 'anonymous',
      });
      
      if (attempt < config.maxRetries) {
        const delay = Math.min(
          config.baseDelay * Math.pow(config.backoffMultiplier, attempt - 1),
          config.maxDelay
        );
        
        logRecovery('waiting_for_retry', { delay, attempt });
        await sleep(delay);
      }
    }
  }
  
  logRecovery('all_retries_failed', {
    maxRetries: config.maxRetries,
    error: lastError?.message,
    function: fn.name || 'anonymous',
  });
  
  throw lastError;
}

/**
 * Circuit Breaker Pattern Implementation
 */
async function executeWithCircuitBreaker(serviceName, fn, options = {}) {
  const breaker = getCircuitBreaker(serviceName);
  
  if (breaker.state === 'open') {
    if (Date.now() - breaker.lastFailureTime > options.timeout || RECOVERY_CONFIG.circuitBreakerTimeout) {
      // Try half-open state
      breaker.state = 'half-open';
      logCircuitBreaker(serviceName, 'half_open', 'Attempting recovery');
    } else {
      logCircuitBreaker(serviceName, 'open', 'Circuit breaker open, rejecting request');
      throw new Error(`Circuit breaker open for service: ${serviceName}`);
    }
  }
  
  try {
    const result = await fn();
    
    if (breaker.state === 'half-open') {
      logCircuitBreaker(serviceName, 'closed', 'Service recovered, closing circuit');
    }
    
    breaker.state = 'closed';
    breaker.failureCount = 0;
    breaker.lastSuccessTime = Date.now();
    
    return result;
  } catch (error) {
    breaker.failureCount++;
    breaker.lastFailureTime = Date.now();
    
    if (breaker.failureCount >= (options.threshold || RECOVERY_CONFIG.circuitBreakerThreshold)) {
      breaker.state = 'open';
      logCircuitBreaker(serviceName, 'open', `Threshold reached (${breaker.failureCount} failures)`);
    }
    
    throw error;
  }
}

/**
 * Get or create circuit breaker for a service
 */
function getCircuitBreaker(serviceName) {
  if (!circuitBreakers.has(serviceName)) {
    circuitBreakers.set(serviceName, {
      state: 'closed',
      failureCount: 0,
      lastFailureTime: 0,
      lastSuccessTime: 0,
    });
  }
  return circuitBreakers.get(serviceName);
}

/**
 * Graceful Degradation Handler
 * Tries primary function, falls back to alternatives on failure
 */
async function executeWithFallback(primary, fallbacks = [], options = {}) {
  const functions = [primary, ...fallbacks];
  
  for (let i = 0; i < functions.length; i++) {
    try {
      const result = await functions[i]();
      
      if (i > 0) {
        logDegradation('fallback_used', {
          level: i,
          function: functions[i].name || 'anonymous',
        });
      }
      
      return result;
    } catch (error) {
      logDegradation('fallback_failed', {
        level: i,
        function: functions[i].name || 'anonymous',
        error: error.message,
      });
      
      if (i === functions.length - 1) {
        // All fallbacks exhausted
        if (options.defaultReturn !== undefined) {
          logDegradation('returning_default', { default: options.defaultReturn });
          return options.defaultReturn;
        }
        throw error;
      }
    }
  }
}

/**
 * Health Check System
 */
async function checkServiceHealth(serviceName, healthCheckFn) {
  try {
    const isHealthy = await healthCheckFn();
    
    serviceHealth.set(serviceName, {
      status: isHealthy ? 'healthy' : 'unhealthy',
      lastCheck: Date.now(),
      consecutiveFailures: isHealthy ? 0 : (serviceHealth.get(serviceName)?.consecutiveFailures || 0) + 1,
    });
    
    return isHealthy;
  } catch (error) {
    serviceHealth.set(serviceName, {
      status: 'error',
      lastCheck: Date.now(),
      error: error.message,
      consecutiveFailures: (serviceHealth.get(serviceName)?.consecutiveFailures || 0) + 1,
    });
    
    return false;
  }
}

/**
 * Get overall system health status
 */
function getSystemHealth() {
  const status = {
    timestamp: new Date().toISOString(),
    services: {},
    overall: 'healthy',
    unhealthyCount: 0,
  };
  
  serviceHealth.forEach((health, serviceName) => {
    status.services[serviceName] = {
      status: health.status,
      lastCheck: new Date(health.lastCheck).toISOString(),
      consecutiveFailures: health.consecutiveFailures,
    };
    
    if (health.status !== 'healthy') {
      status.unhealthyCount++;
    }
  });
  
  if (status.unhealthyCount > 0) {
    status.overall = status.unhealthyCount > 2 ? 'degraded' : 'partial';
  }
  
  return status;
}

/**
 * Error Classification
 */
function classifyError(error) {
  const errorType = {
    category: 'unknown',
    isRetryable: false,
    severity: 'medium',
    suggestedAction: 'log_and_continue',
  };
  
  const message = error?.message?.toLowerCase() || '';
  
  // Network errors
  if (/network|connection|timeout|econnrefused|enotfound/i.test(message)) {
    errorType.category = 'network';
    errorType.isRetryable = true;
    errorType.suggestedAction = 'retry_with_backoff';
  }
  
  // Authentication errors
  if (/auth|unauthorized|forbidden|401|403/i.test(message)) {
    errorType.category = 'authentication';
    errorType.isRetryable = false;
    errorType.severity = 'high';
    errorType.suggestedAction = 'refresh_credentials';
  }
  
  // Rate limiting
  if (/rate.?limit|too many requests|429/i.test(message)) {
    errorType.category = 'rate_limit';
    errorType.isRetryable = true;
    errorType.suggestedAction = 'wait_and_retry';
  }
  
  // Validation errors
  if (/invalid|validation|parse|syntax/i.test(message)) {
    errorType.category = 'validation';
    errorType.isRetryable = false;
    errorType.suggestedAction = 'fix_input_data';
  }
  
  // Resource not found
  if (/not found|404|does not exist/i.test(message)) {
    errorType.category = 'not_found';
    errorType.isRetryable = false;
    errorType.suggestedAction = 'create_or_skip';
  }
  
  // Server errors
  if (/internal server error|500|502|503/i.test(message)) {
    errorType.category = 'server';
    errorType.isRetryable = true;
    errorType.severity = 'high';
    errorType.suggestedAction = 'retry_with_backoff';
  }
  
  return errorType;
}

/**
 * Automatic Error Recovery Strategy
 */
async function attemptAutoRecovery(error, context = {}) {
  const errorType = classifyError(error);
  
  logRecovery('error_classified', {
    error: error.message,
    category: errorType.category,
    isRetryable: errorType.isRetryable,
    suggestedAction: errorType.suggestedAction,
  });
  
  const recoveryStrategies = {
    network: async () => {
      // Wait for network to stabilize
      await sleep(2000);
      return { recovered: true, action: 'network_stabilized' };
    },
    
    authentication: async () => {
      // Trigger credential refresh
      if (context.refreshCredentials) {
        await context.refreshCredentials();
        return { recovered: true, action: 'credentials_refreshed' };
      }
      return { recovered: false, action: 'manual_intervention_required' };
    },
    
    rate_limit: async () => {
      // Wait based on retry-after header or default
      const waitTime = context.retryAfter || 5000;
      await sleep(waitTime);
      return { recovered: true, action: 'rate_limit_reset' };
    },
    
    validation: async () => {
      // Try to sanitize input
      if (context.sanitizeInput) {
        const sanitized = await context.sanitizeInput();
        return { recovered: sanitized, action: 'input_sanitized' };
      }
      return { recovered: false, action: 'invalid_input' };
    },
    
    not_found: async () => {
      // Try to create missing resource
      if (context.createMissing) {
        await context.createMissing();
        return { recovered: true, action: 'resource_created' };
      }
      return { recovered: false, action: 'resource_missing' };
    },
    
    server: async () => {
      // Wait and retry
      await sleep(3000);
      return { recovered: true, action: 'server_may_be_ready' };
    },
  };
  
  const strategy = recoveryStrategies[errorType.category];
  if (strategy) {
    try {
      return await strategy();
    } catch (recoveryError) {
      logRecovery('recovery_failed', {
        category: errorType.category,
        error: recoveryError.message,
      });
      return { recovered: false, action: 'recovery_failed' };
    }
  }
  
  return { recovered: false, action: 'no_strategy_available' };
}

/**
 * Queue for failed operations
 */
const failedOperationsQueue = [];

/**
 * Add operation to retry queue
 */
function queueForRetry(operation) {
  failedOperationsQueue.push({
    ...operation,
    queuedAt: Date.now(),
    retryCount: 0,
    nextRetryAt: Date.now() + 60000, // 1 minute from now
  });
  
  logRecovery('operation_queued', {
    operation: operation.name,
    queueLength: failedOperationsQueue.length,
  });
}

/**
 * Process retry queue
 */
async function processRetryQueue() {
  const now = Date.now();
  const toProcess = failedOperationsQueue.filter(op => op.nextRetryAt <= now);
  
  for (const operation of toProcess) {
    try {
      await operation.fn();
      
      // Remove from queue on success
      const index = failedOperationsQueue.indexOf(operation);
      if (index > -1) {
        failedOperationsQueue.splice(index, 1);
      }
      
      logRecovery('queued_operation_succeeded', {
        operation: operation.name,
        remainingQueue: failedOperationsQueue.length,
      });
    } catch (error) {
      operation.retryCount++;
      operation.nextRetryAt = now + Math.pow(2, operation.retryCount) * 60000;
      
      if (operation.retryCount >= 5) {
        // Remove from queue after 5 failures
        const index = failedOperationsQueue.indexOf(operation);
        if (index > -1) {
          failedOperationsQueue.splice(index, 1);
        }
        
        logRecovery('queued_operation_permanently_failed', {
          operation: operation.name,
        });
      }
    }
  }
}

// Start queue processor
setInterval(processRetryQueue, 30000);

// ============================================================================
// Logging Functions
// ============================================================================

function logRecovery(event, details) {
  const log = {
    timestamp: new Date().toISOString(),
    service: 'error_recovery',
    event,
    ...details,
  };
  
  const logFile = path.join(LOGS_DIR, 'error_recovery.jsonl');
  try {
    fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
  } catch (e) {
    console.error('[Error Recovery] Failed to write log:', e.message);
  }
}

function logCircuitBreaker(serviceName, state, message) {
  const log = {
    timestamp: new Date().toISOString(),
    service: 'circuit_breaker',
    serviceName,
    state,
    message,
  };
  
  const logFile = path.join(LOGS_DIR, 'circuit_breakers.jsonl');
  try {
    fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
  } catch (e) {
    console.error('[Circuit Breaker] Failed to write log:', e.message);
  }
}

function logDegradation(event, details) {
  const log = {
    timestamp: new Date().toISOString(),
    service: 'graceful_degradation',
    event,
    ...details,
  };
  
  const logFile = path.join(LOGS_DIR, 'graceful_degradation.jsonl');
  try {
    fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
  } catch (e) {
    console.error('[Degradation] Failed to write log:', e.message);
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// ============================================================================
// Exports
// ============================================================================

module.exports = {
  // Main functions
  executeWithRetry,
  executeWithCircuitBreaker,
  executeWithFallback,
  
  // Health check
  checkServiceHealth,
  getSystemHealth,
  
  // Error handling
  classifyError,
  attemptAutoRecovery,
  
  // Queue management
  queueForRetry,
  
  // Configuration
  RECOVERY_CONFIG,
  
  // State
  circuitBreakers,
  serviceHealth,
  failedOperationsQueue,
};
