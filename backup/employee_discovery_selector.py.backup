#!/usr/bin/env python3
"""
Employee Discovery Toolkit: Search Type Selector

This script provides a user interface to select which type of employee search to perform:
1. LinkedIn scraping via Bing
1a. LinkedIn Search (via Recruitment Geek)
2. Company Website scraping
3. Conference Attendee scraping
4. General Web scraping
"""

import json
import os
import subprocess
import sys
import time

def clear_screen():
    """Clear the terminal screen based on OS."""
    os.system('cls' if os.name == 'nt' else 'clear')

def get_script_directory():
    """Get the directory where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def check_dependencies():
    """Check if required packages are installed."""
    required_packages = [
        "requests", "beautifulsoup4", "selenium", 
        "webdriver-manager", "openpyxl", "pandas"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Installing missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.call([sys.executable, "-m", "pip", "install"] + missing_packages)
            print("Packages installed successfully.")
            return True
        except Exception as e:
            print(f"Failed to install packages: {e}")
            print("Please install these packages manually:")
            print("pip install " + " ".join(missing_packages))
            return False
    return True

def load_config():
    """Load existing configuration or create a new one."""
    config_path = os.path.join(get_script_directory(), "company_config.json")
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("Config file is corrupted. Creating a new one.")
    
    # Default config
    return {
        "company_name": "",
        "location": "",
        "company_website": "",
        "output_file": "employee_search_results.xlsx",
        "temp_data_file": "temp_employee_data.json",
        "pages_to_scrape": 5,
        "debug_mode": True,
        "search_types": [],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }

def collect_basic_info():
    """Collect basic company information from user."""
    clear_screen()
    print("=" * 60)
    print("EMPLOYEE DISCOVERY TOOLKIT: COMPANY INFORMATION")
    print("=" * 60)
    
    # Load existing config or create new one
    config = load_config()
    
    # Get company name
    default_company = config.get('company_name', '')
    company_prompt = f"Enter company name [{default_company}]: " if default_company else "Enter company name: "
    company_name = input(company_prompt).strip()
    if company_name:
        config['company_name'] = company_name
    elif not default_company:
        print("Company name cannot be empty.")
        return collect_basic_info()
    
    # Get location
    default_location = config.get('location', '')
    location_prompt = f"Enter location (city, state, country) [{default_location}]: " if default_location else "Enter location (city, state, country): "
    location = input(location_prompt).strip()
    if location:
        config['location'] = location
    elif not default_location:
        print("Location cannot be empty.")
        return collect_basic_info()
    
    # Get company website
    default_website = config.get('company_website', '')
    website_prompt = f"Enter company website (e.g., www.example.com) [{default_website}]: " if default_website else "Enter company website (e.g., www.example.com): "
    website = input(website_prompt).strip()
    if website:
        # Ensure website has proper format
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        config['company_website'] = website
    elif not default_website:
        print("Company website cannot be empty.")
        return collect_basic_info()
    
    # Get number of pages to scrape
    default_pages = config.get('pages_to_scrape', 5)
    try:
        pages_input = input(f"Enter number of search pages to scrape [default: {default_pages}]: ").strip()
        if pages_input:
            config['pages_to_scrape'] = int(pages_input)
    except ValueError:
        print(f"Invalid input, using default of {default_pages} pages.")
    
    # Get debug mode
    debug_default = "y" if config.get('debug_mode', True) else "n"
    debug_mode = input(f"Enable debug mode for verbose output? (y/n) [default: {debug_default}]: ").strip().lower()
    if debug_mode:
        config['debug_mode'] = debug_mode != 'n'
    
    # Set auto-generated output filename
    company_name_clean = config['company_name'].replace(' ', '_')
    location_clean = config['location'].replace(' ', '_')
    config['output_file'] = f"{company_name_clean}_{location_clean}_employees.xlsx"
    
    # Save the config
    save_config(config)
    
    return config

def save_config(config):
    """Save configuration to file."""
    config_path = os.path.join(get_script_directory(), "company_config.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    print(f"\nConfiguration saved to {config_path}")

def display_search_options():
    """Display available search options."""
    clear_screen()
    print("=" * 70)
    print("EMPLOYEE DISCOVERY TOOLKIT: SEARCH METHOD SELECTION")
    print("=" * 70)
    print("\nSelect a search method to find employees:")
    print("\n1.  LinkedIn Search (via Bing)")
    print("    - Finds employee profiles from LinkedIn using Bing")
    print("    - Extracts names, job titles, and profile links")
    
    print("\n1a. LinkedIn Search (via Recruitment Geek)")
    print("    - Alternative LinkedIn search method using Recruitment Geek")
    print("    - Specialized for recruitment and talent acquisition")
    print("    - May provide different results than standard Bing search")
    
    print("\n2.  Company Website Search")
    print("    - Scans the company's website for employee information")
    print("    - Looks for team/about/leadership pages")
    
    print("\n3.  Conference Attendee Search")
    print("    - Searches for company employees in conference attendee lists")
    print("    - Finds professionals who represent the company publicly")
    
    print("\n4.  General Web Search")
    print("    - Broader search across multiple platforms")
    print("    - Includes news mentions, press releases, and articles")
    
    print("\n5.  Run All Search Methods")
    print("    - Execute all search methods sequentially")
    print("    - Comprehensive but time-consuming")
    
    print("\n0.  Exit")
    
    config = load_config()
    print(f"\nCurrent target: {config.get('company_name', 'Not set')} in {config.get('location', 'Not set')}")

def get_user_choice():
    """Get and validate user choice including 1a option."""
    while True:
        try:
            choice_input = input("\nEnter your choice (0, 1, 1a, 2, 3, 4, 5): ").strip().lower()
            
            if choice_input == '0':
                return 0
            elif choice_input == '1':
                return 1
            elif choice_input == '1a':
                return '1a'
            elif choice_input in ['2', '3', '4', '5']:
                return int(choice_input)
            else:
                print("Invalid option. Please select 0, 1, 1a, 2, 3, 4, or 5.")
                continue
                
        except ValueError:
            print("Invalid input. Please enter a valid option.")
            continue

def execute_search(option, config):
    """Execute the selected search method."""
    script_dir = get_script_directory()
    
    # Update the config with the selected search type
    config['selected_search'] = option
    save_config(config)
    
    # Determine which script to run
    if option == 1:  # LinkedIn Search (via Bing)
        script_path = os.path.join(script_dir, "script2_web_scraping.py")
        search_name = "LinkedIn Search (via Bing)"
    elif option == '1a':  # LinkedIn Search (via Recruitment Geek)
        script_path = os.path.join(script_dir, "script2_geek.py")
        search_name = "LinkedIn Search (via Recruitment Geek)"
    elif option == 2:  # Company Website Search
        script_path = os.path.join(script_dir, "script2a_company_website_search.py")
        search_name = "Company Website Search"
    elif option == 3:  # Conference Attendee Search
        script_path = os.path.join(script_dir, "script_conference_search.py")
        search_name = "Conference Attendee Search"
    elif option == 4:  # General Web Search
        script_path = os.path.join(script_dir, "script_general_web_search.py")
        search_name = "General Web Search"
    elif option == 5:  # Run All
        print("\nRunning all search methods sequentially...")
        search_options = [1, '1a', 2, 3, 4]  # Include 1a in the "run all" sequence
        for opt in search_options:
            print(f"\n--- Running search option {opt} ---")
            config['selected_search'] = opt
            save_config(config)
            execute_search(opt, config)
            time.sleep(2)  # Brief pause between searches
        return
    else:
        print("Invalid option selected.")
        return
    
    print(f"\nLaunching: {search_name}")
    print(f"Script path: {script_path}")
    
    if os.path.exists(script_path):
        try:
            if sys.platform == 'win32':
                # Use this method on Windows
                subprocess.Popen([sys.executable, script_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                # Use this method on Unix-like systems
                subprocess.Popen([sys.executable, script_path])
            print(f"✅ {search_name} launched successfully.")
            print(f"📋 Check the new console window for progress updates.")
        except Exception as e:
            print(f"❌ Error launching script: {e}")
    else:
        print(f"❌ Error: Script not found at {script_path}")
        if option == '1a':
            print("\n📝 The script2_geek.py file needs to be created.")
            print("   This should contain your Recruitment Geek LinkedIn search implementation.")
            create_recruitment_geek_placeholder(script_path)
        else:
            print("Creating script placeholder...")
            create_script_placeholder(option, script_path, search_name)

def create_recruitment_geek_placeholder(script_path):
    """Create a specific placeholder for the Recruitment Geek script."""
    placeholder = '''#!/usr/bin/env python3
"""
Employee Discovery Toolkit: LinkedIn Search (via Recruitment Geek)

This script implements LinkedIn employee search using Recruitment Geek methodology.
Customize this script with your specific Recruitment Geek search implementation.
"""

import json
import os
import sys
import time
from pathlib import Path

def get_script_directory():
    """Get the directory where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """Load configuration from JSON file."""
    config_path = os.path.join(get_script_directory(), "company_config.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

def main():
    print("=" * 70)
    print("EMPLOYEE DISCOVERY TOOLKIT: LINKEDIN SEARCH (VIA RECRUITMENT GEEK)")
    print("=" * 70)
    
    # Load configuration
    config = load_config()
    
    print(f"Company: {config.get('company_name', 'Not set')}")
    print(f"Location: {config.get('location', 'Not set')}")
    print(f"Website: {config.get('company_website', 'Not set')}")
    print(f"Pages to scrape: {config.get('pages_to_scrape', 5)}")
    
    print("\\n🔍 LinkedIn Search via Recruitment Geek")
    print("This search method is designed for specialized recruitment searches.")
    
    print("\\n📝 Implementation needed:")
    print("   • Add your Recruitment Geek search logic here")
    print("   • Implement LinkedIn profile discovery")
    print("   • Add data extraction and processing")
    print("   • Generate Excel output with results")
    
    print("\\n💡 Suggested implementation:")
    print("   1. Use specialized search queries for recruitment")
    print("   2. Target specific job titles and seniority levels")
    print("   3. Extract comprehensive profile information")
    print("   4. Generate recruiter-friendly output format")
    
    # Placeholder for actual implementation
    print("\\n⚠️  This functionality is not yet implemented.")
    print("Replace this placeholder with your Recruitment Geek search logic.")
    
    # Example of what the implementation might look like:
    print("\\n--- Example Implementation Structure ---")
    print("def recruitment_geek_search():")
    print("    # 1. Setup specialized search parameters")
    print("    # 2. Execute targeted LinkedIn searches")
    print("    # 3. Extract profile data optimized for recruitment")
    print("    # 4. Generate recruiter-friendly Excel output")
    print("    pass")
    
    input("\\nPress Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(placeholder)
    
    print(f"✅ Created Recruitment Geek placeholder at {script_path}")
    print("📝 Edit this file to implement your Recruitment Geek LinkedIn search functionality.")

def create_script_placeholder(option, script_path, search_name):
    """Create a placeholder script file for options that don't have implementations yet."""
    placeholder = f'''#!/usr/bin/env python3
"""
Employee Discovery Toolkit: {search_name}

This is a placeholder script for the {search_name} functionality.
Implement the specific search logic for this method here.
"""

import json
import os
import sys
import time

def get_script_directory():
    """Get the directory where the script is located."""
    return os.path.dirname(os.path.abspath(__file__))

def load_config():
    """Load configuration from JSON file."""
    config_path = os.path.join(get_script_directory(), "company_config.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {{e}}")
        sys.exit(1)

def main():
    print("=" * 60)
    print(f"EMPLOYEE DISCOVERY TOOLKIT: {search_name.upper()}")
    print("=" * 60)
    
    # Load configuration
    config = load_config()
    
    print(f"Company: {{config.get('company_name', 'Not set')}}")
    print(f"Location: {{config.get('location', 'Not set')}}")
    print(f"Website: {{config.get('company_website', 'Not set')}}")
    
    print("\\nThis functionality is not yet implemented.")
    print("Implement the {search_name} logic in this script.")
    
    input("\\nPress Enter to exit...")

if __name__ == "__main__":
    main()
'''
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(placeholder)
    
    print(f"✅ Created placeholder at {script_path}")
    print(f"📝 Edit this file to implement {search_name} functionality.")

def main():
    clear_screen()
    print("=" * 70)
    print("EMPLOYEE DISCOVERY TOOLKIT")
    print("=" * 70)
    print("\nThis tool helps you find employees at specific companies using various search methods.")
    print("Now includes LinkedIn Search via Recruitment Geek for specialized recruitment searches.")
    
    # Check dependencies
    if not check_dependencies():
        print("Failed to install required dependencies.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    # Collect or update basic company information
    config = collect_basic_info()
    
    while True:
        # Display search options
        display_search_options()
        
        # Get user choice (including 1a)
        choice = get_user_choice()
        
        if choice == 0:
            print("\nExiting Employee Discovery Toolkit. Goodbye!")
            break
        elif choice in [1, '1a', 2, 3, 4, 5]:
            execute_search(choice, config)
            input("\nPress Enter to return to the main menu...")
        else:
            print("Invalid option. Please select a valid choice.")
            time.sleep(2)

if __name__ == "__main__":
    main()