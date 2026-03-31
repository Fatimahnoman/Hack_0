"""
Gold Tier Orchestrator - Complete Autonomy (Level 5)
=====================================================
The "Brain" of the Personal AI Employee.

Features:
1. Watches gold/needs_action/ folder (The Eyes)
2. Uses Gemini 1.5 Flash API to reason and plan (The Brain)
3. Generates high-quality reply drafts and action plans
4. Moves to gold/pending_approval/ for Human-in-the-Loop review
5. Triggers Action Dispatcher for approved items (The Hands)
6. Updates Dashboard.md with status

Required: pip install watchdog google-generativeai
Run: python gold/tools/gold_orchestrator.py
"""

import os
import sys
import time
import shutil
import logging
import subprocess
import json
import re
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# =============================================================================
# CONFIGURATION - GOLD TIER FOLDER ARCHITECTURE
# =============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
GOLD_DIR = PROJECT_ROOT / "gold"

# Gold Tier folders
NEEDS_ACTION_FOLDER = GOLD_DIR / "needs_action"
PENDING_APPROVAL_FOLDER = GOLD_DIR / "pending_approval"
APPROVED_FOLDER = PENDING_APPROVAL_FOLDER / "approved"
PLANS_FOLDER = GOLD_DIR / "plans"
DONE_FOLDER = GOLD_DIR / "done"
LOGS_FOLDER = GOLD_DIR / "logs"

# Other files
DASHBOARD_FILE = PROJECT_ROOT / "Dashboard.md"
COMPANY_HANDBOOK = PROJECT_ROOT / "Company_Handbook.md"
ACTION_DISPATCHER_SCRIPT = PROJECT_ROOT / "silver" / "tools" / "action_dispatcher.py"

# Gemini API Configuration
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-flash-latest"

# Ensure directories exist
for folder in [NEEDS_ACTION_FOLDER, PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, PLANS_FOLDER, DONE_FOLDER, LOGS_FOLDER]:
    folder.mkdir(parents=True, exist_ok=True)

# =============================================================================
# LOGGING SETUP
# =============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(
            LOGS_FOLDER / f"gold_orchestrator_{datetime.now().strftime('%Y%m%d')}.log",
            encoding='utf-8'
        ),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# =============================================================================
# GEMINI API INTEGRATION
# =============================================================================


def initialize_gemini():
    """Initialize Gemini API client."""
    global genai
    
    if not GEMINI_API_KEY:
        log.warning("[GEMINI] API key not found. Set GEMINI_API_KEY environment variable.")
        return None
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        log.info(f"[GEMINI] Initialized with model: {GEMINI_MODEL}")
        return genai
    except ImportError:
        log.error("[GEMINI] google-generativeai not installed. Run: pip install google-generativeai")
        return None
    except Exception as e:
        log.error(f"[GEMINI] Initialization error: {e}")
        return None


def generate_gemini_response(filename: str, content: str, company_rules: str, genai) -> dict:
    """
    Call Gemini API to analyze task and generate response.
    
    Returns dict with:
    - type: task type (email, whatsapp_message, linkedin_post_draft, action_item)
    - reply_draft: markdown content with YAML frontmatter
    - action_plan: step-by-step action plan
    """
    if not genai:
        return None
    
    prompt = f"""You are an AI Employee Orchestrator for a Gold Tier autonomous system.
Your role is to analyze incoming tasks and generate professional responses.

COMPANY RULES AND GUIDELINES:
{company_rules}

INCOMING TASK:
Filename: {filename}
Content:
{content}

YOUR TASK:
1. Analyze the intent and urgency of this message
2. Determine the appropriate response type (email reply, WhatsApp message, LinkedIn post, or action item)
3. Generate a HIGH-QUALITY professional response draft
4. Create a brief action plan for execution

OUTPUT FORMAT:
You MUST respond with a valid JSON object in this exact format:
{{
    "type": "email" or "whatsapp_message" or "linkedin_post_draft" or "action_item",
    "reply_draft": "---\\ntype: [type]\\nto: [recipient email or contact]\\nsubject: [subject if email]\\npriority: [high/medium/normal]\\nstatus: pending\\n---\\n\\n## Content\\n\\n[Your professional response here]",
    "action_plan": "# Action Plan\\n\\n1. [Step 1]\\n2. [Step 2]\\n3. [Step 3]"
}}

IMPORTANT:
- The reply_draft MUST include proper YAML frontmatter with type, to, subject, priority, and status fields
- For WhatsApp messages, use the contact name from the original message
- For emails, extract or infer the recipient email address
- For LinkedIn posts, create HIGH-CONVERTING and ENGAGING professional content. 
  Follow this strict structure:
  1. **Hook/Headline**: A bold, professional opening line to grab attention.
  2. **Body**: Use bullet points (•) for key takeaways to ensure readability.
  3. **CTA**: End with a Clear Call to Action or a thought-provoking question to drive engagement.
  4. **Hashtags**: Include exactly 2-3 highly relevant hashtags at the very bottom.
- Always maintain a professional, helpful, and slightly energetic brand voice.
- Output ONLY the JSON object, no markdown code blocks or explanations.

Generate the JSON response now:"""

    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        response = model.generate_content(prompt)
        
        # Extract JSON from response
        text = response.text.strip()
        
        # Remove markdown code blocks if present
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\n?', '', text)
            text = re.sub(r'\n?```$', '', text)
            text = text.strip()
        
        # Find JSON object
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            parsed = json.loads(json_str)
            
            # Validate required fields
            if 'reply_draft' not in parsed and 'action_plan' not in parsed:
                log.warning("[GEMINI] Response missing required fields")
                return None
            
            log.info("[GEMINI] Successfully generated response")
            return parsed
        else:
            log.warning(f"[GEMINI] No JSON found in response: {text[:200]}...")
            return None
            
    except json.JSONDecodeError as e:
        log.error(f"[GEMINI] JSON parsing error: {e}")
        return None
    except Exception as e:
        log.error(f"[GEMINI] API error: {e}")
        return None


# =============================================================================
# FILE PROCESSING
# =============================================================================


def extract_metadata(content: str) -> dict:
    """Extract metadata from YAML frontmatter."""
    metadata = {
        'type': 'unknown',
        'from': '',
        'to': '',
        'subject': '',
        'message': '',
        'priority': 'normal',
        'status': 'pending'
    }
    
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            body = parts[2].strip()
            
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    if key in metadata:
                        metadata[key] = value
            
            metadata['body'] = body
    
    return metadata


class NeedsActionHandler(FileSystemEventHandler):
    """Handles new files in gold/needs_action/ folder."""
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            log.info(f"[NEW FILE] Detected: {os.path.basename(event.src_path)}")
            # Give file time to be fully written
            time.sleep(1)
            self.orchestrator.process_file(Path(event.src_path))


class GoldOrchestrator:
    """
    The Autonomous Brain of the AI Employee.
    
    Monitors needs_action folder, processes tasks with Gemini API,
    and creates drafts in pending_approval for human review.
    """
    
    def __init__(self):
        self.company_rules = self._load_company_rules()
        self.stats = {"processed": 0, "errors": 0, "skipped": 0}
        self.genai = initialize_gemini()
        self.processed_files = set()
    
    def _load_company_rules(self) -> str:
        """Load rules from Company_Handbook.md."""
        if COMPANY_HANDBOOK.exists():
            return COMPANY_HANDBOOK.read_text(encoding='utf-8')
        return """
COMPANY VALUES:
- Always be professional and courteous
- Respond promptly to urgent matters
- Prioritize customer satisfaction
- Maintain confidentiality
- Follow up on all commitments
"""
    
    def process_file(self, filepath: Path) -> bool:
        """
        Main processing logic for a new task file.
        
        Flow:
        1. Read file content
        2. Call Gemini API for analysis
        3. Create draft in pending_approval
        4. Create action plan in plans folder
        5. Move original to done folder
        
        Returns True if successful.
        """
        log.info("=" * 70)
        log.info(f"[PROCESS] Starting: {filepath.name}")
        log.info(f"[PROCESS] Source: {filepath}")
        log.info(f"[PROCESS] File exists: {filepath.exists()}")
        log.info("=" * 70)
        
        # Check if file still exists
        if not filepath.exists():
            log.error(f"[ERROR] File no longer exists: {filepath}")
            return False
        
        # Check if already processed
        if str(filepath) in self.processed_files:
            log.info(f"[SKIP] Already processed: {filepath.name}")
            return True
        
        # Check if draft already exists for this file
        existing_drafts = list(PENDING_APPROVAL_FOLDER.glob(f"DRAFT_{filepath.stem}_*.md"))
        if existing_drafts:
            log.info(f"[SKIP] Draft already exists: {existing_drafts[0].name}")
            # Delete original to cleanly end duplicate state
            self._delete_original(filepath)
            return True
        
        try:
            # Read file content
            content = filepath.read_text(encoding='utf-8')
            log.info(f"[CONTENT] Length: {len(content)} characters")
            log.info(f"[CONTENT] Preview: {content[:200]}...")
            
            # Extract metadata
            metadata = extract_metadata(content)
            log.info(f"[META] Type: {metadata.get('type', 'unknown')}")
            log.info(f"[META] Priority: {metadata.get('priority', 'normal')}")
            
            # Call Gemini API
            log.info("[AI] Calling Gemini API for analysis...")
            response = self._generate_ai_response(filepath.name, content)
            
            if not response:
                log.error(f"[ERROR] AI failed to generate response")
                # Use fallback response
                response = self._silver_tier_fallback(filepath.name, content, metadata)
            
            # Create draft and plan files
            log.info("[HITL] Creating draft and action plan...")
            draft_created = self._handle_ai_response(filepath, response)
            
            if not draft_created:
                log.error(f"[ERROR] Failed to create any output files")
                self.stats["errors"] += 1
                self._update_dashboard(f"Failed: {filepath.name}", False)
                return False
            
            # Delete original file to prevent done/ folder confusion
            self._delete_original(filepath)
            self.processed_files.add(str(filepath))
            
            # Update stats and dashboard
            self.stats["processed"] += 1
            self._update_dashboard(f"Processed: {filepath.name}", True)
            
            log.info("=" * 70)
            log.info(f"[SUCCESS] Task completed: {filepath.name}")
            log.info(f"[SUCCESS] Draft created in pending_approval")
            log.info(f"[SUCCESS] Original moved to done")
            log.info("=" * 70)
            
            return True
            
        except Exception as e:
            log.error(f"[CRITICAL] Error processing {filepath.name}: {e}")
            log.error(f"[CRITICAL] Exception type: {type(e).__name__}")
            import traceback
            log.error(f"[CRITICAL] Traceback: {traceback.format_exc()}")
            self.stats["errors"] += 1
            self._update_dashboard(f"Failed: {filepath.name}", False)
            return False
    
    def _generate_ai_response(self, filename: str, content: str) -> dict:
        """Call Gemini API to generate response."""
        if self.genai:
            response = generate_gemini_response(filename, content, self.company_rules, self.genai)
            if response:
                return response
        
        # Fallback to silver tier if Gemini fails
        log.warning("[AI] Falling back to Silver Tier heuristic...")
        return None
    
    def _handle_ai_response(self, original_filepath: Path, response: dict) -> bool:
        """
        Create draft and plan files based on AI response.
        
        Returns True if at least one file was created.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        files_created = 0
        
        try:
            if not response or not isinstance(response, dict):
                log.error(f"[HITL] Invalid response format")
                return False
            
            # Determine target folder (always pending_approval for HITL)
            target_folder = PENDING_APPROVAL_FOLDER
            log.info(f"[HITL] Routing to: {target_folder.name}")
            
            # Create Reply Draft
            if 'reply_draft' in response:
                try:
                    draft_content = response['reply_draft']
                    if draft_content and draft_content.strip():
                        # Ensure proper YAML frontmatter
                        if not draft_content.strip().startswith('---'):
                            draft_content = self._ensure_yaml_frontmatter(draft_content, response)
                        
                        draft_name = f"DRAFT_{original_filepath.stem}_{timestamp}.md"
                        draft_path = target_folder / draft_name
                        draft_path.write_text(draft_content, encoding='utf-8')
                        log.info(f"[DRAFT] Created: {draft_name}")
                        files_created += 1
                    else:
                        log.warning("[HITL] reply_draft is empty")
                except Exception as e:
                    log.error(f"[HITL] Draft creation error: {e}")
            
            # Create Action Plan
            if 'action_plan' in response:
                try:
                    plan_content = response['action_plan']
                    if plan_content and plan_content.strip():
                        plan_name = f"PLAN_{original_filepath.stem}_{timestamp}.md"
                        plan_path = PLANS_FOLDER / plan_name
                        plan_path.write_text(plan_content, encoding='utf-8')
                        log.info(f"[PLAN] Created: {plan_name}")
                        files_created += 1
                    else:
                        log.warning("[HITL] action_plan is empty")
                except Exception as e:
                    log.error(f"[HITL] Plan creation error: {e}")
            
            return files_created > 0
            
        except Exception as e:
            log.error(f"[HITL] Critical error: {e}")
            return False
    
    def _ensure_yaml_frontmatter(self, content: str, response: dict) -> str:
        """Ensure content has proper YAML frontmatter."""
        # Extract values from response or use defaults
        task_type = response.get('type', 'email')
        to = response.get('to', 'recipient@example.com')
        subject = response.get('subject', f"Re: {datetime.now().strftime('%Y-%m-%d')}")
        priority = response.get('priority', 'normal')
        
        # Remove any existing frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                content = parts[2].strip()
        
        frontmatter = f"""---
type: {task_type}
to: {to}
subject: {subject}
priority: {priority}
status: pending
---

## Content

{content}
"""
        return frontmatter
    
    def _silver_tier_fallback(self, filename: str, content: str, metadata: dict) -> dict:
        """
        Heuristic-based response generation when AI fails.
        """
        task_type = metadata.get('type', 'email')
        
        # Determine type from content
        if 'linkedin' in content.lower():
            task_type = 'linkedin_post_draft'
        elif 'whatsapp' in filename.lower():
            task_type = 'whatsapp_message'
        
        # Extract recipient
        to = metadata.get('from', 'recipient@example.com')
        if not to or to == 'Unknown':
            to = 'recipient@example.com'
        
        # Generate subject
        subject = metadata.get('subject', f"Re: {filename}")
        
        if task_type == 'linkedin_post_draft':
            reply_draft = f"""---
type: {task_type}
to: {to}
subject: {subject}
priority: {metadata.get('priority', 'normal')}
status: pending
---

## Content

**🚀 Transforming the Workplace: The Rise of AI Employees in 2026**

As we move further into 2026, the landscape of work is changing rapidly. AI Employees are no longer just tools—they are autonomous partners driving efficiency and innovation.

• **Complete Autonomy**: Handling end-to-end workflows without constant supervision.
• **Unmatched Efficiency**: Processing tasks 24/7 with precision and speed.
• **Safety First**: Maintaining human-in-the-loop control for critical decision-making.

The future of work isn't about replacement; it's about empowerment.

#AI #Automation #FutureOfWork #WorkplaceInnovation
"""
        else:
            reply_draft = f"""---
type: {task_type}
to: {to}
subject: {subject}
priority: {metadata.get('priority', 'normal')}
status: pending
---

## Content

Thank you for your message regarding '{filename}'. We have received your inquiry and our team is reviewing it. We will get back to you with a detailed response shortly.

Best regards,
AI Employee Assistant
"""
        
        action_plan = f"""# Action Plan for {filename}

1. Review the incoming message
2. Verify recipient details
3. Send the drafted response
4. Follow up if needed
"""
        
        return {
            "type": task_type,
            "reply_draft": reply_draft,
            "action_plan": action_plan
        }
    
    def _delete_original(self, filepath: Path) -> bool:
        """Delete processed file to prevent done/ folder pollution."""
        try:
            if filepath.exists():
                filepath.unlink()
            log.info(f"[DELETED] Original file removed: {filepath.name}")
            return True
        except Exception as e:
            log.error(f"[ERROR] Delete failed: {e}")
            return False
    
    def _update_dashboard(self, activity: str, success: bool):
        """Update Dashboard.md with latest activity."""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            status_icon = '✓' if success else '✗'
            activity_line = f"- {timestamp}: {activity} {status_icon}\n"
            
            if DASHBOARD_FILE.exists():
                content = DASHBOARD_FILE.read_text(encoding='utf-8')
                
                if "## Recent Activity" in content:
                    # Insert after Recent Activity header
                    content = content.replace(
                        "## Recent Activity\n",
                        f"## Recent Activity\n{activity_line}"
                    )
                else:
                    # Add section
                    content += f"\n## Recent Activity\n{activity_line}"
                
                DASHBOARD_FILE.write_text(content, encoding='utf-8')
            else:
                # Create new dashboard
                dashboard_content = f"""# AI Employee Dashboard

**Status:** Running
**Last Update:** {timestamp}

## Statistics
- Tasks Processed: {self.stats['processed']}
- Errors: {self.stats['errors']}

## Recent Activity
{activity_line}
"""
                DASHBOARD_FILE.write_text(dashboard_content, encoding='utf-8')
                
        except Exception as e:
            log.error(f"[DASHBOARD] Update error: {e}")
    
    def trigger_action_dispatcher(self):
        """Run Action Dispatcher to process approved items."""
        if ACTION_DISPATCHER_SCRIPT.exists():
            log.info("[HANDS] Triggering Action Dispatcher...")
            subprocess.run(
                [sys.executable, str(ACTION_DISPATCHER_SCRIPT), "--once"],
                capture_output=True,
                text=True
            )
    
    def process_existing_files(self):
        """Process any existing files in needs_action folder."""
        if NEEDS_ACTION_FOLDER.exists():
            files = list(NEEDS_ACTION_FOLDER.glob("*.md"))
            log.info(f"[INIT] Found {len(files)} existing files to process")
            for f in files:
                if str(f) not in self.processed_files:
                    self.process_file(f)
    
    def run(self):
        """
        Start the Gold Orchestrator.
        
        1. Process existing files
        2. Start file watcher for new files
        3. Periodically trigger action dispatcher
        """
        log.info("=" * 70)
        log.info("GOLD ORCHESTRATOR - STARTING (LEVEL 5 AUTONOMY)")
        log.info("=" * 70)
        log.info(f"Monitoring: {NEEDS_ACTION_FOLDER}")
        log.info(f"Drafts folder: {PENDING_APPROVAL_FOLDER}")
        log.info(f"Plans folder: {PLANS_FOLDER}")
        log.info(f"Done folder: {DONE_FOLDER}")
        log.info(f"Gemini API: {'Enabled' if self.genai else 'Disabled'}")
        log.info("=" * 70)
        
        # Process existing files first
        self.process_existing_files()
        
        # Start file watcher
        event_handler = NeedsActionHandler(self)
        observer = Observer()
        observer.schedule(event_handler, str(NEEDS_ACTION_FOLDER), recursive=False)
        observer.start()
        
        log.info("[WATCHER] Started monitoring needs_action folder")
        
        try:
            while True:
                # Periodically trigger action dispatcher
                self.trigger_action_dispatcher()
                time.sleep(60)
        except KeyboardInterrupt:
            log.info("\n[STOP] Orchestrator stopped by user")
            observer.stop()
        except Exception as e:
            log.error(f"[CRITICAL] Orchestrator error: {e}")
            observer.stop()
        
        observer.join()
        
        # Print final stats
        log.info("=" * 70)
        log.info("FINAL STATISTICS")
        log.info("=" * 70)
        log.info(f"  Processed: {self.stats['processed']}")
        log.info(f"  Errors: {self.stats['errors']}")
        log.info(f"  Skipped: {self.stats['skipped']}")
        log.info("=" * 70)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


if __name__ == "__main__":
    orchestrator = GoldOrchestrator()
    orchestrator.run()
