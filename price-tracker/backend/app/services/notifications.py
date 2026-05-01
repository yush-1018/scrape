"""
Notification service — sends price alerts via Email and Telegram.

Both channels are optional — they only fire if the corresponding
environment variables are configured.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import httpx
from app.config.settings import settings

logger = logging.getLogger(__name__)


def _email_configured() -> bool:
    return bool(settings.SMTP_HOST and settings.SMTP_USER and settings.SMTP_PASSWORD)


def _telegram_configured(chat_id: Optional[str] = None) -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and (chat_id or settings.TELEGRAM_CHAT_ID))


def send_email_alert(product, old_price: float, new_price: float, recipient: str = ""):
    """Send a price drop email alert."""
    if not _email_configured():
        logger.debug("Email not configured, skipping alert")
        return

    to_addr = recipient or settings.NOTIFICATION_EMAIL or settings.SMTP_USER
    if not to_addr:
        return

    subject = f"🔍 Scrapo Alert: {product.name} dropped to ₹{new_price:,.0f}!"

    html = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; max-width: 500px; margin: 0 auto;
                background: #0d0f18; color: #e8eaed; padding: 32px; border-radius: 16px;">
        <h1 style="color: #6373ff; font-size: 20px; margin: 0 0 8px;">🔍 Scrapo Alert</h1>
        <h2 style="font-size: 18px; margin: 0 0 20px; font-weight: 600;">{product.name}</h2>

        <div style="background: rgba(52,211,153,0.12); border: 1px solid rgba(52,211,153,0.3);
                    border-radius: 12px; padding: 20px; text-align: center; margin-bottom: 20px;">
            <div style="font-size: 14px; color: #8b8fa3;">Price dropped!</div>
            <div style="font-size: 28px; font-weight: 900; color: #34d399;">₹{new_price:,.0f}</div>
            <div style="font-size: 13px; color: #8b8fa3; margin-top: 4px;">
                was ₹{old_price:,.0f} · down {((old_price - new_price) / old_price * 100):.1f}%
            </div>
        </div>

        <div style="display: flex; gap: 12px; margin-bottom: 20px;">
            <div style="flex:1; background: rgba(99,115,255,0.1); border-radius: 8px; padding: 12px; text-align: center;">
                <div style="font-size: 12px; color: #8b8fa3;">Target</div>
                <div style="font-size: 16px; font-weight: 700; color: #fbbf24;">
                    ₹{product.target_price:,.0f if product.target_price else 'N/A'}
                </div>
            </div>
            <div style="flex:1; background: rgba(99,115,255,0.1); border-radius: 8px; padding: 12px; text-align: center;">
                <div style="font-size: 12px; color: #8b8fa3;">Platform</div>
                <div style="font-size: 16px; font-weight: 700;">{product.platform.title()}</div>
            </div>
        </div>

        <a href="{product.url}" style="display: block; text-align: center; background: #6373ff;
           color: white; padding: 12px; border-radius: 8px; text-decoration: none; font-weight: 600;">
            View Product →
        </a>

        <p style="font-size: 12px; color: #5c6078; margin-top: 20px; text-align: center;">
            Sent by Scrapo Price Tracker
        </p>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_USER
    msg["To"] = to_addr
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USER, to_addr, msg.as_string())
        logger.info(f"📧 Email alert sent to {to_addr} for {product.name}")
    except Exception as e:
        logger.error(f"Failed to send email alert: {e}")


async def send_telegram_alert(product, old_price: float, new_price: float, chat_id: Optional[str] = None):
    """Send a price drop Telegram alert."""
    target_chat = chat_id or settings.TELEGRAM_CHAT_ID
    if not _telegram_configured(target_chat):
        logger.debug("Telegram not configured, skipping alert")
        return

    drop_pct = ((old_price - new_price) / old_price * 100) if old_price > 0 else 0
    target_info = f"🎯 Target: ₹{product.target_price:,.0f}" if product.target_price else ""

    message = (
        f"🔍 *Scrapo Alert*\n\n"
        f"*{product.name}*\n"
        f"📉 Price dropped *{drop_pct:.1f}%*\n\n"
        f"💰 New Price: *₹{new_price:,.0f}*\n"
        f"📊 Was: ₹{old_price:,.0f}\n"
        f"{target_info}\n"
        f"🏪 Platform: {product.platform.title()}\n\n"
        f"[View Product]({product.url})"
    )

    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target_chat,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info(f"📱 Telegram alert sent for {product.name}")
            else:
                logger.error(f"Telegram API error: {resp.status_code} — {resp.text}")
    except Exception as e:
        logger.error(f"Failed to send Telegram alert: {e}")


async def check_and_notify(product, old_price: Optional[float], new_price: float):
    """
    Check if a notification should be sent (price dropped below target)
    and dispatch to all configured channels.
    """
    if not old_price or not new_price:
        return

    # Only notify on price drops
    if new_price >= old_price:
        return

    should_notify = False

    # Notify if target price is hit
    if product.target_price and new_price <= product.target_price and old_price > product.target_price:
        should_notify = True

    # Also notify on significant drops (> 5%)
    drop_pct = ((old_price - new_price) / old_price * 100)
    if drop_pct >= 5:
        should_notify = True

    if not should_notify:
        return

    logger.info(f"🔔 Price alert triggered for {product.name}: ₹{old_price} → ₹{new_price}")

    # Get user email for per-user notifications
    user_email = ""
    user_telegram = None
    if product.owner:
        user_email = product.owner.email
        user_telegram = product.owner.telegram_chat_id

    # Send email
    try:
        send_email_alert(product, old_price, new_price, recipient=user_email)
    except Exception as e:
        logger.error(f"Email notification failed: {e}")

    # Send Telegram
    try:
        await send_telegram_alert(product, old_price, new_price, chat_id=user_telegram)
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
