from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
SNAPSHOT_DIR = DATA_DIR / "snapshots"
EXPORT_DIR = DATA_DIR / "exports"
DB_PATH = ROOT_DIR / "storage" / "analysis_history.db"

BASE_WEIGHTS = {
    "demand": 0.28,
    "competition": 0.22,
    "profit": 0.20,
    "virality": 0.15,
    "saturation": 0.15,
}

MAX_IMPACTS = {
    "demand": 20.0,
    "competition": 18.0,
    "profit": 16.0,
    "virality": 14.0,
    "saturation": 16.0,
}

PLATFORM_FEE_RULES = {
    "Shopify": {"pct": 0.029, "fixed": 0.30},
    "Amazon": {"pct": 0.15, "fixed": 1.80},
    "TikTok Shop": {"pct": 0.08, "fixed": 0.50},
    "TikTok": {"pct": 0.08, "fixed": 0.50},
    "Other": {"pct": 0.05, "fixed": 0.45},
}

MARKET_SHIPPING_BASE = {
    "US": 3.4,
    "EU": 4.2,
    "Global": 5.0,
    "UK": 3.8,
    "Other": 4.5,
}

MARKET_COMPETITIVENESS = {
    "US": "high",
    "EU": "high",
    "Global": "medium",
    "UK": "medium",
    "Other": "medium",
}

CATEGORY_COST_RATIO = {
    "Beauty": 0.24,
    "Home": 0.31,
    "Kitchen": 0.29,
    "Office": 0.34,
    "Pet Care": 0.28,
    "Fitness": 0.26,
    "Baby": 0.33,
    "Auto": 0.35,
    "Tech": 0.42,
    "Travel": 0.30,
    "Garden": 0.32,
}

CATEGORY_COMPLEXITY = {
    "Beauty": 28.0,
    "Home": 40.0,
    "Kitchen": 38.0,
    "Office": 26.0,
    "Pet Care": 34.0,
    "Fitness": 30.0,
    "Baby": 46.0,
    "Auto": 44.0,
    "Tech": 52.0,
    "Travel": 32.0,
    "Garden": 36.0,
}

SOURCE_KIND_CONFIDENCE = {
    "live_scrape": 0.90,
    "snapshot": 0.75,
    "offline_fallback": 0.60,
}

PLATFORM_FIT_COLUMNS = {
    "Shopify": "platform_fit_shopify",
    "Amazon": "platform_fit_amazon",
    "TikTok": "platform_fit_tiktok",
    "TikTok Shop": "platform_fit_tiktok",
}

ADJACENT_TERMS = {
    "pet": ["pet grooming", "dog accessory", "cat care", "pet cleaning", "pet hair"],
    "beauty": ["self care", "skin tool", "beauty gadget", "grooming", "skincare"],
    "foam": ["recovery", "mobility", "stretch", "massage roller"],
    "gym": ["home workout", "strength training", "recovery", "mobility", "fitness"],
    "kitchen": ["home organization", "meal prep", "clean kitchen", "storage", "kitchen gadget"],
    "office": ["workspace", "desk setup", "remote work", "productivity", "desk accessory"],
    "resistance": ["strength training", "mobility", "stretch", "recovery"],
    "fitness": ["recovery", "mobility", "home workout", "wellness", "gym"],
    "travel": ["car organizer", "commuter", "portable storage", "carry-on"],
    "grooming": ["pet grooming", "beauty", "self care", "cleaning"],
    "cleaning": ["home cleaning", "lint remover", "vacuum", "scrubber", "organization"],
    "hair": ["pet hair", "beauty", "grooming", "shedding", "lint"],
    "dog": ["pet grooming", "dog accessory", "pet care", "feeding"],
    "cat": ["cat care", "pet grooming", "pet accessory"],
    "skin": ["skincare", "beauty", "self care", "face roller"],
    "desk": ["desk setup", "office", "cable management", "remote work"],
    "home": ["home organization", "cleaning", "home upgrade", "storage"],
    "baby": ["baby feeding", "parenting", "infant care", "silicone"],
    "car": ["car organizer", "auto accessory", "commuter", "travel"],
    "plant": ["plant care", "garden", "propagation", "home decor"],
    "yoga": ["stretch", "recovery", "wellness", "flexibility"],
    "massage": ["self care", "recovery", "beauty", "wellness"],
    "cable": ["desk setup", "organization", "office", "workspace"],
    "projector": ["gadget", "tech", "entertainment", "home theater"],
    "phone": ["phone case", "phone accessories", "phone mount", "charger", "mobile accessory", "magsafe"],
    "cases": ["phone case", "phone accessories", "shockproof", "clear case", "mobile"],
    "laptop": ["laptop stand", "desk setup", "remote work", "ergonomic"],
    "usb": ["usb hub", "tech accessory", "desk setup", "connectivity"],
    "led": ["led lights", "rgb", "room decor", "lighting", "lamp"],
    "lights": ["led lights", "rgb", "room decor", "sunset lamp", "lighting"],
    "sports": ["resistance bands", "running belt", "workout", "exercise", "fitness"],
    "outdoor": ["camping", "hiking", "hammock", "headlamp", "adventure"],
    "camping": ["outdoor", "headlamp", "portable", "hiking", "tent"],
    "jewelry": ["necklace", "ring", "bracelet", "earring", "fashion"],
    "necklace": ["jewelry", "layered", "fashion", "pendant"],
    "ring": ["jewelry", "anxiety ring", "fidget", "fashion"],
    "stationery": ["planner", "notebook", "washi tape", "craft", "organization"],
    "planner": ["stationery", "notebook", "productivity", "organization"],
    "charger": ["wireless charger", "phone accessories", "charging pad", "tech"],
    "mount": ["phone mount", "car mount", "magnetic", "phone accessories"],
}

GENERIC_DISCOVERY_TERMS = [
    "problem solver",
    "home upgrade",
    "viral gadget",
    "daily use product",
]

BEGINNER_FRIENDLY_COMPLEXITY_MAX = 38.0
BEGINNER_FRIENDLY_MARGIN_MIN = 32.0
