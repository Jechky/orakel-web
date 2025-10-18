import logging
import os
import agentql
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from typing import Generator, Dict
from config import build_url
import colorlog

# Professional colored logging
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    '%(asctime)s %(log_color)s[%(levelname)s]%(reset)s %(message)s',
    datefmt='%H:%M:%S',
    log_colors={
        'DEBUG': 'cyan',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'red',
        'CRITICAL': 'red,bg_white',
    }
))

log = colorlog.getLogger(__name__)
log.addHandler(handler)
log.setLevel(logging.INFO)

# Suppress verbose library logs
logging.getLogger('agentql').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('asyncio').setLevel(logging.WARNING)

# Category color helpers
def scrape_log(msg):
    return f"\033[96m[Scrape]\033[0m {msg}"  # Cyan

def detail_log(msg):
    return f"\033[95m[Detail]\033[0m {msg}"  # Magenta

def db_log(msg):
    return f"\033[92m[Database]\033[0m {msg}"  # Green

# API Key is hardcoded
os.environ['AGENTQL_API_KEY'] = 'Z5kazMYQN6ekQlyFNzAe2dCv2LMvLrsmJtLhpVjUJuzpJYyqsK7NiQ'

# Query with id for unique identification and numeric price
QUERY = """
{
  listing[] {
    id
    title
    price(Euro)
    sqm
    image
    place
    posted
    link
  }
}
"""

def scrape_listings(max_pages: int = 1, filters: Dict = None) -> Generator[Dict, None, None]:
    """Scrape listings using AgentQL with optional filters"""
    
    if filters is None:
        filters = {}
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            try:
                page = agentql.wrap(browser.new_page())
                page.enable_stealth_mode()
                log.info(scrape_log(f"Starting: pages={max_pages}"))
                
                for page_num in range(1, max_pages + 1):
                    # Build URL with filters
                    url = build_url(
                        location=filters.get('location', ''),
                        property_type=filters.get('type', ''),
                        min_price=filters.get('min_price', ''),
                        max_price=filters.get('max_price', ''),
                        min_sqm=filters.get('min_sqm', ''),
                        max_sqm=filters.get('max_sqm', ''),
                        sort=filters.get('sort', 'newest'),
                        page=page_num
                    )
                    
                    log.info(scrape_log(f"Page {page_num}/{max_pages}"))
                    
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=60000)
                        page.wait_for_timeout(5000)
                        
                        # Query with AgentQL in STANDARD mode
                        response = page.query_data(QUERY, mode="standard")
                        
                        # Parse response
                        if response and 'listing' in response:
                            listings = response['listing']
                            log.info(scrape_log(f"Page {page_num}/{max_pages} - Found {len(listings)} listings"))
                            
                            for listing in listings:
                                # Calculate price per sqm
                                price = listing.get('price', 0)
                                sqm_str = str(listing.get('sqm', '0'))
                                try:
                                    sqm = float(sqm_str) if sqm_str else 0
                                    price_per_sqm = round(price / sqm, 2) if sqm > 0 else 0
                                except (ValueError, ZeroDivisionError):
                                    price_per_sqm = 0
                                
                                result = {
                                    'listing_id': str(listing.get('id', '')),
                                    'title': str(listing.get('title', '')),
                                    'price': price,
                                    'sqm': sqm_str,
                                    'price_per_sqm': price_per_sqm,
                                    'place': str(listing.get('place', '')),
                                    'posted': str(listing.get('posted', '')),
                                    'link': str(listing.get('link', '')),
                                    'image': str(listing.get('image', ''))
                                }
                                
                                yield result
                        else:
                            log.warning(scrape_log(f"Page {page_num}: No listings found"))
                            
                    except Exception as e:
                        log.error(f"Error on page {page_num}: {e}", exc_info=True)
                    
            finally:
                browser.close()
                
    except Exception as e:
        log.error(f"Fatal error: {e}", exc_info=True)
        raise

def scrape_detail(url: str) -> Dict:
    """Scrape detailed information from a single listing page"""
    
    # Extract listing ID from URL for logging
    listing_id = url.split('/')[-2].split('_')[0] if url and '/' in url else 'unknown'
    log.info(detail_log(f"ID {listing_id} - Fetching"))
    
    DETAIL_QUERY = """
    {
      advert {
        image_urls[]
        phone_url(tel url)
        whatsapp_url
        posted_time_and_date
      }
    }
    """
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            
            try:
                page = agentql.wrap(browser.new_page())
                page.enable_stealth_mode()
                
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                
                response = page.query_data(DETAIL_QUERY, mode="standard")
                
                if response and 'advert' in response:
                    advert = response['advert']
                    
                    # Extract phone number from tel: URL
                    phone_url = advert.get('phone_url', '')
                    phone_number = phone_url.replace('tel:', '') if phone_url else ''
                    
                    img_count = len(advert.get('image_urls', []))
                    has_phone = 'Yes' if phone_number else 'No'
                    log.info(detail_log(f"ID {listing_id} - Success: {img_count} images, phone: {has_phone}"))
                    
                    return {
                        'success': True,
                        'image_urls': advert.get('image_urls', []),
                        'phone_number': phone_number,
                        'phone_url': phone_url,
                        'whatsapp_url': advert.get('whatsapp_url', ''),
                        'posted_time': advert.get('posted_time_and_date', '')
                    }
                else:
                    return {
                        'success': False,
                        'error': 'No advert data found'
                    }
                    
            finally:
                browser.close()
                
    except Exception as e:
        log.error(f"Error scraping detail: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
