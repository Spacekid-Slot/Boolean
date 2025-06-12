#!/usr/bin/env python3
"""
Enhanced Employee Discovery Toolkit - Input Configuration with Job Title Selection

COMPLETELY FIXED VERSION - All location handling bugs resolved
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
        
        # Load LinkedIn locations database if available
        self.locations_db_file = self.script_dir / "linkedin_locations_database.json"
        self.locations_db = self._load_locations_database()
        
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
        
    def _load_locations_database(self) -> dict:
        """Load LinkedIn locations database if available."""
        try:
            if self.locations_db_file.exists():
                with open(self.locations_db_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info("LinkedIn locations database loaded")
                return data
            else:
                return {}
        except Exception as e:
            logger.warning(f"LinkedIn locations database unavailable: {e}")
            return {}
    
    def clear_screen(self):
        """Clear the terminal screen based on OS."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def validate_company_name(self, name: str) -> bool:
        """Validate company name input."""
        if not name or len(name.strip()) < 2:
            return False
        if len(name) > 100:
            return False
        if not re.match(r'^[a-zA-Z0-9\s&\-.,()]+$', name):
            return False
        return True
    
    def validate_location(self, location: str) -> bool:
        """Validate location input."""
        if not location or len(location.strip()) < 2:
            return False
        if len(location) > 50:
            return False
        if not re.match(r'^[a-zA-Z\s\-,\']+$', location):
            return False
        return True
    
    def validate_website(self, website: str) -> bool:
        """Validate and normalize website URL."""
        if not website:
            return False
        
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            parsed = urlparse(website)
            if not parsed.netloc:
                return False
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
            'requests', 'beautifulsoup4', 'openpyxl', 'selenium', 'webdriver-manager'
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
        
        use_custom = input("Do you want to select specific job titles to search for? (y/n, default: y): ").strip().lower()
        
        if use_custom in ['n', 'no']:
            print("Skipping job title selection - will use general search...")
            return []
        
        selected_titles = []
        
        print("\nOptions:")
        print("1. Select entire categories")
        print("2. Enter custom job titles")
        print("3. Mix of both")
        
        choice = input("\nWhat would you like to do? (1/2/3, default: 1): ").strip()
        
        if choice in ['1', '3', '']:
            self.display_job_title_categories()
            
            print(f"\nSelect categories to include (e.g., '1,3,5' or 'all'):")
            category_input = input("Categories: ").strip().lower()
            
            if category_input == 'all':
                for titles in self.default_job_titles.values():
                    selected_titles.extend(titles)
                print(f"Added all {len(selected_titles)} job titles")
            else:
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
                    print("Invalid input format. Using some default titles.")
                    selected_titles = ["Manager", "Director", "CEO", "CFO", "CTO"]
        
        if choice in ['2', '3']:
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
        
        selected_titles = sorted(list(set(selected_titles)))
        
        if not selected_titles:
            print("No job titles selected. Will use general search...")
            return []
        
        print(f"\nSelected {len(selected_titles)} job titles for searching.")
        
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
            return self.get_job_title_selection()
        
        return selected_titles
    
    def get_location_input(self) -> dict:
        """Get location input - simplified to always work."""
        if not self.locations_db:
            # No database available - simple manual input
            while True:
                location = input("Enter location (city, state, county, or country): ").strip()
                if self.validate_location(location):
                    return {
                        'location_type': 'manual',
                        'primary_location': location,
                        'manual_input': True
                    }
                print("Invalid location. Please use 2-50 characters with letters and basic punctuation.")
        
        # Database available - offer enhanced selection
        print("\n📍 Location Input Options:")
        print("1. Use LinkedIn location database (enhanced targeting)")
        print("2. Enter location manually (quick)")
        
        while True:
            choice = input("\nSelect option (1/2, default: 2): ").strip()
            
            if choice == '1':
                return self._select_from_database()
            elif choice in ['2', '']:
                while True:
                    location = input("Enter location (city, state, county, or country): ").strip()
                    if self.validate_location(location):
                        return {
                            'location_type': 'manual',
                            'primary_location': location,
                            'manual_input': True
                        }
                    print("Invalid location. Please use 2-50 characters with letters and basic punctuation.")
            else:
                print("Please enter 1 or 2")
    
    def _select_from_database(self) -> dict:
        """Select location from LinkedIn database with complete implementation."""
        try:
            primary_markets = self.locations_db['linkedin_locations']['primary_markets']
            
            # Step 1: Select Region
            print("\n🌍 Available Regions:")
            regions = list(primary_markets.keys())
            for i, region in enumerate(regions, 1):
                print(f"   {i}. {region.replace('_', ' ').title()}")
            
            while True:
                try:
                    choice = input(f"\nSelect region (1-{len(regions)}): ").strip()
                    region_idx = int(choice) - 1
                    if 0 <= region_idx < len(regions):
                        break
                    print(f"Please enter 1-{len(regions)}")
                except ValueError:
                    print("Please enter a valid number")
            
            selected_region = regions[region_idx]
            
            # Step 2: Select Country
            countries = list(primary_markets[selected_region].keys())
            print(f"\n🏛️ Countries in {selected_region.replace('_', ' ').title()}:")
            for i, country in enumerate(countries, 1):
                print(f"   {i}. {country.replace('_', ' ').title()}")
            
            while True:
                try:
                    choice = input(f"\nSelect country (1-{len(countries)}): ").strip()
                    country_idx = int(choice) - 1
                    if 0 <= country_idx < len(countries):
                        break
                    print(f"Please enter 1-{len(countries)}")
                except ValueError:
                    print("Please enter a valid number")
            
            selected_country = countries[country_idx]
            country_data = primary_markets[selected_region][selected_country]
            
            # Step 3: Select City (if available)
            cities = list(country_data.get('cities', {}).keys())
            
            if cities:
                print(f"\n🏙️ Cities in {selected_country.replace('_', ' ').title()}:")
                for i, city in enumerate(cities, 1):
                    print(f"   {i}. {city.replace('_', ' ').title()}")
                
                while True:
                    try:
                        choice = input(f"\nSelect city (1-{len(cities)}): ").strip()
                        city_idx = int(choice) - 1
                        if 0 <= city_idx < len(cities):
                            break
                        print(f"Please enter 1-{len(cities)}")
                    except ValueError:
                        print("Please enter a valid number")
                
                selected_city = cities[city_idx]
                city_variations = country_data['cities'][selected_city]
                
                # Return city-level configuration
                return {
                    'location_type': 'primary_city',
                    'primary_location': city_variations[0] if city_variations else selected_city.replace('_', ' ').title(),
                    'city_display_name': selected_city.replace('_', ' ').title(),
                    'country': selected_country,
                    'country_display_name': selected_country.replace('_', ' ').title(),
                    'region': selected_region,
                    'city_variations': city_variations,
                    'location_variations': city_variations,
                    'country_search': selected_country,
                    'manual_input': False
                }
            else:
                # No cities available - return country-level configuration
                country_terms = country_data.get('country_terms', [selected_country.replace('_', ' ').title()])
                return {
                    'location_type': 'secondary_country',
                    'primary_location': country_terms[0] if country_terms else selected_country.replace('_', ' ').title(),
                    'country': selected_country,
                    'country_display_name': selected_country.replace('_', ' ').title(),
                    'region': selected_region,
                    'country_terms': country_terms,
                    'location_variations': country_terms,
                    'country_search': selected_country,
                    'manual_input': False
                }
            
        except Exception as e:
            logger.warning(f"Database selection failed: {e}, falling back to manual input")
            while True:
                location = input("Enter location (city, state, county, or country): ").strip()
                if self.validate_location(location):
                    return {
                        'location_type': 'manual',
                        'primary_location': location,
                        'manual_input': True
                    }
                print("Invalid location. Please use 2-50 characters with letters and basic punctuation.")
    
    def get_user_input(self) -> dict:
        """Collect and validate user input."""
        self.clear_screen()
        print("=" * 60)
        print("ENHANCED EMPLOYEE DISCOVERY TOOLKIT - INPUT CONFIGURATION")
        print("=" * 60)
        print("\nThis script will collect information about employees at a specific company.")
        print("You'll be prompted for company details and can specify job titles to search for.")
        
        if self.locations_db:
            print("Enhanced with LinkedIn location database for precise targeting.")
        print()
        
        # Get company name
        while True:
            company_name = input("Enter company name: ").strip()
            if self.validate_company_name(company_name):
                break
            print("Invalid company name. Please use 2-100 characters with letters, numbers, and basic punctuation.")
        
        # Get location configuration
        location_config = self.get_location_input()
        
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
                pages_input = input("Enter number of search pages to scrape (1-20, default: 5): ").strip()
                if not pages_input:
                    num_pages = 5
                    break
                else:
                    num_pages = int(pages_input)
                    if not 1 <= num_pages <= 20:
                        raise ValueError("Pages must be between 1 and 20")
                    break
            except ValueError as e:
                print(f"Invalid input: {e}. Please enter a number between 1 and 20.")
        
        return {
            "company_name": company_name,
            "location_config": location_config,
            "location": location_config.get('primary_location', ''),
            "company_website": website,
            "job_titles": job_titles,
            "pages_to_scrape": num_pages
        }
    
    def create_config(self, user_input: dict) -> dict:
        """Create configuration dictionary."""
        company_name = user_input["company_name"]
        location_config = user_input["location_config"]
        
        # Get location name for filename
        location_name = (location_config.get('city_display_name') or 
                        location_config.get('country_display_name') or 
                        location_config.get('primary_location', 'Location'))
        
        # Create safe filename
        safe_company = re.sub(r'[^\w\-_]', '_', company_name)
        safe_location = re.sub(r'[^\w\-_]', '_', location_name)
        
        config = {
            "company_name": company_name,
            "location": location_config.get('primary_location', ''),
            "location_config": location_config,
            "company_website": user_input["company_website"],
            "job_titles": user_input["job_titles"],
            "output_file": f"{safe_company}_{safe_location}_employees.xlsx",
            "temp_data_file": "temp_employee_data.json",
            "processed_data_file": "processed_employee_data.json",
            "verified_data_file": "verified_employee_data.json",
            "pages_to_scrape": user_input["pages_to_scrape"],
            "debug_mode": False,
            "review_mode": True,
            "search_types": ["linkedin", "website"],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "version": "2.4-Complete-Fixed"
        }
        
        return config
    
    def save_config(self, config: dict) -> bool:
        """Save configuration to file."""
        try:
            if not isinstance(config.get('job_titles'), list):
                config['job_titles'] = []
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
            
            # Verify save
            with open(self.config_file, 'r', encoding='utf-8') as f:
                saved_config = json.load(f)
                if saved_config.get('job_titles') != config.get('job_titles'):
                    logger.error("Job titles not saved correctly")
                    return False
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            return False
    
    def display_summary(self, config: dict):
        """Display configuration summary."""
        location_config = config.get('location_config', {})
        
        print("\n" + "=" * 60)
        print("CONFIGURATION SUMMARY")
        print("=" * 60)
        print(f"Company: {config['company_name']}")
        print(f"Website: {config['company_website']}")
        print(f"Pages to scrape: {config['pages_to_scrape']}")
        
        # Location display
        if location_config.get('location_type') == 'primary_city':
            print(f"\n📍 ENHANCED LOCATION (City-Level):")
            print(f"   City: {location_config['city_display_name']}")
            print(f"   Country: {location_config['country'].replace('_', ' ').title()}")
            print(f"   Location Variations: {len(location_config.get('location_variations', []))}")
            print(f"   Primary Format: \"{location_config['primary_location']}\"")
        elif location_config.get('location_type') == 'secondary_country':
            print(f"\n🌍 ENHANCED LOCATION (Country-Level):")
            print(f"   Country: {location_config['country_display_name']}")
            print(f"   Location Terms: {len(location_config.get('country_terms', []))}")
        else:
            print(f"\n📍 LOCATION (Manual):")
            print(f"   Location: {location_config.get('primary_location', config.get('location', ''))}")
        
        # Job titles
        job_titles = config.get('job_titles', [])
        if job_titles:
            print(f"\n🎯 JOB TITLES ({len(job_titles)}):")
            print(f"   Search strategy: Targeted search for specific job titles")
            
            if len(job_titles) <= 10:
                print(f"   Job titles to search for:")
                for title in job_titles:
                    print(f"     - {title}")
            else:
                print(f"   Sample job titles to search for:")
                for title in job_titles[:5]:
                    print(f"     - {title}")
                print(f"     ... and {len(job_titles) - 5} more")
        else:
            print(f"\n🎯 JOB TITLES: None specified")
            print(f"   Search strategy: General company search")
        
        print(f"\n💾 Output will be saved to: {config['output_file']}")
        print("=" * 60)
    
    def launch_next_script(self) -> bool:
        """Launch the next script in the process."""
        selector_script = self.script_dir / "employee_discovery_selector.py"
        
        if selector_script.exists():
            script_to_launch = selector_script
            script_name = "Employee Discovery Selector"
        else:
            script2_path = self.script_dir / "script2_web_scraping.py"
            if script2_path.exists():
                script_to_launch = script2_path
                script_name = "LinkedIn Search"
            else:
                print(f"❌ Could not find next script to launch")
                print(f"Please run one of these scripts manually:")
                print(f"  - employee_discovery_selector.py")
                print(f"  - script2_web_scraping.py")
                return False
        
        try:
            print(f"\n🚀 Launching {script_name}...")
            
            if sys.platform == 'win32':
                subprocess.Popen(
                    [sys.executable, str(script_to_launch)], 
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                subprocess.Popen([sys.executable, str(script_to_launch)])
            
            print(f"✅ {script_name} launched successfully!")
            logger.info(f"Successfully launched {script_to_launch.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error launching next script: {e}")
            print(f"❌ Failed to launch {script_name}")
            print(f"Please run {script_to_launch.name} manually")
            return False
    
    def run(self):
        """Main execution method."""
        try:
            # Check dependencies
            print("🔧 Checking dependencies...")
            if not self.check_dependencies():
                print("❌ Failed to install required dependencies.")
                print("Please install manually: pip install requests beautifulsoup4 openpyxl selenium webdriver-manager")
                return False
            
            print("✅ All dependencies ready")
            
            # Collect user input
            user_input = self.get_user_input()
            
            # Create configuration
            config = self.create_config(user_input)
            
            # Display summary for confirmation
            self.display_summary(config)
            
            # Get final confirmation
            confirm = input("\nSave this configuration and proceed? (y/n, default: y): ").strip().lower()
            if confirm == 'n':
                print("❌ Configuration cancelled.")
                return False
            
            # Save configuration
            if not self.save_config(config):
                print("❌ Failed to save configuration. Please check file permissions.")
                return False
            
            print("✅ Configuration saved successfully!")
            
            # Launch next script
            if self.launch_next_script():
                print("\n🎉 Setup complete! The employee discovery process has been launched.")
                if config.get('job_titles'):
                    print(f"🎯 The search will target {len(config['job_titles'])} specific job titles for better results.")
                else:
                    print("🔍 The search will use general company search.")
                print("This window can be closed.")
                return True
            else:
                print("\n⚠️ Configuration saved, but failed to launch next script.")
                print("Please run the next script manually:")
                print("  - employee_discovery_selector.py (preferred)")
                print("  - script2_web_scraping.py (direct)")
                return False
                
        except KeyboardInterrupt:
            print("\n\n❌ Operation cancelled by user.")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            print(f"An unexpected error occurred: {e}")
            return False

def main():
    """Main function."""
    try:
        print("=" * 60)
        print("🚀 EMPLOYEE DISCOVERY TOOLKIT - SETUP")
        print("=" * 60)
        print("Welcome! This will help you find employees at any company.")
        
        collector = InputCollector()
        success = collector.run()
        
        if not success:
            input("\nPress Enter to exit...")
            sys.exit(1)
        else:
            print("\n✅ Setup completed successfully!")
            input("Press Enter to close this window...")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        input("Press Enter to exit...")
        sys.exit(1)

if __name__ == "__main__":
    main()