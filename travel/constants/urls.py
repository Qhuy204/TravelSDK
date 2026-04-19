"""
API URLs and default headers for TravelSDK.
"""

# API Base URLs
PROVIDER_BASE_URL = "https://vexere.com"
PROVIDER_ROUTE_URL = "https://internal-vroute-cmc.vexere.com"
URL_RESOLVER_URL = "https://url-resolver-service.vexere.com"
VCONFIG_URL = "https://vconfiguration.vexere.com"

# Endpoints
GET_TOKEN_URL = f"{PROVIDER_BASE_URL}/getToken"
TRAIN_SEARCH_URL = f"{PROVIDER_ROUTE_URL}/v2/route/train"
TRAIN_COUNT_URL = f"{PROVIDER_ROUTE_URL}/v2/route/train/count"
BUS_SEARCH_URL = f"{PROVIDER_ROUTE_URL}/v2/route"
BUS_COUNT_URL = f"{PROVIDER_ROUTE_URL}/v2/route/count"
FLIGHT_SEARCH_URL = f"{PROVIDER_ROUTE_URL}/v2/route/flight"
FLIGHT_COUNT_URL = f"{PROVIDER_ROUTE_URL}/v2/route/flight/count"
AREA_SEARCH_URL = f"{PROVIDER_ROUTE_URL}/v3/area"
AREA_DETAIL_URL = f"{PROVIDER_ROUTE_URL}/v1/goyolo/area"

# Default Request Headers
DEFAULT_HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "vi-VN",
    "origin": PROVIDER_BASE_URL,
    "referer": f"{PROVIDER_BASE_URL}/",
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/147.0.0.0 Safari/537.36"
    ),
    "origin-request-product": "FE_NEXTJS",
    "sec-ch-ua": '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
}
