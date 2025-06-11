#!/usr/bin/env python3
"""
Git Auto-Sync System

This script automatically syncs any code changes to Git repository.
It monitors file changes and automatically commits and pushes updates.
"""

import os
import subprocess
import sys
import time
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

class GitAutoSync:
    """Automatically sync code changes to Git repository."""
    
    def __init__(self, repo_path: str = None):
        self.repo_path = Path(repo_path) if repo_path else Path.cwd()
        self.config_file = self.repo_path / ".git_autosync_config.json"
        self.file_hashes = {}
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load auto-sync configuration."""
        default_config = {
            "enabled": True,
            "auto_commit": True,
            "auto_push": True,
            "commit_message_prefix": "Auto-sync:",
            "ignore_patterns": [
                "*.pyc", "__pycache__", ".git", "*.tmp", 
                "*.log", "*.xlsx", "*.json"
            ],
            "watch_extensions": [".py", ".md", ".txt", ".yml", ".yaml"],
            "branch": "main",
            "remote": "origin"
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults
                    default_config.update(config)
            except:
                pass
        
        return default_config
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save config: {e}")
    
    def _run_git_command(self, command: List[str]) -> tuple:
        """Run a git command and return result."""
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Git command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get MD5 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored based on patterns."""
        file_str = str(file_path)
        
        for pattern in self.config["ignore_patterns"]:
            if pattern.startswith("*."):
                ext = pattern[1:]
                if file_str.endswith(ext):
                    return True
            elif pattern in file_str:
                return True
        
        # Only watch specific extensions if specified
        if self.config["watch_extensions"]:
            return file_path.suffix not in self.config["watch_extensions"]
        
        return False
    
    def check_git_status(self) -> bool:
        """Check if we're in a git repository and it's properly configured."""
        # Check if .git directory exists
        git_dir = self.repo_path / ".git"
        if not git_dir.exists():
            print("❌ Not a Git repository. Initialize with: git init")
            return False
        
        # Check if git is available
        success, _, _ = self._run_git_command(["--version"])
        if not success:
            print("❌ Git command not available")
            return False
        
        # Check if we have a remote
        success, stdout, _ = self._run_git_command(["remote", "-v"])
        if not success or not stdout.strip():
            print("⚠️ No Git remote configured. Add with: git remote add origin <url>")
            print("   Auto-sync will only commit locally until remote is added")
            self.config["auto_push"] = False
        
        return True
    
    def setup_git_hooks(self):
        """Setup Git hooks for automatic syncing."""
        hooks_dir = self.repo_path / ".git" / "hooks"
        
        # Create post-commit hook for auto-push
        post_commit_hook = hooks_dir / "post-commit"
        
        hook_content = f"""#!/bin/bash
# Auto-generated Git hook for auto-sync
if [ -f "{self.config_file}" ]; then
    python3 "{__file__}" --auto-push
fi
"""
        
        try:
            with open(post_commit_hook, 'w') as f:
                f.write(hook_content)
            
            # Make executable
            os.chmod(post_commit_hook, 0o755)
            print("✅ Git hooks installed for auto-sync")
            
        except Exception as e:
            print(f"⚠️ Could not install Git hooks: {e}")
    
    def scan_for_changes(self) -> List[Path]:
        """Scan for changed files."""
        changed_files = []
        
        # Get all Python files in the repository
        for file_path in self.repo_path.rglob("*"):
            if file_path.is_file() and not self._should_ignore_file(file_path):
                rel_path = file_path.relative_to(self.repo_path)
                current_hash = self._get_file_hash(file_path)
                
                # Check if file changed
                if str(rel_path) not in self.file_hashes or self.file_hashes[str(rel_path)] != current_hash:
                    changed_files.append(rel_path)
                    self.file_hashes[str(rel_path)] = current_hash
        
        return changed_files
    
    def commit_changes(self, files: List[Path] = None, message: str = None) -> bool:
        """Commit changes to Git."""
        if not self.config["auto_commit"]:
            return False
        
        # Check for unstaged changes
        success, stdout, _ = self._run_git_command(["status", "--porcelain"])
        if not success:
            print("❌ Could not check Git status")
            return False
        
        if not stdout.strip():
            print("📝 No changes to commit")
            return True
        
        # Add files
        if files:
            for file in files:
                success, _, stderr = self._run_git_command(["add", str(file)])
                if not success:
                    print(f"⚠️ Could not add {file}: {stderr}")
        else:
            # Add all changes
            success, _, stderr = self._run_git_command(["add", "."])
            if not success:
                print(f"❌ Could not add files: {stderr}")
                return False
        
        # Create commit message
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if files:
                file_list = ", ".join(str(f) for f in files[:3])
                if len(files) > 3:
                    file_list += f" and {len(files) - 3} more"
                message = f"{self.config['commit_message_prefix']} Updated {file_list} ({timestamp})"
            else:
                message = f"{self.config['commit_message_prefix']} Auto-commit ({timestamp})"
        
        # Commit
        success, _, stderr = self._run_git_command(["commit", "-m", message])
        if not success:
            if "nothing to commit" in stderr:
                print("📝 Nothing to commit")
                return True
            else:
                print(f"❌ Could not commit: {stderr}")
                return False
        
        print(f"✅ Committed: {message}")
        return True
    
    def push_changes(self) -> bool:
        """Push changes to remote repository."""
        if not self.config["auto_push"]:
            return False
        
        # Check if we have a remote
        success, stdout, _ = self._run_git_command(["remote", "-v"])
        if not success or not stdout.strip():
            print("⚠️ No remote repository configured")
            return False
        
        # Push to remote
        remote = self.config["remote"]
        branch = self.config["branch"]
        
        success, _, stderr = self._run_git_command(["push", remote, branch])
        if not success:
            print(f"❌ Could not push to {remote}/{branch}: {stderr}")
            return False
        
        print(f"🚀 Pushed to {remote}/{branch}")
        return True
    
    def auto_sync_file(self, file_path: str, content: str = None) -> bool:
        """Auto-sync a specific file with given content."""
        file_path = Path(file_path)
        
        # Write content if provided
        if content is not None:
            try:
                with open(self.repo_path / file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"📝 Updated {file_path}")
            except Exception as e:
                print(f"❌ Could not write {file_path}: {e}")
                return False
        
        # Auto-commit and push
        if self.commit_changes([file_path]):
            if self.config["auto_push"]:
                return self.push_changes()
            return True
        
        return False
    
    def start_watching(self):
        """Start watching for file changes and auto-sync."""
        if not self.check_git_status():
            return
        
        print("👀 Starting Git auto-sync watcher...")
        print(f"📁 Watching: {self.repo_path}")
        print(f"🌿 Branch: {self.config['branch']}")
        print(f"📡 Remote: {self.config['remote']}")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                changed_files = self.scan_for_changes()
                
                if changed_files:
                    print(f"🔄 Detected changes in {len(changed_files)} files")
                    
                    if self.commit_changes(changed_files):
                        if self.config["auto_push"]:
                            self.push_changes()
                
                time.sleep(5)  # Check every 5 seconds
                
        except KeyboardInterrupt:
            print("\n👋 Git auto-sync stopped")
    
    def sync_claude_artifacts(self, artifacts: List[Dict]) -> bool:
        """Sync artifacts from Claude conversation to Git."""
        success_count = 0
        
        for artifact in artifacts:
            file_name = artifact.get('title', 'unnamed_file')
            content = artifact.get('content', '')
            
            # Ensure proper file extension
            if not file_name.endswith('.py') and artifact.get('language') == 'python':
                file_name += '.py'
            
            if self.auto_sync_file(file_name, content):
                success_count += 1
                print(f"✅ Synced artifact: {file_name}")
            else:
                print(f"❌ Failed to sync: {file_name}")
        
        return success_count == len(artifacts)
    
    def setup_claude_integration(self):
        """Setup integration with Claude for automatic syncing."""
        print("🤖 Setting up Claude integration...")
        
        # Create a webhook script for Claude artifacts
        webhook_script = self.repo_path / "claude_sync_webhook.py"
        
        webhook_content = f'''#!/usr/bin/env python3
"""
Claude Sync Webhook - Automatically sync Claude artifacts to Git
"""

import sys
import json
from pathlib import Path

# Import the GitAutoSync class
sys.path.append(str(Path(__file__).parent))
from git_auto_sync import GitAutoSync

def sync_claude_update(file_name: str, content: str):
    """Sync a single Claude update to Git."""
    sync = GitAutoSync()
    return sync.auto_sync_file(file_name, content)

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        file_name = sys.argv[1]
        content = sys.argv[2]
        
        if sync_claude_update(file_name, content):
            print(f"✅ Claude update synced: {{file_name}}")
        else:
            print(f"❌ Failed to sync Claude update: {{file_name}}")
    else:
        print("Usage: python claude_sync_webhook.py <filename> <content>")
'''
        
        try:
            with open(webhook_script, 'w') as f:
                f.write(webhook_content)
            
            print(f"✅ Claude integration setup complete")
            print(f"📁 Webhook created: {webhook_script}")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup Claude integration: {e}")
            return False

def main():
    """Main function."""
    sync = GitAutoSync()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--setup":
            print("🔧 Setting up Git auto-sync...")
            sync.setup_git_hooks()
            sync.setup_claude_integration()
            sync._save_config()
            print("✅ Setup complete!")
            
        elif command == "--watch":
            sync.start_watching()
            
        elif command == "--auto-push":
            sync.push_changes()
            
        elif command == "--sync-file" and len(sys.argv) >= 3:
            file_path = sys.argv[2]
            content = sys.argv[3] if len(sys.argv) > 3 else None
            sync.auto_sync_file(file_path, content)
            
        else:
            print("Unknown command")
            
    else:
        # Interactive mode
        print("=" * 60)
        print("GIT AUTO-SYNC SYSTEM")
        print("=" * 60)
        print("Options:")
        print("1. Setup auto-sync (recommended first time)")
        print("2. Start file watcher")
        print("3. Sync current changes")
        print("4. Configure settings")
        
        choice = input("Choice (1-4): ").strip()
        
        if choice == "1":
            sync.setup_git_hooks()
            sync.setup_claude_integration()
            sync._save_config()
            print("✅ Auto-sync setup complete!")
            
        elif choice == "2":
            sync.start_watching()
            
        elif choice == "3":
            changed_files = sync.scan_for_changes()
            if sync.commit_changes(changed_files):
                sync.push_changes()
                
        elif choice == "4":
            print("Current configuration:")
            for key, value in sync.config.items():
                print(f"  {key}: {value}")

if __name__ == "__main__":
    main()