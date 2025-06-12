#!/usr/bin/env python3
"""
Enhanced Employee Discovery Toolkit: Search Method Selector

This script provides users with enhanced search options including
country-specific LinkedIn domains and simplified data extraction.
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

def check_linkedin_locations_database():
    """Check if LinkedIn locations database is available."""
    db_path = Path(__file__).parent.absolute() / "linkedin_locations_database.json"
    return db_path.exists()

def get_linkedin_domain_info(config):
    """Get information about the LinkedIn domain that will be used."""
    location_config = config.get('location_config', {})
    
    if not location_config:
        return "linkedin.com", "Global"
    
    # Simple domain detection for display purposes
    location_str = location_config.get('primary_location', '').lower()
    
    domain_mappings = {
        'uk': ('uk.linkedin.com', 'United Kingdom'),
        'united kingdom': ('uk.linkedin.com', 'United Kingdom'),
        'england': ('uk.linkedin.com', 'United Kingdom'),
        'scotland': ('uk.linkedin.com', 'United Kingdom'),
        'london': ('uk.linkedin.com', 'United Kingdom'),
        'edinburgh': ('uk.linkedin.com', 'United Kingdom'),
        'manchester': ('uk.linkedin.com', 'United Kingdom'),
        'france': ('fr.linkedin.com', 'France'),
        'paris': ('fr.linkedin.com', 'France'),
        'germany': ('de.linkedin.com', 'Germany'),
        'berlin': ('de.linkedin.com', 'Germany'),
        'australia': ('au.linkedin.com', 'Australia'),
        'sydney': ('au.linkedin.com', 'Australia'),
        'canada': ('ca.linkedin.com', 'Canada'),
        'toronto': ('ca.linkedin.com', 'Canada')
    }
    
    for location_key, (domain, country) in domain_mappings.items():
        if location_key in location_str:
            return domain, country
    
    return "linkedin.com", "Global"

def display_search_options():
    """Display available search options with enhanced information."""
    config = load_config()
    has_locations_db = check_linkedin_locations_database()
    linkedin_domain, target_country = get_linkedin_domain_info(config)
    
    os.system('cls' if os.name == 'nt' else 'clear')
    print("=" * 70)
    print("ENHANCED EMPLOYEE DISCOVERY TOOLKIT: SEARCH METHOD SELECTION")
    print("=" * 70)
    
    print(f"\n📋 Current Configuration:")
    print(f"   Company: {config.get('company_name', 'Not set')}")
    print(f"   Location: {config.get('location', 'Not set')}")
    
    if linkedin_domain != 'linkedin.com':
        print(f"   🎯 Enhanced Targeting: {target_country} ({linkedin_domain})")
        print(f"   ✅ Country-specific LinkedIn domain detected")
    else:
        print(f"   🌍 Standard Targeting: Global (linkedin.com)")
    
    if has_locations_db:
        print(f"   ✅ LinkedIn locations database available")
    
    job_titles = config.get('job_titles', [])
    if job_titles:
        print(f"   🎯 Job titles configured: {len(job_titles)}")
    else:
        print(f"   📝 Job titles: General search")
    
    print(f"\n🔍 Enhanced Search Methods Available:")
    
    print(f"\n1. 🔗 Enhanced LinkedIn Search (via Bing)")
    print(f"   • Uses country-specific LinkedIn domains for better targeting")
    if linkedin_domain != 'linkedin.com':
        print(f"   • Will search: site:{linkedin_domain}/in/")
    else:
        print(f"   • Will search: site:linkedin.com/in/")
    print(f"   • Simplified data extraction: Name + LinkedIn URL only")
    print(f"   • Higher reliability, cleaner results")
    print(f"   • Maintains job title searching without unreliable extraction")
    
    print(f"\n1a. 🔗 Enhanced Recruitment Geek (Alternative LinkedIn)")
    print(f"    • Same enhancements as option 1")
    print(f"    • Alternative search approach via Recruitment Geek")
    if linkedin_domain != 'linkedin.com':
        print(f"    • Will search: site:{linkedin_domain}/in/")
    else:
        print(f"    • Will search: site:linkedin.com/in/")
    print(f"    • Simplified data extraction: Name + LinkedIn URL only")
    print(f"    • Good backup if main LinkedIn search has issues")
    
    print(f"\n2. 🌐 Company Website Search")
    print(f"   • Scans the company's website for employee information")
    print(f"   • Looks for team/about/leadership pages")
    print(f"   • Extracts names and job titles from company site")
    print(f"   • Complements LinkedIn searches")
    
    print(f"\n3. 🔍 Comprehensive Search (LinkedIn + Website)")
    print(f"   • Runs enhanced LinkedIn search first")
    print(f"   • Then runs company website search")
    print(f"   • Most comprehensive results")
    print(f"   • Combines country-specific targeting with website data")
    
    print(f"\n4. 🔍 Comprehensive Search + Recruitment Geek")
    print(f"   • Runs enhanced LinkedIn search")
    print(f"   • Then runs enhanced Recruitment Geek search")
    print(f"   • Then runs company website search")
    print(f"   • Maximum coverage with all enhanced methods")
    
    print(f"\n5. 📊 Excel Report Only")
    print(f"   • Generate Excel from existing search data")
    print(f"   • Use if you already have search results")
    print(f"   • Creates comprehensive report with all data")
    
    print(f"\n0. ❌ Exit")
    
    print(f"\n💡 Recommendations:")
    if linkedin_domain != 'linkedin.com':
        print(f"   • Option 1 or 3 recommended (country-specific targeting available)")
        print(f"   • Enhanced targeting will significantly improve accuracy")
    else:
        print(f"   • Option 3 or 4 recommended for comprehensive coverage")
    
    if job_titles:
        print(f"   • Job title targeting configured - LinkedIn searches will be very targeted")
    else:
        print(f"   • Consider option 3 or 4 for broader coverage without job title targeting")

def get_user_choice():
    """Get user choice with enhanced validation."""
    while True:
        try:
            choice = input("\nEnter your choice (0, 1, 1a, 2, 3, 4, 5): ").strip().lower()
            if choice in ['0', '1', '1a', '2', '3', '4', '5']:
                if choice == '1a':
                    return '1a'
                return int(choice) if choice != '1a' else choice
            else:
                print("Invalid option. Please select 0, 1, 1a, 2, 3, 4, or 5.")
        except:
            print("Invalid input. Please try again.")

def run_script_safely(script_path, description):
    """Run a script safely with enhanced feedback."""
    print(f"\n🚀 Launching: {description}")
    print(f"Script: {script_path.name}")
    
    if not script_path.exists():
        print(f"❌ ERROR: Script not found at {script_path}")
        return False
    
    try:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        
        # Run in same window so we can see output
        result = subprocess.run([sys.executable, str(script_path)], env=env)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description} completed successfully.")
        else:
            print(f"⚠️ WARNING: {description} completed with issues.")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR launching {description}: {e}")
        return False

def execute_search(option):
    """Execute the selected search method with enhanced options."""
    config = load_config()
    script_dir = Path(__file__).parent.absolute()
    
    if not config.get('company_name'):
        print("❌ ERROR: No configuration found. Please run script1_input_collection.py first.")
        input("Press Enter to continue...")
        return
    
    linkedin_domain, target_country = get_linkedin_domain_info(config)
    
    if option == 1:  # Enhanced LinkedIn Search
        print(f"\n🔗 Enhanced LinkedIn Search Selected")
        if linkedin_domain != 'linkedin.com':
            print(f"   Using country-specific domain: {linkedin_domain}")
        print(f"   Simplified data extraction: Name + URL only")
        
        script_path = script_dir / "script2_web_scraping.py"
        run_script_safely(script_path, "Enhanced LinkedIn Search (via Bing)")
        
    elif option == '1a':  # Enhanced Recruitment Geek
        print(f"\n🔗 Enhanced Recruitment Geek Selected")
        if linkedin_domain != 'linkedin.com':
            print(f"   Using country-specific domain: {linkedin_domain}")
        print(f"   Alternative LinkedIn search approach")
        
        script_path = script_dir / "script2_geek.py"
        run_script_safely(script_path, "Enhanced Recruitment Geek Search")
        
    elif option == 2:  # Website Search
        print(f"\n🌐 Company Website Search Selected")
        script_path = script_dir / "script2a_company_website_search.py"
        run_script_safely(script_path, "Company Website Search")
        
    elif option == 3:  # LinkedIn + Website
        print(f"\n🔍 Comprehensive Search (LinkedIn + Website)")
        if linkedin_domain != 'linkedin.com':
            print(f"   Enhanced LinkedIn targeting: {linkedin_domain}")
        
        # Run LinkedIn search first
        script_path = script_dir / "script2_web_scraping.py"
        print(f"\n--- Phase 1: Enhanced LinkedIn Search ---")
        if run_script_safely(script_path, "Enhanced LinkedIn Search"):
            time.sleep(2)
            
            # Then run website search
            script_path = script_dir / "script2a_company_website_search.py"
            print(f"\n--- Phase 2: Company Website Search ---")
            run_script_safely(script_path, "Company Website Search")
        
    elif option == 4:  # All methods
        print(f"\n🔍 Maximum Coverage Search (All Methods)")
        if linkedin_domain != 'linkedin.com':
            print(f"   Enhanced LinkedIn targeting: {linkedin_domain}")
        
        # Run main LinkedIn search
        script_path = script_dir / "script2_web_scraping.py"
        print(f"\n--- Phase 1: Enhanced LinkedIn Search ---")
        if run_script_safely(script_path, "Enhanced LinkedIn Search"):
            time.sleep(2)
            
            # Run Recruitment Geek search
            script_path = script_dir / "script2_geek.py"
            print(f"\n--- Phase 2: Enhanced Recruitment Geek ---")
            if run_script_safely(script_path, "Enhanced Recruitment Geek"):
                time.sleep(2)
                
                # Run website search
                script_path = script_dir / "script2a_company_website_search.py"
                print(f"\n--- Phase 3: Company Website Search ---")
                run_script_safely(script_path, "Company Website Search")
        
    elif option == 5:  # Excel only
        print(f"\n📊 Excel Report Generation Selected")
        script_path = script_dir / "script4_excel_output.py"
        if script_path.exists():
            run_script_safely(script_path, "Excel Report Generation")
        else:
            print(f"❌ Excel script not found. Please check script4_excel_output.py exists.")

def display_post_search_info():
    """Display information about next steps after search completion."""
    print(f"\n" + "=" * 60)
    print(f"🎉 SEARCH COMPLETED!")
    print(f"=" * 60)
    print(f"📋 Next Steps Available:")
    print(f"   1. Review generated Excel reports")
    print(f"   2. Run LinkedIn verification (script5_linkedin_verification.py)")
    print(f"   3. Run data validation (script3a_data_review.py)")
    print(f"   4. Run name validation (script3b_name_validator.py)")
    print(f"\n💡 Recommended workflow:")
    print(f"   Excel Review → LinkedIn Verification → Name Validation → Final Report")

def main():
    """Main function with enhanced user experience."""
    try:
        while True:
            display_search_options()
            choice = get_user_choice()
            
            if choice == 0:
                print("\n❌ Exiting Enhanced Employee Discovery Toolkit. Goodbye!")
                break
            elif choice in [1, '1a', 2, 3, 4, 5]:
                config = load_config()
                linkedin_domain, target_country = get_linkedin_domain_info(config)
                
                print(f"\n🚀 Starting search with enhanced configuration...")
                if linkedin_domain != 'linkedin.com':
                    print(f"✅ Country-specific targeting enabled: {target_country}")
                
                execute_search(choice)
                display_post_search_info()
                input("\nPress Enter to return to the main menu...")
            
    except KeyboardInterrupt:
        print("\n\n❌ Exiting Enhanced Employee Discovery Toolkit. Goodbye!")

if __name__ == "__main__":
    main()