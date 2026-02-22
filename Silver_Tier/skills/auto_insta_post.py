"""
Auto Instagram Post Skill for Silver Tier
Generates professional Instagram captions and creates post requests

Skill Name: Generate_Instagram_Post

Features:
- Reads Vault/Dashboard.md for business context
- Reads Vault/Company_Handbook.md for brand guidelines
- Generates engaging, professional captions
- Creates INSTA_POST_REQUEST.md in Needs_Action/
- Includes approval workflow note
"""

import os
import sys
import random
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
DASHBOARD_PATH = VAULT_PATH / "Dashboard.md"
HANDBOOK_PATH = VAULT_PATH / "Company_Handbook.md"
LOGS_PATH = VAULT_PATH / "Logs"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_PATH / "auto_insta_post.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class InstagramPostGenerator:
    """Generate professional Instagram posts for business."""
    
    def __init__(self):
        self.vault_path = VAULT_PATH
        self.needs_action_path = NEEDS_ACTION_PATH
        self.dashboard_path = DASHBOARD_PATH
        self.handbook_path = HANDBOOK_PATH
        self.logs_path = LOGS_PATH
        
        # Ensure directories exist
        self.needs_action_path.mkdir(parents=True, exist_ok=True)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Hashtag categories
        self.hashtags = {
            "business": [
                "#Business", "#Entrepreneur", "#Success", "#Motivation", 
                "#BusinessOwner", "#Startup", "#Growth", "#Leadership"
            ],
            "tech": [
                "#Technology", "#AI", "#Innovation", "#Tech", "#Digital",
                "#Automation", "#Future", "#Software", "#Coding"
            ],
            "creative": [
                "#Creative", "#Design", "#Art", "#Inspiration", "#CreativeProcess",
                "#Artist", "#DesignThinking", "#Innovation"
            ],
            "engagement": [
                "#Follow", "#Like", "#Share", "#Comment", "#Engage",
                "#Community", "#FollowUs", "#InstaDaily"
            ],
            "trending": [
                "#Trending", "#Viral", "#Explore", "#ExplorePage", "#FYP",
                "#InstaGood", "#PhotoOfTheDay", "#Daily"
            ]
        }
        
        # Call-to-action phrases
        self.ctas = [
            "💬 Drop a comment below!",
            "👉 Tag someone who needs to see this!",
            "🔗 Link in bio for more info!",
            "💾 Save this for later!",
            "📲 Share with your network!",
            "✨ Double-tap if you agree!",
            "🚀 Ready to get started? DM us!",
            "📩 Contact us today!",
        ]
        
        # Emoji sets for different tones
        self.emoji_sets = {
            "professional": ["💼", "📊", "📈", "✅", "🎯", "💡", "🔥", "⭐"],
            "friendly": ["😊", "👋", "💕", "🌟", "✨", "🎉", "🙌", "💫"],
            "energetic": ["🚀", "⚡", "💪", "🔥", "💯", "🎯", "🏆", "⭐"],
            "creative": ["🎨", "✨", "💡", "🌈", "🦋", "🌸", "⭐", "💫"],
        }
        
        logger.info("Instagram Post Generator initialized")
    
    def read_file(self, filepath: Path) -> Optional[str]:
        """Read content from a file."""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return f.read()
                logger.info(f"Read: {filepath}")
            else:
                logger.warning(f"File not found: {filepath}")
                return None
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None
    
    def extract_business_context(self, dashboard_content: str) -> dict:
        """Extract business context from Dashboard.md."""
        context = {
            "business_name": "Our Business",
            "industry": "general",
            "recent_activities": [],
            "goals": []
        }
        
        if not dashboard_content:
            return context
        
        # Try to extract business name
        if "Company:" in dashboard_content:
            for line in dashboard_content.split('\n'):
                if "Company:" in line:
                    context["business_name"] = line.split(":", 1)[1].strip()
                    break
        
        # Extract industry keywords
        industry_keywords = ["tech", "AI", "software", "service", "product", "consulting"]
        content_lower = dashboard_content.lower()
        for keyword in industry_keywords:
            if keyword in content_lower:
                context["industry"] = keyword
                break
        
        # Extract recent activities from logs or notes
        if "## Instagram Posts" in dashboard_content:
            section = dashboard_content.split("## Instagram Posts")[1]
            if "\n##" in section:
                section = section.split("\n##")[0]
            context["recent_activities"] = section.strip().split('\n')[:5]
        
        logger.info(f"Business Context: {context['business_name']} - {context['industry']}")
        return context
    
    def extract_brand_guidelines(self, handbook_content: str) -> dict:
        """Extract brand guidelines from Company_Handbook.md."""
        guidelines = {
            "tone": "professional",
            "rules": [],
            "values": []
        }
        
        if not handbook_content:
            return guidelines
        
        # Extract tone from content
        tone_keywords = {
            "professional": ["professional", "formal", "corporate", "business"],
            "friendly": ["friendly", "casual", "warm", "welcoming"],
            "energetic": ["energetic", "bold", "dynamic", "exciting"],
            "creative": ["creative", "artistic", "unique", "innovative"],
        }
        
        content_lower = handbook_content.lower()
        for tone, keywords in tone_keywords.items():
            if any(kw in content_lower for kw in keywords):
                guidelines["tone"] = tone
                break
        
        # Extract rules
        if "Rules:" in handbook_content or "##" in handbook_content:
            for line in handbook_content.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    guidelines["rules"].append(line.strip())
        
        logger.info(f"Brand Tone: {guidelines['tone']}")
        return guidelines
    
    def generate_caption(self, context: dict, guidelines: dict, topic: Optional[str] = None) -> str:
        """Generate a professional Instagram caption."""
        
        # Select appropriate emojis based on tone
        emojis = self.emoji_sets.get(guidelines["tone"], self.emoji_sets["professional"])
        
        # Select hashtags based on industry
        industry = context.get("industry", "general")
        selected_hashtags = []
        
        if industry in self.hashtags:
            selected_hashtags = random.sample(self.hashtags[industry], min(5, len(self.hashtags[industry])))
        
        # Always add some general hashtags
        selected_hashtags.extend(random.sample(self.hashtags["engagement"], 2))
        selected_hashtags.extend(random.sample(self.hashtags["trending"], 2))
        
        # Generate caption structure
        structures = [
            # Structure 1: Hook + Value + CTA
            "{hook}\n\n{value}\n\n{cta}\n\n{hashtags}",
            
            # Structure 2: Question + Solution + CTA
            "{question}\n\n{solution}\n\n{cta}\n\n{hashtags}",
            
            # Structure 3: Story + Lesson + CTA
            "{story_intro}\n\n{lesson}\n\n{cta}\n\n{hashtags}",
            
            # Structure 4: Announcement + Details + CTA
            "{announcement}\n\n{details}\n\n{cta}\n\n{hashtags}",
        ]
        
        # Generate content based on topic or business context
        business_name = context.get("business_name", "Our Business")
        
        # Hooks
        hooks = [
            f"{random.choice(emojis)} Exciting news from {business_name}!",
            f"{random.choice(emojis)} Ready to level up your business?",
            f"{random.choice(emojis)} Here's something you need to know!",
            f"{random.choice(emojis)} Game-changer alert! 🚀",
            f"{random.choice(emojis)} Welcome to the future of {industry}!",
        ]
        
        # Value propositions
        values = [
            f"At {business_name}, we're committed to delivering excellence.",
            f"Your success is our priority. Let's grow together!",
            f"Innovation meets expertise. That's the {business_name} difference.",
            f"Transforming ideas into reality, one project at a time.",
        ]
        
        # Questions
        questions = [
            f"{random.choice(emojis)} Want to know the secret to success?",
            f"{random.choice(emojis)} Ready to take your business to the next level?",
            f"{random.choice(emojis)} What's holding you back from growth?",
        ]
        
        # Solutions
        solutions = [
            f"The answer? Strategic planning + expert execution.",
            f"We've got you covered with our proven solutions.",
            f"Let our team help you achieve your goals faster.",
        ]
        
        # Story intros
        story_intros = [
            f"{random.choice(emojis)} Behind every success is a story...",
            f"{random.choice(emojis)} Here's what happened at {business_name}...",
            f"{random.choice(emojis)} Today's journey begins with...",
        ]
        
        # Lessons
        lessons = [
            "Consistency + dedication = results that speak for themselves.",
            "The key to growth? Never stop learning and adapting.",
            "Success isn't just about the destination—it's about the journey.",
        ]
        
        # Announcements
        announcements = [
            f"{random.choice(emojis)} Big news from {business_name}!",
            f"{random.choice(emojis)} We're thrilled to announce...",
            f"{random.choice(emojis)} Something amazing is coming!",
        ]
        
        # Details
        details = [
            "Stay tuned for more updates. You won't want to miss this!",
            "Our team has been working hard to bring you the best.",
            "This is just the beginning of something great.",
        ]
        
        # Build caption components
        caption_data = {
            "hook": random.choice(hooks),
            "value": random.choice(values),
            "question": random.choice(questions),
            "solution": random.choice(solutions),
            "story_intro": random.choice(story_intros),
            "lesson": random.choice(lessons),
            "announcement": random.choice(announcements),
            "details": random.choice(details),
            "cta": random.choice(self.ctas),
            "hashtags": " ".join(selected_hashtags),
        }
        
        # Select and format structure
        structure = random.choice(structures)
        caption = structure.format(**caption_data)
        
        return caption
    
    def create_post_request(self, caption: str, image_path: Optional[str] = None) -> Optional[Path]:
        """Create INSTA_POST_REQUEST.md in Needs_Action/"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = "INSTA_POST_REQUEST.md"
        filepath = self.needs_action_path / filename
        
        content = f"""# Instagram Post Request

**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Status:** pending_approval
**Skill:** Generate_Instagram_Post

---

## Post Details

caption: "{caption}"

image_path: {image_path if image_path else "None"}

---

## Approval Workflow

⚠️ **IMPORTANT:** Move this file to `Approved/` folder to post to Instagram.

1. Review the caption above
2. Add image_path if you want to include an image
3. Move file to: `Vault/Approved/`
4. Instagram Watcher will process and post
5. File will auto-move to `Vault/Done/` after posting

---

## Quick Actions

- To Approve: Move to `Approved/` folder
- To Edit: Modify caption or image_path, then move to `Approved/`
- To Cancel: Delete this file or move to `Logs/`

---

*Generated by Auto Instagram Post Skill - Silver Tier AI Employee*
"""
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✓ Created post request: {filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating file: {e}")
            return None
    
    def generate_and_create(self, topic: Optional[str] = None) -> Optional[Path]:
        """Main function: Generate caption and create request file."""
        logger.info("=" * 50)
        logger.info("Generating Instagram Post")
        logger.info("=" * 50)
        
        # Read source files
        dashboard_content = self.read_file(self.dashboard_path)
        handbook_content = self.read_file(self.handbook_path)
        
        # Extract context and guidelines
        context = self.extract_business_context(dashboard_content or "")
        guidelines = self.extract_brand_guidelines(handbook_content or "")
        
        # Generate caption
        caption = self.generate_caption(context, guidelines, topic)
        
        logger.info(f"Generated Caption:\n{caption[:200]}...")
        
        # Create request file
        filepath = self.create_post_request(caption, image_path=None)
        
        if filepath:
            logger.info("=" * 50)
            logger.info("✓ Instagram post request created!")
            logger.info(f"File: {filepath}")
            logger.info("Next: Move to Approved/ to post")
            logger.info("=" * 50)
        
        return filepath


def auto_insta_post(filename: str = "") -> Optional[Path]:
    """
    Skill function: Generate_Instagram_Post
    
    Can be called from orchestrator or other scripts.
    
    Args:
        filename: Optional filename that triggered this skill
    
    Returns:
        Path to created file or None
    """
    logger.info(f"Skill triggered: Generate_Instagram_Post")
    logger.info(f"Trigger file: {filename}")
    
    generator = InstagramPostGenerator()
    return generator.generate_and_create()


def Generate_Instagram_Post(topic: Optional[str] = None) -> Optional[Path]:
    """
    Alias for auto_insta_post - can be called directly.
    
    Args:
        topic: Optional topic/theme for the post
    
    Returns:
        Path to created INSTA_POST_REQUEST.md
    """
    return auto_insta_post(topic)


def main():
    """Run the skill directly."""
    print("=" * 60)
    print("Auto Instagram Post Skill - Silver Tier")
    print("=" * 60)
    
    generator = InstagramPostGenerator()
    result = generator.generate_and_create()
    
    if result:
        print(f"\n✓ Success! Post request created:")
        print(f"  {result}")
        print("\nNext steps:")
        print("  1. Review the caption in the file")
        print("  2. Add image_path if needed")
        print("  3. Move file to Vault/Approved/ to post")
    else:
        print("\n✗ Failed to create post request")


if __name__ == "__main__":
    main()
