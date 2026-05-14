from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

GENERIC_QUERY_TOKENS = {
    "accessory",
    "accessories",
    "daily",
    "equipment",
    "essential",
    "essentials",
    "gadget",
    "gadgets",
    "gear",
    "home",
    "kit",
    "kits",
    "product",
    "products",
    "solution",
    "solutions",
    "tool",
    "tools",
    "upgrade",
    "upgrades",
    "use",
}

CATEGORY_SYNONYMS: dict[str, set[str]] = {
    "pet": {"pet care", "pet", "dog", "cat", "puppy"},
    "beauty": {"beauty", "skincare", "makeup", "cosmetic", "self care"},
    "kitchen": {"kitchen", "cooking", "meal prep", "food"},
    "fitness": {"fitness", "gym", "workout", "exercise", "recovery", "wellness"},
    "office": {"office", "desk", "workspace", "remote work"},
    "home": {"home", "household", "cleaning", "organization"},
    "tech": {"tech", "electronic", "gadget", "smart"},
    "travel": {"travel", "commuter", "portable", "car"},
    "baby": {"baby", "infant", "parenting", "child"},
    "garden": {"garden", "plant", "outdoor"},
    "auto": {"auto", "car", "vehicle", "automotive"},
    "grooming": {"grooming", "pet care", "beauty", "self care", "cleaning"},
    "cleaning": {"cleaning", "home", "lint", "vacuum", "scrubber"},
}


def utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def normalize_text(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", value.lower())
    return re.sub(r"\s+", " ", cleaned).strip()


def keyword_list(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        return [item.strip() for item in value if item.strip()]
    if not value:
        return []
    return [chunk.strip() for chunk in value.split(",") if chunk.strip()]


def slugify(value: str) -> str:
    normalized = normalize_text(value)
    return normalized.replace(" ", "-")


def overlap_score(target: str, candidates: list[str]) -> float:
    target_tokens = set(normalize_text(target).split())
    if not target_tokens:
        return 0.0
    candidate_tokens: set[str] = set()
    for candidate in candidates:
        candidate_tokens.update(normalize_text(candidate).split())
    return 100.0 * safe_divide(len(target_tokens & candidate_tokens), len(target_tokens), 0.0)


def split_query_phrases(value: str) -> list[str]:
    if not value.strip():
        return []
    phrases = [chunk.strip() for chunk in re.split(r"[,/;|]+", value) if chunk.strip()]
    ordered = [value.strip(), *phrases]
    return list(dict.fromkeys(ordered))


def niche_match_score(niche: str, candidates: list[str]) -> float:
    phrases = split_query_phrases(niche)
    if not phrases:
        return 0.0
    candidate_tokens: list[str] = []
    for candidate in candidates:
        candidate_tokens.extend(_semantic_tokens(candidate))
    if not candidate_tokens:
        return 0.0

    candidate_token_set = set(candidate_tokens)
    candidate_text = " ".join(candidate_tokens)
    # Also check raw candidate text for category-level matching
    raw_candidate_text = " ".join(normalize_text(c) for c in candidates)
    best_score = 0.0
    for phrase in phrases:
        phrase_tokens = _semantic_tokens(phrase)
        if not phrase_tokens:
            continue

        phrase_text = " ".join(phrase_tokens)
        overlap = len(set(phrase_tokens) & candidate_token_set)

        # Check for category synonym matches
        synonym_bonus = _category_synonym_bonus(phrase_tokens, candidate_token_set, raw_candidate_text)

        # For exact substring match, give full score
        if phrase_text and phrase_text in candidate_text:
            best_score = max(best_score, 100.0)
            continue

        # Accept single token overlap for multi-word phrases when there is
        # also a category synonym match
        min_required = 1 if len(phrase_tokens) == 1 else (1 if synonym_bonus > 0 else 2)
        if overlap >= min_required:
            raw_score = 100.0 * safe_divide(overlap, len(phrase_tokens), 0.0)
            best_score = max(best_score, min(100.0, raw_score + synonym_bonus))
        elif synonym_bonus > 0:
            # Even with zero direct token overlap, strong category synonym
            # match should return a meaningful score
            best_score = max(best_score, synonym_bonus)
    return best_score


def _category_synonym_bonus(phrase_tokens: list[str], candidate_tokens: set[str], raw_candidate_text: str) -> float:
    """Return a bonus score (0-50) when phrase tokens map to a category synonym group
    that also covers one or more candidate tokens."""
    bonus = 0.0
    for token in phrase_tokens:
        related = CATEGORY_SYNONYMS.get(token)
        if not related:
            continue
        # Check if any candidate token or raw text belongs to the same synonym group
        for synonym in related:
            syn_tokens = set(normalize_text(synonym).split())
            # For multi-word synonyms, require ALL tokens to be present
            if len(syn_tokens) > 1:
                if syn_tokens.issubset(candidate_tokens) or synonym in raw_candidate_text:
                    bonus = max(bonus, 40.0)
                    break
            else:
                if syn_tokens & candidate_tokens:
                    bonus = max(bonus, 40.0)
                    break
    return bonus


def best_query_match_score(queries: list[str], candidates: list[str]) -> float:
    if not queries:
        return 0.0
    scores = [niche_match_score(query, candidates) for query in queries if query.strip()]
    if not scores:
        return 0.0
    return max(scores)


def _semantic_tokens(value: str) -> list[str]:
    tokens = []
    for token in normalize_text(value).split():
        normalized = _normalize_query_token(token)
        if not normalized or normalized in GENERIC_QUERY_TOKENS:
            continue
        tokens.append(normalized)
    return tokens


def _normalize_query_token(token: str) -> str:
    if len(token) > 3 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def make_json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return make_json_safe(asdict(value))
    if isinstance(value, dict):
        return {str(key): make_json_safe(inner) for key, inner in value.items()}
    if isinstance(value, list):
        return [make_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [make_json_safe(item) for item in value]
    if isinstance(value, Path):
        return str(value)
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return round(value, 4)
    return value


def json_dumps(value: Any) -> str:
    return json.dumps(make_json_safe(value), ensure_ascii=True, indent=2)


def psych_price(price: float, premium: bool = False) -> float:
    if price <= 0:
        return 0.0
    if price < 15:
        rounded = math.ceil(price) - 0.01
    elif price < 50:
        rounded = math.ceil(price / 5.0) * 5 - 0.01
    else:
        rounded = math.ceil(price / 10.0) * 10 - 0.01
    if premium and rounded >= 20:
        rounded += 4.0
    return round(rounded, 2)


def format_currency(value: float) -> str:
    return f"${value:,.2f}"
