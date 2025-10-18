const startBtn = document.getElementById('startBtn');
const statusDiv = document.getElementById('status');
const resultsBody = document.getElementById('results');
const statsDiv = document.getElementById('stats');
const maxPagesInput = document.getElementById('max_pages');

// Filter elements
const locationSelect = document.getElementById('location');
const typeSelect = document.getElementById('type');
const sortSelect = document.getElementById('sort');
const minPriceInput = document.getElementById('min_price');
const maxPriceInput = document.getElementById('max_price');
const minSqmInput = document.getElementById('min_sqm');
const maxSqmInput = document.getElementById('max_sqm');

let eventSource = null;
let stats = { total: 0, new: 0, updated: 0 };
let allListings = [];  // Store all listings for sorting
let currentSort = { column: null, direction: 'asc' };  // Track sort state

// Load config and populate dropdowns
fetch('/api/config')
    .then(r => r.json())
    .then(config => {
        // Populate locations
        config.locations.forEach(loc => {
            const option = document.createElement('option');
            option.value = loc;
            option.textContent = loc;
            locationSelect.appendChild(option);
        });
        
        // Populate types
        config.types.forEach(type => {
            const option = document.createElement('option');
            option.value = type;
            option.textContent = type;
            typeSelect.appendChild(option);
        });
        
        // Populate sort options
        config.sort_options.forEach(sort => {
            const option = document.createElement('option');
            option.value = sort;
            option.textContent = sort;
            sortSelect.appendChild(option);
        });
    });

// Load existing listings
loadExistingListings();

startBtn.addEventListener('click', startScraping);

function loadExistingListings() {
    fetch('/api/listings')
        .then(r => r.json())
        .then(listings => {
            allListings = listings;
            renderTable();
        });
}

function startScraping() {
    startBtn.disabled = true;
    statusDiv.textContent = 'Starting...';
    resultsBody.innerHTML = '';
    allListings = [];  // Clear listings array
    stats = { total: 0, new: 0, updated: 0 };
    updateStats();
    
    // Collect all filter values
    const filters = {
        max_pages: parseInt(maxPagesInput.value) || 1,
        location: locationSelect.value,
        type: typeSelect.value,
        sort: sortSelect.value,
        min_price: minPriceInput.value,
        max_price: maxPriceInput.value,
        min_sqm: minSqmInput.value,
        max_sqm: maxSqmInput.value
    };
    
    fetch('/api/start-scraping', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(filters)
    })
    .then(r => r.json())
    .then(() => {
        statusDiv.textContent = 'Scraping with filters...';
        connectSSE();
    })
    .catch(err => {
        statusDiv.textContent = 'Error: ' + err.message;
        startBtn.disabled = false;
    });
}

function connectSSE() {
    if (eventSource) eventSource.close();
    
    eventSource = new EventSource('/api/stream');
    
    eventSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        
        if (data.type === 'connected') {
            statusDiv.textContent = 'Connected. Waiting...';
        }
        else if (data.type === 'listing') {
            // Add to array for sorting later
            allListings.unshift(data.data);
            
            // Also add to table immediately for live effect
            addListingToTableLive(data.data);
            
            statusDiv.textContent = `Scraping... Found ${allListings.length} listings`;
        }
        else if (data.type === 'complete') {
            statusDiv.textContent = `Complete! Found ${allListings.length} listings`;
            eventSource.close();
            startBtn.disabled = false;
        }
    };
    
    eventSource.onerror = function() {
        statusDiv.textContent = 'Connection error';
        eventSource.close();
        startBtn.disabled = false;
    };
}

function renderTable() {
    resultsBody.innerHTML = '';
    stats = { total: 0, new: 0, updated: 0 };
    
    allListings.forEach(listing => {
        const row = createListingRow(listing);
        resultsBody.appendChild(row);
        
        stats.total++;
        if (listing.status === 'new') stats.new++;
        if (listing.status === 'updated') stats.updated++;
    });
    
    updateStats();
    updateSortIndicators();
}

function addListingToTableLive(listing) {
    // Add single listing to top of table (for live updates)
    const row = createListingRow(listing);
    resultsBody.insertBefore(row, resultsBody.firstChild);
    
    stats.total++;
    if (listing.status === 'new') stats.new++;
    if (listing.status === 'updated') stats.updated++;
    updateStats();
}

function createListingRow(listing) {
    const row = document.createElement('tr');
    row.className = listing.status || 'existing';
    
    // Format price per sqm
    const pricePerSqm = listing.price_per_sqm ? `€${listing.price_per_sqm}` : '-';
    
    row.innerHTML = `
        <td>${listing.status || 'existing'}</td>
        <td>${listing.title || '-'}</td>
        <td data-value="${listing.price || 0}">€${listing.price || '-'}</td>
        <td>${listing.sqm || '-'} m²</td>
        <td data-value="${listing.price_per_sqm || 0}">${pricePerSqm}</td>
        <td>${listing.place || '-'}</td>
        <td data-value="${listing.posted || ''}">${listing.posted || '-'}</td>
        <td><a href="#" class="view-btn" onclick="openModal('${listing.link}'); return false;">View</a></td>
    `;
    
    return row;
}

function sortTable(column) {
    // Toggle direction if same column, else default to ascending
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    
    // Sort the listings array
    allListings.sort((a, b) => {
        let aVal, bVal;
        
        if (column === 'price' || column === 'price_per_sqm') {
            aVal = parseFloat(a[column]) || 0;
            bVal = parseFloat(b[column]) || 0;
        } else if (column === 'posted') {
            // Simple string comparison for posted date
            aVal = a[column] || '';
            bVal = b[column] || '';
        } else {
            aVal = a[column] || '';
            bVal = b[column] || '';
        }
        
        if (currentSort.direction === 'asc') {
            return aVal > bVal ? 1 : aVal < bVal ? -1 : 0;
        } else {
            return aVal < bVal ? 1 : aVal > bVal ? -1 : 0;
        }
    });
    
    renderTable();
}

function updateSortIndicators() {
    // Clear all indicators
    document.querySelectorAll('th span').forEach(span => span.textContent = '');
    
    // Set current indicator
    if (currentSort.column) {
        const indicator = document.getElementById(`sort-${currentSort.column}`);
        if (indicator) {
            indicator.textContent = currentSort.direction === 'asc' ? ' ▲' : ' ▼';
        }
    }
}

function updateStats() {
    statsDiv.textContent = `Total: ${stats.total} | New: ${stats.new} | Updated: ${stats.updated}`;
}

// Modal functions
function openModal(url) {
    const modal = document.getElementById('detailModal');
    const modalBody = document.getElementById('modalBody');
    
    // Show modal with loading state
    modal.classList.add('show');
    modalBody.innerHTML = '<div class="modal-loading">Loading details... This may take 10-20 seconds...</div>';
    
    // Fetch detail data
    fetch('/api/scrape-detail', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            displayDetailData(data);
        } else {
            modalBody.innerHTML = `<div class="modal-error">Error: ${data.error}</div>`;
        }
    })
    .catch(err => {
        modalBody.innerHTML = `<div class="modal-error">Error loading details: ${err.message}</div>`;
    });
}

function closeModal() {
    const modal = document.getElementById('detailModal');
    modal.classList.remove('show');
}

function displayDetailData(data) {
    const modalBody = document.getElementById('modalBody');
    
    let html = '';
    
    // Phone number
    if (data.phone_number) {
        html += `
            <div class="detail-section">
                <div class="detail-label">Phone Number</div>
                <div class="detail-value">
                    <a href="tel:${data.phone_number}">${data.phone_number}</a>
                </div>
            </div>
        `;
    }
    
    // WhatsApp
    if (data.whatsapp_url) {
        html += `
            <div class="detail-section">
                <div class="detail-label">WhatsApp</div>
                <div class="detail-value">
                    <a href="${data.whatsapp_url}" target="_blank">Open WhatsApp Chat</a>
                </div>
            </div>
        `;
    }
    
    // Posted time
    if (data.posted_time) {
        html += `
            <div class="detail-section">
                <div class="detail-label">Posted</div>
                <div class="detail-value">${data.posted_time}</div>
            </div>
        `;
    }
    
    // Images
    if (data.image_urls && data.image_urls.length > 0) {
        html += `
            <div class="detail-section">
                <div class="detail-label">Images (${data.image_urls.length})</div>
                <div class="image-gallery">
        `;
        
        data.image_urls.forEach(imgUrl => {
            html += `<img src="${imgUrl}" alt="Property" onclick="window.open('${imgUrl}', '_blank')">`;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = html;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('detailModal');
    if (event.target === modal) {
        closeModal();
    }
}
