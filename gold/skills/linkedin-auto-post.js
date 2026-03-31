/**
 * LinkedIn Auto-Post & Comments Reader
 * 
 * Features:
 * - Auto-post to LinkedIn
 * - Read and analyze comments
 * - Auto-reply to comments
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
  accessToken: process.env.LINKEDIN_ACCESS_TOKEN || '',
  organizationId: process.env.LINKEDIN_ORG_ID || '',
  personId: process.env.LINKEDIN_PERSON_ID || '',
  autoReply: process.env.LINKEDIN_AUTO_REPLY || 'false',
};

/**
 * Make LinkedIn API Request
 */
function linkedinRequest(endpoint, method = 'POST', body = {}) {
  return new Promise((resolve, reject) => {
    const url = new URL(`https://api.linkedin.com/v2/${endpoint}`);

    const options = {
      hostname: 'api.linkedin.com',
      path: url.pathname + url.search,
      method,
      headers: {
        'Authorization': `Bearer ${CONFIG.accessToken}`,
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0',
      },
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => { data += chunk; });
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (res.statusCode >= 400) {
            reject(new Error(response.message || `HTTP ${res.statusCode}`));
          } else {
            resolve(response);
          }
        } catch (e) {
          reject(e);
        }
      });
    });

    req.on('error', reject);
    
    if (body && method !== 'GET') {
      req.write(JSON.stringify(body));
    }
    
    req.end();
  });
}

/**
 * Post to LinkedIn
 */
async function postToLinkedIn(content) {
  const { text, imageUrl, title = 'Update' } = content;

  const authorUrn = CONFIG.organizationId 
    ? `urn:li:organization:${CONFIG.organizationId}`
    : `urn:li:person:${CONFIG.personId}`;

  const postContent = {
    author: authorUrn,
    lifecycleState: 'PUBLISHED',
    specificContent: {
      'com.linkedin.ugc.ShareContent': {
        shareCommentary: {
          text: text,
        },
        shareMediaCategory: imageUrl ? 'IMAGE' : 'NONE',
      },
    },
    visibility: {
      'com.linkedin.ugc.MemberNetworkVisibility': 'PUBLIC',
    },
  };

  if (imageUrl) {
    // First upload image
    const mediaId = await uploadImageToLinkedIn(imageUrl);
    postContent.specificContent['com.linkedin.ugc.ShareContent'].media = [mediaId];
  }

  const result = await linkedinRequest('ugcPosts', 'POST', postContent);

  // Log post
  logPost(content, result);

  return {
    success: !!result?.id,
    post_id: result?.id,
    platform: 'linkedin',
    timestamp: new Date().toISOString(),
  };
}

/**
 * Upload image to LinkedIn
 */
async function uploadImageToLinkedIn(imageUrl) {
  const authorUrn = CONFIG.organizationId
    ? `urn:li:organization:${CONFIG.organizationId}`
    : `urn:li:person:${CONFIG.personId}`;

  // Step 1: Initialize upload
  const initializeResponse = await linkedinRequest('assets', 'POST', {
    registerUploadRequest: {
      recipes: ['urn:li:digitalmediaRecipe:feedshare-image'],
      owner: authorUrn,
      serviceRelationships: [{
        relationshipType: 'OWNER',
        identifier: 'urn:li:userGeneratedContent',
      }],
    },
  });

  return initializeResponse.value?.asset;
}

/**
 * Get comments from a post
 */
async function getPostComments(postId) {
  // Decode post ID if it's encoded
  const decodedPostId = decodeURIComponent(postId);
  
  const result = await linkedinRequest(
    `socialActions/${encodeURIComponent(decodedPostId)}/comments`,
    'GET'
  );

  const comments = result.elements || [];

  // Log comments
  logComments(postId, comments);

  return {
    post_id: postId,
    count: comments.length,
    comments,
    paging: result.paging,
  };
}

/**
 * Get all recent posts with comments
 */
async function getRecentPostsComments(options = {}) {
  const { count = 10 } = options;

  const authorUrn = CONFIG.organizationId
    ? `urn:li:organization:${CONFIG.organizationId}`
    : `urn:li:person:${CONFIG.personId}`;

  const result = await linkedinRequest(
    `ugcPosts?q=authors&authors=${encodeURIComponent(authorUrn)}&count=${count}`,
    'GET'
  );

  const postsWithComments = [];

  for (const post of result.elements || []) {
    if (post.id) {
      const commentsData = await getPostComments(post.id);
      postsWithComments.push({
        post,
        comments: commentsData.comments,
        comment_count: commentsData.count,
      });
    }
  }

  return postsWithComments;
}

/**
 * Reply to a comment
 */
async function replyToComment(parentCommentId, message) {
  const authorUrn = CONFIG.organizationId
    ? `urn:li:organization:${CONFIG.organizationId}`
    : `urn:li:person:${CONFIG.personId}`;

  const result = await linkedinRequest('socialActions', 'POST', {
    actor: authorUrn,
    object: parentCommentId,
    message: {
      text: message,
    },
  });

  logReply(parentCommentId, message, result);

  return {
    success: !!result?.id,
    comment_id: result?.id,
  };
}

/**
 * Analyze LinkedIn comments
 */
function analyzeComments(comments) {
  const analysis = {
    total_comments: comments.length,
    total_likes: 0,
    professional_keywords: [],
    sentiment: {
      positive: 0,
      neutral: 0,
      negative: 0,
    },
    questions: 0,
    avg_comment_length: 0,
  };

  const professionalKeywords = [
    'experience', 'skills', 'opportunity', 'career', 'professional',
    'industry', 'business', 'leadership', 'management', 'strategy',
    'innovation', 'growth', 'success', 'team', 'project',
  ];

  const positiveWords = ['great', 'excellent', 'impressive', 'amazing', 'wonderful', 'congratulations', '👏', '🎉'];
  const negativeWords = ['disappointed', 'concerned', 'issue', 'problem', 'difficult'];

  let totalLength = 0;
  const keywordFrequency = {};

  comments.forEach(comment => {
    const message = (comment.message?.text || '').toLowerCase();
    totalLength += message.length;

    // Count likes (if available)
    analysis.total_likes += comment.numLikes || 0;

    // Sentiment
    if (positiveWords.some(word => message.includes(word))) {
      analysis.sentiment.positive++;
    } else if (negativeWords.some(word => message.includes(word))) {
      analysis.sentiment.negative++;
    } else {
      analysis.sentiment.neutral++;
    }

    // Questions
    if (message.includes('?')) {
      analysis.questions++;
    }

    // Professional keywords
    professionalKeywords.forEach(keyword => {
      if (message.includes(keyword)) {
        keywordFrequency[keyword] = (keywordFrequency[keyword] || 0) + 1;
      }
    });
  });

  analysis.avg_comment_length = comments.length > 0 ? Math.round(totalLength / comments.length) : 0;

  analysis.professional_keywords = Object.entries(keywordFrequency)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([keyword, count]) => ({ keyword, count }));

  return analysis;
}

/**
 * Smart auto-reply for LinkedIn
 */
async function smartAutoReply(comment) {
  const message = (comment.message?.text || '').toLowerCase();
  
  let reply = null;

  // Thank for positive/professional comments
  if (message.includes('great') || message.includes('excellent') || message.includes('congratulations')) {
    reply = 'Thank you for your kind words! We appreciate your support and engagement.';
  }
  
  // Respond to questions professionally
  else if (message.includes('?')) {
    reply = 'Thank you for your question. We\'ll review this and get back to you shortly with a detailed response.';
  }
  
  // Acknowledge feedback
  else if (message.includes('feedback') || message.includes('suggestion')) {
    reply = 'We value your feedback! Thank you for taking the time to share your thoughts.';
  }

  if (reply && CONFIG.autoReply === 'true') {
    return await replyToComment(comment.id, reply);
  }

  return { success: false, reason: 'No matching reply or auto-reply disabled' };
}

/**
 * Process new comments
 */
async function processNewComments() {
  const postsWithComments = await getRecentPostsComments({ count: 5 });
  
  const processed = {
    total_comments: 0,
    auto_replies_sent: 0,
    errors: 0,
  };

  for (const postData of postsWithComments) {
    for (const comment of postData.comments || []) {
      // Skip own comments
      if (comment.actor?.includes(CONFIG.personId) || comment.actor?.includes(CONFIG.organizationId)) {
        continue;
      }

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

  logProcessing(processed);
  return processed;
}

/**
 * Generate LinkedIn engagement report
 */
function generateEngagementReport(days = 7) {
  const since = new Date();
  since.setDate(since.getDate() - days);

  const report = {
    report_type: 'linkedin_engagement',
    period: { days, from: since.toISOString(), to: new Date().toISOString() },
    generated_at: new Date().toISOString(),
    metrics: {
      total_posts: 0,
      total_comments: 0,
      total_reactions: 0,
      engagement_rate: 0,
    },
    sentiment_analysis: null,
    top_keywords: [],
    recommendations: [],
  };

  // Save report
  const filename = `linkedin-engagement-report-${since.toISOString().split('T')[0]}.json`;
  const filepath = path.join(DATA_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(report, null, 2));

  return report;
}

// Logging functions
function logPost(content, result) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'linkedin_post',
    content: { text: content.text?.substring(0, 100) },
    result: result?.id ? 'success' : 'failed',
    post_id: result?.id,
  };
  
  const logFile = path.join(LOGS_DIR, 'linkedin-posts.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logComments(postId, comments) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'linkedin_comments',
    post_id: postId,
    count: comments.length,
  };
  
  const logFile = path.join(LOGS_DIR, 'linkedin-comments.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logReply(commentId, message, result) {
  const log = {
    timestamp: new Date().toISOString(),
    event: 'linkedin_reply',
    comment_id: commentId,
    message: message.substring(0, 100),
    result: result?.id ? 'success' : 'failed',
  };
  
  const logFile = path.join(LOGS_DIR, 'linkedin-replies.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logError(event, details) {
  const log = { timestamp: new Date().toISOString(), event, ...details };
  const logFile = path.join(LOGS_DIR, 'linkedin-errors.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

function logProcessing(summary) {
  const log = { timestamp: new Date().toISOString(), event: 'linkedin_processing', ...summary };
  const logFile = path.join(LOGS_DIR, 'linkedin-processing.jsonl');
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

// Export
module.exports = {
  postToLinkedIn,
  getPostComments,
  getRecentPostsComments,
  replyToComment,
  analyzeComments,
  smartAutoReply,
  processNewComments,
  generateEngagementReport,
  CONFIG,
};
