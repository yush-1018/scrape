from urllib.parse import urlparse
from app.scraper.base import BaseScraper
from app.scraper.amazon import AmazonScraper
from app.scraper.flipkart import FlipkartScraper
from app.scraper.blinkit import BlinkitScraper
from app.scraper.zepto import ZeptoScraper


def detect_platform(url: str) -> str:
    """
    Detect the e-commerce platform from a product URL.

    Returns:
        Platform identifier string: "amazon", "flipkart", "blinkit", "zepto", or "unknown"
    """
    parsed = urlparse(url)
    domain = parsed.netloc.lower()

    if "amazon" in domain:
        return "amazon"
    elif "flipkart" in domain:
        return "flipkart"
    elif "blinkit" in domain:
        return "blinkit"
    elif "zepto" in domain or "zeptonow" in domain:
        return "zepto"
    else:
        return "unknown"


def get_scraper(url: str) -> BaseScraper:
    """
    Factory function that returns the appropriate scraper for a given URL.

    Args:
        url: The product page URL.

    Returns:
        An instance of the appropriate scraper.

    Raises:
        ValueError: If the platform is not supported.
    """
    platform = detect_platform(url)

    scrapers = {
        "amazon": AmazonScraper,
        "flipkart": FlipkartScraper,
        "blinkit": BlinkitScraper,
        "zepto": ZeptoScraper,
    }

    scraper_class = scrapers.get(platform)
    if not scraper_class:
        supported = ", ".join(scrapers.keys())
        raise ValueError(
            f"Unsupported platform: '{platform}'. "
            f"Supported platforms: {supported}"
        )

    return scraper_class()
