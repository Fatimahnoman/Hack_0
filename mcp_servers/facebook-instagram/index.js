/**
 * Facebook/Instagram MCP Server
 * 
 * Integrates with Meta Graph API for posting to Facebook Pages and Instagram
 * Provides posting, scheduling, and analytics summary features
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  appId: process.env.FB_APP_ID || '',
  appSecret: process.env.FB_APP_SECRET || '',
  accessToken: process.env.FB_ACCESS_TOKEN || '',
  instagramAccountId: process.env.INSTAGRAM_ACCOUNT_ID || '',
  facebookPageId: process.env.FB_PAGE_ID || '',
};

const MCP_CONFIG = {
  name: 'facebook-instagram',
  version: '1.0.0',
  description: 'Facebook & Instagram Integration via Meta Graph API',
};

// Audit logging
const LOG_FILE = path.join(__dirname, '../../Logs/facebook-instagram-audit.jsonl');

function logAudit(action, details, result = 'success') {
  const logEntry = {
    timestamp: new Date().toISOString(),
    service: 'facebook-instagram',
    action,
    details,
    result,
  };
  
  try {
    fs.appendFileSync(LOG_FILE, JSON.stringify(logEntry) + '\n');
  } catch (e) {
    console.error('[FB/IG Audit] Failed to write log:', e.message);
  }
}

/**
 * Make HTTPS request to Graph API
 */
function graphRequest(endpoint, method = 'GET', params = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(`https://graph.facebook.com/v18.0/${endpoint}`);
    url.searchParams.append('access_token', CONFIG.accessToken);
    
    Object.keys(params).forEach(key => {
      url.searchParams.append(key, params[key]);
    });

    const options = {
      hostname: 'graph.facebook.com',
      path: url.pathname + url.search,
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.error) {
            reject(new Error(response.error.message));
          } else {
            resolve(response);
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    
    if (method === 'POST' && params.body) {
      req.write(JSON.stringify(params.body));
    }
    
    req.end();
  });
}

/**
 * Post to Facebook Page
 */
async function postToFacebook(content) {
  const { message, link, photo_url, scheduled_time } = content;

  let result;
  
  if (photo_url) {
    // Photo post
    result = await graphRequest(`${CONFIG.facebookPageId}/photos`, 'POST', {
      url: photo_url,
      message: message || '',
      published: !scheduled_time,
      scheduled_publish_time: scheduled_time ? Math.floor(new Date(scheduled_time).getTime() / 1000) : undefined,
    });
  } else if (link) {
    // Link post
    result = await graphRequest(`${CONFIG.facebookPageId}/feed`, 'POST', {
      message: message || '',
      link: link,
      published: !scheduled_time,
      scheduled_publish_time: scheduled_time ? Math.floor(new Date(scheduled_time).getTime() / 1000) : undefined,
    });
  } else {
    // Text-only post
    result = await graphRequest(`${CONFIG.facebookPageId}/feed`, 'POST', {
      message: message,
      published: !scheduled_time,
      scheduled_publish_time: scheduled_time ? Math.floor(new Date(scheduled_time).getTime() / 1000) : undefined,
    });
  }

  logAudit('facebook_post', { content, post_id: result?.id }, result?.id ? 'success' : 'failed');
  
  return {
    success: !!result?.id,
    post_id: result?.id,
    platform: 'facebook',
    message: result?.id ? 'Posted to Facebook successfully' : 'Failed to post',
  };
}

/**
 * Post to Instagram
 */
async function postToInstagram(content) {
  const { caption, media_url, media_type = 'IMAGE', is_story = false } = content;

  // Step 1: Create media container
  const containerParams = {
    image_url: media_type === 'IMAGE' ? media_url : undefined,
    video_url: media_type === 'VIDEO' ? media_url : undefined,
    caption: caption || '',
    is_carousel_item: false,
    media_type,
  };

  const container = await graphRequest(
    `${CONFIG.instagramAccountId}/media`,
    'POST',
    containerParams
  );

  if (!container?.id) {
    logAudit('instagram_post', { content, step: 'container_creation' }, 'failed');
    return { success: false, error: 'Failed to create media container' };
  }

  // Step 2: Publish the media
  const publishResult = await graphRequest(
    `${CONFIG.instagramAccountId}/media_publish`,
    'POST',
    { creation_id: container.id }
  );

  logAudit('instagram_post', { content, post_id: publishResult?.id }, publishResult?.id ? 'success' : 'failed');

  return {
    success: !!publishResult?.id,
    post_id: publishResult?.id,
    platform: 'instagram',
    message: publishResult?.id ? 'Posted to Instagram successfully' : 'Failed to post',
  };
}

/**
 * Post to both Facebook and Instagram
 */
async function postToBoth(content) {
  const results = {
    facebook: null,
    instagram: null,
  };

  try {
    results.facebook = await postToFacebook(content);
  } catch (error) {
    results.facebook = { success: false, error: error.message };
  }

  try {
    results.instagram = await postToInstagram(content);
  } catch (error) {
    results.instagram = { success: false, error: error.message };
  }

  return {
    success: results.facebook?.success || results.instagram?.success,
    results,
  };
}

/**
 * Get Facebook Page insights
 */
async function getFacebookInsights(days = 7) {
  const since = new Date();
  since.setDate(since.getDate() - days);
  
  const insights = await graphRequest(`${CONFIG.facebookPageId}/insights`, 'GET', {
    metric: 'page_impressions_unique,page_engaged_users,page_post_engagements,page_likes',
    since: since.toISOString().split('T')[0],
    until: new Date().toISOString().split('T')[0],
  });

  const summary = {
    platform: 'facebook',
    period: { days, from: since.toISOString(), to: new Date().toISOString() },
    metrics: {},
  };

  if (insights?.data) {
    insights.data.forEach(metric => {
      const values = metric.values.reduce((sum, v) => sum + (v.value || 0), 0);
      summary.metrics[metric.name] = values;
    });
  }

  return summary;
}

/**
 * Get Instagram insights
 */
async function getInstagramInsights(days = 7) {
  const since = new Date();
  since.setDate(since.getDate() - days);
  
  const insights = await graphRequest(`${CONFIG.instagramAccountId}/insights`, 'GET', {
    metric: 'impressions,reach,profile_views,follower_count',
    period: 'day',
    since: since.toISOString().split('T')[0],
    until: new Date().toISOString().split('T')[0],
  });

  const summary = {
    platform: 'instagram',
    period: { days, from: since.toISOString(), to: new Date().toISOString() },
    metrics: {},
  };

  if (insights?.data) {
    insights.data.forEach(metric => {
      const values = metric.values.reduce((sum, v) => sum + (v.value || 0), 0);
      summary.metrics[metric.name] = values;
    });
  }

  return summary;
}

/**
 * Get combined social media summary
 */
async function getSocialMediaSummary(days = 7) {
  const [fbInsights, igInsights] = await Promise.all([
    getFacebookInsights(days).catch(e => ({ error: e.message })),
    getInstagramInsights(days).catch(e => ({ error: e.message })),
  ]);

  return {
    period: { days },
    generated_at: new Date().toISOString(),
    facebook: fbInsights,
    instagram: igInsights,
    total_reach: (fbInsights?.metrics?.page_impressions_unique || 0) + 
                 (igInsights?.metrics?.reach || 0),
    total_engagement: (fbInsights?.metrics?.page_post_engagements || 0) + 
                      (igInsights?.metrics?.engagement || 0),
  };
}

/**
 * Get recent posts from Facebook
 */
async function getFacebookPosts(limit = 10) {
  const posts = await graphRequest(`${CONFIG.facebookPageId}/posts`, 'GET', {
    fields: 'id,message,created_time,permalink_url,shares,likes.summary(true),comments.summary(true)',
    limit,
  });

  return {
    platform: 'facebook',
    count: posts?.data?.length || 0,
    posts: posts?.data || [],
  };
}

/**
 * Get recent media from Instagram
 */
async function getInstagramMedia(limit = 10) {
  const media = await graphRequest(`${CONFIG.instagramAccountId}/media`, 'GET', {
    fields: 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
    limit,
  });

  return {
    platform: 'instagram',
    count: media?.data?.length || 0,
    media: media?.data || [],
  };
}

/**
 * Delete a Facebook post
 */
async function deleteFacebookPost(postId) {
  const result = await graphRequest(postId, 'DELETE');
  
  logAudit('facebook_delete', { post_id: postId }, result?.success ? 'success' : 'failed');
  
  return {
    success: result?.success || false,
    message: result?.success ? 'Post deleted successfully' : 'Failed to delete post',
  };
}

// ============================================================================
// MCP Tools Definition
// ============================================================================

const TOOLS = [
  {
    name: 'facebook_post',
    description: 'Post content to Facebook Page',
    inputSchema: {
      type: 'object',
      properties: {
        message: { type: 'string', description: 'Post message' },
        link: { type: 'string', description: 'URL to share' },
        photo_url: { type: 'string', description: 'Image URL for photo post' },
        scheduled_time: { type: 'string', description: 'Schedule time (ISO 8601)' },
      },
      required: ['message'],
    },
  },
  {
    name: 'instagram_post',
    description: 'Post content to Instagram',
    inputSchema: {
      type: 'object',
      properties: {
        caption: { type: 'string', description: 'Post caption' },
        media_url: { type: 'string', description: 'Image or video URL' },
        media_type: { type: 'string', enum: ['IMAGE', 'VIDEO', 'CAROUSEL'] },
        is_story: { type: 'boolean', description: 'Post as story' },
      },
      required: ['caption', 'media_url'],
    },
  },
  {
    name: 'social_post_both',
    description: 'Post to both Facebook and Instagram',
    inputSchema: {
      type: 'object',
      properties: {
        message: { type: 'string', description: 'Post message/caption' },
        media_url: { type: 'string', description: 'Image URL' },
        link: { type: 'string', description: 'URL to share' },
      },
      required: ['message'],
    },
  },
  {
    name: 'get_social_summary',
    description: 'Get combined Facebook and Instagram insights summary',
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'integer', description: 'Number of days to summarize', default: 7 },
      },
    },
  },
  {
    name: 'get_facebook_insights',
    description: 'Get Facebook Page insights',
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'integer', description: 'Number of days', default: 7 },
      },
    },
  },
  {
    name: 'get_instagram_insights',
    description: 'Get Instagram account insights',
    inputSchema: {
      type: 'object',
      properties: {
        days: { type: 'integer', description: 'Number of days', default: 7 },
      },
    },
  },
  {
    name: 'get_facebook_posts',
    description: 'Get recent Facebook posts',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', description: 'Number of posts', default: 10 },
      },
    },
  },
  {
    name: 'get_instagram_media',
    description: 'Get recent Instagram media',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'integer', description: 'Number of media items', default: 10 },
      },
    },
  },
  {
    name: 'delete_facebook_post',
    description: 'Delete a Facebook post',
    inputSchema: {
      type: 'object',
      properties: {
        post_id: { type: 'string', description: 'Facebook post ID' },
      },
      required: ['post_id'],
    },
  },
];

async function handleToolCall(name, args) {
  console.log(`[FB/IG MCP] Calling tool: ${name}`, args);

  switch (name) {
    case 'facebook_post':
      return await postToFacebook(args);
    case 'instagram_post':
      return await postToInstagram(args);
    case 'social_post_both':
      return await postToBoth(args);
    case 'get_social_summary':
      return await getSocialMediaSummary(args.days || 7);
    case 'get_facebook_insights':
      return await getFacebookInsights(args.days || 7);
    case 'get_instagram_insights':
      return await getInstagramInsights(args.days || 7);
    case 'get_facebook_posts':
      return await getFacebookPosts(args.limit || 10);
    case 'get_instagram_media':
      return await getInstagramMedia(args.limit || 10);
    case 'delete_facebook_post':
      return await deleteFacebookPost(args.post_id);
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
  console.log('[FB/IG MCP] Starting server...');
  console.log('[FB/IG MCP] Config:', {
    appId: CONFIG.appId ? '***' : 'not set',
    pageId: CONFIG.facebookPageId || 'not set',
    igAccount: CONFIG.instagramAccountId || 'not set',
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
        console.error('[FB/IG MCP] Error:', error.message);
      }
    }
  });

  console.log('[FB/IG MCP] Server ready');
}

main().catch(console.error);
