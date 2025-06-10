#!/usr/bin/env python3
"""
Claude-Git Bridge - Sync Claude artifacts directly to Git

This script acts as a bridge between Claude conversations and Git repository.
Run this after getting code from Claude to automatically sync it to Git.
"""

import sys
import json
import os
import subprocess
import time
from pathlib import Path
from datetime import datetime

class ClaudeGitBridge:
    """Bridge between Claude and Git for automatic syncing."""
    
    def __init__(self):
        self.repo_path = Path.cwd()
        self.git_available = self._check_git()
        
    def _check_git(self) -> bool:
        """Check if Git is available and we're in a repo."""
        try:
            result = subprocess.run(["git", "status"], 
                                  capture_output=True, cwd=self.repo_path)
            return result.returncode == 0
        except:
            return False
    
    def _run_git(self, command: list) -> tuple:
        """Run git command and return success, stdout, stderr."""
        try:
            result = subprocess.run(["git"] + command, 
                                  capture_output=True, text=True, cwd=self.repo_path)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def sync_claude_file(self, filename: str, content: str, commit_message: str = None) -> bool:
        """Sync a single file from Claude to Git."""
        if not self.git_available:
            print("❌ Git not available or not in a Git repository")
            return False
        
        try:
            # Write the file
            file_path = self.repo_path / filename
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print(f"📝 Written: {filename}")
            
            # Add to Git
            success, _, stderr = self._run_git(["add", filename])
            if not success:
                print(f"⚠️ Could not add to Git: {stderr}")
                return False
            
            # Create commit message
            if not commit_message:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                commit_message = f"Claude update: {filename} ({timestamp})"
            
            # Commit
            success, _, stderr = self._run_git(["commit", "-m", commit_message])
            if not success:
                if "nothing to commit" in stderr:
                    print(f"📝 No changes in {filename}")
                    return True
                else:
                    print(f"⚠️ Could not commit: {stderr}")
                    return False
            
            print(f"✅ Committed: {filename}")
            
            # Try to push
            success, _, stderr = self._run_git(["push"])
            if success:
                print(f"🚀 Pushed to remote repository")
            else:
                print(f"⚠️ Could not push (commit saved locally): {stderr}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error syncing {filename}: {e}")
            return False
    
    def sync_multiple_files(self, files: dict) -> bool:
        """Sync multiple files from Claude."""
        success_count = 0
        
        for filename, content in files.items():
            if self.sync_claude_file(filename, content):
                success_count += 1
        
        print(f"\n📊 Synced {success_count}/{len(files)} files successfully")
        return success_count == len(files)
    
    def quick_sync(self):
        """Quick sync for common Claude artifacts."""
        print("🤖 Claude-Git Bridge - Quick Sync")
        print("=" * 40)
        
        # Common files that Claude might update
        common_files = {
            "script5_linkedin_verification.py": "LinkedIn verification script",
            "auto_sync_pipeline.py": "Auto-sync pipeline",
            "fix_pipeline.py": "Pipeline fix script",
            "git_auto_sync.py": "Git auto-sync system"
        }
        
        print("Which file(s) did Claude just create/update?")
        for i, (filename, description) in enumerate(common_files.items(), 1):
            exists = "✅" if (self.repo_path / filename).exists() else "➕"
            print(f"{i}. {exists} {filename} - {description}")
        
        print("0. Custom filename")
        print("a. All files listed above")
        
        choice = input("\nChoice: ").strip().lower()
        
        if choice == "a":
            # Sync all existing files
            files_to_sync = {}
            for filename in common_files.keys():
                file_path = self.repo_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        files_to_sync[filename] = f.read()
            
            if files_to_sync:
                self.sync_multiple_files(files_to_sync)
            else:
                print("❌ No files found to sync")
                
        elif choice == "0":
            filename = input("Enter filename: ").strip()
            if filename:
                file_path = self.repo_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    self.sync_claude_file(filename, content)
                else:
                    print(f"❌ File not found: {filename}")
                    
        elif choice.isdigit() and 1 <= int(choice) <= len(common_files):
            filename = list(common_files.keys())[int(choice) - 1]
            file_path = self.repo_path / filename
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.sync_claude_file(filename, content)
            else:
                print(f"❌ File not found: {filename}")
                print("💡 Copy the code from Claude and paste it into the file first")
    
    def setup_auto_sync(self):
        """Setup automatic syncing for future Claude updates."""
        print("🔧 Setting up auto-sync for Claude updates...")
        
        # Create a simple sync script
        sync_script = self.repo_path / "sync_claude.py"
        
        script_content = '''#!/usr/bin/env python3
"""
Quick sync script for Claude updates.
Run this after copying code from Claude to automatically commit and push.
"""

import sys
import subprocess
from pathlib import Path

def quick_commit_push():
    """Quickly commit and push all changes."""
    repo_path = Path.cwd()
    
    try:
        # Add all changes
        subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
        
        # Commit with timestamp
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"Claude update ({timestamp})"
        
        result = subprocess.run(["git", "commit", "-m", message], 
                              cwd=repo_path, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Committed: {message}")
            
            # Push
            push_result = subprocess.run(["git", "push"], 
                                       cwd=repo_path, capture_output=True, text=True)
            if push_result.returncode == 0:
                print("🚀 Pushed to remote")
            else:
                print("⚠️ Push failed, but committed locally")
        else:
            if "nothing to commit" in result.stderr:
                print("📝 Nothing to commit")
            else:
                print(f"⚠️ Commit failed: {result.stderr}")
                
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_commit_push()
'''
        
        try:
            with open(sync_script, 'w') as f:
                f.write(script_content)
            
            # Make executable on Unix systems
            if sys.platform != 'win32':
                os.chmod(sync_script, 0o755)
            
            print(f"✅ Created quick sync script: {sync_script}")
            print("\n💡 Usage:")
            print("1. Copy code from Claude and save to files")
            print("2. Run: python sync_claude.py")
            print("3. Everything syncs automatically!")
            
        except Exception as e:
            print(f"❌ Could not create sync script: {e}")

def main():
    """Main function."""
    bridge = ClaudeGitBridge()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "--setup":
            bridge.setup_auto_sync()
        elif command == "--quick":
            bridge.quick_sync()
        elif command == "--file" and len(sys.argv) >= 3:
            filename = sys.argv[2]
            file_path = bridge.repo_path / filename
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                bridge.sync_claude_file(filename, content)
            else:
                print(f"❌ File not found: {filename}")
        else:
            print("Unknown command")
            print("Usage: python claude_git_bridge.py [--setup|--quick|--file <filename>]")
    else:
        # Interactive mode
        print("🤖 Claude-Git Bridge")
        print("=" * 30)
        print("1. Quick sync (choose files to sync)")
        print("2. Setup auto-sync")
        print("3. Sync specific file")
        
        choice = input("Choice (1-3): ").strip()
        
        if choice == "1":
            bridge.quick_sync()
        elif choice == "2":
            bridge.setup_auto_sync()
        elif choice == "3":
            filename = input("Enter filename: ").strip()
            if filename:
                file_path = bridge.repo_path / filename
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    bridge.sync_claude_file(filename, content)
                else:
                    print(f"❌ File not found: {filename}")

if __name__ == "__main__":
    main()