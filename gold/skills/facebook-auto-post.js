/**
 * Facebook Auto-Post Scheduler & Comments Reader
 * 
 * Features:
 * - Schedule automatic posts to Facebook
 * - Read and analyze comments
 * - Auto-reply to comments (optional)
 * - Generate engagement reports
 */

const https = require('https');
const fs = require('fs');
const path = require('path');

const LOGS_DIR = path.join(__dirname, '../../Logs');
const DATA_DIR = path.join(__dirname, '../data');

// Ensure directories exist
[LOGS_DIR, DATA_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

// Configuration
const CONFIG = {
  appId: process.env.FB_APP_ID || '',
  appSecret: process.env.FB_APP_SECRET || '',
  accessToken: process.env.FB_ACCESS_TOKEN || '',
  pageId: process.env.FB_PAGE_ID || '',
  autoReply: process.env.FB_AUTO_REPLY || 'false',
  postSchedule: process.env.FB_POST_SCHEDULE || '0 9,15,21 * * *', // 9 AM, 3 PM, 9 PM
};

// Posts queue
const postsQueue = [];
const commentsCache = new Map();

/**
 * Make Graph API Request
 */
function graphRequest(endpoint, method = 'GET', params = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(`https://graph.facebook.com/v18.0/${endpoint}`);
    url.searchParams.append('access_token', CONFIG.accessToken);
    
    Object.keys(params).forEach(key => {
      if (key !== 'body') {
        url.searchParams.append(key, params[key]);
      }
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
  const { message, link, photo_url, video_url, scheduled_time } = content;

  let result;
  
  if (photo_url) {
    result = await graphRequest(`${CONFIG.pageId}/photos`, 'POST', {
      url: photo_url,
      message: message || '',
      published: !scheduled_time,
      scheduled_publish_time: scheduled_time ? Math.floor(new Date(scheduled_time).getTime() / 1000) : undefined,
    });
  } else if (video_url) {
    result = await graphRequest(`${CONFIG.pageId}/videos`, 'POST', {
      file_url: video_url,
      description: message || '',
      published: !scheduled_time,
    });
  } else if (link) {
    result = await graphRequest(`${CONFIG.pageId}/feed`, 'POST', {
      message: message || '',
      link: link,
      published: !scheduled_time,
    });
  } else {
    result = await graphRequest(`${CONFIG.pageId}/feed`, 'POST', {
      message: message,
      published: true,
    });
  }

  // Log post
  logPost(content, result);

  return {
    success: !!result?.id,
    post_id: result?.id,
    platform: 'facebook',
    timestamp: new Date().toISOString(),
  };
}

/**
 * Schedule a post
 */
function schedulePost(content, scheduledTime) {
  const post = {
    id: `post_${Date.now()}`,
    content,
    scheduledTime,
    status: 'scheduled',
    createdAt: new Date().toISOString(),
  };

  postsQueue.push(post);
  savePostsQueue();
  
  logSchedule(post);
  
  return post;
}

/**
 * Get comments from a post
 */
async function getPostComments(postId, options = {}) {
  const { limit = 100, since, until } = options;
  
  const params = {
    fields: 'id,from,message,created_time,like_count,comment_count,attachment',
    limit,
    order: 'chronological',
  };

  if (since) params.since = since;
  if (until) params.until = until;

  const result = await graphRequest(`${postId}/comments`, 'GET', params);
  
  // Cache comments
  commentsCache.set(postId, {
    comments: result?.data || [],
    fetchedAt: new Date().toISOString(),
  });

  // Log comments
  logComments(postId, result?.data || []);

  return {
    post_id: postId,
    count: result?.data?.length || 0,
    comments: result?.data || [],
    paging: result?.paging,
  };
}

/**
 * Get all recent page posts with comments
 */
async function getPagePostsComments(options = {}) {
  const { limit = 10, days = 7 } = options;
  
  const since = new Date();
  since.setDate(since.getDate() - days);

  // Get recent posts
  const posts = await graphRequest(`${CONFIG.pageId}/posts`, 'GET', {
    fields: 'id,message,created_time,permalink_url',
    limit,
    since: since.toISOString().split('T')[0],
  });

  const postsWithComments = [];

  for (const post of posts?.data || []) {
    const commentsData = await getPostComments(post.id, { limit: 50 });
    postsWithComments.push({
      post,
      comments: commentsData.comments,
      comment_count: commentsData.count,
    });
  }

  return postsWithComments;
}

/**
 * Analyze comments sentiment and engagement
 */
function analyzeComments(comments) {
  const analysis = {
    total_comments: comments.length,
    positive: 0,
    neutral: 0,
    negative: 0,
    questions: 0,
    total_likes: 0,
    avg_comment_length: 0,
    top_keywords: [],
    sentiment_breakdown: {},
  };

  const positiveWords = ['great', 'awesome', 'love', 'excellent', 'amazing', 'good', 'wonderful', 'fantastic', '👍', '❤️', '😊'];
  const negativeWords = ['bad', 'terrible', 'awful', 'hate', 'worst', 'poor', 'disappointed', '😡', '😞', '👎'];
  const questionWords = ['what', 'when', 'where', 'why', 'how', 'who', 'which', '?'];

  let totalLength = 0;
  const wordFrequency = {};

  comments.forEach(comment => {
    const message = (comment.message || '').toLowerCase();
    totalLength += message.length;

    // Count likes
    analysis.total_likes += comment.like_count || 0;

    // Simple sentiment analysis
    let sentiment = 'neutral';
    positiveWords.forEach(word => {
      if (message.includes(word)) sentiment = 'positive';
    });
    negativeWords.forEach(word => {
      if (message.includes(word)) sentiment = 'negative';
    });

    analysis[sentiment]++;

    // Check for questions
    if (questionWords.some(word => message.includes(word))) {
      analysis.questions++;
    }

    // Word frequency
    message.split(/\s+/).forEach(word => {
      if (word.length > 3) {
        wordFrequency[word] = (wordFrequency[word] || 0) + 1;
      }
    });
  });

  // Average comment length
  analysis.avg_comment_length = comments.length > 0 ? Math.round(totalLength / comments.length) : 0;

  // Top keywords
  analysis.top_keywords = Object.entries(wordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([word, count]) => ({ word, count }));

  // Sentiment breakdown
  analysis.sentiment_breakdown = {
    positive_percentage: ((analysis.positive / analysis.total_comments) * 100).toFixed(1),
    neutral_percentage: ((analysis.neutral / analysis.total_comments) * 100).toFixed(1),
    negative_percentage: ((analysis.negative / analysis.total_comments) * 100).toFixed(1),
  };

  return analysis;
}

/**
 * Auto-reply to comments
 */
async function autoReplyToComment(commentId, replyMessage) {
  const result = await graphRequest(`${commentId}/comments`, 'POST', {
    message: replyMessage,
  });

  logAutoReply(commentId, replyMessage, result);

  return {
    success: !!result?.id,
    comment_id: result?.id,
  };
}

/**
 * Smart auto-reply based on comment content
 */
async function smartAutoReply(comment) {
  const message = (comment.message || '').toLowerCase();
  
  let reply = null;

  // Thank for positive comments
  if (message.includes('great') || message.includes('awesome') || message.includes('love')) {
    reply = 'Thank you so much for your kind words! We appreciate your support! 🙏';
  }
  
  // Respond to questions
  else if (message.includes('?') || message.match(/\b(what|when|where|why|how)\b/)) {
    reply = 'Thanks for your question! We\'ll get back to you with more information soon.';
  }
  
  // Address negative comments
  else if (message.includes('bad') || message.includes('disappointed')) {
    reply = 'We\'re sorry to hear about your experience. Please send us a message so we can make it right.';
  }

  if (reply && CONFIG.autoReply === 'true') {
    return await autoReplyToComment(comment.id, reply);
  }

  return { success: false, reason: 'No matching reply template or auto-reply disabled' };
}

/**
 * Process all new comments with auto-reply
 */
async function processNewComments() {
  const postsWithComments = await getPagePostsComments({ limit: 5, days: 1 });
  
  const processed = {
    total_comments: 0,
    auto_replies_sent: 0,
    errors: 0,
  };

  for (const postData of postsWithComments) {
    for (const comment of postData.comments || []) {
      // Skip if already processed
      if (comment.from?.name === 'Page Name') continue;

      processed.total_comments++;

      try {
        const replyResult = await smartAutoReply(comment);
        if (replyResult.success) {
          processed.auto_replies_sent++;
        }
      } catch (error) {
        processed.errors++;
        logError('auto_reply_failed', { comment_id: comment.id, error: error.message });
      }
    }
  }

  logProcessingSummary(processed);
  return processed;
}

/**
 * Generate engagement report
 */
function generateEngagementReport(days = 7) {
  const since = new Date();
  since.setDate(since.getDate() - days);

  const report = {
    report_type: 'facebook_engagement',
    period: {
      days,
      from: since.toISOString(),
      to: new Date().toISOString(),
    },
    generated_at: new Date().toISOString(),
    posts: [],
    total_comments: 0,
    total_reactions: 0,
    sentiment_analysis: null,
    top_posts: [],
    recommendations: [],
  };

  // Get cached comments data
  const allComments = [];
  commentsCache.forEach(data => {
    allComments.push(...data.comments);
  });

  report.total_comments = allComments.length;
  
  if (allComments.length > 0) {
    report.sentiment_analysis = analyzeComments(allComments);
  }

  // Save report
  const filename = `facebook-engagement-report-${since.toISOString().split('T')[0]}-to-${new Date().toISOString().split('T')[0]}.json`;
  const filepath = path.join(DATA_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(report, null, 2));

  return report;
}

// Queue management
function savePostsQueue() {
  const filepath = path.join(DATA_DIR, 'facebook-posts-queue.json');
  fs.writeFileSync(filepath, JSON.stringify(postsQueue, null, 2));
}

function loadPostsQueue() {
  const filepath = path.join(DATA_DIR, 'facebook-posts-queue.json');
  if (fs.existsSync(filepath)) {
    const data = fs.readFileSync(filepath, 'utf-8');
    const queue = JSON.parse(data);
    postsQueue.push(...queue);
  }
}

function processScheduledPosts() {
  const now = new Date();
  
  const toPost = postsQueue.filter(post => 
    post.status === 'scheduled' && 
    new Date(post.scheduledTime) <= now
  );

  toPost.forEach(async (post) => {
    try {
      const result = await postToFacebook(post.content);
      post.status = 'posted';
      post.postedAt = result.timestamp;
      post.post_id = result.post_id;
      savePostsQueue();
    } catch (error) {
      post.status = 'failed';
      post.error = error.message;
      savePostsQueue();
    }
  });
}

// Logging functions
function logPost(content, result) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'facebook_post',
    content: { message: content.message?.substring(0, 100) },
    result: result?.id ? 'success' : 'failed',
    post_id: result?.id,
  };
  
  const logFile = path.join(LOGS_DIR, 'facebook-posts.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logSchedule(post) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'facebook_schedule',
    post_id: post.id,
    scheduled_time: post.scheduledTime,
  };
  
  const logFile = path.join(LOGS_DIR, 'facebook-schedule.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logComments(postId, comments) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'facebook_comments',
    post_id: postId,
    count: comments.length,
  };
  
  const logFile = path.join(LOGS_DIR, 'facebook-comments.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logAutoReply(commentId, reply, result) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'facebook_auto_reply',
    comment_id: commentId,
    reply: reply.substring(0, 100),
    result: result?.id ? 'success' : 'failed',
  };
  
  const logFile = path.join(LOGS_DIR, 'facebook-auto-reply.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logError(event, details) {
  const log = {
    timestamp: new Date().toISOString(),
    event,
    ...details,
  };
  
  const logFile = path.join(LOGS_DIR, 'facebook-errors.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logProcessingSummary(summary) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'facebook_processing_summary',
    ...summary,
  };
  
  const logFile = path.join(LOGS_DIR, 'facebook-processing.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

// Start scheduler
loadPostsQueue();
setInterval(processScheduledPosts, 60000); // Check every minute

// Export functions
module.exports = {
  postToFacebook,
  schedulePost,
  getPostComments,
  getPagePostsComments,
  analyzeComments,
  autoReplyToComment,
  smartAutoReply,
  processNewComments,
  generateEngagementReport,
  processScheduledPosts,
  CONFIG,
};
