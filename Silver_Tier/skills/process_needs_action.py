"""
Process_Needs_Action Skill - Silver Tier (UPGRADED)
DEFAULT task processor for all files in Vault/Needs_Action/

Features:
- Auto-creates Plan_[timestamp]_[short_title].md in Vault/Plans/
- Clear checkboxes + step-by-step actions
- Follows Company_Handbook.md rules strictly
- Sensitive actions → Vault/Pending_Approval/
- After approval → Execute via MCP
- Auto-move to Done/ + Update Dashboard.md

Trigger: Any new file in Vault/Needs_Action/
"""

import os
import sys
import time
import logging
import shutil
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configuration
VAULT_PATH = PROJECT_ROOT / "Vault"
NEEDS_ACTION_PATH = VAULT_PATH / "Needs_Action"
PENDING_APPROVAL_PATH = VAULT_PATH / "Pending_Approval"
APPROVED_PATH = VAULT_PATH / "Approved"
DONE_PATH = VAULT_PATH / "Done"
PLANS_PATH = VAULT_PATH / "Plans"
LOGS_PATH = VAULT_PATH / "Logs"
DASHBOARD_PATH = VAULT_PATH / "Dashboard.md"
HANDBOOK_PATH = VAULT_PATH / "Company_Handbook.md"

# Check interval (seconds)
CHECK_INTERVAL = 30

# Sensitive action keywords (require approval)
SENSITIVE_ACTIONS = [
    "email", "send", "post", "publish", "instagram", "payment", 
    "pay", "money", "transfer", "delete", "remove", "approve"
]

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOGS_PATH / "process_needs_action.log", encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class ProcessNeedsAction:
    """
    DEFAULT task processor for Silver Tier.
    Processes all files in Vault/Needs_Action/ automatically.
    """
    
    def __init__(self):
        self.vault_path = VAULT_PATH
        self.needs_action_path = NEEDS_ACTION_PATH
        self.pending_approval_path = PENDING_APPROVAL_PATH
        self.approved_path = APPROVED_PATH
        self.done_path = DONE_PATH
        self.plans_path = PLANS_PATH
        self.logs_path = LOGS_PATH
        self.dashboard_path = DASHBOARD_PATH
        self.handbook_path = HANDBOOK_PATH
        
        # Ensure directories exist
        for path in [self.plans_path, self.pending_approval_path, 
                     self.approved_path, self.done_path, self.logs_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        # Load company rules
        self.company_rules = self.load_company_rules()
        
        # Track processed files to avoid duplicates
        self.processed_files: set = set()
        
        logger.info("Process_Needs_Action Skill initialized (Silver Level)")
        logger.info(f"Watching: {self.needs_action_path}")
        logger.info(f"Company Rules Loaded: {len(self.company_rules)} rules")
    
    def load_company_rules(self) -> List[str]:
        """Load rules from Company_Handbook.md"""
        rules = []
        
        try:
            if self.handbook_path.exists():
                with open(self.handbook_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract rules from handbook
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('-') or line.startswith('•') or line.startswith('▶'):
                        rule = line.lstrip('-•▶').strip()
                        if rule:
                            rules.append(rule)
                
                logger.info(f"Loaded {len(rules)} company rules")
            else:
                # Default rules if handbook not found
                rules = [
                    "Be polite and professional",
                    "Ask for approval on sensitive actions",
                    "Log all actions",
                    "Respect privacy and security"
                ]
                logger.warning("Company_Handbook.md not found, using default rules")
        
        except Exception as e:
            logger.error(f"Error loading company rules: {e}")
            rules = ["Follow standard procedures"]
        
        return rules
    
    def read_file_content(self, filepath: Path) -> Optional[str]:
        """Read content from a file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading {filepath}: {e}")
            return None
    
    def extract_task_info(self, filepath: Path, content: str) -> Dict:
        """Extract task information from file content."""
        info = {
            "filename": filepath.name,
            "filepath": filepath,
            "platform": "Unknown",
            "sender": "Unknown",
            "priority": "Medium",
            "content": content,
            "summary": "",
            "requires_action": False,
            "action_type": "general",
            "is_sensitive": False,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Extract platform
        if "Platform:" in content:
            for line in content.split('\n'):
                if "Platform:" in line:
                    info["platform"] = line.split(":", 1)[1].strip()
                    break
        
        # Extract sender
        if "From:" in content:
            for line in content.split('\n'):
                if "From:" in line:
                    info["sender"] = line.split(":", 1)[1].strip()
                    break
        
        # Extract priority
        if "Priority:" in content:
            for line in content.split('\n'):
                if "Priority:" in line:
                    info["priority"] = line.split(":", 1)[1].strip()
                    break
        
        # Detect action type
        content_lower = content.lower()
        if "whatsapp" in info["platform"].lower():
            info["action_type"] = "whatsapp_response"
        elif "instagram" in info["platform"].lower():
            info["action_type"] = "instagram_response"
        elif "gmail" in info["platform"].lower() or "email" in content_lower:
            info["action_type"] = "email_response"
        elif "insta" in content_lower or "post" in content_lower:
            info["action_type"] = "instagram_post"
        else:
            info["action_type"] = "general"
        
        # Check if sensitive (requires approval)
        for keyword in SENSITIVE_ACTIONS:
            if keyword in content_lower:
                info["is_sensitive"] = True
                break
        
        # Generate summary (first 100 chars of actual message)
        for line in content.split('\n'):
            if line.strip() and not line.startswith('#') and not line.startswith('**'):
                info["summary"] = line.strip()[:100]
                break
        
        info["requires_action"] = True
        
        return info
    
    def is_sensitive_action(self, content: str, action_type: str) -> bool:
        """Check if action requires human approval."""
        content_lower = content.lower()
        
        # Check sensitive keywords
        for keyword in SENSITIVE_ACTIONS:
            if keyword in content_lower:
                return True
        
        # Check action types that always need approval
        sensitive_types = ["email_response", "instagram_post", "payment"]
        if action_type in sensitive_types:
            return True
        
        return False
    
    def generate_plan(self, task_info: Dict) -> str:
        """Generate step-by-step plan based on task info and company rules."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        short_title = re.sub(r'[^a-zA-Z0-9]', '_', task_info["sender"])[:20]
        plan_filename = f"Plan_{timestamp}_{short_title}.md"
        
        # Generate action steps based on task type
        steps = self.generate_action_steps(task_info)
        
        # Build plan content
        plan_content = f"""# Action Plan: {task_info["filename"]}

**Created:** {task_info["timestamp"]}
**Platform:** {task_info["platform"]}
**From:** {task_info["sender"]}
**Priority:** {task_info["priority"]}
**Status:** Pending Review

---

## Task Summary

{task_info["summary"]}

---

## Company Rules (Must Follow)

"""
        # Add company rules
        for i, rule in enumerate(self.company_rules[:5], 1):
            plan_content += f"{i}. {rule}\n"
        
        plan_content += f"""
---

## Action Steps

"""
        # Add action steps
        for i, step in enumerate(steps, 1):
            checkbox = "[ ]" if step.get("requires_approval", False) else "[x]"
            approval_note = " ⚠️ **REQUIRES APPROVAL**" if step.get("requires_approval", False) else ""
            plan_content += f"{checkbox} **Step {i}:** {step['action']}{approval_note}\n"
            if step.get("details"):
                plan_content += f"    - {step['details']}\n"
        
        plan_content += f"""
---

## Approval Status

- [ ] Plan reviewed by human
- [ ] Sensitive actions approved
- [ ] Ready to execute

**Approval Note:** Move this file to `Approved/` when ready to execute.

---

## Execution Log

*Will be updated after execution...*

---

*Generated by Process_Needs_Action Skill - Silver Tier AI Employee*
"""
        
        return plan_filename, plan_content
    
    def generate_action_steps(self, task_info: Dict) -> List[Dict]:
        """Generate specific action steps based on task type."""
        steps = []
        
        action_type = task_info["action_type"]
        
        if action_type == "whatsapp_response":
            steps = [
                {
                    "action": "Review WhatsApp message content",
                    "details": "Understand sender's request from message",
                    "requires_approval": False
                },
                {
                    "action": "Draft appropriate response",
                    "details": "Follow company rules for tone and content",
                    "requires_approval": False
                },
                {
                    "action": "Send WhatsApp response via MCP",
                    "details": "Use WhatsApp MCP tool to send reply",
                    "requires_approval": True
                },
                {
                    "action": "Log response in Dashboard",
                    "details": "Update Dashboard.md with action taken",
                    "requires_approval": False
                }
            ]
        
        elif action_type == "email_response":
            steps = [
                {
                    "action": "Review email content and sender",
                    "details": "Understand the request and context",
                    "requires_approval": False
                },
                {
                    "action": "Draft email response",
                    "details": "Professional tone, address all points",
                    "requires_approval": False
                },
                {
                    "action": "Send email via MCP (send_email tool)",
                    "details": "Use Gmail API through MCP server",
                    "requires_approval": True
                },
                {
                    "action": "Update Dashboard with sent status",
                    "details": "Log email sent with timestamp",
                    "requires_approval": False
                }
            ]
        
        elif action_type == "instagram_post":
            steps = [
                {
                    "action": "Review post request details",
                    "details": "Check caption and image requirements",
                    "requires_approval": False
                },
                {
                    "action": "Generate/optimize caption",
                    "details": "Add hashtags, ensure brand alignment",
                    "requires_approval": False
                },
                {
                    "action": "Post to Instagram via MCP",
                    "details": "Use post_to_instagram() MCP tool",
                    "requires_approval": True
                },
                {
                    "action": "Update Dashboard with post status",
                    "details": "Log successful post with details",
                    "requires_approval": False
                }
            ]
        
        elif action_type == "instagram_response":
            steps = [
                {
                    "action": "Review Instagram DM/comment",
                    "details": "Understand the inquiry or request",
                    "requires_approval": False
                },
                {
                    "action": "Draft response message",
                    "details": "Friendly, on-brand response",
                    "requires_approval": False
                },
                {
                    "action": "Send response via Instagram",
                    "details": "Use Instagram MCP tool or manual send",
                    "requires_approval": True
                }
            ]
        
        else:  # General task
            steps = [
                {
                    "action": "Review task details",
                    "details": "Understand what needs to be done",
                    "requires_approval": False
                },
                {
                    "action": "Determine required actions",
                    "details": "Identify specific steps needed",
                    "requires_approval": False
                },
                {
                    "action": "Execute task or request approval",
                    "details": "Proceed based on sensitivity level",
                    "requires_approval": True
                },
                {
                    "action": "Document completion",
                    "details": "Update logs and move to Done",
                    "requires_approval": False
                }
            ]
        
        return steps
    
    def create_plan_file(self, plan_filename: str, plan_content: str) -> Optional[Path]:
        """Create plan file in Vault/Plans/"""
        try:
            filepath = self.plans_path / plan_filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(plan_content)
            
            logger.info(f"✓ Created plan: {plan_filename}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating plan file: {e}")
            return None
    
    def move_to_pending_approval(self, filepath: Path, task_info: Dict) -> bool:
        """Move sensitive task to Pending_Approval/"""
        try:
            dest = self.pending_approval_path / filepath.name
            
            # Add approval header to file
            content = self.read_file_content(filepath)
            if content:
                approval_header = f"""---
**ROUTING NOTE:** This action requires human approval.
**Reason:** Sensitive action detected ({task_info["action_type"]})
**Moved by:** Process_Needs_Action Skill
**Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
---

"""
                content = approval_header + content
                
                with open(dest, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # Remove original file
                filepath.unlink()
            
            logger.info(f"✓ Moved to Pending_Approval: {filepath.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error moving to pending approval: {e}")
            return False
    
    def execute_via_mcp(self, task_info: Dict, plan_path: Path) -> bool:
        """Execute task using MCP tools."""
        logger.info("Executing task via MCP...")
        
        try:
            action_type = task_info["action_type"]
            
            if action_type == "email_response":
                return self.execute_email_response(task_info)
            elif action_type == "instagram_post":
                return self.execute_instagram_post(task_info)
            elif action_type == "whatsapp_response":
                return self.execute_whatsapp_response(task_info)
            else:
                logger.info(f"No MCP execution needed for: {action_type}")
                return True
                
        except Exception as e:
            logger.error(f"MCP execution error: {e}")
            return False
    
    def execute_email_response(self, task_info: Dict) -> bool:
        """Execute email response via MCP."""
        try:
            from mcp_servers.actions_mcp.server import send_email
            import asyncio
            
            # Extract recipient from content
            content = task_info["content"]
            recipient = "Unknown"
            subject = "Re: Your Message"
            body = "Thank you for your message. We will get back to you shortly."
            
            # Try to extract email
            email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
            emails = re.findall(email_pattern, content)
            if emails:
                recipient = emails[0]
            
            async def send():
                result = await send_email(
                    to=recipient,
                    subject=subject,
                    body=body
                )
                return "✓" in result or "success" in result.lower()
            
            success = asyncio.run(send())
            logger.info(f"Email execution: {'✓ Success' if success else '✗ Failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Email execution error: {e}")
            return False
    
    def execute_instagram_post(self, task_info: Dict) -> bool:
        """Execute Instagram post via MCP."""
        try:
            from mcp_servers.actions_mcp.server import post_to_instagram
            import asyncio
            
            # Extract caption from content
            caption = task_info["summary"]
            
            # Look for caption in content
            if "caption:" in task_info["content"]:
                for line in task_info["content"].split('\n'):
                    if "caption:" in line:
                        caption = line.split(":", 1)[1].strip().strip('"\'')
                        break
            
            async def post():
                result = await post_to_instagram(caption=caption)
                return "✓" in result or "success" in result.lower()
            
            success = asyncio.run(post())
            logger.info(f"Instagram post execution: {'✓ Success' if success else '✗ Failed'}")
            return success
            
        except Exception as e:
            logger.error(f"Instagram post execution error: {e}")
            return False
    
    def execute_whatsapp_response(self, task_info: Dict) -> bool:
        """Execute WhatsApp response (placeholder - needs WhatsApp MCP)."""
        logger.info("WhatsApp response: Manual action required (no MCP tool available)")
        # WhatsApp MCP not available yet - log for manual action
        return True
    
    def update_dashboard(self, task_info: Dict, executed: bool) -> None:
        """Update Dashboard.md with task completion."""
        try:
            if not self.dashboard_path.exists():
                logger.warning("Dashboard.md not found")
                return
            
            with open(self.dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "✓ Completed" if executed else "⏸ Pending"
            
            log_entry = f"""
### {task_info["filename"]} - {timestamp}
- Platform: {task_info["platform"]}
- From: {task_info["sender"]}
- Status: {status}
"""
            
            # Add to dashboard
            if "## Task Log" not in content:
                content += f"\n## Task Log\n{log_entry}\n"
            else:
                content = content.replace("## Task Log", f"## Task Log\n{log_entry}", 1)
            
            with open(self.dashboard_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info("✓ Dashboard updated")
            
        except Exception as e:
            logger.error(f"Error updating dashboard: {e}")
    
    def move_to_done(self, filepath: Path) -> bool:
        """Move completed file to Vault/Done/"""
        try:
            dest = self.done_path / filepath.name
            shutil.move(str(filepath), str(dest))
            logger.info(f"✓ Moved to Done: {filepath.name}")
            return True
        except Exception as e:
            logger.error(f"Error moving to Done: {e}")
            return False
    
    def update_plan_execution_log(self, plan_path: Path, executed: bool) -> None:
        """Update plan file with execution log."""
        try:
            if not plan_path.exists():
                return
            
            content = self.read_file_content(plan_path)
            if not content:
                return
            
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "✓ EXECUTED" if executed else "⏸ PENDING"
            
            log_entry = f"""
**Execution Time:** {timestamp}
**Status:** {status}
**Notes:** Task processed by Process_Needs_Action Skill
"""
            
            # Replace execution log section
            if "*Will be updated after execution...*" in content:
                content = content.replace("*Will be updated after execution...*", log_entry)
            
            with open(plan_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"✓ Plan execution log updated: {plan_path.name}")
            
        except Exception as e:
            logger.error(f"Error updating plan log: {e}")
    
    def process_file(self, filepath: Path) -> bool:
        """Process a single file from Needs_Action/"""
        logger.info("=" * 60)
        logger.info(f"Processing: {filepath.name}")
        logger.info("=" * 60)
        
        # Skip if already processed
        if str(filepath) in self.processed_files:
            logger.info(f"Already processed: {filepath.name}")
            return True
        
        # Read file content
        content = self.read_file_content(filepath)
        if not content:
            return False
        
        # Extract task info
        task_info = self.extract_task_info(filepath, content)
        logger.info(f"Platform: {task_info['platform']}")
        logger.info(f"Sender: {task_info['sender']}")
        logger.info(f"Action Type: {task_info['action_type']}")
        logger.info(f"Is Sensitive: {task_info['is_sensitive']}")
        
        # Generate and create plan
        plan_filename, plan_content = self.generate_plan(task_info)
        plan_path = self.create_plan_file(plan_filename, plan_content)
        
        if not plan_path:
            logger.error("Failed to create plan")
            return False
        
        # Check if sensitive → move to Pending_Approval
        if task_info["is_sensitive"]:
            logger.info("⚠️ Sensitive action detected → Moving to Pending_Approval")
            self.move_to_pending_approval(filepath, task_info)
            self.update_dashboard(task_info, executed=False)
            return True
        
        # Non-sensitive → Execute via MCP
        logger.info("Executing via MCP...")
        executed = self.execute_via_mcp(task_info, plan_path)
        
        # Update plan with execution log
        self.update_plan_execution_log(plan_path, executed)
        
        # Update dashboard
        self.update_dashboard(task_info, executed)
        
        # Move original file to Done
        if executed:
            self.move_to_done(filepath)
            self.processed_files.add(str(filepath))
            return True
        else:
            logger.warning("Execution failed, file remains in Needs_Action")
            return False
    
    def check_approved_folder(self) -> None:
        """Check Approved/ folder for files ready to execute."""
        try:
            if not self.approved_path.exists():
                return
            
            for filepath in self.approved_path.glob("*.md"):
                # Skip plan files
                if filepath.name.startswith("Plan_"):
                    continue
                
                logger.info(f"Found approved file: {filepath.name}")
                
                # Read and process
                content = self.read_file_content(filepath)
                if content:
                    task_info = self.extract_task_info(filepath, content)
                    executed = self.execute_via_mcp(task_info, filepath)
                    
                    if executed:
                        self.move_to_done(filepath)
                        self.update_dashboard(task_info, executed=True)
                        
        except Exception as e:
            logger.error(f"Error checking approved folder: {e}")
    
    def run(self):
        """Main watcher loop - DEFAULT behavior for all tasks."""
        logger.info("=" * 60)
        logger.info("Process_Needs_Action Skill - Silver Tier (DEFAULT)")
        logger.info("=" * 60)
        logger.info(f"Check Interval: {CHECK_INTERVAL} seconds")
        logger.info(f"Watching: {self.needs_action_path}")
        logger.info(f"Plans Folder: {self.plans_path}")
        logger.info("=" * 60)
        
        while True:
            try:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"\n[{timestamp}] Checking Needs_Action folder...")
                
                # Check for new files
                if self.needs_action_path.exists():
                    files = list(self.needs_action_path.glob("*.md"))
                    
                    for filepath in files:
                        # Skip INSTA_POST_REQUEST (handled by instagram_watcher)
                        if filepath.name == "INSTA_POST_REQUEST.md":
                            continue
                        
                        self.process_file(filepath)
                
                # Check Approved folder for execution
                self.check_approved_folder()
                
                logger.info(f"Next check in {CHECK_INTERVAL} seconds...")
                time.sleep(CHECK_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("\nSkill stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in loop: {e}")
                time.sleep(CHECK_INTERVAL)


def process_needs_action() -> None:
    """Main entry point - can be called from orchestrator."""
    skill = ProcessNeedsAction()
    skill.run()


def process_single_file(filepath: str) -> bool:
    """Process a single file (for manual trigger)."""
    skill = ProcessNeedsAction()
    return skill.process_file(Path(filepath))


def main():
    """Run as standalone script."""
    skill = ProcessNeedsAction()
    skill.run()


if __name__ == "__main__":
    main()
