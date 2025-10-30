"""
Linktree scraper module for VoiceTree
Scrapes Linktree pages to extract user information and links
"""
import requests
from bs4 import BeautifulSoup
from typing import Dict, List
import re


class LinktreeScraper:
    """Scraper for Linktree profiles"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def extract_username_from_url(self, url: str) -> str:
        """Extract username from Linktree URL"""
        url = url.strip().rstrip('/')
        url = re.sub(r'^https?://', '', url)
        url = re.sub(r'^www\.', '', url)
        
        if 'linktr.ee/' in url:
            username = url.split('linktr.ee/')[-1]
        else:
            username = url.split('/')[-1]
        
        return username.lower()
    
    def scrape_linktree(self, url: str) -> Dict:
        """
        Scrape a Linktree page and extract profile information and links
        
        Args:
            url: Linktree profile URL
            
        Returns:
            Dict containing username, display_name, bio, and links
        """
        try:
            # Normalize URL
            if not url.startswith('http'):
                url = f'https://linktr.ee/{url}'
            
            # Extract username
            username = self.extract_username_from_url(url)
            
            # Fetch the page
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract display name
            display_name = username
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text()
                if '|' in title_text:
                    display_name = title_text.split('|')[0].strip()
                elif 'Linktree' in title_text:
                    display_name = title_text.replace('Linktree', '').strip()
            
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                display_name = og_title['content']
            
            # Extract bio
            bio = ""
            og_description = soup.find('meta', property='og:description')
            if og_description and og_description.get('content'):
                bio = og_description['content']
            
            # Extract links
            links = []
            link_selectors = [
                'a[data-testid*="link"]',
                'a[class*="Link"]',
                'a[href]:not([href^="#"]):not([href^="javascript"])'
            ]
            
            for selector in link_selectors:
                link_elements = soup.select(selector)
                for link in link_elements:
                    href = link.get('href', '')
                    title = link.get_text(strip=True)
                    
                    if not href or not title or len(title) < 2:
                        continue
                    
                    if 'cookie' in title.lower() or 'privacy' in title.lower():
                        continue
                    
                    if href.startswith('http') or href.startswith('//'):
                        if href.startswith('//'):
                            href = 'https:' + href
                        
                        if not any(l['url'] == href for l in links):
                            links.append({
                                'title': title,
                                'url': href
                            })
                
                if links:
                    break
            
            return {
                'username': username,
                'display_name': display_name or username,
                'bio': bio,
                'links': links[:20]
            }
            
        except requests.RequestException as e:
            raise Exception(f"Failed to fetch Linktree page: {str(e)}")
        except Exception as e:
            raise Exception(f"Error scraping Linktree: {str(e)}")


scraper = LinktreeScraper()
