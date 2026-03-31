// Test Social Media Auto-Post & Comments Features

console.log('===========================================');
console.log('  SOCIAL MEDIA AUTO-POST & COMMENTS TEST');
console.log('===========================================\n');

const tests = [];

// Feature 1: Facebook Auto-Post
console.log('[1/6] Testing Facebook Auto-Post...');
try {
  const { postToFacebook, schedulePost } = require('./gold/skills/facebook-auto-post');
  console.log('       ✓ Facebook Auto-Post - Module loaded');
  console.log('         Functions: postToFacebook, schedulePost');
  tests.push({ name: 'Facebook Auto-Post', status: 'PASS' });
} catch (e) {
  console.log('       ✗ Facebook Auto-Post - FAIL:', e.message);
  tests.push({ name: 'Facebook Auto-Post', status: 'FAIL', error: e.message });
}

// Feature 2: Facebook Comments Reader
console.log('\n[2/6] Testing Facebook Comments Reader...');
try {
  const { getPostComments, getPagePostsComments, analyzeComments } = require('./gold/skills/facebook-auto-post');
  console.log('       ✓ Facebook Comments Reader - Module loaded');
  console.log('         Functions: getPostComments, getPagePostsComments, analyzeComments');
  tests.push({ name: 'Facebook Comments Reader', status: 'PASS' });
} catch (e) {
  console.log('       ✗ Facebook Comments Reader - FAIL:', e.message);
  tests.push({ name: 'Facebook Comments Reader', status: 'FAIL', error: e.message });
}

// Feature 3: LinkedIn Auto-Post
console.log('\n[3/6] Testing LinkedIn Auto-Post...');
try {
  const { postToLinkedIn, getPostComments } = require('./gold/skills/linkedin-auto-post');
  console.log('       ✓ LinkedIn Auto-Post - Module loaded');
  console.log('         Functions: postToLinkedIn, getPostComments');
  tests.push({ name: 'LinkedIn Auto-Post', status: 'PASS' });
} catch (e) {
  console.log('       ✗ LinkedIn Auto-Post - FAIL:', e.message);
  tests.push({ name: 'LinkedIn Auto-Post', status: 'FAIL', error: e.message });
}

// Feature 4: LinkedIn Comments Reader
console.log('\n[4/6] Testing LinkedIn Comments Reader...');
try {
  const { getRecentPostsComments, analyzeComments, smartAutoReply } = require('./gold/skills/linkedin-auto-post');
  console.log('       ✓ LinkedIn Comments Reader - Module loaded');
  console.log('         Functions: getRecentPostsComments, analyzeComments, smartAutoReply');
  tests.push({ name: 'LinkedIn Comments Reader', status: 'PASS' });
} catch (e) {
  console.log('       ✗ LinkedIn Comments Reader - FAIL:', e.message);
  tests.push({ name: 'LinkedIn Comments Reader', status: 'FAIL', error: e.message });
}

// Feature 5: Social Media Analytics
console.log('\n[5/6] Testing Social Media Analytics...');
try {
  const { generateSocialMediaSummary, autoPostToAll, readAllComments } = require('./gold/skills/social-media-analytics');
  console.log('       ✓ Social Media Analytics - Module loaded');
  console.log('         Functions: generateSocialMediaSummary, autoPostToAll, readAllComments');
  
  // Test summary generation
  console.log('\n       Testing summary generation...');
  generateSocialMediaSummary({ days: 7 })
    .then(summary => {
      console.log('       ✓ Social Media Summary generated');
      console.log('         Period:', summary.period.days, 'days');
      console.log('         Total Posts:', summary.totals.posts);
      console.log('         Platforms:', Object.keys(summary.platforms).join(', '));
      tests.push({ name: 'Social Media Analytics', status: 'PASS' });
    })
    .catch(e => {
      console.log('       ✗ Summary generation - FAIL:', e.message);
      tests.push({ name: 'Social Media Analytics', status: 'FAIL', error: e.message });
    })
    .then(() => {
      // Feature 6: Comment Analysis
      console.log('\n[6/6] Testing Comment Analysis...');
      const { analyzeComments } = require('./gold/skills/facebook-auto-post');
      const mockComments = [
        { message: 'Great post! Love it!', like_count: 5 },
        { message: 'When will this be available?', like_count: 2 },
        { message: 'Awesome work team! 👏', like_count: 8 },
      ];
      const analysis = analyzeComments(mockComments);
      console.log('       ✓ Comment Analysis - PASS');
      console.log('         Total Comments:', analysis.total_comments);
      console.log('         Positive:', analysis.positive);
      console.log('         Questions:', analysis.questions);
      console.log('         Top Keywords:', analysis.top_keywords.map(k => k.word).join(', ') || 'none');
      
      // Final summary
      setTimeout(() => {
        console.log('\n===========================================');
        console.log('              TEST SUMMARY');
        console.log('===========================================');
        const passed = tests.filter(t => t.status === 'PASS').length;
        const failed = tests.filter(t => t.status === 'FAIL').length;
        console.log(`Total Tests: ${tests.length}`);
        console.log(`Passed: ${passed}`);
        console.log(`Failed: ${failed}`);
        console.log('\nResults:');
        tests.forEach(t => {
          console.log(`  ${t.status === 'PASS' ? '✓' : '✗'} ${t.name}`);
        });
        console.log('\n===========================================');
        console.log(passed === tests.length ? '   ALL TESTS PASSED! 🎉' : '   SOME TESTS FAILED');
        console.log('===========================================\n');
        
        console.log('Usage Examples:');
        console.log('---------------');
        console.log('1. Auto-post to all platforms:');
        console.log('   node -e "const {autoPostToAll}=require(\'./gold/skills/social-media-analytics\'); autoPostToAll({message: \'Hello World!\'}, {platforms:[\'facebook\',\'linkedin\']}).then(r=>console.log(r));"');
        console.log('\n2. Read all comments:');
        console.log('   node -e "const {readAllComments}=require(\'./gold/skills/social-media-analytics\'); readAllComments({days:1}).then(r=>console.log(\'Total comments:\',r.total_comments));"');
        console.log('\n3. Generate social media summary:');
        console.log('   node -e "const {generateSocialMediaSummary}=require(\'./gold/skills/social-media-analytics\'); generateSocialMediaSummary({days:7}).then(r=>console.log(\'Posts:\',r.totals.posts));"');
        console.log('');
      }, 500);
    });
  
} catch (e) {
  console.log('       ✗ Social Media Analytics - FAIL:', e.message);
  tests.push({ name: 'Social Media Analytics', status: 'FAIL', error: e.message });
}
