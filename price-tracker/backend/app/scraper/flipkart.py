import httpx
from bs4 import BeautifulSoup
from app.scraper.base import BaseScraper, ScrapedData
from app.utils.headers import get_random_headers, random_delay
import logging

logger = logging.getLogger(__name__)


class FlipkartScraper(BaseScraper):
    """Scraper for Flipkart.com product pages."""

    PRICE_SELECTORS = [
        "div.Nx9bqj.CxhGGd",       # Current main price selector
        "div._30jeq3._16Jk6d",      # Older price selector
        "div._30jeq3",              # Fallback
        "div.Nx9bqj",              # Alternative
        "span._2I_WiA div._30jeq3",
    ]

    TITLE_SELECTORS = [
        "span.VU-ZEz",              # Current product title
        "span.B_NuCI",              # Older title selector
        "h1._9E25nV",               # Alternative
        "h1.yhB1nd span",
    ]

    IMAGE_SELECTORS = [
        "img._396cs4._2amPTt._3qGmMb",
        "img._396cs4",
        "div._3kidJX img",
        "img.DByuf4",
        "img._2r_T1I",
    ]

    async def scrape(self, url: str) -> ScrapedData:
        """Scrape product details from a Flipkart product page."""
        await random_delay(1.5, 3.5)

        headers = get_random_headers()
        async with httpx.AsyncClient(follow_redirects=True, timeout=20.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")
        data = ScrapedData()

        # Extract product name
        for selector in self.TITLE_SELECTORS:
            element = soup.select_one(selector)
            if element and element.get_text(strip=True):
                data.name = element.get_text(strip=True)[:500]
                break

        # Extract price
        for selector in self.PRICE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                price = self.clean_price(element.get_text(strip=True))
                if price and price > 0:
                    data.price = price
                    break

        # Extract product image
        for selector in self.IMAGE_SELECTORS:
            element = soup.select_one(selector)
            if element:
                img_url = element.get("src")
                if img_url and img_url.startswith("http"):
                    data.image_url = img_url
                    break

        # Detect availability
        oos_selectors = ["div._16FRp0", "div._2xQkkC"]  # Common Flipkart OOS selectors
        for selector in oos_selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True).lower()
                if "sold out" in text or "out of stock" in text or "currently unavailable" in text:
                    data.is_available = False
                    break

        # Fallback: check page text
        page_text = soup.get_text().lower()
        if "sold out" in page_text and not data.price:
            data.is_available = False

        if not data.price:
            logger.warning(f"Could not extract price from Flipkart URL: {url}")

        return data
