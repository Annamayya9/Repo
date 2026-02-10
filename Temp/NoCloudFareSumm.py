from newspaper import Article
from transformers import pipeline
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse
import re
import json
from bs4 import BeautifulSoup

#Fixed author extraction to use JSON-LD and meta tags more effectively
#Summary includes correct data. 

@dataclass
class ArticleSummary:
    title: str
    author: str
    summary: str
    url: str
    publication: str
    topics: List[str] = None

class ArticleSummarizer:
    def __init__(self, model: str = "facebook/bart-large-cnn"):
        """Initialize the summarizer with BART CNN model"""
        print(f"Loading model: {model} ... this may take a moment.")
        self.summarizer = pipeline("summarization", model=model)

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
            print(f"❌ Error summarizing article {article_url}: {e}")
            return None


def extract_publication_name(url: str) -> str:
    domain = urlparse(url).netloc.replace("www.", "").split(".")[0]
    return domain.title()


###def extract_author(article: Article, content: str) -> str:
    """Try multiple strategies to get the author (only first match)"""
    # Try newspaper3k first
    if article.authors:
        return article.authors[0]  # only first author

    # Regex fallback — stop at the first match only
    patterns = [
        r"\b[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"\b[Ww]ritten\s+by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
        r"\b[Aa]uthor:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, content[:500])  # only scan first 500 chars
        if match:
            return match.group(1)

    return "Unknown"###


###def extract_author(article: Article, text: str) -> str:
    """Extract author using newspaper3k primarily, fallback to regex if needed."""
    # First, trust newspaper3k's built-in author detection
    if article.authors and len(article.authors) > 0:
        return article.authors[0]

    # Fallback: look for "By ..." in the article text
    match = re.search(r"\b[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", article.text)
    if match:
        return match.group(1)

    return "Unknown"
###


def extract_author(article: Article, text: str) -> str:
    """Extract author name using JSON-LD, meta tags, or regex scanning."""
    author = None

    # 1. Try JSON-LD parsing
    try:
        soup = BeautifulSoup(article.html, "html.parser")
        scripts = soup.find_all("script", type="application/ld+json")
        for script in scripts:
            try:
                data = json.loads(script.string)
                # Handle case where JSON-LD contains list of dicts
                if isinstance(data, list):
                    for entry in data:
                        if isinstance(entry, dict) and "author" in entry:
                            author = _get_author_from_jsonld(entry["author"])
                            if author:
                                return author
                elif isinstance(data, dict) and "author" in data:
                    author = _get_author_from_jsonld(data["author"])
                    if author:
                        return author
            except Exception:
                continue
    except Exception:
        pass

    # 2. Fallback: use newspaper3k's authors field
    if article.authors:
        return article.authors[0]

    # 3. Regex scan of title, meta description, and body text
    combined_text = " ".join([
        article.title or "",
        getattr(article, "meta_description", "") or "",
        article.text or ""
    ])

    match = re.search(r"\b[Bb]y\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", combined_text)
    if match:
        return match.group(1)

    return "Unknown"


def _get_author_from_jsonld(author_field):
    """Helper to safely parse author name(s) from JSON-LD structures."""
    if isinstance(author_field, dict) and "name" in author_field:
        return author_field["name"]
    elif isinstance(author_field, list):
        for entry in author_field:
            if isinstance(entry, dict) and "name" in entry:
                return entry["name"]
    return None


def main():
    print("=== Luxury-Focused Article Summarizer (BART CNN) ===")

    url = input("Enter article URL: ").strip()
    if not url:
        print("⚠️ URL required!")
        return

    # Extract article
    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        print(f"❌ Error extracting article: {e}")
        return

    # Extract author separately
    author = extract_author(article, article.text)

    summarizer = ArticleSummarizer("facebook/bart-large-cnn")
    summary = summarizer.summarize_article(
        article.text,
        url,
        extract_publication_name(url),
        article.title,
        author
    )

    if not summary:
        print("❌ No summary generated.")
        return

    # Structured output (each field on its own line)
    print("\n✅ SUMMARY RESULT:")
    print(f"Title       : {summary.title}")
    print(f"Author      : {summary.author}")
    print(f"Summary     : {summary.summary}")
    print(f"Link        : {summary.url}")
    print(f"Publication : {summary.publication}")


if __name__ == "__main__":
    main()
