#!/usr/bin/env python3
"""
Git Restore to Working Version

This script checks your Git history and restores to the last working version.
"""

import subprocess
import sys
from pathlib import Path

def run_git_command(command):
    """Run a git command and return the result."""
    try:
        result = subprocess.run(
            ["git"] + command,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Check Git history and restore working version."""
    print("🔍 CHECKING GIT HISTORY FOR WORKING VERSIONS")
    print("=" * 60)
    
    # Check if we're in a Git repo
    success, _, _ = run_git_command(["status"])
    if not success:
        print("❌ Not in a Git repository or Git not available")
        print("💡 Try manually finding your backup files")
        return
    
    # Show recent commits
    print("📋 Recent Git commits:")
    success, commits, _ = run_git_command(["log", "--oneline", "-10"])
    if success and commits:
        print(commits)
        
        print("\n🎯 RECOMMENDED RESTORE POINTS:")
        lines = commits.strip().split('\n')
        
        # Look for commits before the auto-sync mess
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['before', 'working', 'initial', 'setup']):
                commit_hash = line.split()[0]
                print(f"✅ GOOD: {line}")
            elif any(keyword in line.lower() for keyword in ['auto-sync', 'fix', 'update', 'claude']):
                commit_hash = line.split()[0]
                print(f"❌ AVOID: {line}")
            else:
                commit_hash = line.split()[0]
                print(f"❓ MAYBE: {line}")
        
        print(f"\n🔧 TO RESTORE TO A WORKING VERSION:")
        print(f"1. Find a commit hash from BEFORE the auto-sync problems")
        print(f"2. Run: git checkout [commit-hash]")
        print(f"3. Or run: git reset --hard [commit-hash]")
        
        print(f"\n⚠️ CAUTION:")
        print(f"- git checkout: View old version (can go back)")
        print(f"- git reset --hard: Permanently revert (loses recent changes)")
        
        # Look for the earliest commit that might be working
        earliest_good = None
        for line in reversed(lines):
            if not any(bad in line.lower() for bad in ['auto-sync', 'fix', 'claude update']):
                earliest_good = line.split()[0]
                break
        
        if earliest_good:
            print(f"\n💡 SUGGESTED RESTORE POINT:")
            print(f"git reset --hard {earliest_good}")
            
            restore = input(f"\nRestore to this commit now? (y/n): ").strip().lower()
            if restore == 'y':
                print(f"🔄 Restoring to {earliest_good}...")
                success, _, stderr = run_git_command(["reset", "--hard", earliest_good])
                if success:
                    print("✅ Successfully restored to working version!")
                    print("🎯 Try running your scripts now")
                else:
                    print(f"❌ Restore failed: {stderr}")
    else:
        print("❌ Could not retrieve Git history")
        
    # Also check for backup files
    print(f"\n📁 CHECKING FOR BACKUP FILES:")
    backup_dir = Path.cwd() / "backup"
    if backup_dir.exists():
        print(f"✅ Found backup directory: {backup_dir}")
        backup_files = list(backup_dir.glob("*.backup"))
        if backup_files:
            print("📋 Available backups:")
            for backup in backup_files:
                print(f"  - {backup.name}")
            
            restore_backup = input(f"\nRestore from backup files? (y/n): ").strip().lower()
            if restore_backup == 'y':
                for backup in backup_files:
                    original_name = backup.name.replace('.backup', '')
                    original_path = Path.cwd() / original_name
                    try:
                        # Copy backup to original location
                        import shutil
                        shutil.copy2(backup, original_path)
                        print(f"✅ Restored {original_name} from backup")
                    except Exception as e:
                        print(f"❌ Could not restore {original_name}: {e}")
        else:
            print("📁 Backup directory exists but no .backup files found")
    else:
        print("📁 No backup directory found")
    
    print(f"\n💡 IF NOTHING WORKS:")
    print(f"1. Start fresh in a new directory")
    print(f"2. Copy only script1_input_collection.py")
    print(f"3. Run script1 to recreate config")
    print(f"4. Use the working scripts from early in our chat")

if __name__ == "__main__":
    main()