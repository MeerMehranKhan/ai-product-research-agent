from __future__ import annotations

import pandas as pd
import streamlit as st

from utils.helpers import format_currency

try:
    import plotly.graph_objects as go
except ImportError:  # pragma: no cover - optional during local verification
    go = None


def render_app_intro() -> None:
    st.markdown(
        """
        <div class="intro-card">
            <div class="eyebrow">Search Better</div>
            <div class="intro-title">Describe a product lane with 2-4 focused phrases.</div>
            <div class="hero-subtitle">Comma-separated phrases work best. They help the agent stay on-topic and reduce generic spillover.</div>
            <div class="chip-row">
                <span class="intro-chip">phone cases, laptop stands, USB hubs</span>
                <span class="intro-chip">home gym equipment, resistance bands, foam rollers</span>
                <span class="intro-chip">pet grooming, dog cleaning tools, shedding control</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_run_summary(run: dict[str, object]) -> None:
    request = run.get("request", {})
    products = run.get("top_products", [])
    avoided = run.get("avoided_products", [])
    summary_cols = st.columns(4)
    summary_cols[0].metric("Niche", str(request.get("niche") or "All niches"))
    summary_cols[1].metric("Market / Platform", f"{request.get('market', 'US')} / {request.get('platform', 'Shopify')}")
    summary_cols[2].metric("Opportunities", len(products))
    summary_cols[3].metric("Rejected", len(avoided))
    st.caption(
        f"Run outcome: {str(run.get('outcome', 'pending')).title()} | Budget: "
        f"{format_currency(float(request.get('budget_min', 0.0)))} to {format_currency(float(request.get('budget_max', 0.0)))}"
    )


def render_top_opportunity(product: dict[str, object]) -> None:
    tags = _badges(product)
    st.markdown(
        f"""
        <div class="hero-card">
            <div class="eyebrow">Top Opportunity</div>
            <div class="hero-title">{product['name']}</div>
            <div>{tags}</div>
            <div class="hero-subtitle">{product['surface_reasoning']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    metrics = st.columns(5)
    metrics[0].metric("Opportunity", f"{product['opportunity_score']:.1f}")
    metrics[1].metric("Confidence", f"{product['confidence_score']:.1f}")
    metrics[2].metric("Profit / Unit", format_currency(product["estimated_profit_per_unit"]))
    metrics[3].metric("Break-Even Ad", format_currency(product["break_even_ad_cost"]))
    metrics[4].metric("Margin", f"{product['estimated_margin_pct']:.1f}%")


def render_run_story(run: dict[str, object]) -> None:
    insights = run.get("run_insights", {})
    st.markdown("**Run-Level Insights**")
    insight_cols = st.columns(4)
    insight_cols[0].metric("Best Opportunity", _nested_name(insights.get("best_opportunity")))
    insight_cols[1].metric("Safest Opportunity", _nested_name(insights.get("safest_opportunity")))
    insight_cols[2].metric("Most Overlooked", _nested_name(insights.get("most_overlooked_opportunity")))
    insight_cols[3].metric("Outcome", str(run.get("outcome", "")).title())
    if insights.get("biggest_red_flag"):
        st.warning(f"Biggest red flag: {insights['biggest_red_flag']}")
    if insights.get("adjacent_niche_suggestion"):
        st.info(f"Adjacent niche suggestion: {insights['adjacent_niche_suggestion']}")


def render_product_dashboard(products: list[dict[str, object]]) -> None:
    if not products:
        return
    st.markdown("**Opportunity Snapshot**")
    render_product_highlights(products[:3])
    render_run_charts(products)


def render_product_highlights(products: list[dict[str, object]]) -> None:
    columns = st.columns(len(products))
    for column, product in zip(columns, products, strict=False):
        column.markdown(
            f"""
            <div class="mini-card">
                <div class="mini-card-title">{product['name']}</div>
                <div class="mini-card-score">Score {product['opportunity_score']:.1f} | Confidence {product['confidence_score']:.1f}</div>
                <div class="muted">{product['surface_reasoning']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_products(products: list[dict[str, object]]) -> None:
    st.markdown("**Shortlist**")
    if not products:
        st.warning("No products cleared the current thresholds.")
        return

    for product in products:
        with st.expander(f"{product['name']} | Score {product['opportunity_score']:.1f}", expanded=product is products[0]):
            tags = _badges(product)
            st.markdown(tags, unsafe_allow_html=True)
            summary_cols = st.columns(4)
            summary_cols[0].metric("Opportunity", f"{product['opportunity_score']:.1f}")
            summary_cols[1].metric("Confidence", f"{product['confidence_score']:.1f}")
            summary_cols[2].metric("Risk", product["risk_level"])
            summary_cols[3].metric("Discovery Gap", f"{product['discovery_gap_score']:.1f}")
            tabs = st.tabs(["Score Breakdown", "Money View", "Action Plan", "Why It Ranked"])
            with tabs[0]:
                render_score_story(product)
            with tabs[1]:
                render_money_view(product)
            with tabs[2]:
                render_action_plan(product["action_plan"])
            with tabs[3]:
                st.markdown(f"**Quick Read**  \n{product['surface_reasoning']}")
                st.markdown(f"**Deeper Take**  \n{product['deep_reasoning']}")
                st.markdown(f"**Strategic Fit**  \n{product['strategic_reasoning']}")


def render_empty_results(run: dict[str, object]) -> None:
    request = run.get("request", {})
    niche = request.get("niche", "this niche")
    st.markdown(
        f"""
        <div class="empty-card">
            <div class="eyebrow">No Strong Matches</div>
            <div class="intro-title">The agent did not find enough relevant products for <strong>{niche}</strong>.</div>
            <div class="hero-subtitle">That is usually better than forcing weak or off-topic recommendations. Try narrower product phrases, a wider budget, or a nearby sub-niche.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_avoided_products(products: list[dict[str, object]]) -> None:
    st.markdown("**Avoid These Products**")
    if not products:
        st.caption("No avoided products were captured for this run.")
        return

    columns = st.columns(2)
    for index, product in enumerate(products[:6]):
        column = columns[index % 2]
        column.markdown(
            f"""
            <div class="avoid-card">
                <strong>{product['name']}</strong> | {product['category']}<br/>
                <span class="muted">{product['reason']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_run_charts(products: list[dict[str, object]]) -> None:
    if go is None or not products:
        return

    product_frame = pd.DataFrame(products).copy()
    left, right = st.columns([1.05, 0.95])

    with left:
        scatter = go.Figure(
            data=[
                go.Scatter(
                    x=product_frame["estimated_profit_per_unit"],
                    y=product_frame["opportunity_score"],
                    customdata=product_frame[
                        ["name", "confidence_score", "estimated_margin_pct", "discovery_gap_score", "risk_level"]
                    ],
                    mode="markers",
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Profit / Unit: %{x:$,.2f}<br>"
                        "Opportunity: %{y:.1f}<br>"
                        "Confidence: %{customdata[1]:.1f}<br>"
                        "Margin: %{customdata[2]:.1f}%<br>"
                        "Discovery Gap: %{customdata[3]:.1f}<br>"
                        "Risk: %{customdata[4]}<extra></extra>"
                    ),
                    marker=dict(
                        size=(product_frame["confidence_score"] / 4).clip(lower=13),
                        color=product_frame["discovery_gap_score"],
                        colorscale=[
                            [0.0, "#163c3c"],
                            [0.5, "#0ea5a5"],
                            [1.0, "#7dd3fc"],
                        ],
                        colorbar=dict(title="Discovery Gap"),
                        showscale=True,
                        line=dict(color="rgba(8, 15, 28, 0.9)", width=1.2),
                        opacity=0.9,
                    ),
                )
            ]
        )
        scatter.update_layout(
            height=360,
            title="Profitability vs Opportunity",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.6)",
            font=dict(color="#e2e8f0"),
            margin=dict(l=10, r=10, t=48, b=10),
            xaxis=dict(title="Profit per Unit", gridcolor="rgba(148, 163, 184, 0.16)", zeroline=False),
            yaxis=dict(title="Opportunity Score", gridcolor="rgba(148, 163, 184, 0.16)", zeroline=False),
        )
        st.plotly_chart(scatter, use_container_width=True)

    with right:
        ranked = product_frame.sort_values(["opportunity_score", "confidence_score"], ascending=[True, True]).copy()
        ranked["chart_label"] = ranked["name"].apply(_short_label)
        bar_chart = go.Figure(
            data=[
                go.Bar(
                    x=ranked["opportunity_score"],
                    y=ranked["chart_label"],
                    orientation="h",
                    text=[f"{score:.1f}" for score in ranked["opportunity_score"]],
                    textposition="outside",
                    customdata=ranked[
                        ["name", "confidence_score", "estimated_profit_per_unit", "estimated_margin_pct", "risk_level"]
                    ],
                    hovertemplate=(
                        "<b>%{customdata[0]}</b><br>"
                        "Opportunity: %{x:.1f}<br>"
                        "Confidence: %{customdata[1]:.1f}<br>"
                        "Profit / Unit: %{customdata[2]:$,.2f}<br>"
                        "Margin: %{customdata[3]:.1f}%<br>"
                        "Risk: %{customdata[4]}<extra></extra>"
                    ),
                    marker=dict(
                        color=ranked["confidence_score"],
                        colorscale=[
                            [0.0, "#7f1d1d"],
                            [0.45, "#f59e0b"],
                            [1.0, "#14b8a6"],
                        ],
                        cmin=0,
                        cmax=100,
                        colorbar=dict(title="Confidence"),
                        line=dict(color="rgba(8, 15, 28, 0.92)", width=1.1),
                    ),
                )
            ]
        )
        bar_chart.update_layout(
            height=max(360, 76 * len(ranked.index)),
            title="Top Opportunity Ranking",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.6)",
            font=dict(color="#e2e8f0"),
            margin=dict(l=10, r=40, t=48, b=10),
            xaxis=dict(
                title="Opportunity Score",
                gridcolor="rgba(148, 163, 184, 0.16)",
                zeroline=False,
                range=[0, max(ranked["opportunity_score"].max() * 1.18, 10)],
            ),
            yaxis=dict(title=None, automargin=True),
        )
        st.plotly_chart(bar_chart, use_container_width=True)


def render_score_story(product: dict[str, object]) -> None:
    adjustments = product.get("factor_adjustments", {})
    cols = st.columns(len(adjustments) or 1)
    for idx, (factor, value) in enumerate(adjustments.items()):
        cols[idx].metric(_display_label(factor), f"{value:+.1f}")

    if go is not None and adjustments:
        ranked_adjustments = sorted(adjustments.items(), key=lambda item: item[1])
        figure = go.Figure(
            data=[
                go.Bar(
                    x=[value for _, value in ranked_adjustments],
                    y=[_display_label(name) for name, _ in ranked_adjustments],
                    orientation="h",
                    text=[f"{value:+.1f}" for _, value in ranked_adjustments],
                    textposition="outside",
                    marker_color=["#22c55e" if value >= 0 else "#ef4444" for _, value in ranked_adjustments],
                )
            ]
        )
        figure.update_layout(
            height=max(220, 52 * len(ranked_adjustments)),
            title="Factor Adjustments",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.6)",
            font=dict(color="#e2e8f0"),
            margin=dict(l=10, r=36, t=48, b=10),
            xaxis=dict(gridcolor="rgba(148, 163, 184, 0.16)", zeroline=True, zerolinecolor="rgba(226, 232, 240, 0.35)"),
            yaxis=dict(title=None, automargin=True),
        )
        st.plotly_chart(figure, use_container_width=True)

    for line in product.get("score_explanations", []):
        st.write(f"- {line}")
    st.caption(f"Weight mix: {product.get('weight_summary', '')}")


def render_money_view(product: dict[str, object]) -> None:
    cols = st.columns(5)
    cols[0].metric("Suggested Price", format_currency(product["suggested_selling_price"]))
    cols[1].metric("Landed Cost", format_currency(product["estimated_landed_cost"]))
    cols[2].metric("Platform Fee", format_currency(product["platform_fee_estimate"]))
    cols[3].metric("Break-Even Ad", format_currency(product["break_even_ad_cost"]))
    cols[4].metric("Target Ad Cost", format_currency(product["target_ad_cost"]))
    st.write(
        f"Estimated supplier cost: {format_currency(product['estimated_supplier_cost'])} | "
        f"Profit per unit: {format_currency(product['estimated_profit_per_unit'])} | "
        f"Pricing strategy: {product['pricing_strategy_suggestion']}"
    )


def render_action_plan(action_plan: dict[str, object]) -> None:
    st.markdown(f"**Target Persona**  \n{action_plan['target_persona']['label']}: {action_plan['target_persona']['pain_points']}")
    for label, items in [
        ("Demand Validation", action_plan["demand_validation_plan"]),
        ("Supplier Search", action_plan["supplier_search_plan"]),
        ("Store / Listing", action_plan["store_or_listing_plan"]),
        ("Launch Plan", action_plan["launch_plan"]),
        ("Marketing Angles", action_plan["marketing_angles"]),
    ]:
        st.markdown(f"**{label}**")
        for item in items:
            st.write(f"- {item}")


def render_history(history: list[dict[str, object]]) -> str | None:
    st.sidebar.markdown("### Past Runs")
    if not history:
        st.sidebar.caption("No saved runs yet.")
        return None

    labels = {entry["run_id"]: _history_label(entry) for entry in history}
    selected = st.sidebar.selectbox(
        "Load saved run",
        options=[""] + list(labels.keys()),
        format_func=lambda value: labels.get(value, "Current session"),
    )
    return selected or None


def _badges(product: dict[str, object]) -> str:
    tags = [
        f'<span class="score-badge">Opportunity {product["opportunity_score"]:.1f}</span>',
        f'<span class="score-badge">Confidence {product["confidence_score"]:.1f}</span>',
        f'<span class="tag-badge">Risk {product["risk_level"]}</span>',
    ]
    if product.get("undiscovered_opportunity"):
        tags.append('<span class="tag-badge">Undiscovered Opportunity</span>')
    if product.get("beginner_friendly"):
        tags.append('<span class="tag-badge">Beginner Friendly</span>')
    return "".join(tags)


def _history_label(entry: dict[str, object]) -> str:
    request = entry.get("request", {})
    niche = request.get("niche") or "All niches"
    return f"{entry['created_at']} | {request.get('platform', 'Platform')} | {niche}"


def _nested_name(payload: dict[str, object] | None) -> str:
    if not payload:
        return "N/A"
    return str(payload.get("name", "N/A"))


def _display_label(value: object) -> str:
    return str(value).replace("_", " ").title()


def _short_label(value: object, max_length: int = 28) -> str:
    label = str(value)
    if len(label) <= max_length:
        return label
    return f"{label[: max_length - 3].rstrip()}..."
