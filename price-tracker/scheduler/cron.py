"""
Scheduler module — integrates APScheduler with the FastAPI application
to periodically refresh all tracked product prices.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.models.database import SessionLocal
from app.services.product_service import refresh_all_prices
from app.config.settings import settings

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def scheduled_refresh_job():
    """Job that runs on schedule to refresh all product prices."""
    logger.info("⏰ Scheduled price refresh triggered")
    db = SessionLocal()
    try:
        await refresh_all_prices(db)
    except Exception as e:
        logger.error(f"Scheduled refresh failed: {e}")
    finally:
        db.close()


def start_scheduler():
    """Start the background price-check scheduler."""
    interval_minutes = settings.SCRAPE_INTERVAL_MINUTES

    scheduler.add_job(
        scheduled_refresh_job,
        trigger=IntervalTrigger(minutes=interval_minutes),
        id="price_refresh",
        name=f"Refresh prices every {interval_minutes} minutes",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(f"🚀 Scheduler started — refreshing every {interval_minutes} minutes")


def stop_scheduler():
    """Gracefully stop the scheduler."""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")
