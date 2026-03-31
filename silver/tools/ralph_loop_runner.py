"""
Ralph Wiggum Loop Runner - Silver Tier
=======================================
Implements iterative reasoning loop for processing tasks in /Needs_Action.
Uses Ralph Wiggum pattern: analyze → act → verify → repeat until complete.

DAEMON MODE:
- Continuously monitors Needs_Action folder
- Triggers Action Dispatcher for approved files
- Runs 24/7 with 60-second check interval

Install: pip install watchdog
Run: 
  python silver/tools/ralph_loop_runner.py --daemon
  python silver/tools/ralph_loop_runner.py "Process Needs_Action" --max-iterations 10
"""

import os
import re
import sys
import shutil
import argparse
import time
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
NEEDS_ACTION_FOLDER = os.path.join(PROJECT_ROOT, "Needs_Action")
DONE_FOLDER = os.path.join(PROJECT_ROOT, "Done")
PLANS_FOLDER = os.path.join(PROJECT_ROOT, "Plans")
PENDING_APPROVAL_FOLDER = os.path.join(PROJECT_ROOT, "Pending_Approval")
APPROVED_FOLDER = os.path.join(PENDING_APPROVAL_FOLDER, "Approved")
COMPANY_HANDBOOK = os.path.join(PROJECT_ROOT, "Company_Handbook.md")
ACTION_DISPATCHER_SCRIPT = os.path.join(PROJECT_ROOT, "silver", "tools", "action_dispatcher.py")

# Task type keywords
TASK_KEYWORDS = {
    "sales": ["sales", "client", "project", "lead", "opportunity"],
    "payment": ["payment", "invoice", "bill", "price", "cost"],
    "file_drop": ["file", "document", "attachment"],
    "action_item": ["action", "task", "todo", "urgent"],
    "review": ["review", "approve", "check", "verify"]
}

# Completion promise marker
COMPLETION_PROMISE = "TASK_COMPLETE"
MAX_ITERATIONS = 10


class RalphWiggumLoop:
    """Implements the Ralph Wiggum reasoning loop pattern."""
    
    def __init__(self, max_iterations=MAX_ITERATIONS):
        self.max_iterations = max_iterations
        self.iteration_count = 0
        self.processed_files = []
        self.pending_approval = []
        self.completed_tasks = []
        self.company_rules = self.load_company_rules()
    
    def load_company_rules(self) -> dict:
        """Load company rules from handbook."""
        rules = {"polite": True, "approval_threshold": 500}
        
        if os.path.exists(COMPANY_HANDBOOK):
            with open(COMPANY_HANDBOOK, "r", encoding="utf-8") as f:
                content = f.read().lower()
                rules["polite"] = "polite" in content
                rules["approval_flag"] = "$500" in content or "500" in content
        
        return rules
    
    def analyze_file(self, filepath: str) -> dict:
        """Analyze a file and determine task type."""
        result = {
            "filepath": filepath,
            "filename": os.path.basename(filepath),
            "type": "unknown",
            "priority": "normal",
            "needs_approval": False,
            "keywords_found": [],
            "content": "",
            "summary": ""
        }
        
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
                result["content"] = content
                content_lower = content.lower()
                
                # Detect task type
                for task_type, keywords in TASK_KEYWORDS.items():
                    found = [kw for kw in keywords if kw in content_lower]
                    if found:
                        result["keywords_found"].extend(found)
                        result["type"] = task_type
                
                # Determine priority
                if "urgent" in content_lower:
                    result["priority"] = "high"
                elif "invoice" in content_lower or "payment" in content_lower:
                    result["priority"] = "medium"
                
                # Check approval needed
                if result["type"] == "payment":
                    result["needs_approval"] = True
                if "linkedin" in content_lower or "post" in content_lower:
                    result["needs_approval"] = True
                
                # Generate summary
                result["summary"] = self.generate_summary(content)
        
        except Exception as e:
            result["summary"] = f"Error reading file: {e}"
        
        return result
    
    def generate_summary(self, content: str) -> str:
        """Generate brief summary of file content."""
        # Extract first meaningful lines
        lines = [l.strip() for l in content.split("\n") if l.strip() and not l.strip().startswith("---")]
        return " ".join(lines[:3])[:200]
    
    def create_plan(self, task: dict) -> str:
        """Create action plan for a task."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plan_filename = f"Plan_{task['filename']}_{timestamp}.md"
        plan_filepath = os.path.join(PLANS_FOLDER, plan_filename)
        
        # Generate action steps based on task type
        steps = self.generate_action_steps(task)
        
        plan_content = f"""---
type: action_plan
source: {task['filename']}
task_type: {task['type']}
priority: {task['priority']}
created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: in_progress
needs_approval: {str(task['needs_approval']).lower()}
---

# Action Plan: {task['filename']}

## Task Analysis
- **Type:** {task['type']}
- **Priority:** {task['priority']}
- **Keywords:** {', '.join(task['keywords_found']) if task['keywords_found'] else 'none'}
- **Summary:** {task['summary']}

## Action Steps

{self.format_steps(steps)}

## Company Rules Applied
- Polite communication: {'[OK]' if self.company_rules.get('polite') else '[MISSING]'}
- Approval flag for payments > $500: {'[OK]' if self.company_rules.get('approval_flag') else '[MISSING]'}

## Status
- [ ] Steps completed
- [ ] Ready for review
- [ ] {COMPLETION_PROMISE}

---
*Created by Ralph Wiggum Loop Runner*
"""
        
        with open(plan_filepath, "w", encoding="utf-8") as f:
            f.write(plan_content)
        
        return plan_filepath
    
    def generate_action_steps(self, task: dict) -> list:
        """Generate action steps based on task type."""
        steps = []
        
        if task["type"] == "sales":
            steps = [
                "Review sales lead details",
                "Identify service/product offering",
                "Draft LinkedIn post (use Auto LinkedIn Poster skill)",
                "Move to Pending_Approval for HITL review",
                "Await approval before posting"
            ]
        elif task["type"] == "payment":
            steps = [
                "Extract payment amount and details",
                "Check if amount > $500 (requires approval)",
                "Flag for approval if needed",
                "Move to Pending_Approval",
                "Notify for manual review"
            ]
        elif task["type"] == "file_drop":
            steps = [
                "Review file content",
                "Determine required action",
                "Process or route appropriately",
                "Move to Done after processing"
            ]
        elif task["type"] == "action_item":
            steps = [
                "Understand action required",
                "Execute action or delegate",
                "Verify completion",
                "Move to Done"
            ]
        elif task["type"] == "review":
            steps = [
                "Review content thoroughly",
                "Check against company rules",
                "Provide feedback or approval",
                "Move to Done or Pending_Approval"
            ]
        else:
            steps = [
                "Analyze task requirements",
                "Determine appropriate action",
                "Execute action",
                "Verify completion",
                "Move to Done"
            ]
        
        return steps
    
    def format_steps(self, steps: list) -> str:
        """Format steps as markdown checklist."""
        return "\n".join([f"- [ ] {step}" for step in steps])
    
    def handle_multi_step_task(self, task: dict) -> str:
        """Handle multi-step tasks (e.g., sales lead → draft post → HITL)."""
        actions_taken = []
        
        if task["type"] == "sales":
            # Step 1: Create plan
            plan_path = self.create_plan(task)
            actions_taken.append(f"Created plan: {plan_path}")
            
            # Step 2: Create LinkedIn post draft
            post_draft = self.create_linkedin_post_draft(task)
            actions_taken.append(f"Created post draft: {post_draft}")
            
            # Step 3: Move to pending approval
            if task["needs_approval"]:
                approval_path = self.move_to_approval(task)
                actions_taken.append(f"Moved to approval: {approval_path}")
        
        elif task["needs_approval"]:
            # For other tasks needing approval
            plan_path = self.create_plan(task)
            actions_taken.append(f"Created plan: {plan_path}")
            approval_path = self.move_to_approval(task)
            actions_taken.append(f"Moved to approval: {approval_path}")
        
        else:
            # Simple task - just create plan and move to done
            plan_path = self.create_plan(task)
            actions_taken.append(f"Created plan: {plan_path}")
            done_path = self.move_to_done(task)
            actions_taken.append(f"Moved to done: {done_path}")
        
        return "; ".join(actions_taken)
    
    def create_linkedin_post_draft(self, task: dict) -> str:
        """Create LinkedIn post draft for sales leads."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        draft_filename = f"linkedin_post_draft_{timestamp}.md"
        draft_filepath = os.path.join(PENDING_APPROVAL_FOLDER, draft_filename)
        
        # Extract service/benefit from content (simplified)
        content = task.get("content", "")
        service = "our professional services"
        benefit = "your business success"
        
        # Check for specific keywords to customize
        if "project" in content.lower():
            service = "our project delivery services"
            benefit = "timely and quality results"
        elif "client" in content.lower():
            service = "our client-focused solutions"
            benefit = "your specific needs"
        
        draft_content = f"""---
type: linkedin_post_draft
source: {task['filename']}
created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
status: pending_approval
---

## LinkedIn Post Draft

[LAUNCH] Excited to offer {service} for {benefit}! DM for more.

#Business #Professional #Services

---
*Draft created by Ralph Wiggum Loop - Requires HITL Approval*
"""
        
        with open(draft_filepath, "w", encoding="utf-8") as f:
            f.write(draft_content)
        
        return draft_filepath
    
    def move_to_approval(self, task: dict) -> str:
        """Move file to Pending_Approval folder."""
        src = task["filepath"]
        filename = os.path.basename(src)
        dst = os.path.join(PENDING_APPROVAL_FOLDER, filename)
        
        # Ensure directory exists
        if not os.path.exists(PENDING_APPROVAL_FOLDER):
            os.makedirs(PENDING_APPROVAL_FOLDER)
        
        shutil.copy2(src, dst)
        self.pending_approval.append(dst)
        
        return dst
    
    def move_to_done(self, task: dict) -> str:
        """Move file to Done folder."""
        src = task["filepath"]
        filename = os.path.basename(src)
        dst = os.path.join(DONE_FOLDER, filename)
        
        # Ensure directory exists
        if not os.path.exists(DONE_FOLDER):
            os.makedirs(DONE_FOLDER)
        
        shutil.copy2(src, dst)
        self.completed_tasks.append(dst)
        
        return dst
    
    def process_iteration(self) -> list:
        """Process one iteration of the loop."""
        iteration_results = []
        
        # Get all files in Needs_Action
        if not os.path.exists(NEEDS_ACTION_FOLDER):
            return iteration_results
        
        files = [f for f in os.listdir(NEEDS_ACTION_FOLDER) 
                 if os.path.isfile(os.path.join(NEEDS_ACTION_FOLDER, f))]
        
        for filename in files:
            filepath = os.path.join(NEEDS_ACTION_FOLDER, filename)
            
            # Skip already processed
            if filepath in self.processed_files:
                continue
            
            # Analyze file
            task = self.analyze_file(filepath)
            self.processed_files.append(filepath)
            
            # Handle task
            actions = self.handle_multi_step_task(task)
            
            iteration_results.append({
                "file": filename,
                "type": task["type"],
                "priority": task["priority"],
                "actions": actions
            })
        
        return iteration_results
    
    def check_completion(self) -> bool:
        """Check if all tasks are complete."""
        if not os.path.exists(NEEDS_ACTION_FOLDER):
            return True

        remaining = [f for f in os.listdir(NEEDS_ACTION_FOLDER)
                     if os.path.isfile(os.path.join(NEEDS_ACTION_FOLDER, f))]

        # Filter out already processed
        unprocessed = [f for f in remaining
                       if os.path.join(NEEDS_ACTION_FOLDER, f) not in self.processed_files]

        return len(unprocessed) == 0

    def trigger_action_dispatcher(self):
        """Trigger Action Dispatcher to process approved files."""
        try:
            if not os.path.exists(ACTION_DISPATCHER_SCRIPT):
                print(f"[WARNING] Action Dispatcher not found: {ACTION_DISPATCHER_SCRIPT}")
                return False

            # Run action dispatcher once
            result = subprocess.run(
                [sys.executable, ACTION_DISPATCHER_SCRIPT, "--once"],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                print("[INFO] Action Dispatcher executed successfully")
                return True
            else:
                print(f"[WARNING] Action Dispatcher returned: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("[WARNING] Action Dispatcher timed out")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to trigger Action Dispatcher: {e}")
            return False

    def run_daemon(self, check_interval: int = 60):
        """Run Ralph Wiggum Loop in daemon mode (continuous monitoring)."""
        print("=" * 70)
        print("Ralph Wiggum Loop Runner - DAEMON MODE")
        print("=" * 70)
        print(f"Monitoring: {NEEDS_ACTION_FOLDER}")
        print(f"Check interval: {check_interval} seconds")
        print(f"Action Dispatcher: {ACTION_DISPATCHER_SCRIPT}")
        print("=" * 70)

        # Ensure directories exist
        for folder in [PLANS_FOLDER, PENDING_APPROVAL_FOLDER, APPROVED_FOLDER, DONE_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"[INFO] Created directory: {folder}")

        try:
            while True:
                print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking for new tasks...")

                # Process Needs_Action folder
                results = self.process_iteration()

                if results:
                    for r in results:
                        print(f"  [PROCESSED] {r['file']} - Type: {r['type']}")

                # Trigger Action Dispatcher to handle approved files
                print("[INFO] Triggering Action Dispatcher...")
                self.trigger_action_dispatcher()

                # Check completion
                if self.check_completion():
                    print(f"[INFO] All tasks processed. Waiting for new files...")

                # Sleep before next check
                time.sleep(check_interval)

        except KeyboardInterrupt:
            print("\n[INFO] Daemon stopped by user")
        except Exception as e:
            print(f"[ERROR] Daemon crashed: {e}")
            raise
        finally:
            # Print stats
            print("\n" + "=" * 70)
            print("DAEMON STATS")
            print("=" * 70)
            print(f"Total files processed: {len(self.processed_files)}")
            print(f"Moved to Done: {len(self.completed_tasks)}")
            print(f"Moved to Pending_Approval: {len(self.pending_approval)}")
            print("=" * 70)

    def run(self, description: str = "Process Needs_Action") -> dict:
        """Run the complete Ralph Wiggum loop."""
        print("=" * 60)
        print("Ralph Wiggum Loop Runner - Silver Tier")
        print("=" * 60)
        print(f"Description: {description}")
        print(f"Max iterations: {self.max_iterations}")
        print(f"Needs_Action folder: {NEEDS_ACTION_FOLDER}")
        print("-" * 60)
        
        # Ensure directories exist
        for folder in [PLANS_FOLDER, PENDING_APPROVAL_FOLDER, DONE_FOLDER]:
            if not os.path.exists(folder):
                os.makedirs(folder)
                print(f"[INFO] Created directory: {folder}")
        
        all_results = []
        
        while self.iteration_count < self.max_iterations:
            self.iteration_count += 1
            
            print(f"\n[Iteration {self.iteration_count}/{self.max_iterations}]")
            print("-" * 40)
            
            # Process iteration
            results = self.process_iteration()

            if results:
                for r in results:
                    print(f"  [FILE] {r['file']}")
                    print(f"     Type: {r['type']}, Priority: {r['priority']}")
                    print(f"     Actions: {r['actions']}")
                all_results.extend(results)
            else:
                print("  No new files to process")
            
            # Check completion
            if self.check_completion():
                print(f"\n[COMPLETE] {COMPLETION_PROMISE}")
                break

        # Final summary
        print("\n" + "=" * 60)
        print("LOOP COMPLETE")
        print("=" * 60)
        print(f"Iterations used: {self.iteration_count}/{self.max_iterations}")
        print(f"Files processed: {len(self.processed_files)}")
        print(f"Completed (moved to Done): {len(self.completed_tasks)}")
        print(f"Pending approval: {len(self.pending_approval)}")
        print("=" * 60)

        return {
            "iterations": self.iteration_count,
            "processed": len(self.processed_files),
            "completed": len(self.completed_tasks),
            "pending_approval": len(self.pending_approval),
            "results": all_results,
            "completion_promise": COMPLETION_PROMISE
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Ralph Wiggum Loop Runner - Iterative task processing"
    )
    parser.add_argument(
        "description",
        nargs="?",
        default="Process Needs_Action",
        help="Description of the task to process"
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=MAX_ITERATIONS,
        help=f"Maximum number of iterations (default: {MAX_ITERATIONS})"
    )
    parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (continuous monitoring, 24/7)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=60,
        help="Check interval in seconds for daemon mode (default: 60)"
    )

    args = parser.parse_args()

    loop = RalphWiggumLoop(max_iterations=args.max_iterations)

    if args.daemon:
        loop.run_daemon(check_interval=args.interval)
    else:
        result = loop.run(description=args.description)

        # Output result summary
        print(f"\n[SUMMARY]:")
        print(f"   Completion Promise: {result['completion_promise']}")
        print(f"   Total Files Processed: {result['processed']}")
        print(f"   Moved to Done: {result['completed']}")
        print(f"   Moved to Pending_Approval: {result['pending_approval']}")


if __name__ == "__main__":
    main()
