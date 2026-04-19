# Train Station Codes
# Maps human-readable city names to station codes and location IDs
TRAIN_STATIONS: dict[str, dict] = {
    "hanoi": {
        "code": "HNO",
        "name": "Hà Nội",
        "location_id": 102188,
        "region_id": 24,
        "aliases": ["ha noi", "hà nội", "hn"],
    },
    "saigon": {
        "code": "SGO",
        "name": "Sài Gòn",
        "location_id": 28284,
        "region_id": 29,
        "aliases": ["ho chi minh", "hcm", "sai gon", "hồ chí minh", "tphcm"],
    },
    "danang": {
        "code": "DAN",
        "name": "Đà Nẵng",
        "region_id": 15,
        "aliases": ["da nang", "đà nẵng", "dn"],
    },
    "nhatrang": {
        "code": "NTR",
        "name": "Nha Trang",
        "region_id": 417,
        "aliases": ["nha trang", "nt"],
    },
    "hue": {
        "code": "HUE",
        "name": "Huế",
        "region_id": 705,
        "aliases": ["hue", "huế"],
    },
    "vinh": {
        "code": "VIN",
        "name": "Vinh",
        "region_id": None,
        "aliases": ["vinh"],
    },
    "quynhon": {
        "code": "QUN",
        "name": "Quy Nhơn",
        "region_id": 131,
        "aliases": ["quy nhon", "quy nhơn"],
    },
}

# Direct lookup by station code
TRAIN_CODE_TO_INFO: dict[str, dict] = {
    v["code"]: v for v in TRAIN_STATIONS.values()
}

# Flight Airport IATA Codes
FLIGHT_AIRPORTS: dict[str, dict] = {
    "HAN": { "name": "Nội Bài", "city": "Hà Nội", "region_id": 24, "location_id": 102188, "aliases": ["hanoi", "ha noi", "hà nội", "hn"] },
    "SGN": { "name": "Tân Sơn Nhất", "city": "Sài Gòn", "region_id": 29, "location_id": 28284, "aliases": ["saigon", "ho chi minh", "hcm", "sai gon", "tphcm"] },
    "DAD": { "name": "Đà Nẵng", "city": "Đà Nẵng", "region_id": 15, "aliases": ["danang", "da nang"] },
    "CXR": { "name": "Cam Ranh", "city": "Nha Trang", "region_id": 417, "aliases": ["nhatrang", "nha trang"] },
    "PQC": { "name": "Phú Quốc", "city": "Phú Quốc", "region_id": 431, "aliases": ["phuquoc", "phu quoc"] },
    "DLI": { "name": "Liên Khương", "city": "Đà Lạt", "region_id": 457, "aliases": ["dalat", "da lat"] },
    "HUI": { "name": "Phú Bài", "city": "Huế", "region_id": 705, "aliases": ["hue", "huế"] },
    "BMV": { "name": "Buôn Ma Thuột", "city": "Buôn Ma Thuột", "region_id": 204, "aliases": ["buonmathuot", "bmt"] },
    "PXU": { "name": "Pleiku", "city": "Pleiku", "region_id": 274, "aliases": ["pleiku"] },
    "VDH": { "name": "Đồng Hới", "city": "Đồng Hới", "region_id": 27, "aliases": ["donghoi"] },
    "VII": { "name": "Vinh", "city": "Vinh", "region_id": None, "aliases": ["vinh"] },
    "VCL": { "name": "Chu Lai", "city": "Tam Kỳ", "region_id": None, "aliases": ["tamky", "chulai"] },
}

# Bus Region IDs
BUS_REGIONS: dict[str, dict] = {
    "hanoi": { "id": 24, "name": "Hà Nội", "slug": "ha-noi", "aliases": ["ha noi", "hà nội", "hn"] },
    "saigon": { "id": 29, "name": "Sài Gòn", "slug": "ho-chi-minh", "aliases": ["ho chi minh", "hcm", "sai gon", "hồ chí minh", "tphcm"] },
    "danang": { "id": 15, "name": "Đà Nẵng", "slug": "da-nang", "aliases": ["da nang", "đà nẵng"] },
    "nhatrang": { "id": 468, "name": "Nha Trang", "slug": "nha-trang", "aliases": ["nha trang"] },
    "hue": { "id": 206, "name": "Huế", "slug": "hue", "aliases": ["hue", "huế"] },
    "phuquoc": { "id": 442, "name": "Phú Quốc", "slug": "phu-quoc", "aliases": ["phu quoc", "phú quốc"] },
    "dalat": { "id": 459, "name": "Đà Lạt", "slug": "da-lat", "aliases": ["da lat", "đà lạt"] },
    "vinh": { "id": 172, "name": "Vinh", "slug": "vinh", "aliases": ["vinh"] },
    "quynhon": { "id": 220, "name": "Quy Nhơn", "slug": "quy-nhon", "aliases": ["quy nhon", "quy nhơn"] },
    "sonla": { "id": 54, "name": "Sơn La", "slug": "son-la", "aliases": ["son la", "sơn la"] },
    "laocai": { "id": 36, "name": "Lào Cai", "slug": "lao-cai", "aliases": ["lao cai", "lào cai", "sapa"] },
    "hagiang": { "id": 22, "name": "Hà Giang", "slug": "ha-giang", "aliases": ["ha giang", "hà giang"] },
}

