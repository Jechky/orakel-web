import sqlite3
import hashlib
import logging
from typing import Dict, List

log = logging.getLogger(__name__)
DB_PATH = "orakel.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT UNIQUE NOT NULL,
            hash TEXT NOT NULL,
            title TEXT,
            price REAL,
            sqm TEXT,
            price_per_sqm REAL,
            place TEXT,
            posted TEXT,
            link TEXT,
            image TEXT,
            status TEXT DEFAULT 'existing',
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def compute_hash(listing: Dict) -> str:
    data = f"{listing.get('title', '')}{listing.get('price', '')}{listing.get('place', '')}"
    return hashlib.md5(data.encode()).hexdigest()

def save_listing(listing: Dict) -> Dict:
    """Save or update listing using listing_id, return status: new, updated, or existing"""
    conn = get_connection()
    listing_hash = compute_hash(listing)
    listing_id = listing.get('listing_id', '')
    
    if not listing_id:
        conn.close()
        return {**listing, 'status': 'error'}
    
    # Check if exists by listing_id
    existing = conn.execute("SELECT * FROM listings WHERE listing_id = ?", (listing_id,)).fetchone()
    
    if not existing:
        # New listing
        conn.execute("""
            INSERT INTO listings (listing_id, hash, title, price, sqm, price_per_sqm, place, posted, link, image, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'new')
        """, (
            listing_id,
            listing_hash,
            listing.get('title', ''),
            listing.get('price', 0),
            listing.get('sqm', ''),
            listing.get('price_per_sqm', 0),
            listing.get('place', ''),
            listing.get('posted', ''),
            listing.get('link', ''),
            listing.get('image', '')
        ))
        conn.commit()
        conn.close()
        return {**listing, 'status': 'new', 'hash': listing_hash}
    
    # Check if updated
    if existing['hash'] != listing_hash:
        conn.execute("""
            UPDATE listings 
            SET hash = ?, title = ?, price = ?, sqm = ?, price_per_sqm = ?, place = ?, posted = ?, 
                link = ?, image = ?, status = 'updated', last_seen = CURRENT_TIMESTAMP
            WHERE listing_id = ?
        """, (
            listing_hash,
            listing.get('title', ''),
            listing.get('price', 0),
            listing.get('sqm', ''),
            listing.get('price_per_sqm', 0),
            listing.get('place', ''),
            listing.get('posted', ''),
            listing.get('link', ''),
            listing.get('image', ''),
            listing_id
        ))
        conn.commit()
        conn.close()
        return {**listing, 'status': 'updated', 'hash': listing_hash}
    
    # Existing, just update last_seen
    conn.execute("UPDATE listings SET last_seen = CURRENT_TIMESTAMP WHERE listing_id = ?", (listing_id,))
    conn.commit()
    conn.close()
    return {**listing, 'status': 'existing', 'hash': listing_hash}

def get_all_listings() -> List[Dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM listings ORDER BY last_seen DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]

def reset_status():
    conn = get_connection()
    conn.execute("UPDATE listings SET status = 'existing'")
    conn.commit()
    conn.close()
