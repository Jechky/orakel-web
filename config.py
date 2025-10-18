# Bazaraki configuration based on site structure

BASE_URL = "https://www.bazaraki.com"
SEARCH_PATH = "/real-estate-to-rent/commercial-property/"

LOCATIONS = {
    "All Cyprus": "",
    "Limassol": "lemesos-district-limassol",
    "Nicosia": "lefkosia-district-nicosia",
    "Larnaca": "larnaka-district-larnaca",
    "Paphos": "pafos-district-paphos",
    "Famagusta": "ammochostos-district",
}

TYPES = {
    "All Types": "",
    "Offices": "type---offices/",
    "Shops": "type---shops/",
    "Restaurants": "type---restaurants/",
    "Bars/Pubs": "type---bars-pubs/",
    "Cafes": "type---cafes/",
    "Warehouse": "type---warehouses/",
    "Other": "type---other-commercial-property/"
}

SORT_OPTIONS = {
    "Newest": "newest",
    "Price Low to High": "cheapest",
    "Price High to Low": "expensive"
}

def build_url(location="", property_type="", min_price="", max_price="", 
              min_sqm="", max_sqm="", sort="newest", page=1):
    """
    Build Bazaraki URL with filters
    
    URL Structure:
    /real-estate-to-rent/commercial-property/[TYPE]/[LOCATION]/?query_params
    """
    url = BASE_URL + SEARCH_PATH
    
    # Add type to path (if selected)
    if property_type:
        url += property_type
    
    # Add location to path (if selected)
    if location:
        url += location + "/"
    
    # Build query parameters
    params = []
    if min_price:
        params.append(f"min_price={min_price}")
    if max_price:
        params.append(f"max_price={max_price}")
    if min_sqm:
        params.append(f"min_sqm={min_sqm}")
    if max_sqm:
        params.append(f"max_sqm={max_sqm}")
    if sort and sort != "newest":
        params.append(f"ordering={sort}")
    if page > 1:
        params.append(f"page={page}")
    
    if params:
        url += "?" + "&".join(params)
    
    return url
