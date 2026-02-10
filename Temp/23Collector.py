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
            'investment', 'trends', 'style', 'fashion week'
        ]
        
        # Your specific publication sources
        self.target_sources = {
            # UK Newspapers & Luxury
            'The Guardian': {
                'base_url': 'https://www.theguardian.com/fashion/womens-jewellery',
                'rss_feed': 'https://www.theguardian.com/fashion/womens-jewellery/rss'
            },
            'The Telegraph': {
                'base_url': 'https://www.telegraph.co.uk/luxury/',
                'rss_feed': 'https://www.telegraph.co.uk/luxury/rss'
            },
            'Evening Standard': {
                'base_url': 'https://www.standard.co.uk/shopping/esbest/fashion/jewellery',
                'rss_feed': None  # Will use sitemap/scraping
            },
            'The Times': {
                'base_url': 'https://www.thetimes.com/life-style/luxury',
                'rss_feed': None  # Subscription based
            },
            'Financial Times': {
                'base_url': 'https://www.ft.com/fashion',
                'rss_feed': 'https://www.ft.com/rss/fashion'
            },
            
            # Business Publications
            'Forbes': {
                'base_url': 'https://www.forbes.com/business/',
                'rss_feed': 'https://www.forbes.com/business/feed/'
            },
            'Business of Fashion': {
                'base_url': 'https://www.businessoffashion.com/',
                'rss_feed': 'https://www.businessoffashion.com/feed/'
            },
            'Vogue Business': {
                'base_url': 'https://www.voguebusiness.com/',
                'rss_feed': 'https://www.voguebusiness.com/feed'
            },
            
            # Fashion & Lifestyle
            'Harper\'s Bazaar UK': {
                'base_url': 'https://www.harpersbazaar.com/uk/',
                'rss_feed': 'https://www.harpersbazaar.com/uk/rss/'
            },
            'Vogue UK': {
                'base_url': 'https://www.vogue.co.uk/',
                'rss_feed': 'https://www.vogue.co.uk/rss'
            },
            'Vanity Fair': {
                'base_url': 'https://www.vanityfair.com/',
                'rss_feed': 'https://www.vanityfair.com/feed/rss'
            },
            'Tatler': {
                'base_url': 'https://www.tatler.com/',
                'rss_feed': 'https://www.tatler.com/rss'
            },
            'Red Online': {
                'base_url': 'https://www.redonline.co.uk/',
                'rss_feed': 'https://www.redonline.co.uk/rss'
            },
            'Town & Country': {
                'base_url': 'https://www.townandcountrymag.com/style/',
                'rss_feed': 'https://www.townandcountrymag.com/rss/all.xml/'
            },
            'StyleCaster': {
                'base_url': 'https://stylecaster.com/c/fashion/',
                'rss_feed': 'https://stylecaster.com/feed/'
            },
            'The Handbook': {
                'base_url': 'https://www.thehandbook.com/',
                'rss_feed': None
            },
            'Something About Rocks': {
                'base_url': 'https://somethingaboutrocks.com/',
                'rss_feed': 'https://somethingaboutrocks.com/feed/'
            },
            'The Cut': {
                'base_url': 'https://www.thecut.com/',
                'rss_feed': 'https://www.thecut.com/rss/index.xml'
            },
            'The Jewels Club': {
                'base_url': 'https://thejewels.club/',
                'rss_feed': None
            },
            
            # Industry Publications
            'Retail Jeweller': {
                'base_url': 'https://www.retail-jeweller.com/',
                'rss_feed': 'https://www.retail-jeweller.com/feed/'
            },
            'Professional Jeweller': {
                'base_url': 'https://www.professionaljeweller.com/',
                'rss_feed': 'https://www.professionaljeweller.com/feed/'
            },
            'Rapaport': {
                'base_url': 'https://rapaport.com/',
                'rss_feed': 'https://rapaport.com/rss/'
            },
            'National Jeweler': {
                'base_url': 'https://nationaljeweler.com/',
                'rss_feed': 'https://nationaljeweler.com/rss.xml'
            }
        }
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
    def calculate_relevance_score(self, title: str, content: str) -> tuple:
        """Calculate relevance score based on your custom keywords"""
        combined_text = f"{title} {content}".lower()
        found_keywords = []
        score = 0.0
        
        for keyword in self.luxury_keywords:
            if keyword.lower() in combined_text:
                found_keywords.append(keyword)
                
                # Custom scoring based on your priorities (case-insensitive)
                if keyword.lower() in ['luxury', 'jewellery', 'fine jewellery', 'craftsmanship']:
                    score += 4.0  # Your core priority keywords
                elif keyword.lower() in ['jewelry', 'diamond', 'engagement ring']:
                    score += 3.0  # Core jewelry terms
                elif keyword.lower() in ['fashion', 'collection', 'launch']:
                    score += 2.5  # Important luxury terms
                elif keyword.lower() in ['cartier', 'tiffany', 'bulgari', 'chanel']:
                    score += 3.5  # Premium brands
                elif keyword.lower() in ['red carpet', 'celebrity', 'fashion week']:
                    score += 2.0  # High-profile events
                else:
                    score += 1.0  # General relevant terms
        
        # Bonus for multiple keyword matches
        if len(found_keywords) > 2:
            score *= 1.2
        if len(found_keywords) > 4:
            score *= 1.4
            
        return score, found_keywords
    
    def try_rss_feed(self, publication: str, feed_url: str) -> List[ArticleCandidate]:
        """Try to fetch articles from RSS feed"""
        candidates = []
        
        if not feed_url:
            return candidates
            
        try:
            print(f"  📡 Trying RSS feed for {publication}...")
            
            response = self.session.get(feed_url, timeout=10)
            if response.status_code == 200:
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:20]:  # Limit to recent entries
                    try:
                        # Parse date
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        else:
                            pub_date = datetime.now()
                        
                        # Skip very old articles
                        if (datetime.now() - pub_date).days > 30:
                            continue
                        
                        title = entry.get('title', '').strip()
                        summary = entry.get('summary', '').strip()
                        url = entry.get('link', '').strip()
                        
                        if not title or not url:
                            continue
                        
                        # Quick relevance check
                        score, keywords = self.calculate_relevance_score(title, summary)
                        
                        if score >= 1.0:  # Minimum relevance threshold
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
                
                print(f"    ✅ Found {len(candidates)} relevant articles from RSS")
                
        except Exception as e:
            print(f"    ⚠️  RSS failed: {e}")
        
        return candidates
    
    def scrape_publication_homepage(self, publication: str, base_url: str) -> List[ArticleCandidate]:
        """Scrape homepage/section page for article links"""
        candidates = []
        
        try:
            print(f"  🕷️  Scraping homepage for {publication}...")
            
            response = self.session.get(base_url, timeout=15)
            if response.status_code != 200:
                print(f"    ❌ HTTP {response.status_code}")
                return candidates
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find article links (common patterns)
            article_links = set()
            
            # Look for common article link patterns
            link_selectors = [
                'a[href*="/article"]',
                'a[href*="/news"]', 
                'a[href*="/fashion"]',
                'a[href*="/style"]',
                'a[href*="/jewelry"]',
                'a[href*="/luxury"]',
                '.article-link a',
                '.headline a',
                'h2 a', 'h3 a',
                '[class*="headline"] a',
                '[class*="article"] a'
            ]
            
            for selector in link_selectors:
                links = soup.select(selector)
                for link in links[:10]:  # Limit per selector
                    href = link.get('href')
                    if href:
                        # Convert relative URLs to absolute
                        if href.startswith('/'):
                            href = urljoin(base_url, href)
                        
                        if href.startswith('http') and len(href) > 20:
                            article_links.add(href)
            
            # Quick relevance check on titles
            for url in list(article_links)[:15]:  # Limit total links
                try:
                    title_elem = soup.find('a', href=url.replace(base_url, ''))
                    title = title_elem.get_text().strip() if title_elem else ""
                    
                    if title:
                        score, keywords = self.calculate_relevance_score(title, "")
                        
                        if score >= 0.5:  # Lower threshold for homepage scraping
                            candidate = ArticleCandidate(
                                title=title,
                                url=url,
                                publication=publication,
                                published_date=datetime.now(),
                                summary="",
                                relevance_score=score,
                                keywords_found=keywords
                            )
                            candidates.append(candidate)
                            
                except Exception:
                    continue
            
            print(f"    ✅ Found {len(candidates)} potential articles from scraping")
            
        except Exception as e:
            print(f"    ❌ Scraping failed: {e}")
        
        return candidates
    
    def collect_from_source(self, publication: str, source_info: dict) -> List[ArticleCandidate]:
        """Collect articles from a single source using multiple methods"""
        all_candidates = []
        
        print(f"\n📰 Collecting from {publication}")
        
        # Method 1: Try RSS feed first
        if source_info.get('rss_feed'):
            rss_candidates = self.try_rss_feed(publication, source_info['rss_feed'])
            all_candidates.extend(rss_candidates)
        
        # Method 2: Scrape homepage if RSS failed or yielded few results
        if len(all_candidates) < 3:
            scrape_candidates = self.scrape_publication_homepage(publication, source_info['base_url'])
            all_candidates.extend(scrape_candidates)
        
        # Remove duplicates
        unique_candidates = []
        seen_urls = set()
        for candidate in all_candidates:
            if candidate.url not in seen_urls:
                unique_candidates.append(candidate)
                seen_urls.add(candidate.url)
        
        print(f"  📊 Total unique articles: {len(unique_candidates)}")
        return unique_candidates
    
    def extract_full_content(self, candidate: ArticleCandidate) -> ArticleCandidate:
        """Extract full article content and enhance relevance scoring"""
        try:
            print(f"    📖 {candidate.title[:60]}...")
            
            article = Article(candidate.url)
            article.download()
            article.parse()
            
            if not article.text or len(article.text) < 150:
                print(f"    ⚠️  Content too short")
                return None
            
            candidate.full_content = article.text
            
            # Enhanced relevance scoring with full content
            full_score, full_keywords = self.calculate_relevance_score(
                candidate.title, article.text
            )
            
            candidate.relevance_score = full_score
            candidate.keywords_found = full_keywords
            
            # Extract author
            if article.authors:
                candidate.author = article.authors[0]
            else:
                author_match = re.search(r'\b[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', article.text[:800])
                if author_match:
                    candidate.author = author_match.group(1)
            
            # Update summary if better one available
            if article.meta_description and len(article.meta_description) > len(candidate.summary):
                candidate.summary = article.meta_description
            
            print(f"    ✅ Score: {full_score:.1f} | Keywords: {len(full_keywords)} | Author: {candidate.author}")
            return candidate
            
        except Exception as e:
            print(f"    ❌ Content extraction failed: {e}")
            return None
    
    def collect_trending_articles(self, max_articles: int = 25, sources_subset: List[str] = None) -> List[ArticleCandidate]:
        """
        Main method to collect articles from your specified sources
        """
        print("🚀 Starting Custom Article Collection")
        print("=" * 60)
        
        # Use subset of sources if specified, otherwise use all
        sources_to_use = sources_subset if sources_subset else list(self.target_sources.keys())
        
        print(f"📊 Targeting {len(sources_to_use)} publications")
        
        all_candidates = []
        
        # Collect from each source
        for publication in sources_to_use:
            if publication in self.target_sources:
                source_candidates = self.collect_from_source(
                    publication, 
                    self.target_sources[publication]
                )
                all_candidates.extend(source_candidates)
                
                # Rate limiting between sources
                time.sleep(2)
        
        if not all_candidates:
            print("❌ No candidates found across all sources")
            return []
        
        print(f"\n📈 INITIAL COLLECTION COMPLETE")
        print(f"Total candidates found: {len(all_candidates)}")
        
        # Sort by relevance and take top candidates for full analysis
        all_candidates.sort(key=lambda x: x.relevance_score, reverse=True)
        top_candidates = all_candidates[:max_articles * 2]  # Get extras
        
        print(f"\n🔍 ANALYZING FULL CONTENT")
        print(f"Processing top {len(top_candidates)} candidates...")
        
        final_articles = []
        for candidate in top_candidates:
            enhanced = self.extract_full_content(candidate)
            if enhanced and enhanced.relevance_score >= 1.5:  # Final threshold
                final_articles.append(enhanced)
            
            time.sleep(1.5)  # Respectful rate limiting
            
            if len(final_articles) >= max_articles:
                break
        
        final_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        print(f"\n🎯 COLLECTION COMPLETE")
        print(f"Final articles: {len(final_articles)}")
        
        return final_articles
    
    def generate_collection_report(self, articles: List[ArticleCandidate]) -> str:
        """Generate detailed collection report"""
        if not articles:
            return "❌ No articles collected"
        
        report = []
        report.append("📊 CUSTOM ARTICLE COLLECTION REPORT")
        report.append("=" * 60)
        report.append(f"📈 Total Articles: {len(articles)}")
        report.append(f"🎯 Average Relevance: {sum(a.relevance_score for a in articles) / len(articles):.1f}")
        
        # Publication breakdown
        pub_counts = {}
        for article in articles:
            pub_counts[article.publication] = pub_counts.get(article.publication, 0) + 1
        
        report.append(f"\n📰 ARTICLES BY PUBLICATION:")
        for pub, count in sorted(pub_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  • {pub}: {count} articles")
        
        # Top keywords
        all_keywords = []
        for article in articles:
            all_keywords.extend(article.keywords_found or [])
        
        keyword_counts = {}
        for keyword in all_keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        report.append(f"\n🏷️ TOP KEYWORDS:")
        for keyword, count in sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:15]:
            report.append(f"  • {keyword}: {count} mentions")
        
        report.append(f"\n🔝 COLLECTED ARTICLES:")
        for i, article in enumerate(articles, 1):
            report.append(f"\n{i:2d}. {article.title}")
            report.append(f"    📰 {article.publication} | 👤 {article.author}")
            report.append(f"    🎯 Relevance: {article.relevance_score:.1f}")
            report.append(f"    📅 {article.published_date.strftime('%Y-%m-%d %H:%M')}")
            report.append(f"    🏷️ Keywords: {', '.join((article.keywords_found or [])[:4])}")
            report.append(f"    📝 Content: {len(article.full_content)} chars")
            report.append(f"    🔗 {article.url}")
        
        return "\n".join(report)
    
    def save_results(self, articles: List[ArticleCandidate], filename: str = "custom_collected_articles.json"):
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
        
        print(f"💾 Results saved to {filename}")
        return filename

def main():
    """Test the custom collector with your sources"""
    print("🎯 Custom Article Collector for Luxury/Fashion Publications")
    print("=" * 60)
    
    collector = CustomArticleCollector()
    
    # Show available sources
    print(f"\n📰 Available Sources ({len(collector.target_sources)}):")
    for i, pub in enumerate(collector.target_sources.keys(), 1):
        print(f"{i:2d}. {pub}")
    
    # Get user preferences
    try:
        max_articles = int(input(f"\nHow many articles to collect? (default: 20): ") or "20")
        
        use_subset = input("Use specific sources only? (y/N): ").lower().startswith('y')
        sources_subset = None
        
        if use_subset:
            source_names = input("Enter source numbers (comma-separated, e.g., 1,3,5): ")
            if source_names.strip():
                indices = [int(x.strip()) - 1 for x in source_names.split(',')]
                sources_list = list(collector.target_sources.keys())
                sources_subset = [sources_list[i] for i in indices if 0 <= i < len(sources_list)]
                print(f"Using sources: {', '.join(sources_subset)}")
        
    except (ValueError, KeyboardInterrupt):
        max_articles = 20
        sources_subset = None
        print("Using default settings...")
    
    # Run collection
    articles = collector.collect_trending_articles(
        max_articles=max_articles,
        sources_subset=sources_subset
    )
    
    # Generate report
    report = collector.generate_collection_report(articles)
    print(f"\n{report}")
    
    # Save results
    if articles:
        filename = collector.save_results(articles)
        print(f"\n✅ Collection complete! {len(articles)} articles ready for summarization.")
        print(f"📁 Data saved to: {filename}")
        
        # Quick integration test
        print(f"\n🔗 Integration Preview:")
        print(f"Articles are ready to feed into your BART summarizer!")
        for i, article in enumerate(articles[:3], 1):
            print(f"{i}. {article.title} ({article.publication})")
            print(f"   Content: {len(article.full_content)} characters")
        
    else:
        print("\n❌ No relevant articles found. Try adjusting keywords or sources.")

if __name__ == "__main__":
    main()