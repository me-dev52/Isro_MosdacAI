"""
Base scraper class for web content extraction
"""

import time
import requests
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger

from config.config import get_mosdac_config
from src.utils.logger import get_logger

class BaseScraper(ABC):
    """Base class for web scrapers"""
    
    def __init__(self, base_url: str = None):
        self.config = get_mosdac_config()
        self.base_url = base_url or self.config.base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.logger = get_logger(self.__class__.__name__)
        self.driver = None
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
        if self.session:
            self.session.close()
            
    def get_page_content(self, url: str, use_selenium: bool = False) -> Optional[str]:
        """
        Get page content using requests or selenium
        
        Args:
            url: URL to scrape
            use_selenium: Whether to use selenium for dynamic content
            
        Returns:
            Page content as string
        """
        try:
            if use_selenium:
                return self._get_with_selenium(url)
            else:
                return self._get_with_requests(url)
        except Exception as e:
            self.logger.error(f"Error getting content from {url}: {e}")
            return None
            
    def _get_with_requests(self, url: str) -> Optional[str]:
        """Get content using requests"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            self.logger.error(f"Requests error for {url}: {e}")
            return None
            
    def _get_with_selenium(self, url: str) -> Optional[str]:
        """Get content using selenium for dynamic content"""
        try:
            if not self.driver:
                self._setup_selenium()
                
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            return self.driver.page_source
            
        except Exception as e:
            self.logger.error(f"Selenium error for {url}: {e}")
            return None
            
    def _setup_selenium(self):
        """Setup selenium webdriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
    def parse_html(self, html_content: str) -> BeautifulSoup:
        """
        Parse HTML content with BeautifulSoup
        
        Args:
            html_content: HTML content as string
            
        Returns:
            BeautifulSoup object
        """
        return BeautifulSoup(html_content, 'html.parser')
        
    def extract_links(self, soup: BeautifulSoup, base_url: str = None) -> List[str]:
        """
        Extract all links from HTML
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for relative links
            
        Returns:
            List of absolute URLs
        """
        base_url = base_url or self.base_url
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Filter out external links and non-HTML resources
            if self._is_valid_link(absolute_url):
                links.append(absolute_url)
                
        return list(set(links))  # Remove duplicates
        
    def _is_valid_link(self, url: str) -> bool:
        """
        Check if a link is valid for scraping
        
        Args:
            url: URL to check
            
        Returns:
            True if valid, False otherwise
        """
        parsed = urlparse(url)
        
        # Must be HTTP/HTTPS
        if parsed.scheme not in ['http', 'https']:
            return False
            
        # Must be from same domain (optional)
        if not url.startswith(self.base_url):
            return False
            
        # Exclude common non-content URLs
        excluded_extensions = ['.pdf', '.zip', '.exe', '.jpg', '.png', '.gif']
        if any(url.lower().endswith(ext) for ext in excluded_extensions):
            return False
            
        return True
        
    def extract_text_content(self, soup: BeautifulSoup) -> str:
        """
        Extract clean text content from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Clean text content
        """
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
            
        # Get text and clean it
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text
        
    def extract_metadata(self, soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extract metadata from HTML
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Dictionary of metadata
        """
        metadata = {}
        
        # Title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
            
        # Meta tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
                
        # Headings
        headings = {}
        for i in range(1, 7):
            h_tags = soup.find_all(f'h{i}')
            if h_tags:
                headings[f'h{i}'] = [h.get_text().strip() for h in h_tags]
        metadata['headings'] = headings
        
        return metadata
        
    def rate_limit(self):
        """Apply rate limiting between requests"""
        time.sleep(self.config.scraping_delay)
        
    @abstractmethod
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Main scraping method to be implemented by subclasses
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing scraped data
        """
        pass
        
    def scrape_multiple(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs
        
        Args:
            urls: List of URLs to scrape
            
        Returns:
            List of scraped data dictionaries
        """
        results = []
        
        for i, url in enumerate(urls):
            try:
                self.logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
                result = self.scrape(url)
                if result:
                    results.append(result)
                self.rate_limit()
            except Exception as e:
                self.logger.error(f"Error scraping {url}: {e}")
                continue
                
        return results
