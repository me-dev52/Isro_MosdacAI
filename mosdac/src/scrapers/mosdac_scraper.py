"""
MOSDAC portal specific scraper
"""

import re
import json
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from src.scrapers.base_scraper import BaseScraper
from src.utils.logger import get_logger

class MOSDACScraper(BaseScraper):
    """Specialized scraper for MOSDAC portal"""
    
    def __init__(self):
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        
        # MOSDAC-specific patterns
        self.faq_patterns = [
            r'/faq',
            r'/help',
            r'/support',
            r'/documentation'
        ]
        
        self.data_patterns = [
            r'/data',
            r'/products',
            r'/satellite',
            r'/imagery',
            r'/download'
        ]
        
        self.api_patterns = [
            r'/api',
            r'/services',
            r'/rest'
        ]
        
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        Scrape MOSDAC portal content
        
        Args:
            url: URL to scrape
            
        Returns:
            Dictionary containing scraped data
        """
        try:
            # Determine content type and scraping strategy
            content_type = self._classify_content(url)
            
            if content_type == 'faq':
                return self._scrape_faq_page(url)
            elif content_type == 'data':
                return self._scrape_data_page(url)
            elif content_type == 'api':
                return self._scrape_api_page(url)
            else:
                return self._scrape_general_page(url)
                
        except Exception as e:
            self.logger.error(f"Error scraping {url}: {e}")
            return {}
            
    def _classify_content(self, url: str) -> str:
        """
        Classify content type based on URL patterns
        
        Args:
            url: URL to classify
            
        Returns:
            Content type string
        """
        url_lower = url.lower()
        
        if any(re.search(pattern, url_lower) for pattern in self.faq_patterns):
            return 'faq'
        elif any(re.search(pattern, url_lower) for pattern in self.data_patterns):
            return 'data'
        elif any(re.search(pattern, url_lower) for pattern in self.api_patterns):
            return 'api'
        else:
            return 'general'
            
    def _scrape_faq_page(self, url: str) -> Dict[str, Any]:
        """Scrape FAQ page content"""
        html_content = self.get_page_content(url)
        if not html_content:
            return {}
            
        soup = self.parse_html(html_content)
        
        # Extract FAQ content
        faqs = []
        
        # Look for common FAQ patterns
        faq_selectors = [
            '.faq-item',
            '.faq-question',
            '.question',
            '.accordion-item',
            'dt',  # Definition term
            'h3', 'h4'  # Headings that might be questions
        ]
        
        for selector in faq_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    question = element.get_text().strip()
                    if len(question) > 10:  # Filter out very short text
                        # Try to find corresponding answer
                        answer = self._find_faq_answer(element, soup)
                        if answer:
                            faqs.append({
                                'question': question,
                                'answer': answer,
                                'source_url': url
                            })
                            
        return {
            'url': url,
            'content_type': 'faq',
            'faqs': faqs,
            'metadata': self.extract_metadata(soup),
            'text_content': self.extract_text_content(soup)
        }
        
    def _scrape_data_page(self, url: str) -> Dict[str, Any]:
        """Scrape data/product page content"""
        html_content = self.get_page_content(url)
        if not html_content:
            return {}
            
        soup = self.parse_html(html_content)
        
        # Extract data product information
        data_info = {}
        
        # Look for product specifications
        spec_selectors = [
            '.product-specs',
            '.data-specs',
            '.specifications',
            'table',
            '.info-table'
        ]
        
        for selector in spec_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    if element.name == 'table':
                        data_info['specifications'] = self._extract_table_data(element)
                    else:
                        data_info['specifications'] = element.get_text().strip()
                    break
                    
        # Look for download links
        download_links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(ext in href.lower() for ext in ['.zip', '.tif', '.nc', '.hdf', '.xml']):
                download_links.append({
                    'url': urljoin(url, href),
                    'text': link.get_text().strip(),
                    'file_type': self._get_file_type(href)
                })
                    
        return {
            'url': url,
            'content_type': 'data',
            'data_info': data_info,
            'download_links': download_links,
            'metadata': self.extract_metadata(soup),
            'text_content': self.extract_text_content(soup)
        }
        
    def _scrape_api_page(self, url: str) -> Dict[str, Any]:
        """Scrape API/service page content"""
        html_content = self.get_page_content(url)
        if not html_content:
            return {}
            
        soup = self.parse_html(html_content)
        
        # Extract API information
        api_info = {}
        
        # Look for API documentation
        api_selectors = [
            '.api-docs',
            '.endpoint',
            '.method',
            'code',
            'pre'
        ]
        
        for selector in api_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    if element.name in ['code', 'pre']:
                        api_info['code_examples'] = element.get_text().strip()
                    else:
                        api_info['documentation'] = element.get_text().strip()
                        
        return {
            'url': url,
            'content_type': 'api',
            'api_info': api_info,
            'metadata': self.extract_metadata(soup),
            'text_content': self.extract_text_content(soup)
        }
        
    def _scrape_general_page(self, url: str) -> Dict[str, Any]:
        """Scrape general page content"""
        html_content = self.get_page_content(url)
        if not html_content:
            return {}
            
        soup = self.parse_html(html_content)
        
        # Extract general content
        content = {
            'url': url,
            'content_type': 'general',
            'metadata': self.extract_metadata(soup),
            'text_content': self.extract_text_content(soup),
            'links': self.extract_links(soup, url)
        }
        
        # Look for specific MOSDAC content patterns
        content.update(self._extract_mosdac_specific_content(soup))
        
        return content
        
    def _find_faq_answer(self, question_element, soup: BeautifulSoup) -> Optional[str]:
        """Find the answer for a FAQ question"""
        # Try to find answer in next sibling or parent
        answer = None
        
        # Check next sibling
        next_sibling = question_element.find_next_sibling()
        if next_sibling:
            answer = next_sibling.get_text().strip()
            
        # Check parent container
        if not answer:
            parent = question_element.parent
            if parent:
                # Look for answer-like content in parent
                answer_elements = parent.find_all(['p', 'div', 'span'])
                for elem in answer_elements:
                    if elem != question_element and elem.get_text().strip():
                        answer = elem.get_text().strip()
                        break
                        
        return answer if answer and len(answer) > 20 else None
        
    def _extract_table_data(self, table_element) -> List[Dict[str, str]]:
        """Extract data from HTML table"""
        table_data = []
        
        rows = table_element.find_all('tr')
        if not rows:
            return table_data
            
        # Check if first row is header
        header_row = rows[0]
        headers = [th.get_text().strip() for th in header_row.find_all(['th', 'td'])]
        
        # Process data rows
        for row in rows[1:]:
            cells = row.find_all('td')
            if len(cells) == len(headers):
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        row_data[headers[i]] = cell.get_text().strip()
                table_data.append(row_data)
                
        return table_data
        
    def _get_file_type(self, url: str) -> str:
        """Extract file type from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()
        
        if '.zip' in path:
            return 'ZIP'
        elif '.tif' in path or '.tiff' in path:
            return 'GeoTIFF'
        elif '.nc' in path:
            return 'NetCDF'
        elif '.hdf' in path:
            return 'HDF'
        elif '.xml' in path:
            return 'XML'
        else:
            return 'Unknown'
            
    def _extract_mosdac_specific_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract MOSDAC-specific content patterns"""
        content = {}
        
        # Look for satellite data information
        satellite_info = []
        satellite_keywords = ['satellite', 'sensor', 'resolution', 'coverage', 'temporal']
        
        for keyword in satellite_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                parent = element.parent
                if parent:
                    context = parent.get_text().strip()
                    if len(context) > 50:
                        satellite_info.append({
                            'keyword': keyword,
                            'context': context
                        })
                        
        if satellite_info:
            content['satellite_info'] = satellite_info
            
        # Look for geospatial information
        geo_info = []
        geo_keywords = ['latitude', 'longitude', 'coordinate', 'bounding box', 'extent']
        
        for keyword in geo_keywords:
            elements = soup.find_all(text=re.compile(keyword, re.IGNORECASE))
            for element in elements:
                parent = element.parent
                if parent:
                    context = parent.get_text().strip()
                    if len(context) > 50:
                        geo_info.append({
                            'keyword': keyword,
                            'context': context
                        })
                        
        if geo_info:
            content['geospatial_info'] = geo_info
            
        return content
        
    def discover_content(self, start_url: str, max_depth: int = 3) -> List[str]:
        """
        Discover content URLs from MOSDAC portal
        
        Args:
            start_url: Starting URL for discovery
            max_depth: Maximum depth for crawling
            
        Returns:
            List of discovered URLs
        """
        discovered_urls = set()
        urls_to_visit = [(start_url, 0)]  # (url, depth)
        visited_urls = set()
        
        while urls_to_visit:
            current_url, depth = urls_to_visit.pop(0)
            
            if depth > max_depth or current_url in visited_urls:
                continue
                
            visited_urls.add(current_url)
            
            try:
                html_content = self.get_page_content(current_url)
                if html_content:
                    soup = self.parse_html(html_content)
                    new_links = self.extract_links(soup, current_url)
                    
                    # Add new URLs to visit
                    for link in new_links:
                        if link not in visited_urls and link not in discovered_urls:
                            discovered_urls.add(link)
                            if depth + 1 <= max_depth:
                                urls_to_visit.append((link, depth + 1))
                                
                    self.rate_limit()
                    
            except Exception as e:
                self.logger.error(f"Error discovering content from {current_url}: {e}")
                continue
                
        return list(discovered_urls)
