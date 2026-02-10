import feedparser
import requests
from newspaper import Article
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional
import re
from urllib.parse import urlparse, urljoin
import time
import json
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import random

# Try to import cloudscraper for CloudFlare bypass
try:
    import cloudscraper
    CLOUDSCRAPER_AVAILABLE = True
except ImportError:
    CLOUDSCRAPER_AVAILABLE = False
    print("Note: Install cloudscraper for better anti-blocking: pip install cloudscraper")

@dataclass
class ArticleCandidate:
    title: str
    url: str
    publication: str
    published_date: datetime
    summary: str
    author: str = "Unknown"
    relevance_score: float = 0.0
    keywords_found: List[str] = None
    full_content: str = ""

class CustomArticleCollector:
    def __init__(self):
        """Initialize collector with your specific sources and keywords"""
        
        # Your custom keywords for relevance filtering (British English)
        self.luxury_keywords = [
            # Core keywords (your specific additions)
            'luxury', 'jewellery', 'fine jewellery', 'craftsmanship',
            
            # Additional jewelry terms (British spelling preference)
            'jewelry', 'diamond', 'engagement ring', 'wedding ring',
            'fashion', 'accessories', 'watches', 'timepiece',
            'necklace', 'bracelet', 'earrings', 'pendant', 'brooch',
            'gold', 'platinum', 'silver', 'emerald', 'sapphire', 'ruby',
            
            # Luxury brands
            'cartier', 'tiffany', 'bulgari', 'chanel', 'dior', 'van cleef',
            'graff', 'harry winston', 'chopard', 'piaget', 'boucheron',
            
            # Industry & events
            'red carpet', 'celebrity', 'haute couture', 'collection',
            'launch', 'collaboration', 'limited edition', 'auction',
            'investment', 'trends', 'style', 'fashion week', 'royal',
            'royals',
        ]
        
        # Your specific publication sources (updated with fixes)
        self.target_sources = {
            # UK Newspapers & Luxury
            'The Guardian': {
                'base_url': 'https://www.theguardian.com/fashion/womens-jewellery',
                'rss_feed': 'https://www.theguardian.com/fashion/womens-jewellery/rss',
                'sitemap_url': None
            },
            'The Telegraph': {
                'base_url': 'https://www.telegraph.co.uk/luxury/',
                'rss_feed': 'https://www.telegraph.co.uk/luxury/rss',  # Try RSS first
                'sitemap_url': None  # Sitemap is blocked (403)
            },
            'Evening Standard': {
                'base_url': 'https://www.standard.co.uk/topic/jewellery',
                'rss_feed': 'https://www.standard.co.uk/rss',
                'sitemap_url': 'https://www.standard.co.uk/sitemaps/googlenews'
            },
            'The Times': {
                'base_url': 'https://www.thetimes.com/life-style/luxury',
                'rss_feed': None,
                'sitemap_url': 'https://www.thetimes.com/sitemaps/main-pages'
            },
            'Financial Times': {
                'base_url': 'https://www.ft.com/fashion',
                'rss_feed': 'https://www.ft.com/rss/fashion',
                'sitemap_url': None
            },
            
            # Business Publications
            'Forbes': {
                'base_url': 'https://www.forbes.com/business/',
                'rss_feed': 'https://www.forbes.com/business/feed/',
                'sitemap_url': 'https://www.forbes.com/news_sitemap.xml'
            },
            'Business of Fashion': {
                'base_url': 'https://www.businessoffashion.com/',
                'rss_feed': 'https://www.businessoffashion.com/feed/',
                'sitemap_url': None
            },
            'Vogue Business': {
                'base_url': 'https://www.voguebusiness.com/',
                'rss_feed': 'https://www.voguebusiness.com/feed',
                'sitemap_url': 'https://www.vogue.com/feed/google-latest-news/sitemap-google-news'
            },
            
            # Fashion & Lifestyle
            'Harper\'s Bazaar': {
                'base_url': 'https://www.harpersbazaar.com/',
                'rss_feed': None,
                'sitemap_url': 'https://www.harpersbazaar.com/sitemap_index.xml'
            },
            'Elle': {
                'base_url': 'https://www.elle.com/jewelry/',
                'rss_feed': None,
                'sitemap_url': 'https://www.elle.com/sitemap_google_news.xml'
            },
            'Vogue UK': {
                'base_url': 'https://www.vogue.co.uk/',
                'rss_feed': 'https://www.vogue.co.uk/feed/rss',
                'sitemap_url': 'https://www.vogue.co.uk/feed/sitemap/sitemap-google-news'
            },
            'Vanity Fair': {
                'base_url': 'https://www.vanityfair.com/',
                'rss_feed': 'https://www.vanityfair.com/feed/rss',
                'sitemap_url': 'https://www.vanityfair.com/feed/google-latest-news/sitemap-google-news'
            },
            'Tatler': {
                'base_url': 'https://www.tatler.com/',
                'rss_feed': None,
                'sitemap_url': None
            },
            'Red Online': {
                'base_url': 'https://www.redonline.co.uk/',
                'rss_feed': None,
                'sitemap_url': 'https://www.redonline.co.uk/sitemap_google_news.xml'
            },
            'Town & Country': {
                'base_url': 'https://www.townandcountrymag.com/style/',
                'rss_feed': 'https://www.townandcountrymag.com/rss/all.xml/',
                'sitemap_url': 'https://www.townandcountrymag.com/sitemap_google_news.xml'
            },
            'StyleCaster': {
                'base_url': 'https://stylecaster.com/c/fashion/',
                'rss_feed': 'https://stylecaster.com/feed/',
                'sitemap_url': 'https://stylecaster.com/news-sitemap.xml'
            },
            'The Handbook': {
                'base_url': 'https://www.thehandbook.com/',
                'rss_feed': None,
                'sitemap_url': 'https://www.thehandbook.com/sitemap.xml?postType=editorial&offset=0'
            },
            'Something About Rocks': {
                'base_url': 'https://somethingaboutrocks.com/',
                'rss_feed': 'https://somethingaboutrocks.com/feed/',
                'sitemap_url': None
            },
            'The Cut': {
                'base_url': 'https://www.thecut.com/',
                'rss_feed': 'https://www.thecut.com/rss/index.xml',
                'sitemap_url': 'https://www.thecut.com/sitemaps/sitemap-2025.xml'
            },
            'The Monocle': {
                'base_url': 'https://monocle.com/',
                'rss_feed': None,
                'sitemap_url': 'https://monocle.com/the-monocle-minute/'
            },
            'The Jewels Club': {
                'base_url': 'https://thejewels.club/',
                'rss_feed': None,
                'sitemap_url': 'https://thejewels.club/sitemap.xml'
            },
            
            # Industry Publications
            'Retail Jeweller': {
                'base_url': 'https://www.retail-jeweller.com/',
                'rss_feed': 'https://www.retail-jeweller.com/feed/',
                'sitemap_url': None
            },
            'Professional Jeweller': {
                'base_url': 'https://www.professionaljeweller.com/',
                'rss_feed': None,
                'sitemap_url': None
            },
            'Rapaport': {
                'base_url': 'https://rapaport.com/',
                'rss_feed': 'https://rapaport.com/rss/',
                'sitemap_url': None
            },
            'National Jeweler': {
                'base_url': 'https://nationaljeweler.com/',
                'rss_feed': None,  # Try standard RSS path
                'sitemap_url': 'https://nationaljeweler.com/sitemap.xml'  # Try standard sitemap
            }
        }
        
        self.session = requests.Session()
        
        # Use CloudScraper if available, otherwise regular requests
        if CLOUDSCRAPER_AVAILABLE:
            self.scraper = cloudscraper.create_scraper(
                browser={
                    'browser': 'chrome',
                    'platform': 'windows',
                    'mobile': False
                }
            )
            print("CloudScraper enabled for anti-blocking\n")
        else:
            self.scraper = self.session
        
        # List of realistic User-Agents to rotate
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 OPR/107.0.0.0'
        ]
        
        # Rate limiting configuration
        self.request_count = 0
        self.last_request_time = time.time()
        self.min_delay_between_requests = 2.0  # Minimum 2 seconds between requests
        self.max_delay_between_requests = 5.0  # Maximum 5 seconds between requests
        self.requests_per_source = 0
        self.max_requests_per_minute = 20  # Don't exceed 20 requests per minute
    
    def get_random_user_agent(self):
        """Get a random User-Agent from the pool"""
        return random.choice(self.user_agents)
    
    def apply_rate_limit(self):
        """Apply intelligent rate limiting to avoid detection and blocking"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Ensure minimum delay between requests
        if time_since_last < self.min_delay_between_requests:
            sleep_time = self.min_delay_between_requests - time_since_last
            time.sleep(sleep_time)
        
        # Add random human-like delay
        random_delay = random.uniform(0, self.max_delay_between_requests - self.min_delay_between_requests)
        time.sleep(random_delay)
        
        # Update tracking
        self.last_request_time = time.time()
        self.request_count += 1
        
        # Enforce per-minute rate limit
        if self.request_count % self.max_requests_per_minute == 0:
            print(f"  Rate limit: Processed {self.request_count} requests, brief pause...")
            time.sleep(random.uniform(5, 10))  # Longer pause every 20 requests
    
    def make_request(self, url: str, timeout: int = 10):
        """Make request with CloudScraper, rate limiting, and rotating User-Agent"""
        # Apply rate limiting before each request
        self.apply_rate_limit()
        
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://www.google.com/'  # Add referer to look more natural
        }
        
        try:
            response = self.scraper.get(url, headers=headers, timeout=timeout)
            
            if response.status_code != 200:
                # Enhanced error reporting for Telegraph specifically
                domain = urlparse(url).netloc
                if 'telegraph' in domain.lower():
                    print(f"    HTTP {response.status_code} - Telegraph blocking detected")
                    print(f"    Response preview: {response.text[:200]}")
                else:
                    print(f"    HTTP {response.status_code} error for {url}")
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"    Request error: {str(e)}")
            raise

    def calculate_relevance_score(self, title: str, content: str) -> tuple:
        """Calculate relevance score based on your custom keywords"""
        combined_text = f"{title} {content}".lower()
        found_keywords = []
        score = 0.0
        
        for keyword in self.luxury_keywords:
            if keyword.lower() in combined_text:
                found_keywords.append(keyword)
                
                if keyword.lower() in ['luxury', 'jewellery', 'fine jewellery', 'craftsmanship']:
                    score += 4.0
                elif keyword.lower() in ['jewelry', 'diamond', 'engagement ring']:
                    score += 3.0
                elif keyword.lower() in ['fashion', 'collection', 'launch']:
                    score += 2.5
                elif keyword.lower() in ['cartier', 'tiffany', 'bulgari', 'chanel']:
                    score += 3.5
                elif keyword.lower() in ['red carpet', 'celebrity', 'fashion week']:
                    score += 2.0
                else:
                    score += 1.0
        
        if len(found_keywords) > 2:
            score *= 1.2
        if len(found_keywords) > 4:
            score *= 1.4
            
        return score, found_keywords
    
    def try_rss_feed(self, publication: str, feed_url: str) -> List[ArticleCandidate]:
        """Try to fetch articles from RSS feed with rotating User-Agent and error reporting"""
        candidates = []
        
        if not feed_url:
            return candidates
            
        try:
            response = self.make_request(feed_url, timeout=10)
            
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:20]:
                    try:
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        else:
                            pub_date = datetime.now()
                        
                        if (datetime.now() - pub_date).days > 30:
                            continue
                        
                        title = entry.get('title', '').strip()
                        summary = entry.get('summary', '').strip()
                        url = entry.get('link', '').strip()
                        
                        if not title or not url:
                            continue
                        
                        score, keywords = self.calculate_relevance_score(title, summary)
                        
                        if score >= 1.0:
                            candidate = ArticleCandidate(
                                title=title,
                                url=url,
                                publication=publication,
                                published_date=pub_date,
                                summary=summary,
                                relevance_score=score,
                                keywords_found=keywords
                            )
                            candidates.append(candidate)
                            
                    except Exception as e:
                        continue
                
                if candidates:
                    print(f"  RSS: Found {len(candidates)} articles")
                
        except Exception as e:
            print(f"  RSS error: {str(e)}")
        
        return candidates
    
    def is_relevant_url(self, url: str) -> bool:
        """Quick URL-based relevance check"""
        url_lower = url.lower()
        
        # Explicitly exclude National Jeweler category/section pages
        national_jeweler_excluded = [
            'https://nationaljeweler.com/',
            'https://nationaljeweler.com/industry',
            'https://nationaljeweler.com/industry/industry-other',
            'https://nationaljeweler.com/industry/independents',
            'https://nationaljeweler.com/industry/events-awards',
            'https://nationaljeweler.com/industry/financials',
            'https://nationaljeweler.com/industry/supplier-bulletin',
            'https://nationaljeweler.com/industry/technology',
            'https://nationaljeweler.com/industry/surveys',
            'https://nationaljeweler.com/industry/policies-issues',
            'https://nationaljeweler.com/industry/crime',
            'https://nationaljeweler.com/industry/majors',
            'https://nationaljeweler.com/diamonds-gems',
            'https://nationaljeweler.com/diamonds-gems/diamonds-gems-other',
            'https://nationaljeweler.com/diamonds-gems/lab-grown',
            'https://nationaljeweler.com/diamonds-gems/grading',
            'https://nationaljeweler.com/diamonds-gems/sourcing',
            'https://nationaljeweler.com/style',
            'https://nationaljeweler.com/style/style-other',
            'https://nationaljeweler.com/style/trends',
            'https://nationaljeweler.com/style/auctions',
            'https://nationaljeweler.com/style/watches',
            'https://nationaljeweler.com/style/collections',
            'https://nationaljeweler.com/opinions',
            'https://nationaljeweler.com/opinions/editors',
            'https://nationaljeweler.com/opinions/columnists'
        ]
        
        # Check if URL is in excluded list (with or without trailing slash)
        url_clean = url.rstrip('/')
        if url_clean in national_jeweler_excluded or url in national_jeweler_excluded:
            return False
        
        relevant_terms = [
            'jewelry', 'jewellery', 'diamond', 'engagement', 'wedding',
            'luxury', 'fashion', 'style', 'watches', 'accessories',
            'cartier', 'tiffany', 'bulgari', 'chanel'
        ]
        
        exclude_terms = [
            'recipe', 'food', 'travel', 'politics', 'sports', 'health'
        ]
        
        has_relevant = any(term in url_lower for term in relevant_terms)
        has_excluded = any(term in url_lower for term in exclude_terms)
        
        return has_relevant and not has_excluded
    
    def fetch_urls_from_sitemap(self, sitemap_url: str) -> List[tuple]:
        """Helper to fetch URLs from a single sitemap with rotating User-Agent"""
        urls = []
        try:
            response = self.make_request(sitemap_url, timeout=10)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                for url_elem in root:
                    loc_elem = url_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    lastmod_elem = url_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                    
                    if loc_elem is not None:
                        url = loc_elem.text
                        if lastmod_elem is not None:
                            try:
                                lastmod_str = lastmod_elem.text
                                if 'T' in lastmod_str:
                                    lastmod_date = datetime.fromisoformat(lastmod_str.replace('Z', '+00:00'))
                                else:
                                    lastmod_date = datetime.strptime(lastmod_str[:10], '%Y-%m-%d')
                                lastmod_date = lastmod_date.replace(tzinfo=None)
                            except:
                                lastmod_date = datetime.now()
                        else:
                            lastmod_date = datetime.now()
                        
                        urls.append((url, lastmod_date))
        except:
            pass
        
        return urls
    
    def fetch_sitemap_articles(self, publication: str, sitemap_url: str) -> List[ArticleCandidate]:
        """Fetch articles from XML sitemap with rotating User-Agent and error reporting"""
        candidates = []
        
        try:
            response = self.make_request(sitemap_url, timeout=15)
            
            if response.status_code != 200:
                return candidates
            
            root = ET.fromstring(response.content)
            urls = []
            
            if 'sitemapindex' in root.tag:
                for sitemap in root[:3]:
                    loc_elem = sitemap.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    if loc_elem is not None:
                        sub_sitemap_url = loc_elem.text
                        urls.extend(self.fetch_urls_from_sitemap(sub_sitemap_url))
            
            elif 'urlset' in root.tag:
                for url_elem in root:
                    loc_elem = url_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                    lastmod_elem = url_elem.find('.//{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
                    
                    if loc_elem is not None:
                        url = loc_elem.text
                        
                        if lastmod_elem is not None:
                            try:
                                lastmod_str = lastmod_elem.text
                                if 'T' in lastmod_str:
                                    lastmod_date = datetime.fromisoformat(lastmod_str.replace('Z', '+00:00'))
                                else:
                                    lastmod_date = datetime.strptime(lastmod_str[:10], '%Y-%m-%d')
                                lastmod_date = lastmod_date.replace(tzinfo=None)
                                
                                if (datetime.now() - lastmod_date).days > 30:
                                    continue
                            except:
                                lastmod_date = datetime.now()
                        else:
                            lastmod_date = datetime.now()
                        
                        urls.append((url, lastmod_date))
            
            for url, pub_date in urls[:50]:
                try:
                    if self.is_relevant_url(url):
                        candidate = ArticleCandidate(
                            title="",
                            url=url,
                            publication=publication,
                            published_date=pub_date,
                            summary="",
                            relevance_score=1.0
                        )
                        candidates.append(candidate)
                        
                except Exception:
                    continue
            
            if candidates:
                print(f"  Sitemap: Found {len(candidates)} articles")
            
        except Exception as e:
            print(f"  Sitemap error: {str(e)}")
        
        return candidates
    
    def collect_from_source(self, publication: str, source_info: dict) -> List[ArticleCandidate]:
        """Collect articles from a single source using RSS and sitemap only"""
        all_candidates = []
        
        if source_info.get('rss_feed'):
            rss_candidates = self.try_rss_feed(publication, source_info['rss_feed'])
            all_candidates.extend(rss_candidates)
        
        if len(all_candidates) < 3 and source_info.get('sitemap_url'):
            sitemap_candidates = self.fetch_sitemap_articles(publication, source_info['sitemap_url'])
            all_candidates.extend(sitemap_candidates)
        
        unique_candidates = []
        seen_urls = set()
        for candidate in all_candidates:
            if candidate.url not in seen_urls:
                unique_candidates.append(candidate)
                seen_urls.add(candidate.url)
        
        return unique_candidates
    
    def extract_full_content(self, candidate: ArticleCandidate) -> ArticleCandidate:
        """Extract full article content using CloudScraper for download, newspaper for parsing"""
        try:
            # Download HTML using CloudScraper (bypasses CloudFlare blocks)
            response = self.make_request(candidate.url, timeout=20)
            
            if response.status_code != 200:
                return None
            
            # Use newspaper to parse the HTML we downloaded with CloudScraper
            article = Article(candidate.url)
            article.download_state = 2  # Mark as already downloaded
            article.html = response.text  # Feed our CloudScraper HTML
            article.parse()  # Only parse, don't download
            
            if not article.text or len(article.text) < 150:
                return None
            
            candidate.full_content = article.text
            
            if not candidate.title and article.title:
                candidate.title = article.title
            
            full_score, full_keywords = self.calculate_relevance_score(
                candidate.title or "", article.text
            )
            
            candidate.relevance_score = full_score
            candidate.keywords_found = full_keywords
            
            if article.authors:
                candidate.author = article.authors[0]
            else:
                author_match = re.search(r'\b[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', article.text[:800])
                if author_match:
                    candidate.author = author_match.group(1)
            
            if article.meta_description and len(article.meta_description) > len(candidate.summary):
                candidate.summary = article.meta_description
            
            if full_score >= 1.5:
                return candidate
            else:
                return None
            
        except Exception as e:
            error_msg = str(e)
            if '403' in error_msg or 'Forbidden' in error_msg:
                print(f"  Error: HTTP 403 Forbidden - {candidate.publication}")
            elif '404' in error_msg or 'Not Found' in error_msg:
                print(f"  Error: HTTP 404 Not Found - {candidate.publication}")
            elif '429' in error_msg or 'Too Many' in error_msg:
                print(f"  Error: HTTP 429 Rate Limited - {candidate.publication}")
            elif 'timeout' in error_msg.lower():
                print(f"  Error: Timeout - {candidate.publication}")
            else:
                print(f"  Error: {error_msg[:60]} - {candidate.publication}")
            return None
    
    def collect_trending_articles(self, max_articles: int = 25, sources_subset: List[str] = None) -> List[ArticleCandidate]:
        """Main method to collect articles from your specified sources"""
        print("Custom Article Collection")
        print("=" * 60)
        
        sources_to_use = sources_subset if sources_subset else list(self.target_sources.keys())
        print(f"Targeting {len(sources_to_use)} publications\n")
        
        all_candidates = []
        
        for publication in sources_to_use:
            if publication in self.target_sources:
                print(f"{publication}:")
                
                # Reset per-source request counter
                self.requests_per_source = 0
                
                source_candidates = self.collect_from_source(
                    publication, 
                    self.target_sources[publication]
                )
                all_candidates.extend(source_candidates)
                
                # Longer delay between different sources (3-6 seconds)
                time.sleep(random.uniform(3, 6))
        
        if not all_candidates:
            print("\nNo candidates found")
            return []
        
        print(f"\nAnalyzing {len(all_candidates)} candidates...\n")
        
        all_candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        top_candidates = all_candidates[:max_articles * 2]
        
        final_articles = []
        for candidate in top_candidates:
            enhanced = self.extract_full_content(candidate)
            if enhanced:
                final_articles.append(enhanced)
            
            # Reduced delay since rate limiting is now in make_request()
            time.sleep(random.uniform(1, 2))
            
            if len(final_articles) >= max_articles:
                break
        
        final_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"\nCollection complete: {len(final_articles)} articles")
        
        return final_articles
    
    def generate_collection_report(self, articles: List[ArticleCandidate]) -> str:
        """Generate detailed collection report"""
        if not articles:
            return "No articles collected"
        
        report = []
        report.append("\nARTICLE COLLECTION REPORT")
        report.append("=" * 60)
        report.append(f"Total Articles: {len(articles)}")
        report.append(f"Average Relevance Score: {sum(a.relevance_score for a in articles) / len(articles):.1f}\n")
        
        pub_counts = {}
        for article in articles:
            pub_counts[article.publication] = pub_counts.get(article.publication, 0) + 1
        
        report.append("By Publication:")
        for pub, count in sorted(pub_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  {pub}: {count}")
        
        all_keywords = []
        for article in articles:
            all_keywords.extend(article.keywords_found or [])
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        report.append("\nTop Keywords:")
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            report.append(f"  {keyword} ({count})")
        
        report.append("\nArticles:\n")
        for i, article in enumerate(articles, 1):
            report.append(f"{i}. {article.title}")
            report.append(f"   {article.publication} | {article.author} | Score: {article.relevance_score:.1f}")
            report.append(f"   {article.published_date.strftime('%Y-%m-%d')}")
            report.append(f"   {article.url}\n")
        
        return "\n".join(report)
    
    def save_results(self, articles: List[ArticleCandidate], filename: str = "collected_articles.json"):
        """Save results with full content for integration"""
        data = []
        for article in articles:
            data.append({
                'title': article.title,
                'url': article.url,
                'publication': article.publication,
                'author': article.author,
                'published_date': article.published_date.isoformat(),
                'summary': article.summary,
                'full_content': article.full_content,
                'relevance_score': article.relevance_score,
                'keywords_found': article.keywords_found,
                'content_length': len(article.full_content)
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filename

def main():
    """Test the custom collector with your sources"""
    print("Luxury Article Collector")
    print("=" * 60)
    
    collector = CustomArticleCollector()
    
    print(f"\nAvailable Sources ({len(collector.target_sources)}):")
    for i, pub in enumerate(collector.target_sources.keys(), 1):
        print(f"{i:2d}. {pub}")
    
    try:
        max_articles = int(input(f"\nHow many articles to collect? (default: 20): ") or "20")
        
        use_subset = input("Use specific sources only? (y/N): ").lower().startswith('y')
        sources_subset = None
        
        if use_subset:
            source_names = input("Enter source numbers (comma-separated): ")
            if source_names.strip():
                indices = [int(x.strip()) - 1 for x in source_names.split(',')]
                sources_list = list(collector.target_sources.keys())
                sources_subset = [sources_list[i] for i in indices if 0 <= i < len(sources_list)]
                print(f"Using: {', '.join(sources_subset)}\n")
        
    except (ValueError, KeyboardInterrupt):
        max_articles = 20
        sources_subset = None
    
    articles = collector.collect_trending_articles(
        max_articles=max_articles,
        sources_subset=sources_subset
    )
    
    report = collector.generate_collection_report(articles)
    print(f"{report}")
    
    if articles:
        filename = collector.save_results(articles)
        print(f"Saved to: {filename}")
        
        print(f"\nIntegration Preview:")
        print(f"Articles are ready to feed into your BART summarizer!")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article.title} ({article.publication})")
            print(f"   Content: {len(article.full_content)} characters")
    else:
        print("No relevant articles found.")

if __name__ == "__main__":
    main()