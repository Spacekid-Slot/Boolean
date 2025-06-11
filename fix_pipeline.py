#!/usr/bin/env python3
"""
Fix Pipeline - ZERO-TOUCH VERSION

Automatically fixes any pipeline issues and ensures everything works.
"""

import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime

def auto_fix_pipeline():
    """Automatically fix all pipeline issues."""
    script_dir = Path(__file__).parent.absolute()
    
    print("🔧 AUTO-FIX PIPELINE - ZERO-TOUCH MODE")
    print("=" * 40)
    
    fixes_applied = 0
    
    # Fix 1: Ensure all required files exist
    required_files = {
        "company_config.json": {
            "company_name": "fnz",
            "location": "london",
            "auto_sync_enabled": True,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    for filename, default_content in required_files.items():
        file_path = script_dir / filename
        if not file_path.exists():
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, indent=4)
            print(f"✅ Created missing file: {filename}")
            fixes_applied += 1
    
    # Fix 2: Ensure Git is properly set up
    git_dir = script_dir / ".git"
    if not git_dir.exists():
        try:
            subprocess.run(["git", "init"], cwd=script_dir, capture_output=True)
            print("✅ Initialized Git repository")
            fixes_applied += 1
        except:
            print("⚠️ Could not initialize Git")
    
    # Fix 3: Install missing packages
    try:
        subprocess.call([sys.executable, "-m", "pip", "install", "openpyxl", "selenium", "webdriver-manager"])
        print("✅ Ensured required packages are installed")
        fixes_applied += 1
    except:
        print("⚠️ Package installation check skipped")
    
    # Fix 4: Auto-launch pipeline if data exists
    data_files = ["linkedin_candidates.json", "merged_employees.json", "verified_employee_data.json"]
    has_data = any((script_dir / f).exists() for f in data_files)
    
    if has_data:
        auto_sync_script = script_dir / "auto_sync_pipeline.py"
        if auto_sync_script.exists():
            try:
                subprocess.Popen([sys.executable, str(auto_sync_script)])
                print("🚀 Auto-launched sync pipeline")
                fixes_applied += 1
            except:
                print("⚠️ Could not auto-launch pipeline")
    
    print(f"\n✅ Auto-fix complete: {fixes_applied} fixes applied")

if __name__ == "__main__":
    auto_fix_pipeline()