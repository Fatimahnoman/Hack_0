"""
Silver Tier - Complete System Test
Tests all components to verify everything is working correctly
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 60}{Colors.RESET}\n")

def print_success(text):
    try:
        print(f"{Colors.GREEN}[PASS] {text}{Colors.RESET}")
    except:
        print(f"[PASS] {text}")

def print_error(text):
    try:
        print(f"{Colors.RED}[FAIL] {text}{Colors.RESET}")
    except:
        print(f"[FAIL] {text}")

def print_warning(text):
    try:
        print(f"{Colors.YELLOW}[WARN] {text}{Colors.RESET}")
    except:
        print(f"[WARN] {text}")

def print_info(text):
    try:
        print(f"{Colors.BLUE}[INFO] {text}{Colors.RESET}")
    except:
        print(f"[INFO] {text}")


class SilverTierTest:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.vault_path = self.project_root / "Vault"
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        
    def test_directory_structure(self):
        """Test 1: Check all required directories exist"""
        print_header("TEST 1: Directory Structure")
        
        required_dirs = [
            "Vault",
            "Vault/Inbox",
            "Vault/Needs_Action",
            "Vault/Pending_Approval",
            "Vault/Approved",
            "Vault/Done",
            "Vault/Plans",
            "Vault/Logs",
            "watchers",
            "skills",
            "sessions",
            "mcp_servers/actions_mcp",
        ]
        
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists() and full_path.is_dir():
                print_success(f"Directory exists: {dir_path}")
                self.passed += 1
            else:
                print_error(f"Directory missing: {dir_path}")
                self.failed += 1
    
    def test_required_files(self):
        """Test 2: Check all required files exist"""
        print_header("TEST 2: Required Files")
        
        required_files = [
            "orchestrator.py",
            ".env",
            "credentials.json",
            "watchers/whatsapp_watcher.py",
            "watchers/instagram_watcher.py",
            "watchers/gmail_watcher.py",
            "skills/auto_insta_post.py",
            "skills/process_needs_action.py",
            "mcp_servers/actions_mcp/server.py",
            "mcp_servers/actions_mcp/README.md",
            "Vault/Dashboard.md",
            "Vault/Company_Handbook.md",
            ".claude/mcp.json",
        ]
        
        for file_path in required_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                print_success(f"File exists: {file_path}")
                self.passed += 1
            else:
                print_error(f"File missing: {file_path}")
                self.failed += 1
    
    def test_mcp_config(self):
        """Test 3: Check MCP configuration"""
        print_header("TEST 3: MCP Configuration")
        
        mcp_config_path = self.project_root / ".claude" / "mcp.json"
        
        if not mcp_config_path.exists():
            print_error("MCP config file not found")
            self.failed += 1
            return
        
        try:
            import json
            with open(mcp_config_path, 'r') as f:
                config = json.load(f)
            
            if "mcpServers" in config:
                print_success("MCP servers configured")
                self.passed += 1
                
                if "actions_mcp" in config["mcpServers"]:
                    print_success("actions_mcp server configured")
                    self.passed += 1
                    
                    server = config["mcpServers"]["actions_mcp"]
                    if "command" in server and server["command"] == "python":
                        print_success("MCP command configured (python)")
                        self.passed += 1
                    else:
                        print_warning("MCP command may be incorrect")
                        self.warnings += 1
                        
                    if "cwd" in server:
                        print_success(f"MCP working directory: {server['cwd']}")
                        self.passed += 1
                    else:
                        print_warning("MCP cwd not set")
                        self.warnings += 1
                else:
                    print_error("actions_mcp not found in config")
                    self.failed += 1
            else:
                print_error("No mcpServers in config")
                self.failed += 1
                
        except Exception as e:
            print_error(f"Error reading MCP config: {e}")
            self.failed += 1
    
    def test_env_variables(self):
        """Test 4: Check environment variables"""
        print_header("TEST 4: Environment Variables")
        
        env_path = self.project_root / ".env"
        
        if not env_path.exists():
            print_error(".env file not found")
            self.failed += 1
            return
        
        try:
            with open(env_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_vars = [
                "INSTAGRAM_USERNAME",
                "INSTAGRAM_PASSWORD",
                "GMAIL_CLIENT_ID",
                "GMAIL_CLIENT_SECRET",
            ]
            
            for var in required_vars:
                if var + "=" in content:
                    # Check if value is set (not empty)
                    for line in content.split('\n'):
                        if line.startswith(var + "="):
                            value = line.split('=', 1)[1].strip()
                            if value:
                                print_success(f"{var} is set")
                                self.passed += 1
                            else:
                                print_warning(f"{var} is empty (may need configuration)")
                                self.warnings += 1
                            break
                else:
                    print_error(f"{var} not found in .env")
                    self.failed += 1
                    
        except Exception as e:
            print_error(f"Error reading .env: {e}")
            self.failed += 1
    
    def test_dependencies(self):
        """Test 5: Check Python dependencies"""
        print_header("TEST 5: Python Dependencies")
        
        required_packages = [
            ("playwright", "Playwright"),
            ("apscheduler", "APScheduler"),
            ("fastmcp", "FastMCP"),
            ("google.oauth2", "Google Auth"),
            ("googleapiclient", "Google API Client"),
        ]
        
        for package, display_name in required_packages:
            try:
                __import__(package)
                print_success(f"{display_name} installed")
                self.passed += 1
            except ImportError:
                print_error(f"{display_name} NOT installed")
                self.failed += 1
                print_info(f"  Install with: pip install {package}")
    
    def test_watchers_syntax(self):
        """Test 6: Check watcher scripts syntax"""
        print_header("TEST 6: Watcher Scripts Syntax")
        
        watchers = [
            "watchers/whatsapp_watcher.py",
            "watchers/instagram_watcher.py",
            "watchers/gmail_watcher.py",
        ]
        
        for watcher_path in watchers:
            full_path = self.project_root / watcher_path
            
            if not full_path.exists():
                print_error(f"Watcher not found: {watcher_path}")
                self.failed += 1
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                compile(code, str(full_path), 'exec')
                print_success(f"{watcher_path} - Syntax OK")
                self.passed += 1
                
            except SyntaxError as e:
                print_error(f"{watcher_path} - Syntax Error: {e}")
                self.failed += 1
            except Exception as e:
                print_error(f"{watcher_path} - Error: {e}")
                self.failed += 1
    
    def test_skills_syntax(self):
        """Test 7: Check skill scripts syntax"""
        print_header("TEST 7: Skill Scripts Syntax")
        
        skills = [
            "skills/auto_insta_post.py",
            "skills/process_needs_action.py",
        ]
        
        for skill_path in skills:
            full_path = self.project_root / skill_path
            
            if not full_path.exists():
                print_error(f"Skill not found: {skill_path}")
                self.failed += 1
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                compile(code, str(full_path), 'exec')
                print_success(f"{skill_path} - Syntax OK")
                self.passed += 1
                
            except SyntaxError as e:
                print_error(f"{skill_path} - Syntax Error: {e}")
                self.failed += 1
            except Exception as e:
                print_error(f"{skill_path} - Error: {e}")
                self.failed += 1
    
    def test_mcp_server_syntax(self):
        """Test 8: Check MCP server syntax"""
        print_header("TEST 8: MCP Server Syntax")
        
        mcp_server_path = self.project_root / "mcp_servers" / "actions_mcp" / "server.py"
        
        if not mcp_server_path.exists():
            print_error("MCP server not found")
            self.failed += 1
            return
        
        try:
            with open(mcp_server_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, str(mcp_server_path), 'exec')
            print_success("MCP server.py - Syntax OK")
            self.passed += 1
            
            # Check for required tools
            if "send_email" in code:
                print_success("send_email tool found")
                self.passed += 1
            else:
                print_error("send_email tool NOT found")
                self.failed += 1
            
            if "post_to_instagram" in code:
                print_success("post_to_instagram tool found")
                self.passed += 1
            else:
                print_error("post_to_instagram tool NOT found")
                self.failed += 1
                
        except SyntaxError as e:
            print_error(f"MCP server - Syntax Error: {e}")
            self.failed += 1
        except Exception as e:
            print_error(f"MCP server - Error: {e}")
            self.failed += 1
    
    def test_orchestrator(self):
        """Test 9: Check orchestrator"""
        print_header("TEST 9: Orchestrator")
        
        orchestrator_path = self.project_root / "orchestrator.py"
        
        if not orchestrator_path.exists():
            print_error("orchestrator.py not found")
            self.failed += 1
            return
        
        try:
            with open(orchestrator_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, str(orchestrator_path), 'exec')
            print_success("orchestrator.py - Syntax OK")
            self.passed += 1
            
            # Check for required features
            checks = [
                ("APScheduler", "apscheduler" in code.lower()),
                ("Gmail Watcher", "gmail" in code.lower()),
                ("WhatsApp Watcher", "whatsapp" in code.lower()),
                ("Instagram Watcher", "instagram" in code.lower()),
                ("Dashboard Update", "dashboard" in code.lower()),
                ("Scheduler Setup", "setup_scheduler" in code.lower()),
            ]
            
            for feature, found in checks:
                if found:
                    print_success(f"{feature} configured")
                    self.passed += 1
                else:
                    print_warning(f"{feature} NOT found")
                    self.warnings += 1
                    
        except SyntaxError as e:
            print_error(f"Orchestrator - Syntax Error: {e}")
            self.failed += 1
        except Exception as e:
            print_error(f"Orchestrator - Error: {e}")
            self.failed += 1
    
    def test_dashboard(self):
        """Test 10: Check Dashboard.md"""
        print_header("TEST 10: Dashboard.md")
        
        dashboard_path = self.vault_path / "Dashboard.md"
        
        if not dashboard_path.exists():
            print_error("Dashboard.md not found")
            self.failed += 1
            return
        
        try:
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_sections = [
                "Status",
                "Needs_Action",
                "Pending_Approval",
                "Approved",
                "Done",
            ]
            
            for section in required_sections:
                if section in content:
                    print_success(f"Dashboard contains: {section}")
                    self.passed += 1
                else:
                    print_warning(f"Dashboard missing: {section}")
                    self.warnings += 1
                    
        except Exception as e:
            print_error(f"Error reading Dashboard: {e}")
            self.failed += 1
    
    def test_company_handbook(self):
        """Test 11: Check Company Handbook"""
        print_header("TEST 11: Company Handbook")
        
        handbook_path = self.vault_path / "Company_Handbook.md"
        
        if not handbook_path.exists():
            print_error("Company_Handbook.md not found")
            self.failed += 1
            return
        
        try:
            with open(handbook_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if len(content.strip()) > 50:
                print_success("Company Handbook has content")
                self.passed += 1
            else:
                print_warning("Company Handbook is empty")
                self.warnings += 1
                
        except Exception as e:
            print_error(f"Error reading Handbook: {e}")
            self.failed += 1
    
    def test_sessions_folder(self):
        """Test 12: Check sessions folders"""
        print_header("TEST 12: Sessions Folders")
        
        sessions = [
            "sessions/instagram_session",
            "sessions/whatsapp_session",
        ]
        
        for session_path in sessions:
            full_path = self.project_root / session_path
            if full_path.exists():
                print_success(f"Session folder exists: {session_path}")
                self.passed += 1
            else:
                print_warning(f"Session folder missing: {session_path}")
                print_info(f"  Will be created on first login")
                self.warnings += 1
    
    def print_summary(self):
        """Print test summary"""
        print_header("TEST SUMMARY")
        
        total = self.passed + self.failed + self.warnings
        
        print(f"Total Tests: {total}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Warnings: {self.warnings}")
        print()
        
        if self.failed == 0:
            print("[SUCCESS] ALL TESTS PASSED! Silver Tier is ready!")
            print()
            print("Next steps:")
            print("  1. Add Instagram credentials to .env")
            print("  2. Add Gmail credentials to .env")
            print("  3. Run: python orchestrator.py")
            print("  4. Login to WhatsApp when QR code appears")
            print("  5. System will run automatically!")
        else:
            print(f"[WARNING] {self.failed} tests failed. Please fix the issues above.")
            print()
            print("Common fixes:")
            print("  - Install missing packages: pip install playwright apscheduler fastmcp")
            print("  - Check .env file has required variables")
            print("  - Verify MCP config in .claude/mcp.json")
        
        print()
        print("=" * 60)


def main():
    """Run all tests"""
    print_header("SILVER TIER - COMPLETE SYSTEM TEST")
    print(f"Project Root: Path(__file__).parent")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tester = SilverTierTest()
    
    # Run all tests
    tester.test_directory_structure()
    tester.test_required_files()
    tester.test_mcp_config()
    tester.test_env_variables()
    tester.test_dependencies()
    tester.test_watchers_syntax()
    tester.test_skills_syntax()
    tester.test_mcp_server_syntax()
    tester.test_orchestrator()
    tester.test_dashboard()
    tester.test_company_handbook()
    tester.test_sessions_folder()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    main()
