# 🔍 Scrapo — Smart Price Tracker

Track product prices from **Amazon**, **Flipkart**, **Blinkit**, and **Zepto**. Get price history, interactive charts, and never overpay again.

## Features

- 🔗 **Paste & Track** — Just paste a product URL and we start tracking
- 📊 **Price History Charts** — Interactive Chart.js visualizations
- 🎯 **Target Price Alerts** — Set your desired price, get highlighted when it drops
- ↻ **Auto-Refresh** — Background scheduler checks prices periodically
- 🌙 **Premium Dark UI** — Glassmorphism, animations, fully responsive

## Tech Stack

| Layer | Technology |
|:--|:--|
| Backend | FastAPI (Python) |
| Scraping (Static) | httpx + BeautifulSoup4 |
| Scraping (Dynamic) | Playwright (headless Chromium) |
| Database | SQLite + SQLAlchemy |
| Scheduler | APScheduler |
| Frontend | Vite + Vanilla JS |
| Charts | Chart.js |

## Quick Start

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000` with Swagger docs at `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`.

## API Endpoints

| Method | Endpoint | Description |
|:--|:--|:--|
| `GET` | `/api/products/` | List all tracked products |
| `POST` | `/api/products/` | Add new product to track |
| `GET` | `/api/products/{id}` | Product detail + price history |
| `DELETE` | `/api/products/{id}` | Stop tracking a product |
| `POST` | `/api/products/{id}/refresh` | Manually refresh price |

## Configuration

Edit `backend/.env`:

```
DATABASE_URL=sqlite:///./price_tracker.db
SCRAPE_INTERVAL_MINUTES=30
FRONTEND_URL=http://localhost:5173
```

## Project Structure

```
price-tracker/
├── backend/
│   ├── app/
│   │   ├── config/       # Pydantic settings
│   │   ├── models/       # SQLAlchemy models
│   │   ├── scraper/      # Site-specific scrapers
│   │   ├── services/     # Business logic
│   │   ├── routes/       # API endpoints
│   │   ├── utils/        # Helpers (User-Agent rotation)
│   │   └── main.py       # FastAPI app
│   ├── requirements.txt
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── api.js        # API client
│   │   ├── main.js       # App entry
│   │   └── style.css     # Design system
│   └── index.html
├── scheduler/
│   └── cron.py           # APScheduler integration
└── README.md
```

## License

MIT
