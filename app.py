from flask import Flask, render_template, jsonify, request, Response
import threading
import json
import time
import logging
import colorlog
from database import init_db, save_listing, get_all_listings, reset_status
from scraper import scrape_listings, scrape_detail
from config import LOCATIONS, TYPES, SORT_OPTIONS

app = Flask(__name__)

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

# Suppress Flask debug logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Category color helpers
def api_log(msg):
    return f"\033[93m[API]\033[0m {msg}"  # Yellow

def scrape_log(msg):
    return f"\033[96m[Scrape]\033[0m {msg}"  # Cyan

def db_log(msg):
    return f"\033[92m[Database]\033[0m {msg}"  # Green

init_db()

scraping_active = False
scraping_lock = threading.Lock()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Return filter options for frontend"""
    return jsonify({
        'locations': list(LOCATIONS.keys()),
        'types': list(TYPES.keys()),
        'sort_options': list(SORT_OPTIONS.keys())
    })

@app.route('/api/listings', methods=['GET'])
def get_listings():
    listings = get_all_listings()
    return jsonify(listings)

@app.route('/api/scrape-detail', methods=['POST'])
def scrape_detail_endpoint():
    """Scrape detailed information for a single listing"""
    data = request.json or {}
    url = data.get('url', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'URL is required'}), 400
    
    # Scrape detail (this will take 10-20 seconds)
    result = scrape_detail(url)
    
    return jsonify(result)

@app.route('/api/start-scraping', methods=['POST'])
def start_scraping():
    global scraping_active
    
    with scraping_lock:
        if scraping_active:
            return jsonify({'error': 'Scraping in progress'}), 400
        scraping_active = True
    
    data = request.json or {}
    max_pages = data.get('max_pages', 1)
    
    # Extract filters
    filters = {
        'location': LOCATIONS.get(data.get('location', 'All Cyprus'), ''),
        'type': TYPES.get(data.get('type', 'All Types'), ''),
        'min_price': data.get('min_price', ''),
        'max_price': data.get('max_price', ''),
        'min_sqm': data.get('min_sqm', ''),
        'max_sqm': data.get('max_sqm', ''),
        'sort': SORT_OPTIONS.get(data.get('sort', 'Newest'), 'newest')
    }
    
    log.info(f"Starting scrape with filters: {filters}")
    
    reset_status()
    
    thread = threading.Thread(target=background_scrape, args=(max_pages, filters))
    thread.daemon = True
    thread.start()
    
    return jsonify({'message': 'Scraping started'})

def background_scrape(max_pages, filters):
    """Background task for scraping"""
    global scraping_active
    
    new_count = 0
    updated_count = 0
    existing_count = 0
    
    try:
        for listing in scrape_listings(max_pages, filters):
            result = save_listing(listing)
            
            status = result.get('status')
            if status == 'new':
                new_count += 1
            elif status == 'updated':
                updated_count += 1
            else:
                existing_count += 1
                
            time.sleep(0.1)
            
        log.info(scrape_log(f"Complete: {new_count} new, {updated_count} updated, {existing_count} existing"))
        
    except Exception as e:
        log.error(scrape_log(f"Error: {e}"))
    finally:
        with scraping_lock:
            scraping_active = False

@app.route('/api/stream')
def stream():
    """Server-Sent Events endpoint for live updates"""
    def event_stream():
        last_count = 0
        seen_ids = set()
        
        yield f"data: {json.dumps({'type': 'connected'})}\n\n"
        
        for iteration in range(120):  # 60 seconds max
            listings = get_all_listings()
            current_count = len(listings)
            
            # Send only new listings we haven't seen yet
            if current_count > last_count:
                # Get new listings (ones not in seen_ids)
                for listing in listings:
                    listing_id = listing.get('listing_id', '')
                    if listing_id and listing_id not in seen_ids:
                        seen_ids.add(listing_id)
                        yield f"data: {json.dumps({'type': 'listing', 'data': listing})}\n\n"
                
                last_count = current_count
            
            # Check if scraping is complete
            with scraping_lock:
                if not scraping_active and current_count > 0:
                    yield f"data: {json.dumps({'type': 'complete', 'total': current_count})}\n\n"
                    break
            
            time.sleep(0.5)
    
    return Response(event_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=False, threaded=True, port=5000)
