from __future__ import annotations

from core.models import ContextProfile, ResearchRequest


CATEGORY_PERSONAS = {
    "Beauty": {
        "label": "Routine optimizer",
        "pain_points": "Wants visible results without adding a long routine.",
        "trigger": "A low-friction product that makes self-care feel elevated.",
    },
    "Pet Care": {
        "label": "Problem-solving pet parent",
        "pain_points": "Needs a fast fix for shedding, feeding, or daily cleanup.",
        "trigger": "Anything that saves time while improving pet comfort.",
    },
    "Office": {
        "label": "Remote setup improver",
        "pain_points": "Desk clutter, discomfort, or workflow friction.",
        "trigger": "Products that create a cleaner, calmer, more productive setup.",
    },
    "Kitchen": {
        "label": "Practical home optimizer",
        "pain_points": "Small daily annoyances while cooking or cleaning.",
        "trigger": "Compact upgrades that make routine tasks faster.",
    },
    "Home": {
        "label": "Convenience-seeking homeowner",
        "pain_points": "Recurring cleaning and organization friction.",
        "trigger": "Products that reduce repetitive work at home.",
    },
}


def build_action_block(row: dict[str, object], request: ResearchRequest, context: ContextProfile) -> dict[str, object]:
    persona = _persona(row)
    category = str(row["category"])
    product_name = str(row["name"])
    launch_budget = _launch_budget(context)
    platform = context.platform
    angle_seed = _angle_seed(row)
    return {
        "demand_validation_plan": _demand_validation_steps(product_name, platform, launch_budget),
        "supplier_search_plan": _supplier_steps(product_name, category),
        "store_or_listing_plan": _listing_steps(product_name, platform),
        "launch_plan": _launch_steps(product_name, platform, launch_budget),
        "target_persona": persona,
        "marketing_angles": [
            f"{product_name}: {angle_seed['pain_point']}",
            f"{product_name}: {angle_seed['before_after']}",
            f"{product_name}: {angle_seed['price_psychology']}",
        ],
        "suggested_channel": _primary_channel(platform),
    }


def _persona(row: dict[str, object]) -> dict[str, str]:
    category = str(row["category"])
    default = {
        "label": "Value-seeking online shopper",
        "pain_points": "Needs a clear, immediate reason to buy.",
        "trigger": "A product that solves one everyday annoyance quickly.",
    }
    base = CATEGORY_PERSONAS.get(category, default)
    return {
        "label": base["label"],
        "pain_points": base["pain_points"],
        "trigger": base["trigger"],
        "audience_hint": str(row.get("audience_hint", "")),
    }


def _angle_seed(row: dict[str, object]) -> dict[str, str]:
    category = str(row["category"])
    if category == "Pet Care":
        return {
            "pain_point": "Show the daily mess or feeding issue it removes in one quick demo.",
            "before_after": "Use a split-screen before-and-after of the pet problem disappearing.",
            "price_psychology": "Position it as a cheaper replacement for recurring cleanup frustration.",
        }
    if category == "Beauty":
        return {
            "pain_point": "Lead with visible routine improvement in under 30 seconds.",
            "before_after": "Frame the product as the easiest upgrade to an existing routine.",
            "price_psychology": "Price it as an affordable self-care treat rather than a luxury gadget.",
        }
    if category in {"Office", "Home", "Kitchen"}:
        return {
            "pain_point": "Open with the small daily annoyance most people tolerate for too long.",
            "before_after": "Show the faster, cleaner workflow after the product is installed.",
            "price_psychology": "Compare the price to the time or mental friction it removes every week.",
        }
    return {
        "pain_point": "Start with the friction point the product eliminates immediately.",
        "before_after": "Show the simplest transformation from cluttered or inconvenient to easy.",
        "price_psychology": "Anchor the price against wasted time, not against other gadgets.",
    }


def _demand_validation_steps(product_name: str, platform: str, launch_budget: float) -> list[str]:
    if platform == "Amazon":
        return [
            f"Check top Amazon listings for {product_name} and confirm review velocity still supports demand.",
            "Compare 10 leading listings for price spread, rating spread, and review-count concentration.",
            "Validate that the top 3 listings are not monopolizing the keyword with deep brand equity.",
            f"Only proceed if your target listing can support at least ${launch_budget:.0f} in early testing inventory without negative margin pressure.",
        ]
    if platform in {"TikTok", "TikTok Shop"}:
        return [
            f"Collect 10 short-form content examples for {product_name} and note which hook repeats most often.",
            "Validate that the product can be demonstrated visually in under 5 seconds.",
            "Test 2 problem-first hooks and 1 transformation hook before building a broad campaign.",
            f"Treat the first ${launch_budget:.0f} as signal gathering only and scale only if watch-through and click interest stay efficient.",
        ]
    return [
        f"Build a one-product landing page for {product_name} with one primary promise and one social proof block.",
        "Check search intent, competitor offers, and customer pain-point language before creative work.",
        "Test one utility angle and one aspiration angle instead of launching with too many messages.",
        f"Use the first ${launch_budget:.0f} to validate click-through and add-to-cart quality before pushing spend.",
    ]


def _supplier_steps(product_name: str, category: str) -> list[str]:
    return [
        f"Shortlist 3 suppliers for {product_name} and reject any that cannot prove consistent packaging and replenishment times.",
        "Request updated landed-cost quotes, not just unit prices, so shipping does not destroy margin.",
        f"Confirm category-specific red flags for {category.lower()} products, including material safety, durability, and return-risk issues.",
        "Do not move forward without photo or video proof that matches the expected selling angle.",
    ]


def _listing_steps(product_name: str, platform: str) -> list[str]:
    if platform == "Amazon":
        return [
            f"Write the listing for {product_name} around one core benefit, one proof point, and one objection-handling bullet.",
            "Make the main image benefit-led and keep secondary images focused on use-case proof.",
            "Use a comparison chart only if the product genuinely wins on convenience, quality, or time saved.",
            "Prepare a clear FAQ section around shipping, quality, and common hesitation points.",
        ]
    return [
        f"Build the page for {product_name} with a strong headline, demo visual, and a fast-moving proof section above the fold.",
        "Include one section explaining why the usual workaround is frustrating and why this product is easier.",
        "Use bundles or quantity breaks only if they increase AOV without confusing the main offer.",
        "Make the CTA and guarantee visible before the first scroll ends.",
    ]


def _launch_steps(product_name: str, platform: str, launch_budget: float) -> list[str]:
    channel = _primary_channel(platform)
    return [
        f"Launch {product_name} first on {channel} with one controlled offer instead of multiple discounts.",
        "Keep the initial creative set narrow so the winning angle is obvious within the first test window.",
        f"Use a capped launch budget of about ${launch_budget:.0f} per day until conversion and contribution margin stay aligned.",
        "Scale only after both click quality and contribution margin remain healthy for two consecutive review windows.",
    ]


def _primary_channel(platform: str) -> str:
    if platform == "Amazon":
        return "Amazon listing optimization and internal search"
    if platform in {"TikTok", "TikTok Shop"}:
        return "short-form creative plus creator-style hooks"
    return "paid social to a focused landing page"


def _launch_budget(context: ContextProfile) -> float:
    return {"tight": 25.0, "balanced": 40.0, "flexible": 65.0}.get(context.budget_strictness, 40.0)
