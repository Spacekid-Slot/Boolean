#!/usr/bin/env python3
"""
LinkedIn Search via Bing (X-ray Search) - COMPLETE WORKING VERSION

This script searches LinkedIn profiles using Bing X-ray search with
FULL INTERACTIVE WORKFLOW including configuration review, search strategy
confirmation, progress updates, and results review.

FIXED ISSUES:
- Job title searching now works properly
- Interactive confirmations restored
- Progress updates during search
- Results summary and verification offer
- Proper script chaining
"""

import json
import logging
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import quote_plus
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required packages."""
    required = ['selenium', 'webdriver-manager', 'openpyxl']
    for package in required:
        try:
            if package == 'webdriver-manager':
                import webdriver_manager
            elif package == 'openpyxl':
                import openpyxl
            else:
                __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.call([sys.executable, "-m", "pip", "install", package])

class LinkedInSearcher:
    """LinkedIn searcher with full interactive workflow and job title support."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.script_dir = Path(__file__).parent
        self.driver = None
        self.found_candidates = []
        self.processed_urls = set()
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Configuration error: {e}")
            sys.exit(1)
    
    def display_configuration(self):
        """Display current configuration and get user confirmation."""
        print("\n" + "=" * 60)
        print("📋 CURRENT CONFIGURATION")
        print("=" * 60)
        print(f"🏢 Company: {self.config.get('company_name', 'Not set')}")
        print(f"📍 Location: {self.config.get('location', 'Not set')}")
        
        job_titles = self.config.get('job_titles', [])
        if job_titles:
            print(f"🎯 JOB TITLES TO SEARCH FOR ({len(job_titles)}):")
            for i, title in enumerate(job_titles[:10], 1):  # Show first 10
                print(f"   {i}. {title}")
            if len(job_titles) > 10:
                print(f"   ... and {len(job_titles) - 10} more")
        else:
            print("🎯 JOB TITLES: Using general search (no specific titles)")
        
        print(f"📄 Pages to search: {self.config.get('pages_to_scrape', 5)}")
        print("=" * 60)
        
        while True:
            choice = input("\nDo you want to proceed with this configuration? (y/n/edit): ").strip().lower()
            if choice in ['y', 'yes', '']:
                return True
            elif choice in ['n', 'no']:
                print("❌ Configuration rejected. Exiting.")
                return False
            elif choice == 'edit':
                print("💡 To edit configuration, please run script1_input_collection.py")
                return False
            else:
                print("Please enter 'y' for yes, 'n' for no, or 'edit' to modify configuration.")
    
    def display_search_strategy(self):
        """Display search strategy and get confirmation."""
        company = self.config.get('company_name', '')
        location = self.config.get('location', '')
        job_titles = self.config.get('job_titles', [])
        
        print("\n" + "=" * 60)
        print("🎯 SEARCH STRATEGY")
        print("=" * 60)
        
        if job_titles:
            print("📝 Creating JOB TITLE SPECIFIC searches:")
            sample_titles = job_titles[:5] if len(job_titles) <= 5 else job_titles[:3]
            for title in sample_titles:
                print(f"   🎯 '{title}' at {company} in {location}")
            if len(job_titles) > 5:
                print(f"   🎯 ... and {len(job_titles) - 3} more job titles")
            
            total_queries = len(job_titles) * 3 + 4  # 3 per title + 4 general
            print(f"📊 TOTAL QUERIES: {total_queries}")
            print(f"🎯 EXPECTED RESULTS: Profiles matching {len(job_titles)} specific job titles")
            print(f"⏱️ ESTIMATED TIME: {(total_queries * 30) // 60} minutes")
        else:
            print("📝 Creating GENERAL COMPANY searches:")
            print(f"   🏢 {company} employees in {location}")
            print(f"   🔍 General company profiles")
            print(f"   📊 TOTAL QUERIES: 6")
            print(f"🎯 EXPECTED RESULTS: General company profiles")
            print(f"⏱️ ESTIMATED TIME: 3-4 minutes")
        
        print("=" * 60)
        
        while True:
            choice = input("\nProceed with this search strategy? (y/n): ").strip().lower()
            if choice in ['y', 'yes', '']:
                return True
            elif choice in ['n', 'no']:
                print("❌ Search cancelled.")
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def setup_browser(self):
        """Setup browser for searching."""
        try:
            print("\n🌐 Setting up browser...")
            
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from webdriver_manager.chrome import ChromeDriverManager
            
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Add user agent
            options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            # Hide automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Browser ready")
            return True
            
        except Exception as e:
            print(f"❌ Browser setup failed: {e}")
            return False
    
    def create_search_queries(self):
        """Create search queries based on configuration."""
        company = self.config.get('company_name', '')
        location = self.config.get('location', '')
        job_titles = self.config.get('job_titles', [])
        
        queries = []
        
        if job_titles:
            print(f"\n🔍 Creating targeted searches for {len(job_titles)} job titles...")
            
            # Job title specific searches
            for title in job_titles:
                title_queries = [
                    f'site:linkedin.com/in/ "{company}" "{title}" {location}',
                    f'site:linkedin.com/in/ "{title}" at "{company}" {location}',
                    f'site:linkedin.com/in/ "{title}" "{company}" {location}'
                ]
                queries.extend(title_queries)
                print(f"   📝 Added 3 queries for: {title}")
            
            # Add some general executive queries
            exec_queries = [
                f'site:linkedin.com/in/ "{company}" (Director OR Manager) {location}',
                f'site:linkedin.com/in/ "{company}" (CEO OR President OR "Vice President") {location}',
                f'site:linkedin.com/in/ "{company}" (Executive OR Officer) {location}',
                f'site:linkedin.com/in/ "{company}" {location}'  # General fallback
            ]
            queries.extend(exec_queries)
            print(f"   📝 Added 4 general executive queries")
            
        else:
            print(f"\n🔍 Creating general company searches...")
            # General company searches
            queries = [
                f'site:linkedin.com/in/ "{company}" {location}',
                f'site:linkedin.com/in/ "{company}" employee {location}',
                f'site:linkedin.com/in/ works at "{company}" {location}',
                f'site:linkedin.com/in/ "{company}" team {location}',
                f'site:linkedin.com/in/ "{company}" (Director OR Manager) {location}',
                f'site:linkedin.com/in/ "{company}" (CEO OR CFO OR CTO) {location}'
            ]
            print(f"   📝 Added 6 general company queries")
        
        print(f"✅ Total queries created: {len(queries)}")
        return queries
    
    def search_profiles(self):
        """Main search function with progress updates."""
        queries = self.create_search_queries()
        
        print(f"\n🔍 Starting LinkedIn search...")
        print("=" * 60)
        
        for i, query in enumerate(queries, 1):
            print(f"\n[Query {i}/{len(queries)}] Searching: {query[:80]}...")
            
            try:
                search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
                self.driver.get(search_url)
                time.sleep(random.uniform(3, 5))
                
                # Extract results
                results = self._extract_results()
                
                if results:
                    print(f"✅ Found {len(results)} new profiles")
                    self.found_candidates.extend(results)
                else:
                    print("ℹ️ No new profiles found")
                
                # Show progress every 3 queries
                if i % 3 == 0 and i < len(queries):
                    print(f"\n📊 Progress: {len(self.found_candidates)} profiles found so far")
                    choice = input(f"Continue searching? (y/n, default: y): ").strip().lower()
                    if choice in ['n', 'no']:
                        print("🛑 Search stopped by user")
                        break
                
                # Add delay between queries
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"❌ Error with query {i}: {e}")
                continue
        
        print(f"\n🎉 Search completed! Found {len(self.found_candidates)} total profiles")
        return self.found_candidates
    
    def _extract_results(self):
        """Extract LinkedIn profiles from search results."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        
        results = []
        
        try:
            # Wait for results to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.b_algo'))
            )
            
            # Get search result elements
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, 'li.b_algo')
            
            for result in result_elements:
                try:
                    title_elem = result.find_element(By.CSS_SELECTOR, 'h2 a')
                    title = title_elem.text
                    url = title_elem.get_attribute('href')
                    
                    if url and 'linkedin.com/in/' in url and url not in self.processed_urls:
                        # Extract name from title
                        name_match = re.search(r'^([^-|–]+)', title)
                        if name_match:
                            full_name = name_match.group(1).strip()
                            # Clean up common LinkedIn title patterns
                            full_name = re.sub(r'\s*-\s*LinkedIn.*', '', full_name, flags=re.IGNORECASE)
                            full_name = full_name.strip()
                            
                            name_parts = full_name.split()
                            
                            if len(name_parts) >= 2:
                                first_name = name_parts[0]
                                last_name = ' '.join(name_parts[1:])
                                
                                # Basic name validation
                                if (self._is_valid_name(first_name) and 
                                    self._is_valid_name(last_name)):
                                    
                                    candidate = {
                                        'first_name': first_name,
                                        'last_name': last_name,
                                        'title': self._extract_job_title(title),
                                        'link': url,
                                        'company_name': self.config.get('company_name', ''),
                                        'location': self.config.get('location', ''),
                                        'confidence': self._determine_confidence(title, url),
                                        'source': 'LinkedIn X-ray Search'
                                    }
                                    
                                    results.append(candidate)
                                    self.processed_urls.add(url)
                
                except Exception:
                    continue
                    
        except TimeoutException:
            pass  # No results found
        except Exception as e:
            logger.debug(f"Error extracting results: {e}")
        
        return results
    
    def _is_valid_name(self, name):
        """Basic name validation."""
        if not name or len(name) < 2 or len(name) > 30:
            return False
        if not re.match(r"^[a-zA-Z\-']+$", name):
            return False
        # Exclude obvious non-names
        if name.lower() in ['linkedin', 'profile', 'company', 'limited', 'group']:
            return False
        return True
    
    def _extract_job_title(self, title):
        """Extract job title from LinkedIn title."""
        # Look for common patterns
        patterns = [
            r'[-–]\s*([^|]+?)(?:\s+at\s+|\s+@\s+|\s+\|)',
            r'\|\s*([^|]+?)(?:\s+at\s+|\s+@\s+)',
            r'(?:,\s*)([^,]+?)(?:\s+at\s+|\s+@\s+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                if 3 < len(job_title) < 100:
                    return job_title
        
        return "LinkedIn Profile"
    
    def _determine_confidence(self, title, url):
        """Determine confidence level based on title and URL quality."""
        score = 0
        company = self.config.get('company_name', '').lower()
        
        # Company mention in title
        if company in title.lower():
            score += 3
        
        # Job title quality
        if any(word in title.lower() for word in ['director', 'manager', 'executive', 'president', 'ceo']):
            score += 2
        
        # LinkedIn profile URL quality
        if '/in/' in url:
            score += 1
        
        # Job title matching
        job_titles = self.config.get('job_titles', [])
        if job_titles:
            for job_title in job_titles:
                if job_title.lower() in title.lower():
                    score += 3
                    break
        
        if score >= 5:
            return 'high'
        elif score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def display_results_summary(self):
        """Display search results summary and get user confirmation."""
        if not self.found_candidates:
            print("\n❌ No LinkedIn profiles found!")
            print("\nThis could be due to:")
            print("• Company name spelling or location issues")
            print("• Limited public LinkedIn profiles")
            print("• Search engine restrictions")
            print("• Job titles too specific")
            return False
        
        print("\n" + "=" * 60)
        print("📊 SEARCH RESULTS SUMMARY")
        print("=" * 60)
        print(f"✅ Found {len(self.found_candidates)} LinkedIn profiles")
        
        # Show confidence breakdown
        confidence_counts = {}
        for candidate in self.found_candidates:
            conf = candidate.get('confidence', 'unknown')
            confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
        
        print("\n📈 Confidence Levels:")
        for conf, count in confidence_counts.items():
            print(f"   {conf.title()}: {count}")
        
        # Show sample results
        print(f"\n👥 Sample Profiles Found:")
        for i, candidate in enumerate(self.found_candidates[:5], 1):
            name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}"
            title = candidate.get('title', 'Unknown')
            print(f"   {i}. {name} - {title}")
        
        if len(self.found_candidates) > 5:
            print(f"   ... and {len(self.found_candidates) - 5} more")
        
        # Check if job titles were effective
        job_titles = self.config.get('job_titles', [])
        if job_titles:
            matched_titles = set()
            for candidate in self.found_candidates:
                title = candidate.get('title', '').lower()
                for job_title in job_titles:
                    if job_title.lower() in title:
                        matched_titles.add(job_title)
            
            if matched_titles:
                print(f"\n🎯 Job title matches found:")
                for title in list(matched_titles)[:3]:
                    print(f"   ✅ {title}")
                if len(matched_titles) > 3:
                    print(f"   ... and {len(matched_titles) - 3} more")
        
        print("=" * 60)
        
        while True:
            print("\nWhat would you like to do?")
            print("1. Save results and create Excel report")
            print("2. Try different search terms")
            print("3. Cancel and exit")
            
            choice = input("\nYour choice (1/2/3): ").strip()
            
            if choice == '1':
                return True
            elif choice == '2':
                print("💡 To modify search terms, please run script1_input_collection.py")
                return False
            elif choice == '3':
                print("❌ Search cancelled.")
                return False
            else:
                print("Please enter 1, 2, or 3.")
    
    def save_results(self):
        """Save search results to JSON file."""
        try:
            output_file = 'linkedin_candidates.json'
            with open(output_file, 'w') as f:
                json.dump(self.found_candidates, f, indent=4)
            
            print(f"💾 Results saved to {output_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving results: {e}")
            return False
    
    def create_excel_report(self):
        """Create Excel report with results."""
        try:
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            
            print("📊 Creating Excel report...")
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "LinkedIn Profiles"
            
            # Headers
            headers = ["First Name", "Last Name", "Job Title", "LinkedIn URL", "Company", "Location", "Confidence"]
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.font = Font(color="FFFFFF")
                cell.alignment = Alignment(horizontal="center")
            
            # Data
            for row, candidate in enumerate(self.found_candidates, 2):
                ws.cell(row=row, column=1, value=candidate.get('first_name', ''))
                ws.cell(row=row, column=2, value=candidate.get('last_name', ''))
                ws.cell(row=row, column=3, value=candidate.get('title', ''))
                
                # LinkedIn URL with hyperlink
                url_cell = ws.cell(row=row, column=4, value=candidate.get('link', ''))
                if candidate.get('link'):
                    url_cell.hyperlink = candidate['link']
                    url_cell.font = Font(color="0000FF", underline="single")
                
                ws.cell(row=row, column=5, value=candidate.get('company_name', ''))
                ws.cell(row=row, column=6, value=candidate.get('location', ''))
                
                # Confidence with color
                conf_cell = ws.cell(row=row, column=7, value=candidate.get('confidence', '').title())
                if conf_cell.value == 'High':
                    conf_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif conf_cell.value == 'Medium':
                    conf_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                else:
                    conf_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
            
            # Adjust column widths
            for col in ws.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column].width = min(max_length + 2, 50)
            
            # Save file
            company = self.config.get('company_name', 'Company').replace(' ', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company}_LinkedIn_Results_{timestamp}.xlsx"
            wb.save(filename)
            
            print(f"✅ Excel report created: {filename}")
            
            # Try to open
            try:
                if sys.platform == 'win32':
                    os.startfile(filename)
                elif sys.platform == 'darwin':
                    subprocess.call(['open', filename])
                else:
                    subprocess.call(['xdg-open', filename])
                print("📂 File opened automatically")
            except:
                print(f"📂 Please open manually: {filename}")
            
            return True
            
        except Exception as e:
            print(f"❌ Excel creation error: {e}")
            return False
    
    def offer_verification(self):
        """Offer to run LinkedIn verification."""
        if not self.found_candidates:
            return
        
        print("\n" + "=" * 60)
        print("🔗 LINKEDIN VERIFICATION AVAILABLE")
        print("=" * 60)
        print(f"Found {len(self.found_candidates)} LinkedIn profiles")
        print("\nVerification can:")
        print("✅ Extract current job titles")
        print("✅ Identify current company employees")
        print("✅ Get accurate employment data")
        print("✅ Create verified employee report")
        print("=" * 60)
        
        while True:
            choice = input("\nLaunch LinkedIn verification now? (y/n): ").strip().lower()
            if choice in ['y', 'yes']:
                verification_script = self.script_dir / "script5_linkedin_verification.py"
                if verification_script.exists():
                    try:
                        print("🚀 Launching LinkedIn verification...")
                        if sys.platform == 'win32':
                            subprocess.Popen([sys.executable, str(verification_script)], 
                                           creationflags=subprocess.CREATE_NEW_CONSOLE)
                        else:
                            subprocess.Popen([sys.executable, str(verification_script)])
                        print("✅ Verification script launched!")
                        break
                    except Exception as e:
                        print(f"❌ Error launching verification: {e}")
                        break
                else:
                    print("❌ Verification script not found")
                    # Try alternative script names
                    alt_scripts = ["paste.py", "linkedin_verification.py"]
                    for alt_script in alt_scripts:
                        alt_path = self.script_dir / alt_script
                        if alt_path.exists():
                            try:
                                print(f"🚀 Found alternative verification script: {alt_script}")
                                if sys.platform == 'win32':
                                    subprocess.Popen([sys.executable, str(alt_path)], 
                                                   creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    subprocess.Popen([sys.executable, str(alt_path)])
                                print("✅ Alternative verification script launched!")
                                return
                            except Exception as e:
                                print(f"❌ Error launching {alt_script}: {e}")
                    break
            elif choice in ['n', 'no']:
                print("ℹ️ Verification skipped. You can run it later.")
                print("💡 Available verification scripts:")
                print("   - script5_linkedin_verification.py")
                print("   - paste.py (manual login version)")
                break
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    def cleanup(self):
        """Close browser and cleanup."""
        if self.driver:
            try:
                self.driver.quit()
                print("🌐 Browser closed")
            except:
                pass

def main():
    """Main execution with full interactive workflow."""
    try:
        print("=" * 60)
        print("🔍 LINKEDIN SEARCH - COMPLETE INTERACTIVE VERSION")
        print("=" * 60)
        print("This script finds LinkedIn profiles with full user interaction")
        print("and proper job title searching support.")
        
        # Install dependencies first
        print("\n🔧 Checking dependencies...")
        install_dependencies()
        
        try:
            from selenium import webdriver
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.common.exceptions import TimeoutException, NoSuchElementException
            from webdriver_manager.chrome import ChromeDriverManager
            import openpyxl
            from openpyxl.styles import Font, PatternFill, Alignment
            print("✅ All dependencies loaded successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            input("Press Enter to exit...")
            return
        
        # Load configuration
        config_path = Path(__file__).parent / "company_config.json"
        if not config_path.exists():
            print("❌ Configuration file not found!")
            print("Please run script1_input_collection.py first")
            input("Press Enter to exit...")
            return
        
        # Initialize searcher
        searcher = LinkedInSearcher(str(config_path))
        
        # Step 1: Display and confirm configuration
        if not searcher.display_configuration():
            return
        
        # Step 2: Display and confirm search strategy
        if not searcher.display_search_strategy():
            return
        
        # Step 3: Setup browser
        if not searcher.setup_browser():
            return
        
        try:
            # Step 4: Search for profiles with progress updates
            searcher.search_profiles()
            
            # Step 5: Display results and get confirmation
            if not searcher.display_results_summary():
                return
            
            # Step 6: Save results
            if searcher.save_results():
                print("✅ Results saved successfully!")
                
                # Step 7: Create Excel report
                if searcher.create_excel_report():
                    print("✅ Excel report created successfully!")
                    
                    # Step 8: Offer verification
                    searcher.offer_verification()
                    
                    print(f"\n🎉 SUCCESS! Found {len(searcher.found_candidates)} LinkedIn profiles")
                    print("📊 Excel report created with clickable LinkedIn URLs")
                    print("🔗 LinkedIn verification available")
                    print("\n💡 Next Steps:")
                    print("   1. Review the Excel file")
                    print("   2. Click LinkedIn URLs to verify profiles")
                    print("   3. Run LinkedIn verification for automated checking")
                else:
                    print("⚠️ Excel report creation failed")
            else:
                print("❌ Failed to save results")
                
        finally:
            searcher.cleanup()
    
    except KeyboardInterrupt:
        print("\n\n❌ Search cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()