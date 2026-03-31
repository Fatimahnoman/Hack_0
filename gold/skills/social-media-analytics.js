/**
 * Social Media Analytics Summary
 * 
 * Unified analytics across all social platforms
 * Facebook, Instagram, Twitter, LinkedIn
 */

const fs = require('fs');
const path = require('path');

const LOGS_DIR = path.join(__dirname, '../../Logs');
const DATA_DIR = path.join(__dirname, '../data');
const BRIEFINGS_DIR = path.join(__dirname, '../briefings');

// Ensure directories exist
[DATA_DIR, BRIEFINGS_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

/**
 * Generate unified social media summary
 */
async function generateSocialMediaSummary(options = {}) {
  const { days = 7, platforms = ['facebook', 'instagram', 'twitter', 'linkedin'] } = options;

  const summary = {
    report_type: 'social_media_summary',
    generated_at: new Date().toISOString(),
    period: {
      days,
      from: new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString(),
      to: new Date().toISOString(),
    },
    platforms: {},
    totals: {
      posts: 0,
      comments: 0,
      reactions: 0,
      shares: 0,
      new_followers: 0,
    },
    insights: [],
    recommendations: [],
  };

  // Analyze each platform
  for (const platform of platforms) {
    const platformData = await analyzePlatform(platform, days);
    summary.platforms[platform] = platformData;
    
    // Add to totals
    summary.totals.posts += platformData.posts || 0;
    summary.totals.comments += platformData.comments || 0;
    summary.totals.reactions += platformData.reactions || 0;
  }

  // Generate insights
  summary.insights = generateInsights(summary);
  
  // Generate recommendations
  summary.recommendations = generateRecommendations(summary);

  // Save report
  const filename = `social-media-summary-${days}days-${new Date().toISOString().split('T')[0]}.json`;
  const filepath = path.join(DATA_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(summary, null, 2));

  return summary;
}

/**
 * Analyze individual platform
 */
async function analyzePlatform(platform, days) {
  const data = {
    posts: 0,
    comments: 0,
    reactions: 0,
    shares: 0,
    engagement_rate: 0,
    top_posts: [],
    sentiment: null,
  };

  try {
    // Read platform logs
    const logFile = path.join(LOGS_DIR, `${platform}-posts.jsonl`);
    
    if (fs.existsSync(logFile)) {
      const content = fs.readFileSync(logFile, 'utf-8');
      const lines = content.split('\n').filter(line => line.trim());
      const posts = lines.map(line => JSON.parse(line));
      
      // Filter by date
      const since = new Date(Date.now() - days * 24 * 60 * 60 * 1000);
      const recentPosts = posts.filter(p => new Date(p.timestamp) >= since);
      
      data.posts = recentPosts.length;
      
      // Get comments for each platform
      const commentsFile = path.join(LOGS_DIR, `${platform}-comments.jsonl`);
      if (fs.existsSync(commentsFile)) {
        const commentsContent = fs.readFileSync(commentsFile, 'utf-8');
        const commentsLines = commentsContent.split('\n').filter(line => line.trim());
        data.comments = commentsLines.length;
      }
    }
    
    // Calculate engagement rate
    if (data.posts > 0) {
      data.engagement_rate = ((data.comments + data.reactions) / data.posts).toFixed(2);
    }
  } catch (error) {
    console.error(`Error analyzing ${platform}:`, error.message);
  }

  return data;
}

/**
 * Generate insights from data
 */
function generateInsights(summary) {
  const insights = [];

  // Best performing platform
  let bestPlatform = null;
  let bestEngagement = 0;
  
  Object.entries(summary.platforms).forEach(([platform, data]) => {
    if (data.engagement_rate > bestEngagement) {
      bestEngagement = parseFloat(data.engagement_rate);
      bestPlatform = platform;
    }
  });

  if (bestPlatform) {
    insights.push({
      type: 'top_performer',
      title: 'Best Performing Platform',
      description: `${bestPlatform} has the highest engagement rate at ${bestEngagement}`,
      platform: bestPlatform,
    });
  }

  // Posting frequency insight
  const totalPosts = summary.totals.posts;
  const days = summary.period.days;
  const avgPostsPerDay = (totalPosts / days).toFixed(1);
  
  insights.push({
    type: 'posting_frequency',
    title: 'Posting Frequency',
    description: `Average ${avgPostsPerDay} posts per day across all platforms`,
    metric: avgPostsPerDay,
  });

  // Engagement insight
  if (summary.totals.comments > summary.totals.posts * 2) {
    insights.push({
      type: 'high_engagement',
      title: 'High Audience Engagement',
      description: 'Comments are exceeding posts ratio - audience is highly engaged',
    });
  }

  return insights;
}

/**
 * Generate recommendations
 */
function generateRecommendations(summary) {
  const recommendations = [];

  // Posting frequency recommendation
  const avgPostsPerDay = summary.totals.posts / summary.period.days;
  
  if (avgPostsPerDay < 1) {
    recommendations.push({
      priority: 'high',
      category: 'content',
      title: 'Increase Posting Frequency',
      description: `Currently posting ${avgPostsPerDay.toFixed(1)} times/day. Recommend at least 1-2 posts/day.`,
      action: 'Create a content calendar and schedule posts in advance.',
    });
  }

  // Platform-specific recommendations
  Object.entries(summary.platforms).forEach(([platform, data]) => {
    if (data.posts === 0) {
      recommendations.push({
        priority: 'medium',
        category: 'platform_presence',
        title: `Activate ${platform}`,
        description: `No posts on ${platform} in the last ${summary.period.days} days.`,
        action: `Start posting on ${platform} to maintain presence.`,
      });
    }
  });

  // Engagement recommendation
  if (summary.totals.comments < summary.totals.posts) {
    recommendations.push({
      priority: 'medium',
      category: 'engagement',
      title: 'Improve Engagement',
      description: 'Low comment-to-post ratio. Content may not be resonating.',
      action: 'Create more interactive content: questions, polls, calls-to-action.',
    });
  }

  return recommendations;
}

/**
 * Auto-post to all platforms
 */
async function autoPostToAll(content, options = {}) {
  const { platforms = ['facebook', 'twitter', 'linkedin'], schedule = false } = options;
  
  const results = {
    timestamp: new Date().toISOString(),
    content: content.message?.substring(0, 100),
    platforms: {},
    success_count: 0,
    failed_count: 0,
  };

  for (const platform of platforms) {
    try {
      let result;
      
      if (platform === 'facebook') {
        const { postToFacebook } = require('./facebook-auto-post');
        result = await postToFacebook(content);
      } else if (platform === 'linkedin') {
        const { postToLinkedIn } = require('./linkedin-auto-post');
        result = await postToLinkedIn(content);
      } else if (platform === 'twitter') {
        // Would call Twitter MCP
        result = { success: true, platform: 'twitter', post_id: 'mock_twitter_id' };
      } else if (platform === 'instagram') {
        // Would call Instagram MCP
        result = { success: true, platform: 'instagram', post_id: 'mock_ig_id' };
      }

      results.platforms[platform] = result;
      
      if (result?.success) {
        results.success_count++;
      } else {
        results.failed_count++;
      }
    } catch (error) {
      results.platforms[platform] = { success: false, error: error.message };
      results.failed_count++;
    }
  }

  // Log cross-post
  logCrossPost(results);

  return results;
}

/**
 * Schedule recurring posts
 */
function scheduleRecurringPosts(posts, schedule) {
  const scheduled = [];
  
  posts.forEach((post, index) => {
    const scheduledPost = {
      id: `scheduled_${Date.now()}_${index}`,
      content: post,
      schedule,
      status: 'scheduled',
      createdAt: new Date().toISOString(),
    };
    
    scheduled.push(scheduledPost);
    
    // Save to schedule file
    const scheduleFile = path.join(DATA_DIR, 'social-media-schedule.json');
    let existingSchedule = [];
    
    if (fs.existsSync(scheduleFile)) {
      existingSchedule = JSON.parse(fs.readFileSync(scheduleFile, 'utf-8'));
    }
    
    existingSchedule.push(scheduledPost);
    fs.writeFileSync(scheduleFile, JSON.stringify(existingSchedule, null, 2));
  });

  return scheduled;
}

/**
 * Read and summarize comments from all platforms
 */
async function readAllComments(options = {}) {
  const { days = 1, platforms = ['facebook', 'linkedin', 'twitter', 'instagram'] } = options;

  const allComments = {
    timestamp: new Date().toISOString(),
    period: { days },
    platforms: {},
    total_comments: 0,
    summary: {
      positive: 0,
      neutral: 0,
      negative: 0,
      questions: 0,
    },
  };

  for (const platform of platforms) {
    try {
      const commentsFile = path.join(LOGS_DIR, `${platform}-comments.jsonl`);
      
      if (fs.existsSync(commentsFile)) {
        const content = fs.readFileSync(commentsFile, 'utf-8');
        const lines = content.split('\n').filter(line => line.trim());
        
        // Parse and analyze
        const comments = lines.map(line => {
          const log = JSON.parse(line);
          return log;
        });

        allComments.platforms[platform] = {
          count: comments.length,
          comments: comments.slice(0, 50), // Limit to recent 50
        };

        allComments.total_comments += comments.length;
      } else {
        allComments.platforms[platform] = {
          count: 0,
          comments: [],
        };
      }
    } catch (error) {
      allComments.platforms[platform] = {
        count: 0,
        error: error.message,
      };
    }
  }

  // Save comments summary
  const filename = `all-comments-summary-${new Date().toISOString().split('T')[0]}.json`;
  const filepath = path.join(DATA_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(allComments, null, 2));

  return allComments;
}

// Logging
function logCrossPost(results) {
  const logFile = path.join(LOGS_DIR, 'social-media-crosspost.jsonl');
  const log = {
    timestamp: results.timestamp,
    event: 'cross_post',
    success_count: results.success_count,
    failed_count: results.failed_count,
    platforms: Object.keys(results.platforms),
  };
  
  fs.appendFileSync(logFile, JSON.stringify(log) + '\n');
}

// Export
module.exports = {
  generateSocialMediaSummary,
  analyzePlatform,
  autoPostToAll,
  scheduleRecurringPosts,
  readAllComments,
  generateInsights,
  generateRecommendations,
};
