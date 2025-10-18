# Orakel Live Scraper - Bazaraki Edition

Live scraping of Bazaraki commercial properties with full filtering support.

## Features

✅ **Live Scraping** - Watch listings appear in real-time
✅ **Full Filter Support** - Location, Type, Price, Sqm, Sort
✅ **Multi-Page** - Scrape up to 10 pages
✅ **Stealth Mode** - Bypass bot detection
✅ **Duplicate Prevention** - Uses listing ID (no duplicates)
✅ **Price per sqm** - Automatic calculation (€/sqm column)
✅ **Change Detection** - See new/updated listings
✅ **Detail Modal** - Click "View" for detailed info:
   - 📸 All property images
   - 📞 Phone number (auto-extracted)
   - 💬 WhatsApp link
   - 📅 Posted date/time

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

**Note:** Logs are color-coded for easy reading:
- `[INFO]` = Green, `[WARNING]` = Yellow, `[ERROR]` = Red
- `[Scrape]` = Cyan, `[Detail]` = Magenta, `[Database]` = Green

## Run

```bash
python app.py
```

Open: http://localhost:5000

## Filters

- **Location**: All Cyprus, Limassol, Nicosia, Larnaca, Paphos, Famagusta
- **Type**: All Types, Offices, Shops, Restaurants, Bars/Pubs, Cafes, Warehouse, Other
- **Sort**: Newest, Price Low to High, Price High to Low
- **Price Range**: Min/Max in Euros
- **Area Range**: Min/Max in Sqm
- **Pages**: 1-10 pages

## How It Works

1. Select your filters
2. Click "Start Scraping"
3. Watch listings appear live (30-60 seconds per page)
4. Green = New, Yellow = Updated

## Notes

- API key embedded (no setup needed)
- Stealth mode enabled (anti-bot)
- Standard mode (accurate results)
- Headless browser (runs in background)
