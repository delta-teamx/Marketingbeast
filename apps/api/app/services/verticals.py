"""Per-industry tuning (brief Phase 10).

The same engine, sharper per vertical: each vertical carries a voice, content
angles, hashtags, audience, and offer ideas. `resolve_vertical` maps free-text
industry / business descriptions to a known vertical so content, audits, and ads
come out pre-tuned.
"""

from __future__ import annotations

from typing import Any

VERTICALS: dict[str, dict[str, Any]] = {
    "auto": {
        "label": "Auto & RV",
        "keywords": ["car", "auto", "dealer", "rv", "vehicle", "motors", "truck", "dealership"],
        "voice": "confident, trustworthy, deal-focused",
        "angles": [
            "New arrival walkaround",
            "Deal of the week",
            "Customer delivery photo",
            "Financing made easy",
            "Trade-in tips",
            "Why buy from us",
            "Service special",
        ],
        "hashtags": ["#carsforsale", "#autodealer", "#cardeals"],
        "audience": "local buyers shopping for their next vehicle",
        "offers": ["0% APR weekend", "Free trade-in appraisal", "$500 off this month"],
    },
    "gym": {
        "label": "Gym & Fitness",
        "keywords": ["gym", "fitness", "crossfit", "trainer", "yoga", "pilates", "workout"],
        "voice": "energetic, motivating, community-driven",
        "angles": [
            "Member transformation",
            "Quick form tip",
            "Class of the week",
            "Myth vs fact",
            "Free trial offer",
            "Coach spotlight",
            "Weekly challenge",
        ],
        "hashtags": ["#fitness", "#gymlife", "#fitfam"],
        "audience": "locals wanting to get fit and stay motivated",
        "offers": ["7-day free trial", "Bring-a-friend week", "No joining fee"],
    },
    "restaurant": {
        "label": "Restaurant & Food",
        "keywords": ["restaurant", "cafe", "coffee", "bakery", "food", "bar", "kitchen", "diner"],
        "voice": "warm, mouth-watering, inviting",
        "angles": [
            "Dish of the day",
            "Behind the kitchen",
            "Happy hour",
            "Customer favorite",
            "New menu item",
            "Weekend special",
            "Meet the chef",
        ],
        "hashtags": ["#foodie", "#eatlocal", "#instafood"],
        "audience": "nearby diners looking for their next meal",
        "offers": ["2-for-1 happy hour", "Free dessert with entrée", "Weekend brunch deal"],
    },
    "real_estate": {
        "label": "Real Estate",
        "keywords": [
            "real estate", "realtor", "property", "homes", "broker", "listing", "mortgage",
        ],
        "voice": "professional, local-expert, aspirational",
        "angles": [
            "New listing tour",
            "Just sold",
            "Neighborhood spotlight",
            "Buyer tip",
            "Market update",
            "Open house invite",
            "Client testimonial",
        ],
        "hashtags": ["#realestate", "#justlisted", "#dreamhome"],
        "audience": "local buyers and sellers in the market",
        "offers": ["Free home valuation", "First-time buyer guide", "Open house this weekend"],
    },
    "default": {
        "label": "General",
        "keywords": [],
        "voice": "friendly, helpful, on-brand",
        "angles": ["Tip", "Story", "Customer win", "Myth vs fact", "Offer", "Question", "Recap"],
        "hashtags": ["#smallbusiness", "#shoplocal"],
        "audience": "local customers",
        "offers": ["Limited-time offer", "New customer discount", "This week only"],
    },
}


def resolve_vertical(text: str | None) -> str:
    """Map free-text industry / description to a vertical key."""
    if not text:
        return "default"
    low = text.lower()
    for key, data in VERTICALS.items():
        if key == "default":
            continue
        if any(kw in low for kw in data["keywords"]):
            return key
    return "default"


def vertical_profile(text: str | None) -> dict[str, Any]:
    return VERTICALS[resolve_vertical(text)]


def vertical_hashtag(text: str | None) -> str:
    """The signature hashtag for a vertical (first one)."""
    return vertical_profile(text)["hashtags"][0]
