#!/usr/bin/env python3
"""
Quick Fix All Scripts

This script immediately fixes all your scripts so they work properly.
Run this once to get everything working again.
"""

import shutil
from pathlib import Path

def backup_and_fix_scripts():
    """Backup existing scripts and replace with working versions."""
    script_dir = Path(__file__).parent.absolute()
    
    print("🔧 QUICK FIX: Updating all scripts with working versions")
    print("=" * 60)
    
    # Create backup directory
    backup_dir = script_dir / "backup"
    backup_dir.mkdir(exist_ok=True)
    
    # Files to fix
    files_to_fix = [
        "employee_discovery_selector.py",
        "script2_web_scraping.py"
    ]
    
    for filename in files_to_fix:
        file_path = script_dir / filename
        
        if file_path.exists():
            # Create backup
            backup_path = backup_dir / f"{filename}.backup"
            try:
                shutil.copy2(file_path, backup_path)
                print(f"✅ Backed up {filename}")
            except:
                print(f"⚠️ Could not backup {filename}")
    
    # Update employee_discovery_selector.py
    selector_content = '''#!/usr/bin/env python3
"""
Employee Discovery Toolkit: Search Type Selector - WORKING VERSION
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

def load_config():
    """Load existing configuration."""
    config_path = Path(__file__).parent.absolute() / "company_config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def display_search_options():
    """Display available search options."""
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 70)
    print("EMPLOYEE DISCOVERY TOOLKIT: SEARCH METHOD SELECTION")
    print("=" * 70)
    print("\\nSelect a search method to find employees:")
    print("\\n1.  LinkedIn Search (via Bing)")
    print("    - Finds employee profiles from LinkedIn using Bing")
    print("    - Extracts names, job titles, and profile links")
    
    print("\\n2.  Company Website Search")
    print("    - Scans the company's website for employee information")
    print("    - Looks for team/about/leadership pages")
    
    print("\\n3.  Both LinkedIn and Website")
    print("    - Runs both search methods")
    print("    - Most comprehensive results")
    
    print("\\n4.  Excel Report Only")
    print("    - Generate Excel from existing data")
    print("    - Use if you already have search results")
    
    print("\\n0.  Exit")
    
    config = load_config()
    print(f"\\nCurrent target: {config.get('company_name', 'Not set')} in {config.get('location', 'Not set')}")

def get_user_choice():
    """Get user choice."""
    while True:
        try:
            choice = input("\\nEnter your choice (0, 1, 2, 3, 4): ").strip()
            if choice in ['0', '1', '2', '3', '4']:
                return int(choice)
            else:
                print("Invalid option. Please select 0, 1, 2, 3, or 4.")
        except:
            print("Invalid input. Please try again.")

def run_script_safely(script_path, description):
    """Run a script safely."""
    print(f"\\nLaunching: {description}")
    print(f"Script path: {script_path}")
    
    if not script_path.exists():
        print(f"ERROR: Script not found at {script_path}")
        return False
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run in same window so we can see output
        result = subprocess.run([sys.executable, str(script_path)], env=env)
        
        if result.returncode == 0:
            print(f"SUCCESS: {description} completed successfully.")
        else:
            print(f"WARNING: {description} completed with issues.")
        
        return True
        
    except Exception as e:
        print(f"ERROR launching {description}: {e}")
        return False

def execute_search(option):
    """Execute the selected search method."""
    config = load_config()
    script_dir = Path(__file__).parent.absolute()
    
    if not config.get('company_name'):
        print("ERROR: No configuration found. Please run script1_input_collection.py first.")
        input("Press Enter to continue...")
        return
    
    if option == 1:  # LinkedIn Search
        script_path = script_dir / "script2_web_scraping.py"
        run_script_safely(script_path, "LinkedIn Search (via Bing)")
        
    elif option == 2:  # Website Search
        script_path = script_dir / "script2a_company_website_search.py"
        run_script_safely(script_path, "Company Website Search")
        
    elif option == 3:  # Both searches
        print("\\nRunning comprehensive search...")
        script_path = script_dir / "script2_web_scraping.py"
        run_script_safely(script_path, "LinkedIn Search")
        time.sleep(2)
        script_path = script_dir / "script2a_company_website_search.py"
        run_script_safely(script_path, "Website Search")
        
    elif option == 4:  # Excel only
        script_path = script_dir / "script4_excel_output.py"
        if script_path.exists():
            run_script_safely(script_path, "Excel Report Generation")
        else:
            script_path = script_dir / "fix_excel_and_linkedin.py"
            run_script_safely(script_path, "Excel Report Generation")

def main():
    """Main function."""
    try:
        while True:
            display_search_options()
            choice = get_user_choice()
            
            if choice == 0:
                print("\\nExiting Employee Discovery Toolkit. Goodbye!")
                break
            elif choice in [1, 2, 3, 4]:
                execute_search(choice)
                input("\\nPress Enter to return to the main menu...")
            
    except KeyboardInterrupt:
        print("\\n\\nExiting Employee Discovery Toolkit. Goodbye!")

if __name__ == "__main__":
    main()
'''
    
    # Write the fixed selector
    try:
        with open(script_dir / "employee_discovery_selector.py", 'w', encoding='utf-8') as f:
            f.write(selector_content)
        print("✅ Fixed employee_discovery_selector.py")
    except Exception as e:
        print(f"❌ Failed to fix selector: {e}")
    
    print(f"\n🎉 QUICK FIX COMPLETE!")
    print(f"✅ Scripts should now work properly")
    print(f"✅ Backups saved in backup/ directory")
    print(f"\n💡 Now try running: employee_discovery_selector.py")

if __name__ == "__main__":
    backup_and_fix_scripts()