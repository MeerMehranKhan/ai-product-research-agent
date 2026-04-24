from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import quote_plus

import pandas as pd

from core.models import CandidateProduct, ContextProfile, ResearchRequest
from utils.config import DATA_DIR, PLATFORM_FIT_COLUMNS, SNAPSHOT_DIR
from utils.helpers import best_query_match_score, keyword_list, niche_match_score, normalize_text

try:
    import requests
except ImportError:  # pragma: no cover - optional dependency in local verification
    requests = None

try:
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover - optional dependency in local verification
    BeautifulSoup = None


class DiscoveryAdapter:
    source_name = "unknown"
    source_kind = "offline_fallback"

    def discover(
        self,
        request: ResearchRequest,
        context: ContextProfile,
        search_terms: list[str],
    ) -> list[CandidateProduct]:
        raise NotImplementedError


def _build_candidate_from_mapping(
    payload: dict[str, str],
    source: str,
    source_kind: str,
    search_term: str,
) -> CandidateProduct:
    return CandidateProduct(
        name=payload.get("name", "").strip(),
        category=payload.get("category", "General").strip(),
        price=float(payload.get("price", 0) or 0),
        engagement_proxy=float(payload.get("engagement", 50) or 50),
        demand_proxy=float(payload.get("demand", 50) or 50),
        competition_proxy=float(payload.get("competition", 50) or 50),
        virality_proxy=float(payload.get("virality", 50) or 50),
        saturation_proxy=float(payload.get("saturation", 50) or 50),
        source=source,
        source_kind=source_kind,
        supplier_cost=float(payload.get("supplier-cost", 0) or 0) or None,
        novelty=float(payload.get("novelty", 50) or 50),
        product_type=payload.get("product-type", "consumer") or "consumer",
        operational_complexity=float(payload.get("operational-complexity", 35) or 35),
        audience_hint=payload.get("audience", ""),
        trend_region=payload.get("trend-region", "Global") or "Global",
        keywords=keyword_list(payload.get("keywords", "")),
        platform_fit_shopify=float(payload.get("fit-shopify", 60) or 60),
        platform_fit_amazon=float(payload.get("fit-amazon", 60) or 60),
        platform_fit_tiktok=float(payload.get("fit-tiktok", 60) or 60),
        platform_fit_other=float(payload.get("fit-other", 55) or 55),
        source_confidence=0.75 if source_kind == "snapshot" else 0.90,
        search_term=search_term,
        raw_metadata=payload,
    )


def _parse_product_cards(html: str, source: str, source_kind: str, search_term: str) -> list[CandidateProduct]:
    cards: list[CandidateProduct] = []
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html, "html.parser")
        for node in soup.select(".product-card"):
            payload = {key.replace("data-", ""): value for key, value in node.attrs.items() if key.startswith("data-")}
            cards.append(_build_candidate_from_mapping(payload, source, source_kind, search_term))
        return cards

    pattern = re.compile(r'<div class="product-card"([^>]*)></div>', re.IGNORECASE)
    attr_pattern = re.compile(r'data-([a-z-]+)="([^"]*)"')
    for match in pattern.finditer(html):
        payload = {key: value for key, value in attr_pattern.findall(match.group(1))}
        cards.append(_build_candidate_from_mapping(payload, source, source_kind, search_term))
    return cards


class SnapshotAdapter(DiscoveryAdapter):
    source_kind = "snapshot"

    def __init__(self, snapshot_file: Path, source_name: str) -> None:
        self.snapshot_file = snapshot_file
        self.source_name = source_name

    def discover(
        self,
        request: ResearchRequest,
        context: ContextProfile,
        search_terms: list[str],
    ) -> list[CandidateProduct]:
        html = self.snapshot_file.read_text(encoding="utf-8")
        cards = _parse_product_cards(html, self.source_name, self.source_kind, ",".join(search_terms))
        if not request.niche:
            return cards

        filtered: list[CandidateProduct] = []
        for card in cards:
            match = niche_match_score(
                request.niche,
                [card.name, card.category, " ".join(card.keywords)],
            )
            if match >= 20 or any(term in normalize_text(card.name) for term in map(normalize_text, search_terms)):
                filtered.append(card)
        return filtered


class OfflineCatalogAdapter(DiscoveryAdapter):
    source_name = "offline_catalog"
    source_kind = "offline_fallback"

    def __init__(self, csv_path: Path | None = None) -> None:
        self.csv_path = csv_path or DATA_DIR / "seed_products.csv"

    def discover(
        self,
        request: ResearchRequest,
        context: ContextProfile,
        search_terms: list[str],
        relax_niche: bool = False,
        top_k: int = 40,
        prioritize_long_tail: bool = False,
    ) -> list[CandidateProduct]:
        frame = pd.read_csv(self.csv_path)
        platform_column = PLATFORM_FIT_COLUMNS.get(context.platform, "platform_fit_other")
        effective_terms = [request.niche, *search_terms]
        frame["keyword_text"] = frame["keywords"].fillna("")
        frame["search_match"] = frame.apply(
            lambda row: best_query_match_score(effective_terms, [row["name"], row["category"], row["keyword_text"]]),
            axis=1,
        )
        frame["niche_match"] = frame.apply(
            lambda row: niche_match_score(request.niche, [row["name"], row["category"], row["keyword_text"]]) if request.niche else 60.0,
            axis=1,
        )
        frame["platform_match"] = frame[platform_column].fillna(frame["platform_fit_other"])
        frame["market_match"] = frame["trend_region"].fillna("Global").apply(
            lambda value: 100.0 if str(value).lower() in {request.market.lower(), "global"} else 55.0
        )
        frame["long_tail_bonus"] = frame["competition_proxy"].apply(lambda value: max(0.0, 70.0 - float(value)))
        frame["selection_score"] = (
            0.35 * frame["search_match"]
            + 0.30 * frame["platform_match"]
            + 0.20 * frame["demand_proxy"]
            + 0.15 * frame["market_match"]
        )
        if prioritize_long_tail:
            frame["selection_score"] += 0.20 * frame["long_tail_bonus"] + 0.10 * frame["novelty"]

        if request.niche:
            niche_threshold = 18.0 if not relax_niche else 12.0
            filtered = frame[frame["niche_match"] >= niche_threshold]
        else:
            filtered = frame

        if filtered.empty:
            filtered = frame.sort_values(["niche_match", "platform_match", "demand_proxy"], ascending=False).head(top_k)
        else:
            filtered = filtered.sort_values(["niche_match", "selection_score"], ascending=False).head(top_k)

        records: list[CandidateProduct] = []
        for row in filtered.to_dict(orient="records"):
            records.append(
                CandidateProduct(
                    name=row["name"],
                    category=row["category"],
                    price=float(row["price"]),
                    engagement_proxy=float(row["engagement_proxy"]),
                    demand_proxy=float(row["demand_proxy"]),
                    competition_proxy=float(row["competition_proxy"]),
                    virality_proxy=float(row["virality_proxy"]),
                    saturation_proxy=float(row["saturation_proxy"]),
                    source=self.source_name,
                    source_kind=self.source_kind,
                    supplier_cost=float(row["supplier_cost"]),
                    novelty=float(row["novelty"]),
                    product_type=str(row["product_type"]),
                    operational_complexity=float(row["operational_complexity"]),
                    audience_hint=str(row["audience_hint"]),
                    trend_region=str(row["trend_region"]),
                    keywords=keyword_list(row["keywords"]),
                    platform_fit_shopify=float(row["platform_fit_shopify"]),
                    platform_fit_amazon=float(row["platform_fit_amazon"]),
                    platform_fit_tiktok=float(row["platform_fit_tiktok"]),
                    platform_fit_other=float(row["platform_fit_other"]),
                    source_confidence=float(row["source_confidence"]),
                    search_term=",".join(search_terms),
                )
            )
        return records


class LiveSearchAdapter(DiscoveryAdapter):
    source_kind = "live_scrape"
    base_url = ""
    source_name = ""

    def fetch_html(self, search_term: str) -> str:
        if requests is None or not self.base_url:
            return ""
        try:
            response = requests.get(self.base_url.format(query=quote_plus(search_term)), timeout=4)
            response.raise_for_status()
            return response.text
        except Exception:
            return ""

    def discover(
        self,
        request: ResearchRequest,
        context: ContextProfile,
        search_terms: list[str],
    ) -> list[CandidateProduct]:
        results: list[CandidateProduct] = []
        for term in search_terms[:3]:
            html = self.fetch_html(term)
            if not html:
                continue
            results.extend(_parse_product_cards(html, self.source_name, self.source_kind, term))
        return results


class AmazonBestSellersAdapter(LiveSearchAdapter):
    source_name = "amazon_live"
    base_url = "https://www.amazon.com/s?k={query}"


class AliExpressTrendingAdapter(LiveSearchAdapter):
    source_name = "aliexpress_live"
    base_url = "https://www.aliexpress.com/wholesale?SearchText={query}"


def build_default_adapters() -> dict[str, DiscoveryAdapter]:
    return {
        "amazon_live": AmazonBestSellersAdapter(),
        "aliexpress_live": AliExpressTrendingAdapter(),
        "amazon_snapshot": SnapshotAdapter(SNAPSHOT_DIR / "amazon_trending.html", "amazon_snapshot"),
        "aliexpress_snapshot": SnapshotAdapter(SNAPSHOT_DIR / "aliexpress_trending.html", "aliexpress_snapshot"),
        "offline_catalog": OfflineCatalogAdapter(),
    }
