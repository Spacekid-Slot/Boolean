#!/usr/bin/env python3
"""
Enhanced Employee Discovery Toolkit - Input Configuration with Job Title Selection

This script collects company information, validates inputs, and allows users
to specify job titles to search for before launching the employee discovery process.
"""

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InputCollector:
    """Handles user input collection and validation with job title selection."""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.config_file = self.script_dir / "company_config.json"
        
        # Default job titles categorized by type
        self.default_job_titles = {
            'Executive/Leadership': [
                "CEO", "Chief Executive Officer", "Managing Director", "President",
                "Chief Financial Officer", "CFO", "Chief Technology Officer", "CTO",
                "Chief Operating Officer", "COO", "Chief Marketing Officer", "CMO",
                "Executive Director", "Executive Vice President", "Chairman"
            ],
            'Management': [
                "Director", "Manager", "Head of", "Vice President", "VP",
                "Senior Manager", "Regional Manager", "General Manager",
                "Department Head", "Team Lead", "Operations Manager"
            ],
            'Property/Real Estate': [
                "Property Manager", "Estate Agent", "Letting Agent", "Property Factor",
                "Property Director", "Asset Manager", "Development Manager",
                "Property Investment Manager", "Facilities Manager", "Portfolio Manager",
                "Property Consultant", "Real Estate Manager"
            ],
            'Professional/Technical': [
                "Engineer", "Developer", "Analyst", "Consultant", "Specialist",
                "Senior Engineer", "Lead Developer", "Principal Consultant",
                "Technical Lead", "Project Manager", "Account Manager",
                "Business Analyst", "Systems Analyst"
            ],
            'Finance/Accounting': [
                "Accountant", "Financial Analyst", "Investment Manager", "Fund Manager",
                "Financial Controller", "Finance Manager", "Treasury Manager",
                "Risk Manager", "Compliance Manager", "Audit Manager"
            ],
            'Sales/Marketing': [
                "Sales Manager", "Marketing Manager", "Business Development",
                "Account Executive", "Sales Director", "Marketing Director",
                "Client Manager", "Relationship Manager", "Commercial Manager"
            ]
        }
        
    def clear_screen(self):
        """Clear the terminal screen based on OS."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def validate_company_name(self, name: str) -> bool:
        """Validate company name input."""
        if not name or len(name.strip()) < 2:
            return False
        # Check for reasonable length and characters
        if len(name) > 100:
            return False
        # Allow letters, numbers, spaces, and common business characters
        if not re.match(r'^[a-zA-Z0-9\s&\-.,()]+$', name):
            return False
        return True
    
    def validate_location(self, location: str) -> bool:
        """Validate location input."""
        if not location or len(location.strip()) < 2:
            return False
        if len(location) > 50:
            return False
        # Allow letters, spaces, and common location characters
        if not re.match(r'^[a-zA-Z\s\-,\']+$', location):
            return False
        return True
    
    def validate_website(self, website: str) -> bool:
        """Validate and normalize website URL."""
        if not website:
            return False
        
        # Add protocol if missing
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            parsed = urlparse(website)
            if not parsed.netloc:
                return False
            # Basic domain validation
            if not re.match(r'^[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$', parsed.netloc):
                return False
            return True
        except Exception:
            return False
    
    def normalize_website(self, website: str) -> str:
        """Normalize website URL."""
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        return website.rstrip('/')
    
    def check_dependencies(self) -> bool:
        """Check and install required packages."""
        required_packages = [
            'requests',
            'beautifulsoup4', 
            'openpyxl',
            'selenium',
            'webdriver-manager'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                if package == 'beautifulsoup4':
                    import bs4
                elif package == 'webdriver-manager':
                    import webdriver_manager
                else:
                    __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            print(f"Installing missing packages: {', '.join(missing_packages)}")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", 
                    *missing_packages
                ])
                print("Packages installed successfully.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install packages: {e}")
                return False
        
        return True
    
    def display_job_title_categories(self):
        """Display available job title categories."""
        print("\n" + "=" * 60)
        print("JOB TITLE CATEGORIES")
        print("=" * 60)
        
        for i, (category, titles) in enumerate(self.default_job_titles.items(), 1):
            print(f"\n{i}. {category}:")
            # Show first few titles as examples
            sample_titles = titles[:4]
            print(f"   Examples: {', '.join(sample_titles)}")
            if len(titles) > 4:
                print(f"   (and {len(titles) - 4} more...)")
    
    def get_job_title_selection(self) -> list:
        """Allow user to select job titles to search for."""
        self.clear_screen()
        print("=" * 60)
        print("JOB TITLE SELECTION")
        print("=" * 60)
        print("You can specify which job titles to search for to get more targeted results.")
        print("This will improve search accuracy and find more relevant employees.\n")
        
        # Ask if user wants to select specific job titles
        use_custom = input("Do you want to select specific job titles to search for? (y/n, default: n): ").strip().lower()
        
        if use_custom not in ['y', 'yes']:
            print("Using comprehensive default job title list...")
            # Return flattened list of all default titles
            all_titles = []
            for titles in self.default_job_titles.values():
                all_titles.extend(titles)
            return all_titles
        
        selected_titles = []
        
        print("\nOptions:")
        print("1. Select entire categories")
        print("2. Enter custom job titles")
        print("3. Mix of both")
        
        choice = input("\nWhat would you like to do? (1/2/3, default: 1): ").strip()
        
        if choice in ['1', '3', '']:
            # Category selection
            self.display_job_title_categories()
            
            print(f"\nSelect categories to include (e.g., '1,3,5' or 'all'):")
            category_input = input("Categories: ").strip().lower()
            
            if category_input == 'all':
                # Add all titles
                for titles in self.default_job_titles.values():
                    selected_titles.extend(titles)
            else:
                # Parse category numbers
                try:
                    category_nums = [int(x.strip()) for x in category_input.split(',') if x.strip()]
                    categories = list(self.default_job_titles.items())
                    
                    for num in category_nums:
                        if 1 <= num <= len(categories):
                            category_name, titles = categories[num - 1]
                            selected_titles.extend(titles)
                            print(f"Added {len(titles)} titles from {category_name}")
                        else:
                            print(f"Invalid category number: {num}")
                except ValueError:
                    print("Invalid input format. Using default titles.")
                    for titles in self.default_job_titles.values():
                        selected_titles.extend(titles)
        
        if choice in ['2', '3']:
            # Custom title entry
            print(f"\nEnter custom job titles (one per line, empty line to finish):")
            print("Examples: 'Software Engineer', 'Product Manager', 'HR Director'")
            
            while True:
                custom_title = input("Job title: ").strip()
                if not custom_title:
                    break
                if custom_title not in selected_titles:
                    selected_titles.append(custom_title)
                    print(f"Added: {custom_title}")
                else:
                    print(f"Already added: {custom_title}")
        
        # Remove duplicates and sort
        selected_titles = sorted(list(set(selected_titles)))
        
        if not selected_titles:
            print("No job titles selected. Using default comprehensive list...")
            for titles in self.default_job_titles.values():
                selected_titles.extend(titles)
        
        print(f"\nSelected {len(selected_titles)} job titles for searching.")
        
        # Show confirmation
        if len(selected_titles) <= 20:
            print("Selected titles:")
            for title in selected_titles:
                print(f"  - {title}")
        else:
            print("Sample of selected titles:")
            for title in selected_titles[:10]:
                print(f"  - {title}")
            print(f"  ... and {len(selected_titles) - 10} more")
        
        confirm = input(f"\nProceed with these {len(selected_titles)} job titles? (y/n, default: y): ").strip().lower()
        if confirm == 'n':
            return self.get_job_title_selection()  # Retry
        
        return selected_titles
    
    def get_user_input(self) -> dict:
        """Collect and validate user input including job titles."""
        self.clear_screen()
        print("=" * 60)
        print("ENHANCED EMPLOYEE DISCOVERY TOOLKIT - INPUT CONFIGURATION")
        print("=" * 60)
        print("\nThis script will collect information about employees at a specific company.")
        print("You'll be prompted for company details and can specify job titles to search for.\n")
        
        # Get company name
        while True:
            company_name = input("Enter company name: ").strip()
            if self.validate_company_name(company_name):
                break
            print("Invalid company name. Please use 2-100 characters with letters, numbers, and basic punctuation.")
        
        # Get location
        while True:
            location = input("Enter location (city, state, county, or country): ").strip()
            if self.validate_location(location):
                break
            print("Invalid location. Please use 2-50 characters with letters and basic punctuation.")
        
        # Get company website
        while True:
            website = input("Enter company website (e.g., www.example.com): ").strip()
            if self.validate_website(website):
                website = self.normalize_website(website)
                break
            print("Invalid website. Please enter a valid domain (e.g., example.com or www.example.com)")
        
        # Get job titles
        job_titles = self.get_job_title_selection()
        
        # Get number of pages to scrape
        while True:
            try:
                pages_input = input("Enter number of search pages to scrape (1-100, default: 5): ").strip()
                if not pages_input:
                    num_pages = 5
                    break
                else:
                    num_pages = int(pages_input)
                    if not 1 <= num_pages <= 100:
                        raise ValueError("Pages must be between 1 and 100")
                    
                    # Warning for high page counts
                    if num_pages > 20:
                        print(f"\n⚠️  Warning: Searching {num_pages} pages may take a long time and could trigger rate limiting.")
                        print("Consider starting with fewer pages (5-10) for initial testing.")
                        confirm = input("Continue with this setting? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("Please enter a different number of pages.")
                            continue
                    break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a number between 1 and 100.")
        
        # Get debug mode
        debug_input = input("Enable debug mode for verbose output? (y/n, default: n): ").strip().lower()
        debug_enabled = debug_input in ['y', 'yes']
        
        # Get review mode
        review_input = input("Enable review mode for manual validation? (y/n, default: y): ").strip().lower()
        review_enabled = review_input not in ['n', 'no']
        
        return {
            "company_name": company_name,
            "location": location,
            "company_website": website,
            "job_titles": job_titles,
            "pages_to_scrape": num_pages,
            "debug_mode": debug_enabled,
            "review_mode": review_enabled
        }
    
    def create_config(self, user_input: dict) -> dict:
        """Create configuration dictionary."""
        company_name = user_input["company_name"]
        location = user_input["location"]
        
        # Create safe filename
        safe_company = re.sub(r'[^\w\-_]', '_', company_name)
        safe_location = re.sub(r'[^\w\-_]', '_', location)
        
        config = {
            "company_name": company_name,
            "location": location,
            "company_website": user_input["company_website"],
            "job_titles": user_input["job_titles"],
            "output_file": f"{safe_company}_{safe_location}_employees.xlsx",
            "temp_data_file": "temp_employee_data.json",
            "processed_data_file": "processed_employee_data.json",
            "verified_data_file": "verified_employee_data.json",
            "pages_to_scrape": user_input["pages_to_scrape"],
            "debug_mode": user_input["debug_mode"],
            "review_mode": user_input["review_mode"],
            "search_types": ["linkedin", "website"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "2.1"
        }
        
        return config
    
    def save_config(self, config: dict) -> bool:
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def display_summary(self, config: dict):
        """Display configuration summary."""
        print("\nConfiguration saved successfully!")
        print(f"Company: {config['company_name']}")
        print(f"Location: {config['location']}")
        print(f"Website: {config['company_website']}")
        print(f"Job titles to search: {len(config['job_titles'])}")
        print(f"Pages to scrape: {config['pages_to_scrape']}")
        print(f"Debug mode: {'Enabled' if config['debug_mode'] else 'Disabled'}")
        print(f"Review mode: {'Enabled' if config['review_mode'] else 'Disabled'}")
        print(f"Output will be saved to: {config['output_file']}")
        
        # Show job title summary
        if len(config['job_titles']) <= 10:
            print(f"\nJob titles to search for:")
            for title in config['job_titles']:
                print(f"  - {title}")
        else:
            print(f"\nSample job titles to search for:")
            for title in config['job_titles'][:5]:
                print(f"  - {title}")
            print(f"  ... and {len(config['job_titles']) - 5} more")
    
    def launch_selector(self) -> bool:
        """Launch the employee discovery selector script."""
        selector_script = self.script_dir / "employee_discovery_selector.py"
        
        print("\nLaunching search method selector...")
        
        if not selector_script.exists():
            # If selector doesn't exist, try to launch script2 directly
            script2_path = self.script_dir / "script2_web_scraping.py"
            if script2_path.exists():
                selector_script = script2_path
                print("Selector not found, launching web scraping directly...")
            else:
                print(f"Error: Could not find selector or web scraping script")
                print(f"Looking for: {selector_script}")
                print(f"Current directory: {self.script_dir}")
                return False
        
        try:
            if sys.platform == 'win32':
                subprocess.Popen(
                    [sys.executable, str(selector_script)], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([sys.executable, str(selector_script)])
            
            logger.info(f"Successfully launched {selector_script.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error launching selector script: {e}")
            return False
    
    def run(self):
        """Main execution method."""
        try:
            # Check dependencies
            if not self.check_dependencies():
                print("Failed to install required dependencies.")
                print("Please install manually: pip install requests beautifulsoup4 openpyxl selenium webdriver-manager")
                return False
            
            # Collect user input
            user_input = self.get_user_input()
            
            # Create configuration
            config = self.create_config(user_input)
            
            # Save configuration
            if not self.save_config(config):
                print("Failed to save configuration. Please check file permissions.")
                return False
            
            # Display summary
            self.display_summary(config)
            
            # Launch next script
            if self.launch_selector():
                print("\nSetup complete! The enhanced employee discovery process has been launched.")
                print("The search will now target specific job titles for better results.")
                print("This window can now be closed.")
                return True
            else:
                print("\nConfiguration saved, but failed to launch next script.")
                print("Please run the next script manually.")
                return False
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"An unexpected error occurred: {e}")
            return False

def main():
    """Main function."""
    collector = InputCollector()
    success = collector.run()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()