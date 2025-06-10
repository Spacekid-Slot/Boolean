#!/usr/bin/env python3
"""
Employee Discovery Toolkit: LinkedIn Search (via Recruitment Geek) - IMPROVED DATA EXTRACTION

This script uses the proven data extraction methods from the Bing search script
to dramatically improve the quality of data captured from Recruitment Geek.
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
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
            print(f"Installing {package}...")
            subprocess.call([sys.executable, "-m", "pip", "install", package])

install_dependencies()

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, 
        WebDriverException, SessionNotCreatedException,
        ElementNotInteractableException, StaleElementReferenceException
    )
    from webdriver_manager.chrome import ChromeDriverManager
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
except ImportError as e:
    print(f"Failed to import required packages: {e}")
    sys.exit(1)

@dataclass
class LinkedInCandidate:
    """LinkedIn profile candidate with improved data structure."""
    first_name: str
    last_name: str
    search_title: str  # Job title from search results
    linkedin_url: str
    search_source: str
    company_name: str
    location: str
    confidence: str
    search_query: str
    search_type: str

class ImprovedRecruitmentGeekScraper:
    """Recruitment Geek scraper with improved data extraction from Bing script."""
    
    def __init__(self, config_path: str):
        """Initialize the scraper."""
        self.config = self._load_config(config_path)
        self.script_dir = Path(__file__).parent.absolute()
        self.driver = None
        self.processed_urls: Set[str] = set()
        self.job_titles = self._get_job_titles_to_search()
        
        # User agents from Bing script
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0'
        ]
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Configuration error: {e}")
            sys.exit(1)
    
    def _get_job_titles_to_search(self) -> List[str]:
        """Get job titles from config."""
        if 'job_titles' in self.config and self.config['job_titles']:
            return self.config['job_titles']
        return []
    
    def _setup_browser(self) -> Optional[webdriver.Chrome]:
        """Setup browser with improved configuration."""
        try:
            print("Setting up browser for improved Recruitment Geek search...")
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f'user-agent={random.choice(self.user_agents)}')
            chrome_options.add_argument('--window-size=1200,800')
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("✅ Browser setup successful")
            return driver
            
        except Exception as e:
            print(f"❌ Browser setup error: {e}")
            return None
    
    def _create_search_queries(self, company: str, location: str) -> List[Dict]:
        """Create search queries using Bing script methodology."""
        queries = []
        
        if self.job_titles:
            logger.info(f"Job titles provided. Creating company + title search queries...")
            
            for title in self.job_titles:
                # Use the proven Bing search patterns
                title_queries = [
                    {
                        'query': f'site:linkedin.com/in/ "{company}" "{title}" {location}',
                        'type': 'company_title',
                        'description': f'Company + Title: {title}'
                    },
                    {
                        'query': f'site:linkedin.com/in/ "{title}" at "{company}" {location}',
                        'type': 'company_title', 
                        'description': f'Title at Company: {title}'
                    },
                    {
                        'query': f'site:linkedin.com/in/ "{title}" "{company}" {location}',
                        'type': 'company_title',
                        'description': f'Title + Company: {title}'
                    }
                ]
                queries.extend(title_queries)
            
            # Add general company + role searches
            general_queries = [
                {
                    'query': f'site:linkedin.com/in/ "{company}" (Director OR Manager OR Executive) {location}',
                    'type': 'company_title',
                    'description': 'Company + General Leadership'
                },
                {
                    'query': f'site:linkedin.com/in/ "{company}" (CEO OR President OR "Vice President") {location}',
                    'type': 'company_title', 
                    'description': 'Company + Senior Executive'
                }
            ]
            queries.extend(general_queries)
            
        else:
            logger.info(f"No job titles provided. Creating company-only search queries...")
            
            company_queries = [
                {
                    'query': f'site:linkedin.com/in/ "{company}" "{location}"',
                    'type': 'company_only',
                    'description': 'Company + Location'
                },
                {
                    'query': f'site:linkedin.com/in/ "{company}" {location}',
                    'type': 'company_only',
                    'description': 'Company in Location'
                },
                {
                    'query': f'site:linkedin.com/in/ works at "{company}" {location}',
                    'type': 'company_only',
                    'description': 'Works at Company'
                },
                {
                    'query': f'site:linkedin.com/in/ "{company}" employee {location}',
                    'type': 'company_only',
                    'description': 'Company Employee'
                }
            ]
            queries.extend(company_queries)
        
        logger.info(f"Created {len(queries)} search queries using {'company + title' if self.job_titles else 'company only'} strategy")
        return queries
    
    def _extract_linkedin_profile_candidates_from_bing(self, query_info: Dict) -> List[LinkedInCandidate]:
        """Extract LinkedIn candidates using the proven Bing script method."""
        candidates = []
        
        try:
            # Wait for Bing results using the same method as Bing script
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.b_algo'))
            )
            
            result_elements = self.driver.find_elements(By.CSS_SELECTOR, 'li.b_algo')
            logger.info(f"Found {len(result_elements)} Bing search results")
            
            for result in result_elements:
                try:
                    # Extract title and link using Bing script method
                    title_element = result.find_element(By.CSS_SELECTOR, 'h2 a')
                    title = title_element.text
                    link = title_element.get_attribute('href')
                    
                    if not link or link in self.processed_urls:
                        continue
                    
                    # Only process LinkedIn profile URLs
                    if 'linkedin.com/in/' not in link.lower():
                        continue
                    
                    # Extract description using Bing script method
                    description = ""
                    try:
                        desc_element = result.find_element(By.CSS_SELECTOR, '.b_caption p')
                        description = desc_element.text
                    except NoSuchElementException:
                        pass
                    
                    # Parse candidate using improved method
                    candidate = self._parse_linkedin_candidate_improved(
                        title, description, link, query_info
                    )
                    
                    if candidate:
                        candidates.append(candidate)
                        self.processed_urls.add(link)
                        logger.info(f"Found LinkedIn candidate: {candidate.first_name} {candidate.last_name}")
                    
                except Exception as e:
                    logger.debug(f"Error processing search result: {e}")
                    continue
            
        except TimeoutException:
            logger.warning("Timeout waiting for Bing search results")
        except Exception as e:
            logger.error(f"Error extracting LinkedIn candidates from Bing: {e}")
        
        return candidates
    
    def _parse_linkedin_candidate_improved(self, title: str, description: str, link: str, query_info: Dict) -> Optional[LinkedInCandidate]:
        """Parse LinkedIn candidate using improved method from Bing script."""
        try:
            # Extract name from title using Bing script method
            name_match = re.search(r'^([^-|–]+)', title)
            if not name_match:
                return None
            
            full_name = name_match.group(1).strip()
            
            # Clean up name using Bing script method
            full_name = re.sub(r'\s*-\s*LinkedIn.*', '', full_name, flags=re.IGNORECASE)
            full_name = full_name.strip()
            
            # Split name
            name_parts = full_name.split()
            if len(name_parts) < 2:
                return None
            
            first_name = name_parts[0]
            last_name = ' '.join(name_parts[1:])
            
            # Validate name parts using Bing script method
            if not self._is_valid_name_part(first_name) or not self._is_valid_name_part(last_name):
                return None
            
            # Extract job title using Bing script method
            search_title = self._extract_job_title_from_result(title, description)
            
            # Determine confidence using Bing script method
            confidence = self._determine_search_confidence_improved(title, description, search_title, query_info)
            
            return LinkedInCandidate(
                first_name=first_name,
                last_name=last_name,
                search_title=search_title,
                linkedin_url=link,
                search_source='Recruitment Geek via Bing',
                company_name=self.config['company_name'],
                location=self.config['location'],
                confidence=confidence,
                search_query=query_info['query'],
                search_type='recruitment_geek_bing'
            )
            
        except Exception as e:
            logger.debug(f"Error parsing LinkedIn candidate: {e}")
            return None
    
    def _is_valid_name_part(self, name_part: str) -> bool:
        """Validate name part using Bing script method."""
        if not name_part or len(name_part) < 2 or len(name_part) > 25:
            return False
        
        if not re.match(r"^[a-zA-Z\-']+$", name_part):
            return False
        
        # Filter out common false positives from Bing script
        false_positives = {
            'property', 'building', 'office', 'company', 'limited', 'group',
            'management', 'services', 'solutions', 'consulting', 'holdings'
        }
        
        if name_part.lower() in false_positives:
            return False
        
        return True
    
    def _extract_job_title_from_result(self, title: str, description: str) -> str:
        """Extract job title using Bing script method."""
        # Look for title patterns in the title line
        title_patterns = [
            r'[-–]\s*([^|]+?)(?:\s+at\s+|\s+@\s+|\s+\|)',
            r'\|\s*([^|]+?)(?:\s+at\s+|\s+@\s+)',
            r'(?:,\s*)([^,]+?)(?:\s+at\s+|\s+@\s+)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                job_title = match.group(1).strip()
                if 3 < len(job_title) < 100:
                    return job_title
        
        # Look in description
        if description:
            desc_patterns = [
                r'(?:works as|employed as|position as|role as)\s+([^.,\n]+)',
                r'([^,\n.]*(?:Director|Manager|Officer|Executive|President|CEO|CFO|CTO|COO)[^,\n.]*)',
            ]
            
            for pattern in desc_patterns:
                match = re.search(pattern, description, re.IGNORECASE)
                if match:
                    job_title = match.group(1).strip()
                    if 3 < len(job_title) < 100:
                        return job_title
        
        return "To be verified"
    
    def _determine_search_confidence_improved(self, title: str, description: str, job_title: str, query_info: Dict) -> str:
        """Determine confidence using improved method from Bing script."""
        score = 0
        company = self.config['company_name']
        
        # Base score for search type
        if query_info['type'] == 'company_title':
            score += 3  # Higher base score for targeted company+title searches
        else:  # company_only
            score += 2  # Lower base score for broader company-only searches
        
        # Company name presence in results
        if company.lower() in title.lower():
            score += 3
        if description and company.lower() in description.lower():
            score += 2
        
        # LinkedIn profile URL quality
        if 'linkedin.com/in/' in title.lower():
            score += 2
        
        # Job title quality
        if job_title and job_title != "To be verified":
            score += 2
            
            # For company+title searches, boost if title matches search criteria
            if query_info['type'] == 'company_title' and self.job_titles:
                for search_title in self.job_titles:
                    if search_title.lower() in job_title.lower() or job_title.lower() in search_title.lower():
                        score += 3  # Big boost for title match in targeted search
                        break
            
            # Boost for executive/management titles
            if any(keyword in job_title.lower() for keyword in 
                   ['director', 'manager', 'executive', 'president', 'ceo', 'cfo', 'cto']):
                score += 1
        
        # Query specificity bonus
        if 'site:linkedin.com' in query_info['query']:
            score += 1
        
        # Determine confidence level (adjusted thresholds for search type)
        if query_info['type'] == 'company_title':
            # Higher thresholds for targeted searches
            if score >= 8:
                return 'high'
            elif score >= 5:
                return 'medium'
            else:
                return 'low'
        else:  # company_only
            # Lower thresholds for broader searches
            if score >= 6:
                return 'high'
            elif score >= 4:
                return 'medium'
            else:
                return 'low'
    
    def _navigate_to_next_page(self) -> bool:
        """Navigate to the next page of search results."""
        try:
            next_button = self.driver.find_element(By.CSS_SELECTOR, '.sb_pagN')
            if next_button:
                self.driver.execute_script("arguments[0].scrollIntoView();", next_button)
                time.sleep(1)
                self.driver.execute_script("arguments[0].click();", next_button)
                time.sleep(random.uniform(3, 5))
                return True
        except NoSuchElementException:
            logger.info("No next page button found")
        except Exception as e:
            logger.warning(f"Error navigating to next page: {e}")
        
        return False
    
    def search_linkedin_profiles(self) -> List[Dict]:
        """Main search method with improved data extraction."""
        company_name = self.config['company_name']
        location = self.config['location']
        max_pages = min(self.config.get('pages_to_scrape', 5), 20)  # Reasonable limit
        all_candidates = []
        
        print(f"Starting improved Recruitment Geek search for {company_name} in {location}")
        
        if self.job_titles:
            logger.info(f"Using company + title search strategy with {len(self.job_titles)} job titles")
        else:
            logger.info("Using company-only search strategy (no job titles provided)")
        
        try:
            self.driver = self._setup_browser()
            if not self.driver:
                return []
            
            # Create search queries using proven Bing method
            query_list = self._create_search_queries(company_name, location)
            
            for query_idx, query_info in enumerate(query_list, 1):
                if len(all_candidates) >= 100:  # Reasonable collection limit
                    logger.info("Reached candidate collection limit")
                    break
                
                logger.info(f"Processing query {query_idx}/{len(query_list)}: {query_info['description']}")
                
                try:
                    # Navigate to Bing search with the query
                    search_url = f"https://www.bing.com/search?q={quote_plus(query_info['query'])}"
                    self.driver.get(search_url)
                    time.sleep(random.uniform(2, 4))
                    
                    # Process pages (fewer for broader company-only searches)
                    pages_for_query = min(max_pages, 3) if query_info['type'] == 'company_title' else 2
                    
                    for page_num in range(pages_for_query):
                        logger.info(f"Processing page {page_num + 1}")
                        
                        # Check for search blocking
                        page_source = self.driver.page_source.lower()
                        if any(block_indicator in page_source for block_indicator in [
                            'captcha', 'unusual traffic', 'access denied'
                        ]):
                            logger.warning("Detected search blocking, skipping query")
                            break
                        
                        # Extract LinkedIn candidates using proven Bing method
                        page_candidates = self._extract_linkedin_profile_candidates_from_bing(query_info)
                        all_candidates.extend(page_candidates)
                        
                        # Navigate to next page if needed
                        if page_num < pages_for_query - 1:
                            if not self._navigate_to_next_page():
                                break
                        
                        if len(all_candidates) >= 100:
                            break
                    
                    # Delay between queries
                    time.sleep(random.uniform(5, 8))
                    
                except Exception as e:
                    logger.error(f"Error processing query: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ Search process error: {e}")
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    print("✅ Browser closed")
                except:
                    pass
        
        logger.info(f"Improved LinkedIn profile collection completed. Found {len(all_candidates)} candidates")
        return [candidate.__dict__ for candidate in all_candidates]
    
    def save_linkedin_candidates(self, candidates: List[Dict]) -> bool:
        """Save LinkedIn candidates using the same format as Bing script."""
        try:
            # Convert to standard employee format for compatibility (same as Bing script)
            employees = []
            for candidate in candidates:
                employee = {
                    'first_name': candidate.get('first_name', ''),
                    'last_name': candidate.get('last_name', ''),
                    'title': candidate.get('search_title', ''),
                    'link': candidate.get('linkedin_url', ''),
                    'company_name': candidate.get('company_name', ''),
                    'location': candidate.get('location', ''),
                    'source': f'Recruitment Geek ({candidate.get("search_type", "unknown")})',
                    'confidence': candidate.get('confidence', 'low'),
                    'search_query': candidate.get('search_query', ''),
                    'search_type': candidate.get('search_type', ''),
                    'needs_verification': True
                }
                employees.append(employee)
            
            # Save to LinkedIn-specific file
            linkedin_file = self.script_dir / "linkedin_candidates.json"
            with open(linkedin_file, 'w', encoding='utf-8') as f:
                json.dump(employees, f, indent=4, ensure_ascii=False)
            
            # Also save to standard merged file for compatibility
            merged_file = self.script_dir / "merged_employees.json"
            if merged_file.exists():
                # Load existing and merge
                with open(merged_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                
                # Add new candidates, avoiding duplicates by LinkedIn URL
                existing_urls = {emp.get('link', '') for emp in existing}
                new_count = 0
                for emp in employees:
                    if emp.get('link') and emp['link'] not in existing_urls:
                        existing.append(emp)
                        new_count += 1
                
                with open(merged_file, 'w', encoding='utf-8') as f:
                    json.dump(existing, f, indent=4, ensure_ascii=False)
                
                logger.info(f"Added {new_count} new LinkedIn candidates to merged file")
            else:
                # Create new merged file
                with open(merged_file, 'w', encoding='utf-8') as f:
                    json.dump(employees, f, indent=4, ensure_ascii=False)
            
            logger.info(f"LinkedIn candidates saved: {len(employees)} profiles ready for verification")
            return True
            
        except Exception as e:
            logger.error(f"Error saving LinkedIn candidates: {e}")
            return False
    
    def create_excel_report(self, candidates: List[Dict]) -> bool:
        """Create Excel report with improved data."""
        try:
            if not candidates:
                print("⚠️ No candidates for Excel report")
                return False
            
            print("📊 Creating improved Excel report...")
            
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Improved Recruitment Geek Results"
            
            # Headers (same as Bing script structure)
            headers = ["First Name", "Last Name", "Job Title", "LinkedIn URL", "Company", "Location", "Confidence", "Source"]
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = Font(bold=True, color="FFFFFF")
                cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
                cell.alignment = Alignment(horizontal="center")
            
            # Data rows
            for row, candidate in enumerate(candidates, 2):
                ws.cell(row=row, column=1, value=candidate.get('first_name', ''))
                ws.cell(row=row, column=2, value=candidate.get('last_name', ''))
                ws.cell(row=row, column=3, value=candidate.get('search_title', ''))
                
                # LinkedIn URL with hyperlink
                url = candidate.get('linkedin_url', '')
                url_cell = ws.cell(row=row, column=4, value=url)
                if url:
                    url_cell.hyperlink = url
                    url_cell.font = Font(color="0000FF", underline="single")
                
                ws.cell(row=row, column=5, value=candidate.get('company_name', ''))
                ws.cell(row=row, column=6, value=candidate.get('location', ''))
                
                # Confidence with colors
                conf_cell = ws.cell(row=row, column=7, value=candidate.get('confidence', '').upper())
                if conf_cell.value == 'HIGH':
                    conf_cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif conf_cell.value == 'MEDIUM':
                    conf_cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                else:
                    conf_cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                
                ws.cell(row=row, column=8, value=candidate.get('search_source', ''))
            
            # Auto-adjust columns
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
            company_clean = self.config.get('company_name', 'Company').replace(' ', '_')
            location_clean = self.config.get('location', 'Location').replace(' ', '_')
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{company_clean}_{location_clean}_RecruitmentGeek_Improved_{timestamp}.xlsx"
            filepath = self.script_dir / filename
            
            wb.save(filepath)
            
            if filepath.exists():
                print(f"✅ Improved Excel report created: {filename}")
                
                try:
                    if sys.platform == 'win32':
                        os.startfile(str(filepath))
                    elif sys.platform == 'darwin':
                        subprocess.call(['open', str(filepath)])
                    else:
                        subprocess.call(['xdg-open', str(filepath)])
                    print("📂 File opened automatically")
                except:
                    print(f"📂 Please open manually: {filepath}")
                
                return True
            else:
                print("❌ Excel file creation failed")
                return False
                
        except Exception as e:
            print(f"❌ Excel creation error: {e}")
            return False
    
    def launch_verification_script(self) -> bool:
        """Launch LinkedIn verification script (same as Bing script)."""
        verification_script = self.script_dir / "script5_linkedin_verification.py"
        
        if verification_script.exists():
            try:
                logger.info("Launching LinkedIn verification script...")
                if sys.platform == 'win32':
                    subprocess.Popen(
                        [sys.executable, str(verification_script)],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    subprocess.Popen([sys.executable, str(verification_script)])
                return True
            except Exception as e:
                logger.error(f"Error launching verification script: {e}")
                return False
        else:
            logger.warning("LinkedIn verification script not found")
            return False

def main():
    """Main execution with improved data extraction."""
    try:
        script_dir = Path(__file__).parent.absolute()
        config_path = script_dir / "company_config.json"
        
        if not config_path.exists():
            print("❌ Configuration file not found.")
            print("Please run script1_input_collection.py first.")
            sys.exit(1)
        
        print("=" * 70)
        print("RECRUITMENT GEEK LINKEDIN SEARCH - IMPROVED DATA EXTRACTION")
        print("=" * 70)
        print("This version uses the proven data extraction methods from the Bing script")
        print("to dramatically improve the quality of LinkedIn profile data captured.")
        
        scraper = ImprovedRecruitmentGeekScraper(str(config_path))
        
        print(f"\n📊 Configuration:")
        print(f"Company: {scraper.config['company_name']}")
        print(f"Location: {scraper.config['location']}")
        print(f"Job titles: {len(scraper.job_titles)}")
        
        if scraper.job_titles:
            print(f"Search strategy: Company + Title combinations")
            if len(scraper.job_titles) <= 10:
                print(f"Titles: {', '.join(scraper.job_titles)}")
            else:
                print(f"Sample titles: {', '.join(scraper.job_titles[:5])}... (+{len(scraper.job_titles)-5} more)")
        else:
            print("Search strategy: Company-only searches")
        
        print(f"\n💡 Improvement Strategy:")
        print(f"   • Uses proven Bing search methodology")
        print(f"   • Same data extraction patterns as working Bing script")
        print(f"   • Improved name parsing and validation")
        print(f"   • Better job title extraction")
        print(f"   • Enhanced confidence scoring")
        
        proceed = input(f"\n🚀 Start improved search? (y/n, default: y): ").strip().lower()
        if proceed == 'n':
            print("Cancelled.")
            return
        
        # Perform improved search
        candidates = scraper.search_linkedin_profiles()
        
        if candidates:
            print(f"\n✅ Improved search completed! Found {len(candidates)} profiles")
            
            # Save results
            if scraper.save_linkedin_candidates(candidates):
                # Show summary by search type and confidence (same as Bing script)
                search_type_counts = {}
                confidence_counts = {}
                for candidate in candidates:
                    search_type = candidate.get('search_type', 'unknown')
                    search_type_counts[search_type] = search_type_counts.get(search_type, 0) + 1
                    
                    conf = candidate.get('confidence', 'unknown')
                    confidence_counts[conf] = confidence_counts.get(conf, 0) + 1
                
                print(f"\nSearch type breakdown:")
                for search_type, count in sorted(search_type_counts.items()):
                    print(f"  - {search_type.replace('_', ' ').title()}: {count}")
                
                print(f"\nConfidence breakdown:")
                for conf, count in sorted(confidence_counts.items()):
                    print(f"  - {conf.title()}: {count}")
                
                print(f"\n🔗 LinkedIn profiles ready for verification:")
                print(f"   • These profiles will be visited to extract current employment")
                print(f"   • Verification will identify who currently works at {scraper.config['company_name']}")
                print(f"   • Results will show current job titles, companies, and locations")
                
                # Show sample results with improved data
                print(f"\n👥 Sample profiles found (with improved data extraction):")
                for i, candidate in enumerate(candidates[:5], 1):
                    name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}"
                    title = candidate.get('search_title', 'Unknown')
                    conf = candidate.get('confidence', 'unknown')
                    print(f"   {i}. {name} - {title} (confidence: {conf})")
                
                if len(candidates) > 5:
                    print(f"   ... and {len(candidates) - 5} more")
                
                # Create Excel report
                print(f"\n📋 Generating improved Excel report...")
                if scraper.create_excel_report(candidates):
                    print("✅ Improved Excel report created successfully")
                    print("   • Better data quality than previous version")
                    print("   • Proven extraction methods from Bing script")
                    print("   • Ready for LinkedIn verification")
                    
                    # Launch verification
                    print(f"\n🚀 Ready to launch LinkedIn verification...")
                    launch_verification = input("Launch LinkedIn verification now? (y/n, default: y): ").strip().lower()
                    
                    if launch_verification != 'n':
                        if scraper.launch_verification_script():
                            print("✅ LinkedIn verification script launched!")
                            print("📋 The verification process will:")
                            print("   • Visit each LinkedIn profile to extract current job info")
                            print("   • Identify who currently works at your target company") 
                            print("   • Create a final Excel report with verified employees")
                            print("   • Use the improved data as a starting point")
                        else:
                            print("⚠️  Could not launch verification script automatically.")
                            print("Please run script5_linkedin_verification.py manually.")
                    else:
                        print("LinkedIn verification skipped.")
                        print("Run script5_linkedin_verification.py when ready to verify profiles.")
                else:
                    print("⚠️ Excel report creation failed")
            else:
                print("Failed to save LinkedIn candidates")
                sys.exit(1)
        else:
            print("❌ No LinkedIn profiles found.")
            print("This could be due to:")
            print("- Limited search results for the company/location combination")
            print("- Network connectivity issues")
            print("- Search engine blocking")
            if scraper.job_titles:
                print("- Job titles might be too specific - try broader titles")
            else:
                print("- Consider adding specific job titles for more targeted results")
    
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()