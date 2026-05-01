import httpx
from bs4 import BeautifulSoup
from app.scraper.base import BaseScraper, ScrapedData
from app.utils.headers import get_random_headers, random_delay
import logging

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    """Scraper for Amazon.in / Amazon.com product pages."""

    # Multiple selector fallbacks — Amazon changes their DOM frequently
    PRICE_SELECTORS = [
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "span.a-price span.a-offscreen",
        "#corePrice_feature_div span.a-offscreen",
        "#corePriceDisplay_desktop_feature_div span.a-offscreen",
        "span.priceToPay span.a-offscreen",
        "#apex_offerDisplay_desktop span.a-offscreen",
        ".a-price .a-offscreen",
    ]

    TITLE_SELECTORS = [
        "#productTitle",
        "#title span",
        "h1.a-size-large span",
    ]

    IMAGE_SELECTORS = [
        "#landingImage",
        "#imgBlkFront",
        "#main-image-container img",
        "#imageBlock img",
    ]

    async def scrape(self, url: str) -> ScrapedData:
        """Scrape product details from an Amazon product page."""
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
                img_url = element.get("src") or element.get("data-old-hires") or element.get("data-a-dynamic-image", "")
                if img_url and img_url.startswith("http"):
                    data.image_url = img_url
                    break

        # Detect availability
        oos_indicators = [
            "#availability",
            "#outOfStock",
            "#availabilityInsideBuyBox_feature_div",
        ]
        for selector in oos_indicators:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True).lower()
                if "unavailable" in text or "out of stock" in text or "currently unavailable" in text:
                    data.is_available = False
                    break

        # Also check: if no price found AND no add-to-cart, likely OOS
        if not data.price:
            add_to_cart = soup.select_one("#add-to-cart-button, #addToCart")
            if not add_to_cart:
                data.is_available = False
            logger.warning(f"Could not extract price from Amazon URL: {url}")

        return data
