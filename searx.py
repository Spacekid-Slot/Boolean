#!/usr/bin/env python3
"""
Searx LinkedIn X-ray Scraper

Uses public Searx instances for LinkedIn searches.
Searx is open-source and doesn't block automated searches.
"""

import time
import random
import re
import json
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from urllib.parse import quote_plus, urljoin
from typing import List, Set
from dataclasses import dataclass

@dataclass
class LinkedInProfile:
    url: str
    domain: str
    query: str
    title: str = ""
    searx_instance: str = ""

class SearxXrayScraper:
    """LinkedIn X-ray scraper using public Searx instances."""
    
    def __init__(self):
        self.driver = None
        self.found_profiles: Set[str] = set()
        self.session_searches = 0
        self.max_searches = 100  # Searx is very permissive
        
        # Use priv.au as primary instance (confirmed working)
        self.searx_instances = [
            "https://priv.au",
            "https://searx.be",  # Backup instances
            "https://search.privacyguides.net",
            "https://searx.tiekoetter.com"
        ]
        
        # Test priv.au first
        self.working_instances = self._test_searx_instances()
        
    def _test_searx_instances(self) -> List[str]:
        """Test which Searx instances are currently working, prioritizing priv.au."""
        working = []
        
        print("Testing Searx instances (prioritizing priv.au)...")
        
        # Test priv.au first
        try:
            response = requests.get("https://priv.au/search", 
                                  params={"q": "test", "format": "json"}, 
                                  timeout=5)
            if response.status_code == 200:
                working.append("https://priv.au")
                print(f"✅ https://priv.au - Working (PRIMARY)")
            else:
                print(f"❌ https://priv.au - Status {response.status_code}")
        except Exception as e:
            print(f"❌ https://priv.au - Error: {e}")
        
        # Test backup instances
        for instance in self.searx_instances[1:4]:  # Test 3 backups
            try:
                response = requests.get(f"{instance}/search", 
                                      params={"q": "test", "format": "json"}, 
                                      timeout=5)
                if response.status_code == 200:
                    working.append(instance)
                    print(f"✅ {instance} - Working (backup)")
                else:
                    print(f"❌ {instance} - Status {response.status_code}")
            except Exception as e:
                print(f"❌ {instance} - Error: {e}")
        
        if not working:
            print("⚠️ No Searx instances responding, using priv.au anyway")
            working = ["https://priv.au"]  # Force priv.au
        
        return working
    
    def setup_browser(self) -> bool:
        """Setup browser for Searx access."""
        try:
            options = Options()
            
            # Minimal setup (Searx doesn't block)
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-images')  # Speed up
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(15)
            
            return True
            
        except Exception as e:
            print(f"Browser setup failed: {e}")
            return False
    
    def search_fnz_via_searx(self) -> List[LinkedInProfile]:
        """Search for FNZ sales professionals using Searx."""
        
        print("=" * 60)
        print("SEARX LINKEDIN X-RAY - FNZ SALES LONDON")
        print("=" * 60)
        print(f"Using priv.au as primary Searx instance")
        print(f"Search syntax: \"uk.linkedin.com/in/\" london fnz sales")
        print(f"Using {len(self.working_instances)} Searx instances")
        
        # Try API method first (faster)
        profiles = self._search_via_api()
        
        if not profiles:
            # Fall back to browser method
            print("API method failed, trying browser method...")
            profiles = self._search_via_browser()
        
        return profiles
    
    def _search_via_api(self) -> List[LinkedInProfile]:
        """Search using Searx JSON API with priv.au syntax."""
        all_profiles = []
        
        # Updated queries using priv.au syntax: "uk.linkedin.com/in/" london fnz sales
        queries = [
            '"uk.linkedin.com/in/" london fnz sales',
            '"uk.linkedin.com/in/" fnz sales director london',
            '"uk.linkedin.com/in/" fnz business development london',
            '"uk.linkedin.com/in/" fnz account manager london',
            '"uk.linkedin.com/in/" fnz sales manager london',
            '"uk.linkedin.com/in/" fnz sales',
            '"linkedin.com/in/" london fnz sales',  # Global backup
        ]
        
        for instance in self.working_instances:
            print(f"\n🔍 Trying Searx instance: {instance}")
            
            for query in queries:
                try:
                    print(f"  Searching: {query}")
                    
                    # Searx API request
                    params = {
                        "q": query,
                        "format": "json",
                        "engines": "bing,google,duckduckgo",  # Use multiple engines
                    }
                    
                    response = requests.get(
                        f"{instance}/search",
                        params=params,
                        timeout=10,
                        headers={"User-Agent": "Mozilla/5.0 (compatible; LinkedIn-Research)"}
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        profiles = self._extract_profiles_from_json(data, query, instance)
                        
                        new_profiles = [p for p in profiles if p.url not in self.found_profiles]
                        all_profiles.extend(new_profiles)
                        
                        for profile in new_profiles:
                            self.found_profiles.add(profile.url)
                        
                        print(f"    Found {len(profiles)} total, {len(new_profiles)} new")
                        
                        # Small delay between queries
                        time.sleep(1)
                    else:
                        print(f"    API error: {response.status_code}")
                        
                except Exception as e:
                    print(f"    Error: {e}")
                    continue
            
            # Delay between instances
            time.sleep(2)
        
        return all_profiles
    
    def _extract_profiles_from_json(self, data: dict, query: str, instance: str) -> List[LinkedInProfile]:
        """Extract LinkedIn profiles from Searx JSON response."""
        profiles = []
        
        try:
            results = data.get("results", [])
            
            for result in results:
                url = result.get("url", "")
                title = result.get("title", "")
                
                # Check if it's a LinkedIn profile
                if re.search(r'linkedin\.com/in/', url, re.IGNORECASE):
                    domain = self._extract_domain_from_url(url)
                    
                    profiles.append(LinkedInProfile(
                        url=url,
                        domain=domain,
                        query=query,
                        title=title,
                        searx_instance=instance
                    ))
        
        except Exception as e:
            print(f"Error parsing JSON results: {e}")
        
        return profiles
    
    def _search_via_browser(self) -> List[LinkedInProfile]:
        """Fallback browser method using priv.au syntax."""
        if not self.setup_browser():
            return []
        
        all_profiles = []
        
        try:
            # Updated queries for priv.au syntax
            queries = [
                '"uk.linkedin.com/in/" london fnz sales',
                '"uk.linkedin.com/in/" fnz sales',
                '"linkedin.com/in/" london fnz sales'
            ]
            
            for instance in self.working_instances[:2]:  # Try first 2 instances
                print(f"\n🌐 Browser search via: {instance}")
                
                for query in queries:
                    try:
                        search_url = f"{instance}/search?q={quote_plus(query)}"
                        
                        self.driver.get(search_url)
                        time.sleep(2)
                        
                        # Extract LinkedIn URLs from page
                        page_source = self.driver.page_source
                        linkedin_urls = self._extract_linkedin_urls(page_source)
                        
                        for url in linkedin_urls:
                            if url not in self.found_profiles:
                                domain = self._extract_domain_from_url(url)
                                all_profiles.append(LinkedInProfile(
                                    url=url,
                                    domain=domain,
                                    query=query,
                                    searx_instance=instance
                                ))
                                self.found_profiles.add(url)
                        
                        print(f"  Found {len(linkedin_urls)} LinkedIn URLs")
                        time.sleep(3)
                        
                    except Exception as e:
                        print(f"  Browser search error: {e}")
                        continue
        
        finally:
            if self.driver:
                self.driver.quit()
        
        return all_profiles
    
    def _extract_linkedin_urls(self, page_source: str) -> List[str]:
        """Extract LinkedIn URLs from page source."""
        pattern = r'https?://(?:www\.)?(?:[a-z]{2}\.)?linkedin\.com/in/[\w\-]+'
        urls = re.findall(pattern, page_source, re.IGNORECASE)
        
        # Remove duplicates
        unique_urls = []
        seen = set()
        for url in urls:
            clean_url = url.split('?')[0]
            if clean_url not in seen:
                unique_urls.append(clean_url)
                seen.add(clean_url)
        
        return unique_urls
    
    def _extract_domain_from_url(self, url: str) -> str:
        """Extract LinkedIn domain from URL."""
        domain_match = re.search(r'((?:[a-z]{2}\.)?linkedin\.com)', url, re.IGNORECASE)
        return domain_match.group(1) if domain_match else 'linkedin.com'
    
    def save_results(self, profiles: List[LinkedInProfile]):
        """Save Searx results."""
        data = []
        for profile in profiles:
            data.append({
                'linkedin_url': profile.url,
                'linkedin_domain': profile.domain,
                'title': profile.title,
                'search_query': profile.query,
                'searx_instance': profile.searx_instance,
                'source': 'Searx X-ray Search',
                'company': 'FNZ',
                'search_type': 'Sales professionals'
            })
        
        filename = 'fnz_sales_searx_results.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"💾 Results saved to {filename}")

def main():
    """Search FNZ sales professionals via Searx."""
    
    scraper = SearxXrayScraper()
    
    try:
        profiles = scraper.search_fnz_via_searx()
        
        if profiles:
            print(f"\n📊 Searx Results Summary:")
            print(f"Total FNZ profiles found: {len(profiles)}")
            
            # Group by instance
            instance_counts = {}
            domain_counts = {}
            
            for profile in profiles:
                instance = profile.searx_instance
                domain = profile.domain
                
                instance_counts[instance] = instance_counts.get(instance, 0) + 1
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            print(f"\nBy Searx instance:")
            for instance, count in instance_counts.items():
                print(f"  {instance}: {count} profiles")
            
            print(f"\nBy LinkedIn domain:")
            for domain, count in domain_counts.items():
                print(f"  {domain}: {count} profiles")
            
            print(f"\n🔗 Sample FNZ profiles found:")
            for i, profile in enumerate(profiles[:5], 1):
                print(f"  {i}. {profile.url}")
                if profile.title:
                    print(f"     Title: {profile.title}")
                print(f"     Found via: {profile.searx_instance}")
            
            if len(profiles) > 5:
                print(f"  ... and {len(profiles) - 5} more")
            
            scraper.save_results(profiles)
            
            print(f"\n✅ Searx search successful! Found {len(profiles)} FNZ profiles")
            print("Searx advantage: No blocking, multiple search engines, privacy-focused")
            
        else:
            print(f"\n❌ No FNZ profiles found via Searx")
            print("Try checking if the Searx instances are working or expand search terms")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()