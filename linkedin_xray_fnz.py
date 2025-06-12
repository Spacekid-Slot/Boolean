#!/usr/bin/env python3
"""
Simplified LinkedIn X-ray Google SERP Scraper

Focus: Extract LinkedIn profile URLs only (much simpler than full SERP scraping)
Use case: LinkedIn recruitment via Google X-ray search
"""

import time
import random
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus
from typing import List, Set
from dataclasses import dataclass

@dataclass
class LinkedInProfile:
    url: str
    domain: str  # linkedin.com, uk.linkedin.com, etc.
    query: str   # What search found this profile

class LinkedInXrayScraper:
    """Simplified scraper focused only on extracting LinkedIn profile URLs."""
    
    def __init__(self):
        self.driver = None
        self.found_profiles: Set[str] = set()  # Avoid duplicates
        self.session_searches = 0
        self.max_searches = 30  # Conservative for LinkedIn X-ray
        
    def setup_browser(self) -> bool:
        """Lightweight browser setup for LinkedIn X-ray."""
        try:
            options = Options()
            
            # Basic anti-detection (lighter than full SERP scraping)
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option('excludeSwitches', ['enable-automation'])
            
            # Speed optimizations (we only need URLs)
            options.add_argument('--disable-images')  # Don't load images
            options.add_argument('--disable-javascript')  # Don't need JS for URLs
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(20)
            
            return True
            
        except Exception as e:
            print(f"Browser setup failed: {e}")
            return False
    
    def xray_search_linkedin(self, company: str, job_titles: List[str] = None, 
                           locations: List[str] = None, domains: List[str] = None) -> List[LinkedInProfile]:
        """
        Perform LinkedIn X-ray search via Google.
        
        Args:
            company: Company name to search for
            job_titles: List of job titles (optional)
            locations: List of locations (optional) 
            domains: LinkedIn domains to target (e.g., ['linkedin.com', 'uk.linkedin.com'])
        """
        
        if not domains:
            domains = ['linkedin.com']  # Default to global
        
        all_profiles = []
        
        # Create search queries
        queries = self._create_xray_queries(company, job_titles, locations, domains)
        
        print(f"Starting LinkedIn X-ray search with {len(queries)} queries")
        
        for i, query_info in enumerate(queries, 1):
            if self.session_searches >= self.max_searches:
                print("Session limit reached")
                break
                
            print(f"[{i}/{len(queries)}] Searching: {query_info['description']}")
            
            profiles = self._search_single_query(query_info['query'])
            all_profiles.extend(profiles)
            
            # Show progress
            new_profiles = len([p for p in profiles if p.url not in self.found_profiles])
            print(f"  Found {len(profiles)} total, {new_profiles} new profiles")
            
            # Update found profiles set
            for profile in profiles:
                self.found_profiles.add(profile.url)
            
            # Delay between searches (conservative for X-ray)
            time.sleep(random.uniform(4, 8))
        
        # Remove duplicates and return
        unique_profiles = []
        seen_urls = set()
        
        for profile in all_profiles:
            if profile.url not in seen_urls:
                unique_profiles.append(profile)
                seen_urls.add(profile.url)
        
        print(f"\nX-ray search completed: {len(unique_profiles)} unique LinkedIn profiles found")
        return unique_profiles
    
    def _create_xray_queries(self, company: str, job_titles: List[str], 
                           locations: List[str], domains: List[str]) -> List[dict]:
        """Create focused LinkedIn X-ray search queries."""
        queries = []
        
        for domain in domains:
            
            if job_titles and locations:
                # Most targeted: company + job title + location (PRIMARY QUERY)
                for title in job_titles:
                    for location in locations:
                        queries.append({
                            'query': f'site:{domain} "{company}" "{title}" "{location}"',
                            'description': f'{title} at {company} in {location} ({domain})'
                        })
            
            if job_titles:
                # Company + job title (SECONDARY)
                for title in job_titles:
                    queries.append({
                        'query': f'site:{domain} "{company}" "{title}"',
                        'description': f'{title} at {company} ({domain})'
                    })
            
            if locations:
                # Company + location (TERTIARY)
                for location in locations:
                    queries.append({
                        'query': f'site:{domain} "{company}" "{location}"',
                        'description': f'{company} employees in {location} ({domain})'
                    })
            
            # General company search (FALLBACK)
            queries.append({
                'query': f'site:{domain} "{company}"',
                'description': f'{company} employees ({domain})'
            })
        
        return queries
    
    def _search_single_query(self, query: str) -> List[LinkedInProfile]:
        """Perform a single Google search and extract LinkedIn URLs."""
        profiles = []
        
        try:
            # Construct Google search URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num=20"
            
            self.driver.get(search_url)
            time.sleep(random.uniform(2, 4))
            
            # Check for blocking
            if self._is_blocked():
                print("  ⚠️ Detected blocking, skipping")
                return []
            
            # Extract all LinkedIn URLs from page source (simple approach)
            page_source = self.driver.page_source
            linkedin_urls = self._extract_linkedin_urls(page_source)
            
            # Create profile objects
            for url in linkedin_urls:
                domain = self._extract_domain_from_url(url)
                profiles.append(LinkedInProfile(
                    url=url,
                    domain=domain,
                    query=query
                ))
            
            self.session_searches += 1
            
        except Exception as e:
            print(f"  Error in search: {e}")
        
        return profiles
    
    def _extract_linkedin_urls(self, page_source: str) -> List[str]:
        """Extract LinkedIn profile URLs from page source using regex (simple & fast)."""
        
        # Regex pattern for LinkedIn profile URLs - CORRECTED
        pattern = r'https?://(?:www\.)?(?:[a-z]{2}\.)?linkedin\.com/in/[\w\-]+'
        
        urls = re.findall(pattern, page_source, re.IGNORECASE)
        
        # Remove duplicates while preserving order
        unique_urls = []
        seen = set()
        for url in urls:
            clean_url = url.split('?')[0]  # Remove query parameters
            if clean_url not in seen:
                unique_urls.append(clean_url)
                seen.add(clean_url)
        
        return unique_urls
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract LinkedIn domain from URL."""
        domain_match = re.search(r'((?:[a-z]{2}\.)?linkedin\.com)', url, re.IGNORECASE)
        return domain_match.group(1) if domain_match else 'linkedin.com'
    
    def _is_blocked(self) -> bool:
        """Simple blocking detection."""
        page_source = self.driver.page_source.lower()
        blocking_terms = ['captcha', 'unusual traffic', 'automated queries']
        return any(term in page_source for term in blocking_terms)
    
    def save_results(self, profiles: List[LinkedInProfile], filename: str = 'linkedin_xray_results.json'):
        """Save results to JSON file."""
        data = []
        for profile in profiles:
            data.append({
                'linkedin_url': profile.url,
                'linkedin_domain': profile.domain,
                'search_query': profile.query,
                'source': 'Google X-ray Search'
            })
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Results saved to {filename}")
    
    def close(self):
        """Close browser."""
        if self.driver:
            self.driver.quit()

# Example usage for your recruitment needs
def main():
    """LinkedIn X-ray search for FNZ sales professionals in London."""
    
    scraper = LinkedInXrayScraper()
    
    if not scraper.setup_browser():
        print("Failed to setup browser")
        return
    
    try:
        # Specific search for FNZ sales in London
        company = "FNZ"
        job_titles = ["Sales"]
        locations = ["London"]
        domains = ["uk.linkedin.com"]  # UK-specific domain
        
        print("=" * 60)
        print("LINKEDIN X-RAY SEARCH - FNZ SALES LONDON")
        print("=" * 60)
        print(f"Target query: site:uk.linkedin.com \"FNZ\" \"Sales\" \"London\"")
        print(f"Expected URLs: https://uk.linkedin.com/in/profile-name")
        print(f"Expected to find: FNZ sales professionals in London")
        print()
        
        # Perform X-ray search
        profiles = scraper.xray_search_linkedin(
            company=company,
            job_titles=job_titles,
            locations=locations,
            domains=domains
        )
        
        # Show results
        print(f"\n📊 X-ray Search Results:")
        print(f"Company: {company}")
        print(f"Job Title: Sales")
        print(f"Location: London")
        print(f"LinkedIn Domain: uk.linkedin.com")
        print(f"Total profiles found: {len(profiles)}")
        
        if profiles:
            print(f"\n🔗 LinkedIn Profiles Found:")
            for i, profile in enumerate(profiles, 1):
                print(f"  {i}. {profile.url}")
            
            # Save results with specific filename
            scraper.save_results(profiles, 'fnz_sales_london_profiles.json')
            print(f"\n💾 Results saved to: fnz_sales_london_profiles.json")
            
            print(f"\n✅ Success! Found {len(profiles)} FNZ sales professionals in London")
            print("These profiles are ready for manual review or further verification.")
        else:
            print(f"\n❌ No profiles found. This could be due to:")
            print("- No FNZ sales professionals in London with public LinkedIn profiles")
            print("- Google blocking the search")
            print("- Profiles not indexed on uk.linkedin.com")
            print("- Search terms too specific")
        
    finally:
        scraper.close()

if __name__ == "__main__":
    main()