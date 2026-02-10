from newspaper import Article
from transformers import pipeline
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlparse

@dataclass
class ArticleSummary:
    title: str
    # author: str   # Commented out for now
    summary: str
    url: str
    publication: str
    topics: List[str] = None

class ArticleSummarizer:
    def __init__(self, model: str = "facebook/bart-large-cnn"):
        """Initialize the summarizer with BART CNN model"""
        print(f"Loading model: {model} ... this may take a moment.")
        self.summarizer = pipeline("summarization", model=model)

    def summarize_article(self, article_content: str, article_url: str, publication: str) -> Optional[ArticleSummary]:
        """Summarize an article focusing on luxury brands, jewelry pieces, and celebrities"""
        try:
            # Prepend luxury-focused prompt with jewelry and celebrity emphasis
            input_text = (
                "You are a PR professional specializing in luxury brands, jewelry, and fashion. "
                "Summarize the article focusing on aspects relevant to luxury clients, trends, high-value deals, "
                "brand positioning, notable jewelry pieces mentioned, and any famous celebrities involved. "
                "Ensure that every jewelry product or celebrity referenced is included in the summary. "
                + article_content
            )

            summary_text = self.summarizer(
                input_text[:3000],  # Limit input length for model
                max_length=120,
                min_length=40,
                do_sample=False
            )[0]["summary_text"]

            return ArticleSummary(
                title="",  # Will fill in later from newspaper3k
                # author="Unknown",  # Commented out
                summary=summary_text.strip(),
                url=article_url,
                publication=publication,
                topics=[]
            )

        except Exception as e:
            print(f"❌ Error summarizing article {article_url}: {e}")
            return None

    def format_summary_output(self, summary: ArticleSummary) -> str:
        """Format summary in bullet point style"""
        if not summary:
            return ""
        hyperlinked_title = f"[{summary.title}]({summary.url})" if summary.title else summary.url
        return f"* {hyperlinked_title} - {summary.summary}"


def extract_publication_name(url: str) -> str:
    domain = urlparse(url).netloc.replace("www.", "").split(".")[0]
    return domain.title()


def main():
    print("=== Luxury-Focused Article Summarizer (BART CNN) ===")

    url = input("Enter article URL: ").strip()
    if not url:
        print("⚠️ URL required!")
        return

    # Extract article using newspaper3k
    try:
        article = Article(url)
        article.download()
        article.parse()
    except Exception as e:
        print(f"❌ Error extracting article: {e}")
        return

    summarizer = ArticleSummarizer("facebook/bart-large-cnn")
    summary = summarizer.summarize_article(article.text, url, extract_publication_name(url))
    summary.title = article.title

    print("\n✅ SUMMARY RESULT:")
    print(summarizer.format_summary_output(summary))
    print(f"Publication: {summary.publication}")


if __name__ == "__main__":
    main()
