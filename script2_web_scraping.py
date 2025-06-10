#!/usr/bin/env python3
"""
LinkedIn Search via Bing (X-ray Search) - FIXED VERSION with AUTOMATION

This script searches LinkedIn profiles using Bing X-ray search and creates Excel output.
Fixed to only search job titles when provided, and restored automation.
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
from typing import List, Dict, Optional, Set
from urllib.parse import quote_plus
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required packages if not available."""
    required_packages = ['selenium', 'webdriver-manager', 'openpyxl']
    
    for package in required_packages:
        try:
            if package == 'webdriver-manager':
                import webdriver_manager
            elif package == 'openpyxl':
                import openpyxl
            else:
                __import__(package)
        except ImportError:
            logger.info(f"Installing {package}...")
            subprocess.call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
    from webdriver_manager.chrome import ChromeDriverManager
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
except ImportError as e:
    logger.error(f"Failed to import required packages: {e}")
    sys.exit(1)

@dataclass
class LinkedInCandidate:
    """LinkedIn profile candidate."""
    first_name: str
    last_name: str
    title: str
    linkedin_url: str
    company_name: str
    location: str
    confidence: str
    source: str

class LinkedInBingSearcher:
    """LinkedIn profile searcher using Bing X-ray search with proper job title filtering."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.script_dir = Path(__file__).parent.absolute()
        self.driver = None
        self.processed_urls = set()
        
        # Check if this script should run
        search_types = self.config.get('search_types', [])
        if 'linkedin' not in search_types:
            print("❌ LinkedIn search not enabled in configuration")
            print(f"Current search types: {search_types}")
            sys.exit(1)
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
    
    def _setup_browser(self) -> Optional[webdriver.Chrome]:
        """Setup Chrome browser for Bing search."""
        try:
            logger.info("Setting up Chrome browser for LinkedIn X-ray search...")
            
            options = Options()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument('--window-size=1200,800')
            
            # Random user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]
            options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(5)
            
            # Anti-detection
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("✅ Browser setup successful")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Browser setup error: {e}")
            return None
    
    def _extract_name_from_title(self, title: str) -> tuple:
        """Extract first and last name from LinkedIn search result title."""
        # Clean the title
        clean_title = re.sub(r'\s*-\s*LinkedIn.*', '', title, flags=re.IGNORECASE)
        clean_title = re.sub(r'\s*\|\s*LinkedIn.*', '', clean_title, flags=re.IGNORECASE)
        clean_title = clean_title.strip()
        
        # Extract name (usually the first part)
        name_match = re.search(r'^([^-|–]+)', clean_title)
        if name_match:
            full_name = name_match.group(1).strip()
            name_parts = full_name.split()
            
            if len(name_parts) >= 2:
                first_name = name_parts[0]
                last_name = ' '.join(name_parts[1:])
                
                # Validate names
                if (self._is_valid_name(first_name) and 
                    self._is_valid_name(last_name)):
                    return first_name, last_name
        
        return None, None
    
    def _is_valid_name(self, name: str) -> bool:
        """Check if a name part is valid."""
        if not name or len(name) < 2 or len(name) > 25:
            return False
        
        if not re.match(r'^[a-zA-Z\-\']+$', name):
            return False
        
        # Filter out common false positives
        false_positives = {
            'linkedin', 'profile', 'company', 'limited', 'group',
            'management', 'services', 'solutions', 'consulting', 'holdings',
            'property', 'building', 'office', 'director', 'manager'
        }
        
        if name.lower() in false_positives:
            return False
        
        return True
    
    def _extract_title_from_result(self, title: str, description: str) -> str:
        """Extract job title from search result."""
        # Patterns to find job titles
        patterns = [
            r'[-–]\s*([^|]+?)(?:\s+at\s+|\s+@\s+|\s*\|)',
            r'\|\s*([^|]+?)(?:\s+at\s+|\s+@\s+)',
            r'(?:,\s*)([^,]+?)(?:\s+at\s+|\s+@\s+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                if 3 < len(job_title) < 100 and not any(x in job_title.lower() for x in ['linkedin', 'profile']):
                    return job_title
        
        # Look in description for job titles
        if description:
            job_patterns = [
                r'([^,\n.]*(?:Director|Manager|Officer|Executive|President|CEO|CFO|CTO|COO|VP|Vice President)[^,\n.]*)',
                r'([^,\n.]*(?:Analyst|Specialist|Consultant|Engineer|Developer|Lead)[^,\n.]*)',
            ]
            
            for pattern in job_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    job_title = match.group(1).strip()
                    if 3 < len(job_title) < 100:
                        return job_title
        
        return "Position to be determined"
    
    def _determine_confidence(self, title: str, description: str, company: str) -> str:
        """Determine confidence level for the candidate with job title matching."""
        score = 0
        
        # Company name appears in results
        if company.lower() in title.lower():
            score += 3
        if description and company.lower() in description.lower():
            score += 2
        
        # LinkedIn profile quality indicators
        if 'linkedin.com/in/' in title.lower():
            score += 2
        
        # Job title quality and matching
        if "to be determined" not in title.lower():
            score += 2
            
            # Check if title matches our specific job titles
            job_titles = self.config.get('job_titles', [])
            for search_title in job_titles:
                # Check for exact match or related terms
                if search_title.lower() in title.lower():
                    score += 4  # Big boost for exact match
                    logger.info(f"Found exact job title match: {search_title} in {title}")
                    break
                
                # For sales, check for sales-related terms
                if search_title.lower() == 'sales':
                    sales_terms = ['sales', 'account', 'business development', 'revenue', 'client']
                    if any(term in title.lower() for term in sales_terms):
                        score += 3  # Good boost for sales-related
                        logger.info(f"Found sales-related title: {title}")
                        break
        
        # Description quality
        if description and len(description) > 50:
            score += 1
        
        # Determine confidence level
        if score >= 8:
            return 'high'
        elif score >= 5:
            return 'medium'
        else:
            return 'low'
    
    def _create_linkedin_search_queries(self, company: str, location: str) -> List[str]:
        """Create LinkedIn X-ray search queries for Bing with FIXED job title targeting."""
        queries = []
        
        # Get job titles from config
        job_titles = self.config.get('job_titles', [])
        
        if job_titles:
            logger.info(f"Creating targeted searches for job titles: {job_titles}")
            
            # ONLY create specific searches for each job title - NO GENERAL SEARCHES
            for title in job_titles:
                # High-priority targeted searches for each job title
                title_queries = [
                    f'site:linkedin.com/in/ "{title}" "{company}" {location}',
                    f'site:linkedin.com/in/ "{title}" at "{company}" {location}',
                    f'site:linkedin.com/in/ "{company}" "{title}" {location}',
                    f'site:linkedin.com/in/ "{title}" "{company}" employee {location}',
                    f'site:linkedin.com/in/ "{title}" works at "{company}" {location}',
                ]
                queries.extend(title_queries)
                
                # Add variations for sales specifically
                if title.lower() == 'sales':
                    sales_variations = [
                        f'site:linkedin.com/in/ "Sales Manager" "{company}" {location}',
                        f'site:linkedin.com/in/ "Sales Director" "{company}" {location}',
                        f'site:linkedin.com/in/ "Sales Executive" "{company}" {location}',
                        f'site:linkedin.com/in/ "Sales Representative" "{company}" {location}',
                        f'site:linkedin.com/in/ "Account Manager" "{company}" {location}',
                        f'site:linkedin.com/in/ "Business Development" "{company}" {location}',
                        f'site:linkedin.com/in/ "Sales Specialist" "{company}" {location}',
                    ]
                    queries.extend(sales_variations)
            
            # REMOVED: No general company searches when job titles are provided
            
        else:
            logger.info("No job titles specified, using general company searches")
            # Fallback to general searches if no job titles
            queries = [
                f'site:linkedin.com/in/ "{company}" "{location}"',
                f'site:linkedin.com/in/ "{company}" {location}',
                f'site:linkedin.com/in/ works at "{company}" {location}',
                f'site:linkedin.com/in/ "{company}" employee {location}',
                f'site:linkedin.com/in/ "{company}" team {location}',
                f'site:linkedin.com/in/ "{company}" (Director OR Manager OR Executive) {location}',
                f'site:linkedin.com/in/ "{company}" (CEO OR President OR "Vice President") {location}',
                f'site:linkedin.com/in/ "{company}" (Chief OR Officer OR Head) {location}',
            ]
        
        logger.info(f"Created {len(queries)} search queries using {'job title only' if job_titles else 'company only'} strategy")
        return queries
    
    def _process_bing_search_results(self, company: str, location: str) -> List[LinkedInCandidate]:
        """Process Bing search results page for LinkedIn profiles."""
        candidates = []
        
        try:
            # Wait for search results
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.b_algo'))
            )
            
            results = self.driver.find_elements(By.CSS_SELECTOR, 'li.b_algo')
            logger.info(f"Found {len(results)} Bing search results")
            
            for result in results:
                try:
                    # Get title and URL
                    title_elem = result.find_element(By.CSS_SELECTOR, 'h2 a')
                    title = title_elem.text
                    url = title_elem.get_attribute('href')
                    
                    if not url or 'linkedin.com/in/' not in url.lower():
                        continue
                    
                    if url in self.processed_urls:
                        continue
                    
                    # Get description
                    description = ""
                    try:
                        desc_elem = result.find_element(By.CSS_SELECTOR, '.b_caption p')
                        description = desc_elem.text
                    except NoSuchElementException:
                        pass
                    
                    # Extract name
                    first_name, last_name = self._extract_name_from_title(title)
                    if not first_name or not last_name:
                        continue
                    
                    # Extract job title
                    job_title = self._extract_title_from_result(title, description)
                    
                    # Determine confidence
                    confidence = self._determine_confidence(title, description, company)
                    
                    # Create candidate
                    candidate = LinkedInCandidate(
                        first_name=first_name,
                        last_name=last_name,
                        title=job_title,
                        linkedin_url=url,
                        company_name=company,
                        location=location,
                        confidence=confidence,
                        source='LinkedIn X-ray Search (Bing)'
                    )
                    
                    candidates.append(candidate)
                    self.processed_urls.add(url)
                    
                    logger.info(f"Found: {first_name} {last_name} - {job_title} ({confidence})")
                    
                except Exception as e:
                    logger.debug(f"Error processing result: {e}")
                    continue
            
        except TimeoutException:
            logger.warning("Timeout waiting for Bing search results")
        except Exception as e:
            logger.error(f"Error processing Bing search results: {e}")
        
        return candidates
    
    def search_linkedin_profiles(self) -> List[Dict]:
        """Main method to search LinkedIn profiles via Bing X-ray."""
        company = self.config['company_name']
        location = self.config['location']
        max_pages = min(self.config.get('pages_to_scrape', 5), 10)
        
        all_candidates = []
        
        logger.info(f"Starting LinkedIn X-ray search for {company} in {location}")
        
        # Setup browser
        self.driver = self._setup_browser()
        if not self.driver:
            logger.error("Failed to setup browser")
            return []
        
        try:
            queries = self._create_linkedin_search_queries(company, location)
            logger.info(f"Created {len(queries)} LinkedIn X-ray search queries")
            
            for i, query in enumerate(queries, 1):
                if len(all_candidates) >= 100:  # Reasonable limit
                    logger.info("Reached collection limit")
                    break
                
                logger.info(f"Processing query {i}/{len(queries)}: {query[:60]}...")
                
                try:
                    # Navigate to Bing search
                    search_url = f"https://www.bing.com/search?q={quote_plus(query)}"
                    self.driver.get(search_url)
                    time.sleep(random.uniform(2, 4))
                    
                    # Check for blocking
                    page_source = self.driver.page_source.lower()
                    if any(block in page_source for block in ['captcha', 'unusual traffic', 'access denied']):
                        logger.warning("Detected search blocking, skipping query")
                        continue
                    
                    # Process results
                    page_candidates = self._process_bing_search_results(company, location)
                    all_candidates.extend(page_candidates)
                    
                    # Small delay between queries
                    time.sleep(random.uniform(3, 6))
                    
                except Exception as e:
                    logger.error(f"Error with query {i}: {e}")
                    continue
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed")
                except:
                    pass
        
        logger.info(f"LinkedIn X-ray search completed. Found {len(all_candidates)} candidates")
        return [candidate.__dict__ for candidate in all_candidates]
    
    def save_results(self, candidates: List[Dict]) -> bool:
        """Save LinkedIn candidates to files."""
        try:
            # Save to LinkedIn-specific file
            linkedin_file = self.script_dir / "linkedin_candidates.json"
            with open(linkedin_file, 'w', encoding='utf-8') as f:
                json.dump(candidates, f, indent=4, ensure_ascii=False)
            
            # Convert to standard employee format
            employees = []
            for candidate in candidates:
                employee = {
                    'first_name': candidate['first_name'],
                    'last_name': candidate['last_name'],
                    'title': candidate['title'],
                    'link': candidate['linkedin_url'],
                    'company_name': candidate['company_name'],
                    'location': candidate['location'],
                    'source': candidate['source'],
                    'confidence': candidate['confidence'],
                    'needs_verification': True
                }
                employees.append(employee)
            
            # Save to merged file
            merged_file = self.script_dir / "merged_employees.json"
            with open(merged_file, 'w', encoding='utf-8') as f:
                json.dump(employees, f, indent=4, ensure_ascii=False)
            
            logger.info(f"LinkedIn candidates saved: {len(employees)} profiles")
            return True
            
        except Exception as e:
            logger.error(f"Error saving LinkedIn candidates: {e}")
            return False
    
    def create_excel_report(self, candidates: List[Dict]) -> bool:
        """Create Excel report with LinkedIn profiles."""
        try:
            if not candidates:
                logger.warning("No candidates for Excel report")
                return False
            
            logger.info("Creating Excel report...")
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "LinkedIn X-ray Search"
            
            # Title
            ws.merge_cells('A1:H1')
            title_cell = ws['A1']
            title_cell.value = f"{self.config.get('company_name', 'Company')} - LinkedIn X-ray Search Results"
            title_cell.font = Font(bold=True, size=14)
            title_cell.alignment = Alignment(horizontal='center')
            
            # Headers
            headers = [
                "First Name", "Last Name", "Job Title", "LinkedIn URL", 
                "Company", "Location", "Confidence", "Source"
            ]
            
            header_row = 3
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=header_row, column=col, value=header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")
            
            # Data rows
            current_row = header_row + 1
            for candidate in candidates:
                ws.cell(row=current_row, column=1, value=candidate['first_name'])
                ws.cell(row=current_row, column=2, value=candidate['last_name'])
                ws.cell(row=current_row, column=3, value=candidate['title'])
                
                # LinkedIn URL with hyperlink
                url_cell = ws.cell(row=current_row, column=4, value=candidate['linkedin_url'])
                url_cell.hyperlink = candidate['linkedin_url']
                url_cell.font = Font(color="0000FF", underline="single")
                
                ws.cell(row=current_row, column=5, value=candidate['company_name'])
                ws.cell(row=current_row, column=6, value=candidate['location'])
                
                # Confidence with colors
                conf_cell = ws.cell(row=current_row, column=7, value=candidate['confidence'].title())
                if candidate['confidence'] == 'high':
                    conf_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif candidate['confidence'] == 'medium':
                    conf_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                else:
                    conf_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                
                ws.cell(row=current_row, column=8, value=candidate['source'])
                current_row += 1
            
            # Auto-adjust columns
            for col in ws.columns:
                max_length = 0
                column_letter = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                ws.column_dimensions[column_letter].width = min(max_length + 2, 50)
            
            # Save file
            company_clean = self.config.get('company_name', 'Company').replace(' ', '_').replace('/', '_')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{company_clean}_LinkedIn_Xray_{timestamp}.xlsx"
            filepath = self.script_dir / filename
            
            wb.save(filepath)
            logger.info(f"Excel report saved: {filename}")
            
            # Try to open
            try:
                if sys.platform == 'win32':
                    os.startfile(str(filepath))
                elif sys.platform == 'darwin':
                    subprocess.call(['open', str(filepath)])
                else:
                    subprocess.call(['xdg-open', str(filepath)])
                logger.info("Excel file opened automatically")
            except:
                logger.info("Please open Excel file manually")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
            return False

def main():
    """Main execution function."""
    try:
        script_dir = Path(__file__).parent.absolute()
        config_path = script_dir / "company_config.json"
        
        if not config_path.exists():
            logger.error("Configuration file not found. Please run script1_input_collection.py first.")
            sys.exit(1)
        
        print("=" * 70)
        print("LINKEDIN X-RAY SEARCH VIA BING - FIXED VERSION")
        print("=" * 70)
        print("This script searches LinkedIn profiles using Bing X-ray search.")
        
        searcher = LinkedInBingSearcher(str(config_path))
        
        print(f"\nTarget Company: {searcher.config['company_name']}")
        print(f"Location: {searcher.config['location']}")
        print(f"Search Type: LinkedIn X-ray via Bing")
        
        job_titles = searcher.config.get('job_titles', [])
        if job_titles:
            print(f"Job titles to search: {len(job_titles)}")
            print(f"FIXED: Will ONLY search for these specific titles (no general searches)")
            if len(job_titles) <= 5:
                print(f"Titles: {', '.join(job_titles)}")
            else:
                print(f"Sample titles: {', '.join(job_titles[:3])}... (+{len(job_titles)-3} more)")
        else:
            print("No specific job titles - searching all positions")
        
        # Search for profiles
        print(f"\n🔍 Starting LinkedIn X-ray search...")
        candidates = searcher.search_linkedin_profiles()
        
        if candidates:
            print(f"\n✅ LinkedIn X-ray search completed!")
            print(f"Found {len(candidates)} LinkedIn profiles")
            
            # Show summary
            confidence_counts = {}
            sales_profiles = []
            for candidate in candidates:
                conf = candidate['confidence']
                confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
                
                # Highlight sales profiles
                if 'sales' in candidate.get('title', '').lower():
                    sales_profiles.append(f"{candidate['first_name']} {candidate['last_name']} - {candidate['title']}")
            
            print(f"\nConfidence breakdown:")
            for conf, count in sorted(confidence_counts.items()):
                print(f"  - {conf.title()}: {count}")
            
            if sales_profiles:
                print(f"\n🎯 Found {len(sales_profiles)} sales-related profiles:")
                for profile in sales_profiles:
                    print(f"  ✅ {profile}")
            
            # Save results
            if searcher.save_results(candidates):
                print(f"✅ LinkedIn profiles saved to JSON files")
                
                # AUTO Excel creation - INTEGRATED like before
                print(f"\n📊 Creating Excel report automatically...")
                if searcher.create_excel_report(candidates):
                    print(f"✅ Excel report created successfully!")
                    print(f"📁 LinkedIn profiles ready for verification")
                    
                    # AUTO script5 launch - INTEGRATED like before
                    launch_script5 = input(f"\n🚀 Launch LinkedIn verification now? (y/n, default: y): ").strip().lower()
                    if launch_script5 != 'n':
                        try:
                            script5_path = script_dir / "script5_linkedin_verification.py"
                            if script5_path.exists():
                                print(f"🚀 Launching LinkedIn verification...")
                                if sys.platform == 'win32':
                                    subprocess.Popen([sys.executable, str(script5_path)], creationflags=subprocess.CREATE_NEW_CONSOLE)
                                else:
                                    subprocess.Popen([sys.executable, str(script5_path)])
                                print(f"✅ LinkedIn verification launched!")
                            else:
                                print(f"⚠️ script5_linkedin_verification.py not found")
                        except Exception as e:
                            print(f"⚠️ Could not launch script5: {e}")
                    else:
                        print(f"💡 Run script5_linkedin_verification.py manually when ready")
                else:
                    print(f"⚠️ Excel report creation failed")
            else:
                print(f"❌ Failed to save LinkedIn profiles")
        else:
            print(f"\n❌ No LinkedIn profiles found.")
            print(f"This could be due to:")
            print(f"  - Limited search results for the company/location")
            print(f"  - Network connectivity issues")
            print(f"  - Search engine blocking")
            print(f"  - Company name or location needs adjustment")
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ An error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()