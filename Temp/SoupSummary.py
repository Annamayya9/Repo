from newspaper import Article
from transformers import pipeline
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse
import re
import json
import requests
from bs4 import BeautifulSoup
import time
import random

@dataclass
class ArticleSummary:
    title: str
    author: str
    summary: str
    url: str
    publication: str
    topics: List[str] = None

class EnhancedArticleSummarizer:
    def __init__(self, model: str = "facebook/bart-large-cnn"):
        """Initialize the summarizer with BART CNN model"""
        print(f"Loading model: {model} ... this may take a moment.")
        self.summarizer = pipeline("summarization", model=model)
        
import requests
from bs4 import BeautifulSoup
import time
import random
from fake_useragent import UserAgent
import json
from typing import List, Optional, Dict

class HumanLikeExtractor:
    def __init__(self):
        """Initialize with human-like browsing patterns"""
        
        # Proxy rotation (you'll need to configure these)
        self.proxy_list = [
            # Add your proxy servers here
            # {'http': 'http://proxy1:port', 'https': 'https://proxy1:port'},
            # {'http': 'http://proxy2:port', 'https': 'https://proxy2:port'},
        ]
        self.current_proxy_index = 0
        
        # User agent rotation
        try:
            self.ua = UserAgent()
        except:
            self.user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            self.ua = None
        
        # Session with connection pooling
        self.session = requests.Session()
        self.request_count = 0
        self.last_request_time = 0
        
        # Browsing behavior patterns
        self.min_delay = 3.0  # Minimum seconds between requests
        self.max_delay = 8.0  # Maximum seconds between requests
        self.session_rotation_interval = 10  # Rotate session every N requests
    
    def get_next_proxy(self) -> Optional[Dict]:
        """Rotate to next proxy in list"""
        if not self.proxy_list:
            return None
            
        proxy = self.proxy_list[self.current_proxy_index]
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxy_list)
        return proxy
    
    def get_random_headers(self) -> Dict[str, str]:
        """Generate realistic, rotating headers"""
        
        if self.ua:
            try:
                user_agent = self.ua.random
            except:
                user_agent = random.choice(self.user_agents)
        else:
            user_agent = random.choice(self.user_agents)
        
        # Realistic header combinations
        headers = {
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': random.choice([
                'en-US,en;q=0.9',
                'en-GB,en;q=0.9',
                'en-US,en;q=0.5'
            ]),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': random.choice(['none', 'same-origin', 'cross-site']),
            'Cache-Control': random.choice(['no-cache', 'max-age=0']),
        }
        
        # Randomly add optional headers
        if random.random() > 0.5:
            headers['DNT'] = '1'
        
        if random.random() > 0.7:
            headers['Sec-GPC'] = '1'
            
        return headers
    
    def human_delay(self):
        """Implement human-like delays between requests"""
        current_time = time.time()
        
        # Ensure minimum time between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            additional_delay = self.min_delay - time_since_last
            time.sleep(additional_delay)
        
        # Add random human-like delay
        human_delay = random.uniform(self.min_delay, self.max_delay)
        time.sleep(human_delay)
        
        self.last_request_time = time.time()
        print(f"Waited {human_delay:.1f}s (human-like delay)")
    
    def rotate_session_if_needed(self):
        """Rotate session periodically to avoid fingerprinting"""
        if self.request_count % self.session_rotation_interval == 0:
            print("Rotating session for anti-fingerprinting")
            self.session.close()
            self.session = requests.Session()
    
    def make_request(self, url: str, max_retries: int = 3) -> Optional[requests.Response]:
        """Make a human-like request with rotation and retry logic"""
        
        self.human_delay()
        self.rotate_session_if_needed()
        
        for attempt in range(max_retries):
            try:
                headers = self.get_random_headers()
                proxy = self.get_next_proxy()
                
                print(f"Request attempt {attempt + 1}/{max_retries}")
                if proxy:
                    print(f"Using proxy: {list(proxy.values())[0]}")
                
                response = self.session.get(
                    url,
                    headers=headers,
                    proxies=proxy,
                    timeout=20,
                    allow_redirects=True
                )
                
                self.request_count += 1
                
                # Check response
                if response.status_code == 200:
                    # Additional check for blocking content
                    text_lower = response.text.lower()
                    if any(block_word in text_lower for block_word in 
                          ['blocked', 'forbidden', 'captcha', 'access denied', 'datadome']):
                        print(f"Response contains blocking indicators")
                        if attempt < max_retries - 1:
                            print("Trying different proxy/headers...")
                            time.sleep(random.uniform(10, 20))  # Longer delay on block
                            continue
                        else:
                            return None
                    
                    print(f"Request successful ({len(response.content)} bytes)")
                    return response
                
                elif response.status_code == 403:
                    print(f"403 Forbidden - trying different proxy")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(15, 30))  # Long delay on 403
                        continue
                    else:
                        return None
                
                else:
                    print(f"HTTP {response.status_code}")
                    return None
                    
            except Exception as e:
                print(f"Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 15))
                    continue
        
        return None

    def extract_with_newspaper(self, url: str) -> Optional[dict]:
        """Primary method: Extract using newspaper3k"""
        try:
            print(f"Trying newspaper3k extraction...")
            article = Article(url)
            article.download()
            article.parse()
            
            if not article.text or len(article.text) < 150:
                print(f"Newspaper3k: Content too short")
                return None
            
            return {
                'title': article.title or "",
                'text': article.text,
                'authors': article.authors,
                'meta_description': getattr(article, 'meta_description', ''),
                'html': article.html
            }
            
        except Exception as e:
            print(f"Newspaper3k failed: {e}")
            return None

    def __init__(self, model: str = "facebook/bart-large-cnn"):
        """Initialize the summarizer with BART CNN model"""
        print(f"Loading model: {model} ... this may take a moment.")
        self.summarizer = pipeline("summarization", model=model)
        
        # Initialize human-like extractor
        self.extractor = HumanLikeExtractor()

    def extract_with_requests(self, url: str) -> Optional[dict]:
        """Enhanced requests method with human-like behavior"""
        try:
            print(f"Using human-like requests extraction...")
            
            response = self.extractor.make_request(url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_selectors = ['title', 'h1', '.headline', '.article-title', '[class*="title"]']
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    if len(title) > 5:
                        break
            
            # Extract main content
            content_text = ""
            content_selectors = [
                'article', '.article-content', '.post-content', '.entry-content',
                '.article-body', '.story-content', '.content', 'main',
                '[class*="article"]', '[class*="post"]', '[class*="content"]'
            ]
            
            # Remove unwanted elements first
            for unwanted in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
                unwanted.decompose()
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text().strip()
                    # Clean up whitespace
                    content_text = ' '.join(content_text.split())
                    if len(content_text) > 300:
                        break
            
            if len(content_text) < 150:
                print(f"Content too short ({len(content_text)} chars)")
                return None
            
            # Try to extract meta description
            meta_desc = ""
            meta_elem = soup.find('meta', attrs={'name': 'description'})
            if meta_elem:
                meta_desc = meta_elem.get('content', '')
            
            print(f"Human-like extraction successful: {len(content_text)} chars")
            
            return {
                'title': title,
                'text': content_text,
                'authors': [],
                'meta_description': meta_desc,
                'html': response.text
            }
            
        except Exception as e:
            print(f"Human-like extraction failed: {e}")
            return None

    def extract_author_from_data(self, article_data: dict) -> str:
        """Extract author from article data (works with both extraction methods)"""
        
        # Method 1: From newspaper3k authors
        if article_data.get('authors'):
            return article_data['authors'][0]
        
        # Method 2: JSON-LD parsing
        if article_data.get('html'):
            try:
                soup = BeautifulSoup(article_data['html'], 'html.parser')
                scripts = soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, list):
                            for entry in data:
                                if isinstance(entry, dict) and 'author' in entry:
                                    author = self._get_author_from_jsonld(entry['author'])
                                    if author:
                                        return author
                        elif isinstance(data, dict) and 'author' in data:
                            author = self._get_author_from_jsonld(data['author'])
                            if author:
                                return author
                    except:
                        continue
            except:
                pass
        
        # Method 3: Regex scan
        combined_text = f"{article_data.get('title', '')} {article_data.get('meta_description', '')} {article_data.get('text', '')}"
        patterns = [
            r'[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'[Ww]ritten\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'[Aa]uthor:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, combined_text[:800])
            if match:
                return match.group(1)
        
        return "Unknown"

    def _get_author_from_jsonld(self, author_field):
        """Helper to safely parse author name(s) from JSON-LD structures"""
        if isinstance(author_field, dict) and 'name' in author_field:
            return author_field['name']
        elif isinstance(author_field, list):
            for entry in author_field:
                if isinstance(entry, dict) and 'name' in entry:
                    return entry['name']
        return None

    def extract_with_selenium(self, url: str) -> Optional[dict]:
        """Advanced fallback: Extract using Selenium (real browser)"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            print(f"Advanced fallback: Using Selenium browser...")
            
            chrome_options = Options()
            # Anti-detection settings
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Run headless for production
            chrome_options.add_argument('--headless')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Navigate like a human
            driver.get(url)
            time.sleep(random.uniform(3, 6))  # Wait for page load
            
            # Check if blocked
            page_source = driver.page_source.lower()
            if any(block_word in page_source for block_word in ['blocked', 'forbidden', 'captcha', 'access denied']):
                driver.quit()
                print("Selenium also blocked")
                return None
            
            # Extract content
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # Get title
            title = ""
            try:
                title = driver.title
            except:
                title_elem = soup.select_one('title, h1')
                if title_elem:
                    title = title_elem.get_text().strip()
            
            # Remove unwanted elements
            for unwanted in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                unwanted.decompose()
            
            # Extract main content
            content_selectors = [
                'article', '.article-content', '.post-content', '.entry-content',
                '.article-body', '.story-content', '.content', 'main'
            ]
            
            content_text = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    content_text = content_elem.get_text().strip()
                    content_text = ' '.join(content_text.split())
                    if len(content_text) > 300:
                        break
            
            driver.quit()
            
            if len(content_text) < 150:
                print(f"Selenium: Content too short")
                return None
            
            print(f"Selenium extraction successful: {len(content_text)} chars")
            
            return {
                'title': title,
                'text': content_text,
                'authors': [],
                'meta_description': '',
                'html': driver.page_source
            }
            
        except ImportError:
            print("Selenium not installed. Run: pip install selenium")
            return None
        except Exception as e:
            print(f"Selenium extraction failed: {e}")
            try:
                driver.quit()
            except:
                pass
            return None
    def extract_article_content(self, url: str) -> Optional[dict]:
        """Extract article using three-tier approach: newspaper3k -> requests -> selenium"""
        
        # Method 1: Try newspaper3k first
        article_data = self.extract_with_newspaper(url)
        if article_data:
            return article_data
        
        # Method 2: Fallback to requests
        print("Newspaper3k blocked or failed, trying requests fallback...")
        article_data = self.extract_with_requests(url)
        if article_data:
            return article_data
        
        # Method 3: Final fallback to Selenium (real browser)
        print("Requests also blocked, trying Selenium fallback...")
        article_data = self.extract_with_selenium(url)
        if article_data:
            return article_data
        
        print("All extraction methods failed")
        return None

    def summarize_article(
        self,
        article_content: str,
        article_url: str,
        publication: str,
        title: str,
        author: str
    ) -> Optional[ArticleSummary]:
        """Summarize an article focusing on luxury brands, jewelry pieces, and celebrities"""
        try:
            # Luxury-focused instruction
            input_text = (
                "You are a PR professional specializing in luxury brands, jewelry, and fashion. "
                "Summarize only the key details of the article, focusing on jewelry pieces, collections, luxury brands, and celebrity names. "
                "Include all important facts, figures, numbers, dates, and numeric comparisons relevant to these mentions. "
                "Avoid unnecessary explanations or background — only include details that a luxury PR expert would need to know to quickly understand the article. "
                "Keep sentences short, clear, and easy to read, so that the summary can save time and fully convey the essential points of the article. "
                + article_content
            )
            
            summary_text = self.summarizer(
                input_text[:3000],
                max_length=120,
                min_length=40,
                do_sample=False
            )[0]["summary_text"]

            return ArticleSummary(
                title=title,
                author=author if author else "Unknown",
                summary=summary_text.strip(),
                url=article_url,
                publication=publication,
                topics=[]
            )

        except Exception as e:
            print(f"Error summarizing article {article_url}: {e}")
            return None

    def process_url(self, url: str) -> Optional[ArticleSummary]:
        """Complete processing pipeline: extract + summarize"""
        
        print(f"Processing: {url}")
        
        # Extract article content
        article_data = self.extract_article_content(url)
        if not article_data:
            return None
        
        # Extract author
        author = self.extract_author_from_data(article_data)
        
        # Get publication name
        publication = self.extract_publication_name(url)
        
        # Summarize
        summary = self.summarize_article(
            article_data['text'],
            url,
            publication,
            article_data['title'],
            author
        )
        
        return summary

    def extract_publication_name(self, url: str) -> str:
        """Extract publication name from URL"""
        domain = urlparse(url).netloc.replace("www.", "").split(".")[0]
        return domain.title()

    def process_url(self, url: str) -> Optional[ArticleSummary]:
        """Complete processing pipeline: extract + summarize"""
        
        print(f"Processing: {url}")
        
        # Extract article content
        article_data = self.extract_article_content(url)
        if not article_data:
            return None
        
        # Extract author
        author = self.extract_author_from_data(article_data)
        
        # Get publication name
        publication = self.extract_publication_name(url)
        
        # Summarize
        summary = self.summarize_article(
            article_data['text'],
            url,
            publication,
            article_data['title'],
            author
        )
        
        return summary

    def extract_publication_name(self, url: str) -> str:
        """Extract publication name from URL"""
        domain = urlparse(url).netloc.replace("www.", "").split(".")[0]
        return domain.title()

def main():
    """Test the enhanced summarizer"""
    print("Enhanced Article Summarizer with Anti-Block Fallback")
    print("=" * 55)

    url = input("Enter article URL: ").strip()
    if not url:
        print("URL required!")
        return

    summarizer = EnhancedArticleSummarizer("facebook/bart-large-cnn")
    summary = summarizer.process_url(url)

    if summary:
        print("\nSUMMARY RESULT:")
        print("=" * 30)
        print(f"Title       : {summary.title}")
        print(f"Author      : {summary.author}")
        print(f"Summary     : {summary.summary}")
        print(f"Link        : {summary.url}")
        print(f"Publication : {summary.publication}")
        
        # Format for your existing workflow
        formatted = f"* [{summary.title}]({summary.url}) by {summary.author} - {summary.summary}"
        print(f"\nFormatted Output:")
        print(formatted)
    else:
        print("Failed to process article")

if __name__ == "__main__":
    main()