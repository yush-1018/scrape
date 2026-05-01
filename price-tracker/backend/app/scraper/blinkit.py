"""
Blinkit Scraper — Uses Playwright for JS-rendered grocery pages.

Blinkit (formerly Grofers) is fully JavaScript-rendered and location-dependent.
Static HTTP requests return empty shells, so we use headless Chromium via Playwright.

Playwright operations are routed through playwright_helper to ensure
compatibility with Windows + uvicorn (SelectorEventLoop).
"""

import logging
import re
from app.scraper.base import BaseScraper, ScrapedData
from app.scraper.playwright_helper import run_playwright_scrape

logger = logging.getLogger(__name__)


async def _blinkit_playwright_scrape(url: str) -> dict:
    """
    Standalone async function that does the actual Playwright work.
    Returns a plain dict so it's safe across threads.
    """
    from playwright.async_api import async_playwright

    result = {"name": None, "price": None, "image_url": None, "is_available": True}

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        page = await context.new_page()

        # Navigate and wait for content to render
        await page.goto(url, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)  # Extra time for lazy content

        # --- Extract product name ---
        name_selectors = [
            "h1",
            "[class*='ProductName']",
            "[class*='product-name']",
            "[class*='Name__']",
            "div[class*='ProductDescription'] h1",
        ]
        for sel in name_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    text = (await el.inner_text()).strip()
                    if text and len(text) > 2:
                        result["name"] = text[:500]
                        break
            except Exception:
                continue

        # --- Extract price ---
        price_selectors = [
            "[class*='Price__'] div",
            "[class*='ProductPrice']",
            "[class*='price']",
            "[class*='SellingPrice']",
            "div[class*='Price'] span",
        ]
        for sel in price_selectors:
            try:
                els = await page.query_selector_all(sel)
                for el in els:
                    text = (await el.inner_text()).strip()
                    price = BaseScraper.clean_price(text)
                    if price and price > 0:
                        result["price"] = price
                        break
                if result["price"]:
                    break
            except Exception:
                continue

        # Fallback: scan all text for ₹ pattern
        if not result["price"]:
            try:
                body_text = await page.inner_text("body")
                prices = re.findall(r"₹\s*([\d,]+(?:\.\d{1,2})?)", body_text)
                if prices:
                    price_val = BaseScraper.clean_price("₹" + prices[0])
                    if price_val and price_val > 0:
                        result["price"] = price_val
            except Exception:
                pass

        # --- Extract image ---
        image_selectors = [
            "[class*='ProductImage'] img",
            "[class*='product-image'] img",
            "img[class*='Product']",
            "div[class*='Carousel'] img",
            "main img",
        ]
        for sel in image_selectors:
            try:
                el = await page.query_selector(sel)
                if el:
                    src = await el.get_attribute("src")
                    if src and src.startswith("http"):
                        result["image_url"] = src
                        break
            except Exception:
                continue

        # Detect availability
        try:
            body_text = await page.inner_text("body")
            oos_keywords = ["out of stock", "sold out", "currently unavailable", "not available", "notify me"]
            if any(kw in body_text.lower() for kw in oos_keywords):
                result["is_available"] = False
        except Exception:
            pass

        await browser.close()

    return result


class BlinkitScraper(BaseScraper):
    """Scraper for Blinkit grocery product pages using Playwright."""

    async def scrape(self, url: str) -> ScrapedData:
        """Scrape product details from a Blinkit product page using headless browser."""
        data = ScrapedData()

        try:
            result = await run_playwright_scrape(_blinkit_playwright_scrape, url)
            data.name = result.get("name")
            data.price = result.get("price")
            data.image_url = result.get("image_url")
            data.is_available = result.get("is_available", True)
        except Exception as e:
            logger.error(f"Blinkit scrape failed for {url}: {e}")

        if not data.price:
            logger.warning(f"Could not extract price from Blinkit URL: {url}")

        return data
