/**
 * Twitter (X) MCP Server
 * 
 * Integrates with Twitter API v2 for posting tweets and generating summaries
 * Supports tweets, threads, media uploads, and analytics
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  apiKey: process.env.TWITTER_API_KEY || '',
  apiSecret: process.env.TWITTER_API_SECRET || '',
  accessToken: process.env.TWITTER_ACCESS_TOKEN || '',
  accessSecret: process.env.TWITTER_ACCESS_SECRET || '',
  bearerToken: process.env.TWITTER_BEARER_TOKEN || '',
  userId: process.env.TWITTER_USER_ID || '',
};

const MCP_CONFIG = {
  name: 'twitter',
  version: '1.0.0',
  description: 'Twitter (X) Integration via Twitter API v2',
};

// Audit logging
const LOG_FILE = path.join(__dirname, '../../Logs/twitter-audit.jsonl');

function logAudit(action, details, result = 'success') {
  const logEntry = {
    timestamp: new Date().toISOString(),
    service: 'twitter',
    action,
    details,
    result,
  };
  
  try {
    fs.appendFileSync(LOG_FILE, JSON.stringify(logEntry) + '\n');
  } catch (e) {
    console.error('[Twitter Audit] Failed to write log:', e.message);
  }
}

/**
 * Make authenticated request to Twitter API
 */
function twitterRequest(endpoint, method = 'GET', body = null, isV2 = true) {
  return new Promise((resolve, reject) => {
    const baseUrl = isV2 ? 'https://api.twitter.com/2' : 'https://api.twitter.com/1.1';
    const url = new URL(`${baseUrl}${endpoint}`);

    const options = {
      hostname: 'api.twitter.com',
      path: url.pathname + url.search,
      method,
      headers: {
        'Authorization': `Bearer ${CONFIG.bearerToken}`,
        'Content-Type': 'application/json',
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (res.statusCode >= 400) {
            reject(new Error(response.error?.message || `HTTP ${res.statusCode}`));
          } else {
            resolve(response);
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    
    if (body && method === 'POST') {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

/**
 * Post a tweet
 */
async function postTweet(content) {
  const { text, media_ids, reply_settings, poll } = content;

  const body = { text };
  
  if (media_ids && media_ids.length > 0) {
    body.media = { media_ids };
  }
  
  if (reply_settings) {
    body.reply_settings = reply_settings;
  }

  if (poll) {
    body.poll = {
      duration_minutes: poll.duration_minutes || 1440,
      options: poll.options,
    };
  }

  const result = await twitterRequest('/tweets', 'POST', body);
  
  logAudit('post_tweet', { text: text?.substring(0, 100), media_count: media_ids?.length }, result?.data?.id ? 'success' : 'failed');

  return {
    success: !!result?.data?.id,
    tweet_id: result?.data?.id,
    text: result?.data?.text,
    edit_history_tweet_ids: result?.data?.edit_history_tweet_ids,
  };
}

/**
 * Post a thread (multiple tweets)
 */
async function postThread(tweets) {
  const results = [];
  let previousTweetId = null;

  for (let i = 0; i < tweets.length; i++) {
    const tweet = tweets[i];
    const body = { text: tweet.text };

    if (previousTweetId) {
      body.reply = { in_reply_to_tweet_id: previousTweetId };
    }

    if (tweet.media_ids && tweet.media_ids.length > 0) {
      body.media = { media_ids: tweet.media_ids };
    }

    const result = await twitterRequest('/tweets', 'POST', body);
    
    if (result?.data?.id) {
      results.push({
        index: i,
        tweet_id: result.data.id,
        text: result.data.text,
      });
      previousTweetId = result.data.id;
    } else {
      logAudit('post_thread', { index: i, error: 'Failed to post' }, 'failed');
      throw new Error(`Failed to post tweet ${i + 1} of ${tweets.length}`);
    }
  }

  logAudit('post_thread', { tweet_count: tweets.length, tweet_ids: results.map(r => r.tweet_id) }, 'success');

  return {
    success: true,
    thread_id: results[0].tweet_id,
    tweets: results,
    count: results.length,
  };
}

/**
 * Upload media to Twitter
 */
async function uploadMedia(mediaUrl, mediaType = 'image') {
  // For simplicity, we'll use media_url directly
  // In production, you'd download and upload to media.twitter.com
  
  return {
    media_id_string: `temp_${Date.now()}`,
    size: 0,
    expires_after_secs: 86400,
    image: { image_type: mediaType },
    warning: 'Media upload is simplified. Use Twitter SDK for full upload support.',
  };
}

/**
 * Delete a tweet
 */
async function deleteTweet(tweetId) {
  const result = await twitterRequest(`/tweets/${tweetId}`, 'DELETE');
  
  logAudit('delete_tweet', { tweet_id: tweetId }, result?.data?.deleted ? 'success' : 'failed');

  return {
    success: !!result?.data?.deleted,
    tweet_id: tweetId,
  };
}

/**
 * Get user timeline
 */
async function getUserTimeline(options = {}) {
  const { max_results = 10, exclude = ['retweets', 'replies'] } = options;
  
  const params = new URLSearchParams({
    'max_results': max_results.toString(),
    'tweet.fields': 'created_at,public_metrics,context_annotations,entities',
  });

  if (exclude.length > 0) {
    params.append('exclude', exclude.join(','));
  }

  const result = await twitterRequest(`/users/${CONFIG.userId}/tweets?${params}`);
  
  return {
    count: result?.data?.length || 0,
    tweets: result?.data || [],
    meta: result?.meta,
  };
}

/**
 * Get tweet by ID
 */
async function getTweet(tweetId) {
  const params = new URLSearchParams({
    'tweet.fields': 'created_at,public_metrics,context_annotations,entities,author_id',
  });

  const result = await twitterRequest(`/tweets/${tweetId}?${params}`);
  
  return result?.data || null;
}

/**
 * Get user metrics/summary
 */
async function getUserMetrics() {
  const params = new URLSearchParams({
    'user.fields': 'public_metrics,created_at,description,location',
  });

  const result = await twitterRequest(`/users/${CONFIG.userId}?${params}`);
  
  return {
    user: result?.data,
    metrics: result?.data?.public_metrics,
  };
}

/**
 * Get tweet analytics/summary
 */
async function getTweetAnalytics(tweetId) {
  const params = new URLSearchParams({
    'tweet.fields': 'public_metrics,created_at,entities',
  });

  const result = await twitterRequest(`/tweets/${tweetId}?${params}`);
  
  if (!result?.data) {
    return { error: 'Tweet not found' };
  }

  const tweet = result.data;
  
  return {
    tweet_id: tweetId,
    created_at: tweet.created_at,
    metrics: {
      impressions: tweet.public_metrics?.impression_count || 0,
      likes: tweet.public_metrics?.like_count || 0,
      retweets: tweet.public_metrics?.retweet_count || 0,
      replies: tweet.public_metrics?.reply_count || 0,
      quotes: tweet.public_metrics?.quote_count || 0,
      bookmarks: tweet.public_metrics?.bookmark_count || 0,
    },
    engagement_rate: calculateEngagementRate(tweet.public_metrics),
  };
}

function calculateEngagementRate(metrics) {
  if (!metrics) return 0;
  const impressions = metrics.impression_count || 1;
  const engagements = (metrics.like_count || 0) + 
                      (metrics.retweet_count || 0) + 
                      (metrics.reply_count || 0) +
                      (metrics.quote_count || 0);
  return ((engagements / impressions) * 100).toFixed(2);
}

/**
 * Get Twitter summary for a period
 */
async function getTwitterSummary(days = 7) {
  const since = new Date();
  since.setDate(since.getDate() - days);
  
  const params = new URLSearchParams({
    'start_time': since.toISOString(),
    'tweet.fields': 'public_metrics,created_at',
  });

  const result = await twitterRequest(`/users/${CONFIG.userId}/tweets?${params}`);
  
  const tweets = result?.data || [];
  
  const summary = {
    period: { days, from: since.toISOString(), to: new Date().toISOString() },
    total_tweets: tweets.length,
    total_metrics: {
      impressions: 0,
      likes: 0,
      retweets: 0,
      replies: 0,
      quotes: 0,
    },
    top_tweets: [],
  };

  tweets.forEach(tweet => {
    const metrics = tweet.public_metrics || {};
    summary.total_metrics.impressions += metrics.impression_count || 0;
    summary.total_metrics.likes += metrics.like_count || 0;
    summary.total_metrics.retweets += metrics.retweet_count || 0;
    summary.total_metrics.replies += metrics.reply_count || 0;
    summary.total_metrics.quotes += metrics.quote_count || 0;
  });

  // Get top 3 tweets by engagement
  summary.top_tweets = tweets
    .sort((a, b) => {
      const aEngagement = (a.public_metrics?.like_count || 0) + 
                         (a.public_metrics?.retweet_count || 0);
      const bEngagement = (b.public_metrics?.like_count || 0) + 
                         (b.public_metrics?.retweet_count || 0);
      return bEngagement - aEngagement;
    })
    .slice(0, 3)
    .map(tweet => ({
      id: tweet.id,
      text: tweet.text?.substring(0, 100),
      likes: tweet.public_metrics?.like_count || 0,
      retweets: tweet.public_metrics?.retweet_count || 0,
    }));

  summary.avg_engagement_rate = summary.total_tweets > 0 
    ? ((summary.total_metrics.likes + summary.total_metrics.retweets + summary.total_metrics.replies) / summary.total_tweets).toFixed(2)
    : 0;

  return summary;
}

/**
 * Like a tweet
 */
async function likeTweet(tweetId) {
  const result = await twitterRequest(`/users/${CONFIG.userId}/likes`, 'POST', {
    tweet_id: tweetId,
  });
  
  logAudit('like_tweet', { tweet_id: tweetId }, result?.data?.liked ? 'success' : 'failed');

  return {
    success: !!result?.data?.liked,
    tweet_id: tweetId,
  };
}

/**
 * Retweet
 */
async function retweet(tweetId) {
  const result = await twitterRequest(`/users/${CONFIG.userId}/retweets`, 'POST', {
    tweet_id: tweetId,
  });
  
  logAudit('retweet', { tweet_id: tweetId }, result?.data?.retweeted ? 'success' : 'failed');

  return {
    success: !!result?.data?.retweeted,
    tweet_id: tweetId,
  };
}

// ============================================================================
// MCP Tools Definition
// ============================================================================

const TOOLS = [
  {
    name: 'twitter_post',
    description: 'Post a tweet to Twitter',
    inputSchema: {
      type: 'object',
      properties: {
        text: { type: 'string', description: 'Tweet text (max 280 chars)' },
        media_ids: { type: 'array', items: { type: 'string' }, description: 'Media IDs to attach' },
        reply_settings: { type: 'string', enum: ['everyone', 'mentionedUsers', 'following'] },
      },
      required: ['text'],
    },
  },
  {
    name: 'twitter_post_thread',
    description: 'Post a thread of tweets',
    inputSchema: {
      type: 'object',
      properties: {
        tweets: {
          type: 'array',
          items: {
            type: 'object',
            properties: {
              text: { type: 'string' },
              media_ids: { type: 'array', items: { type: 'string' } },
            },
            required: ['text'],
          },
          description: 'Array of tweets to post as thread',
        },
      },
      required: ['tweets'],
    },
  },
  {
    name: 'twitter_delete',
    description: 'Delete a tweet',
    inputSchema: {
      type: 'object',
      properties: {
        tweet_id: { type: 'string', description: 'Tweet ID to delete' },
      },
      required: ['tweet_id'],
    },
  },
  {
    name: 'twitter_get_timeline',
    description: 'Get user timeline',
    inputSchema: {
      type: 'object',
      properties: {
        max_results: { type: 'integer', default: 10 },
        exclude: { type: 'array', items: { type: 'string' } },
      },
    },
  },
  {
    name: 'twitter_get_tweet',
    description: 'Get tweet by ID',
    inputSchema: {
      type: 'object',
      properties: {
        tweet_id: { type: 'string', description: 'Tweet ID' },
      },
      required: ['tweet_id'],
    },
  },
  {
    name: 'twitter_get_analytics',
    description: 'Get tweet analytics',
    inputSchema: {
      type: 'object',
      properties: {
        tweet_id: { type: 'string', description: 'Tweet ID' },
      },
      required: ['tweet_id'],
    },
  },
  {
    name: 'twitter_get_summary',
    description: 'Get Twitter summary for a period',
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'integer', default: 7, description: 'Number of days' },
      },
    },
  },
  {
    name: 'twitter_get_user_metrics',
    description: 'Get user profile metrics',
    inputSchema: {
      type: 'object',
      properties: {},
    },
  },
  {
    name: 'twitter_like',
    description: 'Like a tweet',
    inputSchema: {
      type: 'object',
      properties: {
        tweet_id: { type: 'string', description: 'Tweet ID to like' },
      },
      required: ['tweet_id'],
    },
  },
  {
    name: 'twitter_retweet',
    description: 'Retweet a tweet',
    inputSchema: {
      type: 'object',
      properties: {
        tweet_id: { type: 'string', description: 'Tweet ID to retweet' },
      },
      required: ['tweet_id'],
    },
  },
];

async function handleToolCall(name, args) {
  console.log(`[Twitter MCP] Calling tool: ${name}`, args);

  switch (name) {
    case 'twitter_post':
      return await postTweet(args);
    case 'twitter_post_thread':
      return await postThread(args.tweets);
    case 'twitter_delete':
      return await deleteTweet(args.tweet_id);
    case 'twitter_get_timeline':
      return await getUserTimeline(args);
    case 'twitter_get_tweet':
      return await getTweet(args.tweet_id);
    case 'twitter_get_analytics':
      return await getTweetAnalytics(args.tweet_id);
    case 'twitter_get_summary':
      return await getTwitterSummary(args.days || 7);
    case 'twitter_get_user_metrics':
      return await getUserMetrics();
    case 'twitter_like':
      return await likeTweet(args.tweet_id);
    case 'twitter_retweet':
      return await retweet(args.tweet_id);
    default:
      throw new Error(`Unknown tool: ${name}`);
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
          capabilities: { tools: {} },
          serverInfo: MCP_CONFIG,
        },
      };
    }

    if (method === 'tools/list') {
      return { jsonrpc: '2.0', id, result: { tools: TOOLS } };
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

    return { jsonrpc: '2.0', id, error: { code: -32601, message: 'Method not found' } };
  } catch (error) {
    return { jsonrpc: '2.0', id, error: { code: -32603, message: error.message } };
  }
}

// Main server
async function main() {
  console.log('[Twitter MCP] Starting server...');
  console.log('[Twitter MCP] Config:', {
    apiKey: CONFIG.apiKey ? '***' : 'not set',
    userId: CONFIG.userId || 'not set',
  });

  // Ensure log directory exists
  const logDir = path.dirname(LOG_FILE);
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true });
  }

  process.stdin.on('data', (data) => {
    const lines = data.toString().split('\n').filter(line => line.trim());
    for (const line of lines) {
      try {
        const request = JSON.parse(line);
        handleRequest(request).then((response) => {
          process.stdout.write(JSON.stringify(response) + '\n');
        });
      } catch (error) {
        console.error('[Twitter MCP] Error:', error.message);
      }
    }
  });

  console.log('[Twitter MCP] Server ready');
}

main().catch(console.error);
