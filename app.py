from __future__ import annotations

from bootstrap import configure_paths

configure_paths()

try:
    import streamlit as st
except ImportError as exc:  # pragma: no cover - depends on local environment
    raise SystemExit(
        "Streamlit is not installed. Run `pip install -r requirements.txt` before starting the app."
    ) from exc

from agents.orchestrator import ProductResearchOrchestrator
from core.models import ResearchRequest
from storage.db import ResearchRepository
from ui.components import (
    render_app_intro,
    render_avoided_products,
    render_empty_results,
    render_history,
    render_product_dashboard,
    render_products,
    render_run_story,
    render_run_summary,
    render_top_opportunity,
)
from ui.theme import inject_theme


def main() -> None:
    st.set_page_config(
        page_title="AI Product Research Agent",
        page_icon="AI",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_theme()

    repository = ResearchRepository()
    orchestrator = ProductResearchOrchestrator(repository=repository)

    st.title("AI Product Research Agent")
    st.caption("Adaptive opportunity discovery for dropshipping, Shopify, Amazon, and social commerce.")
    render_app_intro()

    _init_session()
    selected_run_id = render_history(repository.list_runs())
    if selected_run_id and st.sidebar.button("Load selected run", use_container_width=True):
        st.session_state["active_run"] = repository.get_run(selected_run_id)

    st.markdown(
        """
        <div class="form-shell">
            <div class="eyebrow">Research Setup</div>
            <div class="muted">Use focused phrases so the shortlist stays relevant and easier to trust.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("research_form", clear_on_submit=False):
        col1, col2, col3, col4, col5 = st.columns([2.2, 1.2, 1.1, 1.2, 0.8])
        niche = col1.text_input("Niche", value=st.session_state.get("niche", ""), placeholder="pet grooming, beauty, kitchen gadgets")
        market = col2.selectbox("Market", options=["US", "EU", "Global", "UK", "Other"], index=0)
        budget_min, budget_max = col3.slider("Budget", min_value=10, max_value=200, value=(20, 120), step=5)
        platform = col4.selectbox("Platform", options=["Shopify", "Amazon", "TikTok", "TikTok Shop", "Other"], index=0)
        top_n = col5.number_input("Top N", min_value=3, max_value=10, value=5)
        submitted = st.form_submit_button("Run Agent", use_container_width=True)
    st.caption("Tip: use comma-separated product phrases like `phone cases, laptop stands, USB hubs` or `resistance bands, foam rollers`.")

    if submitted:
        request = ResearchRequest(
            niche=niche,
            market=market,
            budget_min=float(budget_min),
            budget_max=float(budget_max),
            platform=platform,
            top_n=int(top_n),
        )
        with st.spinner("Researching products, scoring opportunities, and preparing results..."):
            run = orchestrator.run(request, generate_pdf=True)
        st.session_state["active_run"] = run.to_dict()
        st.session_state["niche"] = niche

    active_run = st.session_state.get("active_run")
    if not active_run:
        st.info("Run the agent to generate opportunities, avoided products, and an execution plan.")
        return

    products = active_run.get("top_products", [])
    render_run_summary(active_run)
    overview_tab, shortlist_tab, rejected_tab = st.tabs(["Overview", "Shortlist", "Avoid"])

    with overview_tab:
        if products:
            render_top_opportunity(products[0])
            render_run_story(active_run)
            render_product_dashboard(products)
        else:
            render_empty_results(active_run)
            render_run_story(active_run)

    with shortlist_tab:
        render_products(products)

    with rejected_tab:
        render_avoided_products(active_run.get("avoided_products", []))


def _init_session() -> None:
    st.session_state.setdefault("active_run", None)
    st.session_state.setdefault("niche", "")


if __name__ == "__main__":
    main()
