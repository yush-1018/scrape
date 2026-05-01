from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ScrapedData:
    """Data extracted from a product page."""
    name: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    currency: str = "₹"
    is_available: bool = True


class BaseScraper(ABC):
    """Abstract base class for all site-specific scrapers."""

    @abstractmethod
    async def scrape(self, url: str) -> ScrapedData:
        """
        Scrape a product page and return extracted data.

        Args:
            url: The full URL of the product page.

        Returns:
            ScrapedData with name, price, image_url, currency, and is_available.

        Raises:
            Exception: If the page cannot be fetched or parsed.
        """
        pass

    @staticmethod
    def clean_price(price_text: str) -> Optional[float]:
        """
        Extract a numeric price from a text string.
        Handles formats like '₹1,299.00', '$29.99', 'Rs. 1,299', etc.
        """
        if not price_text:
            return None

        # Remove common currency symbols and whitespace
        cleaned = price_text.strip()
        for char in ["₹", "$", "€", "£", "Rs.", "Rs", "INR", ",", " ", "\u00a0"]:
            cleaned = cleaned.replace(char, "")

        # Extract the first valid number (handles cases like "1299.00 - 1599.00")
        cleaned = cleaned.split("-")[0].split("–")[0].strip()

        try:
            return float(cleaned)
        except (ValueError, TypeError):
            return None
