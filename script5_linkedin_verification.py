#!/usr/bin/env python3
"""
LinkedIn Profile Verification Script - Fixed for FNZ

Fixed version of your existing script that removes the broken linkedin_scraper dependency
and uses direct Selenium instead. Everything else stays the same.
"""

import time
import json
import os
import sys
import subprocess
import logging
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import getpass
from datetime import datetime
import re

# Setup logging  
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """Install required packages if not available."""
    required_packages = {
        'pandas': 'pandas',
        'selenium': 'selenium', 
        'webdriver-manager': 'webdriver_manager',
        'openpyxl': 'openpyxl',
        'requests': 'requests'
    }
    
    missing_packages = []
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        logger.info(f"Installing missing packages: {', '.join(missing_packages)}")
        for package in missing_packages:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to install {package}: {e}")
                return False
    
    return True

# Install dependencies before importing
if not install_dependencies():
    print("Failed to install required dependencies. Please install manually:")
    print("pip install pandas selenium webdriver-manager openpyxl requests")
    sys.exit(1)

# REMOVED: linkedin_scraper import (this was causing the error)
# ADDED: Direct selenium imports instead

try:
    import pandas as pd
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import WebDriverException, TimeoutException, NoSuchElementException
    from webdriver_manager.chrome import ChromeDriverManager
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    import requests
except ImportError as e:
    logger.error(f"Failed to import required packages: {e}")
    print("Please ensure all packages are installed:")
    print("pip install pandas selenium webdriver-manager openpyxl requests")
    sys.exit(1)

class LinkedInProfileVerifier:
    """LinkedIn profile verifier using direct Selenium implementation."""
    
    def __init__(self, config_path: str):
        """Initialize the LinkedIn profile verifier."""
        self.config = self._load_config(config_path)
        self.script_dir = Path(__file__).parent.absolute()
        self.driver = None
        
        # LinkedIn credentials
        self.email = None
        self.password = None
        self._load_credentials()
        
        # Load employee data
        self.employees = self._load_employee_data()
        
    def _load_config(self, config_path: str) -> dict:
        """Load configuration from JSON file."""
        try:
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Configuration file not found: {config_path}")
                return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return {}
    
    def _load_credentials(self):
        """Load LinkedIn credentials from various sources."""
        # Try environment variables first
        self.email = os.environ.get('LINKEDIN_EMAIL')
        self.password = os.environ.get('LINKEDIN_PASSWORD')
        
        # Try config file
        if not self.email or not self.password:
            self.email = self.config.get('linkedin_email')
            self.password = self.config.get('linkedin_password')
        
        # Prompt user if still missing
        if not self.email:
            self.email = input("Enter your LinkedIn email: ").strip()
        
        if not self.password:
            self.password = getpass.getpass("Enter your LinkedIn password: ")
    
    def _load_employee_data(self) -> List[Dict]:
        """Load employee data from LinkedIn profile files."""
        logger.info("Loading employee data for verification...")
        
        # Try to load from different sources
        potential_files = [
            "linkedin_candidates.json",
            "merged_employees.json", 
            "verified_employee_data.json",
            "script3a_verified_employees.json",
            "processed_employee_data.json"
        ]
        
        all_employees = []
        
        for filename in potential_files:
            file_path = self.script_dir / filename
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list) and data:
                        logger.info(f"Loaded {len(data)} employees from {filename}")
                        
                        # Filter for LinkedIn profiles only
                        linkedin_profiles = []
                        for emp in data:
                            # Check multiple possible fields for LinkedIn URL
                            linkedin_url = None
                            for field in ['link', 'linkedin_url', 'source_link', 'profile_url', 'url']:
                                url = emp.get(field, '')
                                if url and 'linkedin.com/in/' in str(url).lower():
                                    linkedin_url = url
                                    break
                            
                            if linkedin_url:
                                emp['linkedin_url'] = linkedin_url  # Normalize field name
                                linkedin_profiles.append(emp)
                        
                        if linkedin_profiles:
                            logger.info(f"Found {len(linkedin_profiles)} LinkedIn profiles in {filename}")
                            all_employees.extend(linkedin_profiles)
                            break  # Use the first file with LinkedIn profiles
                            
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON in {filename}: {e}")
                except Exception as e:
                    logger.warning(f"Error loading {filename}: {e}")
        
        if not all_employees:
            logger.warning("No LinkedIn profiles found in any data files")
            logger.info("Available files in directory:")
            for file in sorted(self.script_dir.glob("*.json")):
                logger.info(f"  - {file.name}")
        
        # Remove duplicates based on LinkedIn URL
        unique_employees = {}
        for emp in all_employees:
            url = emp.get('linkedin_url', '')
            if url and url not in unique_employees:
                unique_employees[url] = emp
        
        return list(unique_employees.values())
    
    def setup_driver(self) -> Optional[webdriver.Chrome]:
        """Setup Chrome driver for LinkedIn verification."""
        try:
            logger.info("Setting up Chrome driver for LinkedIn verification...")
            
            options = Options()
            # Don't use headless mode for LinkedIn
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
            options.add_argument("--window-size=1200,800")
            
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
            
            # Execute script to remove webdriver property
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'
            })
            
            logger.info("✅ Chrome driver setup successful")
            return driver
            
        except WebDriverException as e:
            logger.error(f"❌ WebDriver error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Chrome driver setup failed: {e}")
            return None
    
    def login_to_linkedin(self) -> bool:
        """Login to LinkedIn using Selenium."""
        try:
            logger.info("Navigating to LinkedIn login page...")
            self.driver.get("https://www.linkedin.com/login")
            time.sleep(3)
            
            # Find and fill email field
            email_field = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "username"))
            )
            email_field.clear()
            email_field.send_keys(self.email)
            
            # Find and fill password field
            password_field = self.driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self.password)
            
            # Click login button
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            time.sleep(5)
            
            # Check if login was successful
            current_url = self.driver.current_url
            if "feed" in current_url or "mynetwork" in current_url or "/in/" in current_url:
                logger.info("✅ Successfully logged into LinkedIn!")
                return True
            else:
                logger.error("❌ Login failed - please check credentials")
                return False
                
        except Exception as e:
            logger.error(f"❌ Login error: {e}")
            return False
    
    def extract_profile_data(self, linkedin_url: str) -> Dict:
        """Extract profile data from LinkedIn page."""
        profile_data = {
            "verified_name": "Not found",
            "current_title": "Not found",
            "current_company": "Not found",
            "location": "Not found",
            "about": "Not found",
            "connections": "Not found"
        }
        
        try:
            # Navigate to profile
            self.driver.get(linkedin_url)
            time.sleep(4)
            
            # Extract name
            try:
                name_selectors = [
                    "h1.text-heading-xlarge",
                    "[class*='pv-text-details__left-panel'] h1",
                    ".pv-top-card--list li:first-child",
                    "h1"
                ]
                
                for selector in name_selectors:
                    try:
                        name_element = WebDriverWait(self.driver, 5).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        profile_data["verified_name"] = name_element.text.strip()
                        break
                    except:
                        continue
            except:
                pass
            
            # Extract current title and company
            try:
                title_selectors = [
                    ".text-body-medium.break-words",
                    "[class*='pv-text-details__left-panel'] div:nth-child(2)",
                    ".pv-top-card--list li:nth-child(2)"
                ]
                
                for selector in title_selectors:
                    try:
                        title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        title_text = title_element.text.strip()
                        
                        if " at " in title_text:
                            parts = title_text.split(" at ", 1)
                            profile_data["current_title"] = parts[0].strip()
                            profile_data["current_company"] = parts[1].strip()
                        else:
                            profile_data["current_title"] = title_text
                        break
                    except:
                        continue
            except:
                pass
            
            # Extract location
            try:
                location_selectors = [
                    ".text-body-small.inline.t-black--light.break-words",
                    "[class*='pv-text-details__left-panel'] span.text-body-small",
                    ".pv-top-card--list-bullet li"
                ]
                
                for selector in location_selectors:
                    try:
                        location_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        location_text = location_element.text.strip()
                        if location_text and not any(x in location_text.lower() for x in ['connection', 'contact', 'message']):
                            profile_data["location"] = location_text
                            break
                    except:
                        continue
            except:
                pass
            
            # Extract about section
            try:
                about_selectors = [
                    "[class*='pv-about__summary-text']",
                    ".pv-about-section .pv-about__summary-text",
                    "[data-field='summary_info']"
                ]
                
                for selector in about_selectors:
                    try:
                        about_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        profile_data["about"] = about_element.text.strip()[:200]
                        break
                    except:
                        continue
            except:
                pass
            
            # Extract connections
            try:
                connections_selectors = [
                    "a[href*='connections']",
                    "span:contains('connection')",
                    ".pv-top-card--list-bullet"
                ]
                
                for selector in connections_selectors:
                    try:
                        connections_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        connections_text = connections_element.text
                        # Extract number from text like "500+ connections"
                        connections_match = re.search(r'(\d+\+?)', connections_text)
                        if connections_match:
                            profile_data["connections"] = connections_match.group(1)
                            break
                    except:
                        continue
            except:
                pass
            
        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
        
        return profile_data
    
    def verify_linkedin_profiles(self) -> List[Dict]:
        """Verify LinkedIn profiles using Selenium."""
        if not self.employees:
            logger.error("No employee data with LinkedIn profiles found")
            return []
        
        verified_profiles = []
        
        # Setup driver
        self.driver = self.setup_driver()
        if not self.driver:
            logger.error("Failed to setup Chrome driver")
            return []
        
        try:
            # Login to LinkedIn
            if not self.login_to_linkedin():
                logger.error("Failed to login to LinkedIn")
                return []
            
            # Wait a bit after login
            time.sleep(3)
            
            logger.info(f"Starting verification of {len(self.employees)} LinkedIn profiles...")
            
            for i, employee in enumerate(self.employees, 1):
                try:
                    # Get LinkedIn URL
                    linkedin_url = employee.get('linkedin_url', '')
                    
                    if not linkedin_url or 'linkedin.com/in/' not in linkedin_url.lower():
                        logger.warning(f"Skipping employee {i}: No valid LinkedIn URL")
                        continue
                    
                    logger.info(f"Verifying profile {i}/{len(self.employees)}: {linkedin_url}")
                    
                    # Extract profile data
                    profile_data = self.extract_profile_data(linkedin_url)
                    
                    # Create verified data record
                    verified_data = {
                        # Original data
                        "original_first_name": employee.get('first_name', ''),
                        "original_last_name": employee.get('last_name', ''),
                        "original_title": employee.get('title', ''),
                        "original_source": employee.get('source', ''),
                        "original_confidence": employee.get('confidence', ''),
                        
                        # Verified LinkedIn data
                        "verified_name": profile_data["verified_name"],
                        "current_title": profile_data["current_title"],
                        "current_company": profile_data["current_company"],
                        "location": profile_data["location"],
                        "about": profile_data["about"],
                        "connections": profile_data["connections"],
                        
                        # Metadata
                        "linkedin_url": linkedin_url,
                        "verification_status": "verified" if profile_data["verified_name"] != "Not found" else "partial",
                        "company_match": self._check_company_match(
                            profile_data["current_company"], 
                            self.config.get('company_name', '')
                        ),
                        "verification_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    verified_profiles.append(verified_data)
                    
                    logger.info(f"✅ Verified: {verified_data['verified_name']} - {verified_data['current_title']} at {verified_data['current_company']}")
                    
                    # Add delay between profiles
                    delay = 5 + random.randint(0, 3)
                    time.sleep(delay)
                    
                except TimeoutException as e:
                    logger.error(f"❌ Timeout error for profile {i}: {str(e)}")
                    self._add_error_record(verified_profiles, employee, linkedin_url, "Timeout error")
                    time.sleep(5)
                    
                except Exception as e:
                    logger.error(f"❌ Error verifying profile {i}: {str(e)}")
                    self._add_error_record(verified_profiles, employee, linkedin_url, str(e))
                    time.sleep(3)
                    
        except Exception as e:
            logger.error(f"General error during verification: {str(e)}")
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Browser closed successfully")
                except:
                    pass
        
        logger.info(f"Verification completed. Processed {len(verified_profiles)} profiles")
        return verified_profiles
    
    def _add_error_record(self, verified_profiles: List[Dict], employee: Dict, linkedin_url: str, error_msg: str):
        """Add error record to verified profiles."""
        error_data = {
            "original_first_name": employee.get('first_name', ''),
            "original_last_name": employee.get('last_name', ''),
            "original_title": employee.get('title', ''),
            "linkedin_url": linkedin_url,
            "verification_status": "error",
            "error_message": error_msg[:100],
            "verification_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        verified_profiles.append(error_data)
    
    def _check_company_match(self, linkedin_company: str, target_company: str) -> str:
        """Check if LinkedIn company matches target company."""
        if not linkedin_company or not target_company or linkedin_company == "Not found":
            return "unknown"
        
        linkedin_lower = str(linkedin_company).lower()
        target_lower = str(target_company).lower()
        
        # Check for exact match or substring match
        if target_lower in linkedin_lower or linkedin_lower in target_lower:
            return "match"
        
        # Check for common variations
        target_parts = target_lower.split()
        linkedin_parts = linkedin_lower.split()
        
        # Check if main company name matches
        if target_parts and linkedin_parts:
            if target_parts[0] == linkedin_parts[0]:
                return "partial_match"
        
        return "no_match"
    
    def save_verification_results(self, verified_profiles: List[Dict]) -> bool:
        """Save verification results to Excel and JSON files."""
        if not verified_profiles:
            logger.warning("No verification results to save")
            return False
        
        try:
            # Save to JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = self.script_dir / f"linkedin_verification_results_{timestamp}.json"
            
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(verified_profiles, f, indent=4, ensure_ascii=False)
            logger.info(f"Verification results saved to {json_file.name}")
            
            # Create Excel report
            return self._create_excel_report(verified_profiles, timestamp)
            
        except Exception as e:
            logger.error(f"Error saving verification results: {e}")
            return False
    
    def _create_excel_report(self, verified_profiles: List[Dict], timestamp: str) -> bool:
        """Create comprehensive Excel report with verification results."""
        try:
            logger.info("Creating LinkedIn verification Excel report...")
            
            # Create workbook
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Verification Results"
            
            # Define headers
            headers = [
                "Original First Name", "Original Last Name", "Original Title", "Original Source", "Original Confidence",
                "Verified Name", "Current Title", "Current Company", "Location", 
                "About", "Connections",
                "LinkedIn URL", "Company Match", "Verification Status", "Error Message", "Verification Date"
            ]
            
            # Write headers with formatting
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            header_border = Border(
                top=Side(style='thin'),
                bottom=Side(style='thin'),
                left=Side(style='thin'),
                right=Side(style='thin')
            )
            
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
                cell.border = header_border
            
            # Write data rows
            for row, profile in enumerate(verified_profiles, 2):
                data_row = [
                    profile.get('original_first_name', ''),
                    profile.get('original_last_name', ''),
                    profile.get('original_title', ''),
                    profile.get('original_source', ''),
                    profile.get('original_confidence', ''),
                    profile.get('verified_name', ''),
                    profile.get('current_title', ''),
                    profile.get('current_company', ''),
                    profile.get('location', ''),
                    profile.get('about', ''),
                    profile.get('connections', ''),
                    profile.get('linkedin_url', ''),
                    profile.get('company_match', ''),
                    profile.get('verification_status', ''),
                    profile.get('error_message', ''),
                    profile.get('verification_date', '')
                ]
                
                for col, value in enumerate(data_row, 1):
                    cell = ws.cell(row=row, column=col, value=value)
                    
                    # Add borders
                    cell.border = Border(
                        top=Side(style='thin'),
                        bottom=Side(style='thin'),
                        left=Side(style='thin'),
                        right=Side(style='thin')
                    )
                    
                    # Color code company match
                    if col == 13:  # Company Match column
                        if value == 'match':
                            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        elif value == 'partial_match':
                            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                        elif value == 'no_match':
                            cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    
                    # Color code verification status
                    if col == 14:  # Verification Status column
                        if value == 'verified':
                            cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                        elif value == 'partial':
                            cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                        elif value == 'error':
                            cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    
                    # Make LinkedIn URLs clickable
                    if col == 12 and value:  # LinkedIn URL column
                        cell.hyperlink = value
                        cell.font = Font(color="0000FF", underline="single")
            
            # Auto-adjust column widths
            for col in ws.columns:
                max_length = 0
                column_letter = col[0].column_letter
                
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                
                adjusted_width = min(max(max_length + 2, 12), 50)
                ws.column_dimensions[column_letter].width = adjusted_width
            
            # Create summary sheet
            summary_sheet = wb.create_sheet(title="Summary")
            
            # Summary statistics
            total_profiles = len(verified_profiles)
            successful_verifications = len([p for p in verified_profiles if p.get('verification_status') in ['verified', 'partial']])
            errors = len([p for p in verified_profiles if p.get('verification_status') == 'error'])
            company_matches = len([p for p in verified_profiles if p.get('company_match') == 'match'])
            partial_matches = len([p for p in verified_profiles if p.get('company_match') == 'partial_match'])
            
            summary_data = [
                ['LinkedIn Verification Summary', ''],
                ['', ''],
                ['Company', self.config.get('company_name', 'Unknown')],
                ['Location', self.config.get('location', 'Unknown')],
                ['Verification Date', datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                ['', ''],
                ['Total Profiles Processed', total_profiles],
                ['Successfully Verified', successful_verifications],
                ['Failed Verifications', errors],
                ['', ''],
                ['Current Company Matches', company_matches],
                ['Partial Company Matches', partial_matches],
                ['No Company Match', successful_verifications - company_matches - partial_matches if successful_verifications > 0 else 0],
                ['', ''],
                ['Success Rate', f"{(successful_verifications/total_profiles*100):.1f}%" if total_profiles > 0 else "0%"],
                ['Company Match Rate', f"{(company_matches/successful_verifications*100):.1f}%" if successful_verifications > 0 else "0%"]
            ]
            
            # Format summary sheet
            for row, (label, value) in enumerate(summary_data, 1):
                cell1 = summary_sheet.cell(row=row, column=1, value=label)
                cell2 = summary_sheet.cell(row=row, column=2, value=value)
                
                if label and label != '':
                    cell1.font = Font(bold=True)
                
                # Add some color to key metrics
                if label == 'LinkedIn Verification Summary':
                    cell1.font = Font(bold=True, size=14)
                elif label == 'Successfully Verified':
                    cell2.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif label == 'Current Company Matches':
                    cell2.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
            
            # Auto-adjust summary columns
            summary_sheet.column_dimensions['A'].width = 25
            summary_sheet.column_dimensions['B'].width = 30
            
            # Generate filename
            company_name = self.config.get('company_name', 'Company').replace(' ', '_').replace('/', '_')
            excel_file = self.script_dir / f"{company_name}_LinkedIn_Verification_{timestamp}.xlsx"
            
            # Save workbook
            wb.save(excel_file)
            logger.info(f"✅ Excel report created: {excel_file.name}")
            
            # Try to open the file
            try:
                if sys.platform == 'win32':
                    os.startfile(str(excel_file))
                elif sys.platform == 'darwin':
                    subprocess.run(['open', str(excel_file)])
                else:
                    subprocess.run(['xdg-open', str(excel_file)])
                logger.info("📂 Excel file opened automatically")
            except Exception:
                logger.info(f"📂 Please open manually: {excel_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating Excel report: {e}")
            return False
    
    def run_verification(self) -> bool:
        """Main method to run the complete LinkedIn verification process."""
        try:
            print("=" * 70)
            print("LINKEDIN PROFILE VERIFICATION")
            print("=" * 70)
            print("This script will verify LinkedIn profiles and extract current employment information.")
            
            if not self.employees:
                print("\n❌ No LinkedIn profiles found for verification")
                print("\nMake sure you have run the LinkedIn search script first:")
                print("  • script2_web_scraping.py (LinkedIn search)")
                
                # Show available files for debugging
                print(f"\nAvailable JSON files in {self.script_dir}:")
                json_files = list(self.script_dir.glob("*.json"))
                if json_files:
                    for file in sorted(json_files):
                        print(f"  • {file.name}")
                else:
                    print("  • No JSON files found")
                
                return False
            
            print(f"\n📊 Configuration:")
            print(f"Company: {self.config.get('company_name', 'Unknown')}")
            print(f"Location: {self.config.get('location', 'Unknown')}")
            print(f"LinkedIn profiles to verify: {len(self.employees)}")
            
            # Show sample profiles
            print(f"\n👥 Sample profiles to verify:")
            for i, emp in enumerate(self.employees[:5], 1):
                name = f"{emp.get('first_name', '')} {emp.get('last_name', '')}"
                original_title = emp.get('title', 'Unknown')
                print(f"   {i}. {name} - {original_title}")
            
            if len(self.employees) > 5:
                print(f"   ... and {len(self.employees) - 5} more")
            
            print(f"\n🔐 LinkedIn Login: {self.email}")
            print(f"⏱️  Estimated time: {len(self.employees) * 7 // 60} minutes")
            
            proceed = input(f"\n🚀 Start LinkedIn verification? (y/n, default: y): ").strip().lower()
            if proceed == 'n':
                print("Verification cancelled.")
                return False
            
            # Run verification
            print(f"\n🔍 Starting LinkedIn profile verification...")
            verified_profiles = self.verify_linkedin_profiles()
            
            if verified_profiles:
                print(f"\n✅ Verification completed!")
                print(f"📊 Results: {len(verified_profiles)} profiles processed")
                
                # Count successful verifications
                successful = len([p for p in verified_profiles if p.get('verification_status') in ['verified', 'partial']])
                errors = len([p for p in verified_profiles if p.get('verification_status') == 'error'])
                company_matches = len([p for p in verified_profiles if p.get('company_match') == 'match'])
                partial_matches = len([p for p in verified_profiles if p.get('company_match') == 'partial_match'])
                
                print(f"✅ Successfully verified: {successful}")
                print(f"❌ Failed verifications: {errors}")
                print(f"🏢 Current company matches: {company_matches}")
                print(f"🔶 Partial company matches: {partial_matches}")
                
                # Save results
                if self.save_verification_results(verified_profiles):
                    print(f"\n📄 Results saved to Excel and JSON files")
                    print(f"📈 Check the Excel report for detailed verification results")
                    
                    if company_matches > 0:
                        print(f"\n🎯 Found {company_matches} current employees at {self.config.get('company_name', 'the target company')}!")
                    
                    return True
                else:
                    print(f"\n❌ Failed to save results")
                    return False
            else:
                print(f"\n❌ No profiles were successfully verified")
                print("This could be due to:")
                print("  • LinkedIn login issues")
                print("  • Network connectivity problems") 
                print("  • Profile access restrictions")
                print("  • Rate limiting from LinkedIn")
                return False
                
        except KeyboardInterrupt:
            print("\n\nOperation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Verification process error: {e}")
def main():
    """Main execution function."""
    try:
        # Get script directory and config path
        script_dir = Path(__file__).parent.absolute()
        config_path = script_dir / "company_config.json"
        
        # Check if config file exists
        if not config_path.exists():
            print("⚠️  Configuration file not found!")
            print(f"Expected location: {config_path}")
            print("\nCreating a default configuration file...")
            
            # Create default config
            default_config = {
                "company_name": "FNZ",
                "location": "London",
                "linkedin_email": "",
                "linkedin_password": ""
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            
            print(f"✅ Created default configuration at: {config_path}")
            print("Please edit this file with your LinkedIn credentials.")
            print("\nAlternatively, you can set environment variables:")
            print("  export LINKEDIN_EMAIL='your_email@example.com'")
            print("  export LINKEDIN_PASSWORD='your_password'")
            return
        
        # Initialize verifier
        verifier = LinkedInProfileVerifier(str(config_path))
        
        # Run verification
        success = verifier.run_verification()
        
        if success:
            print("\n🎉 LinkedIn verification completed successfully!")
            print("Check the generated Excel report for detailed results.")
        else:
            print("\n❌ LinkedIn verification failed or incomplete.")
            sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ An error occurred: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()