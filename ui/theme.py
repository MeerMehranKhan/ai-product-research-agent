from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
            /* ── Global ───────────────────────────────────────── */
            .stApp {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
                background:
                    radial-gradient(ellipse 80% 50% at 10% 0%, rgba(20, 184, 166, 0.10), transparent),
                    radial-gradient(ellipse 60% 40% at 90% 5%, rgba(99, 102, 241, 0.08), transparent),
                    linear-gradient(180deg, #07111d 0%, #0f172a 55%, #111827 100%);
                color: #e2e8f0;
            }
            [data-testid="stHeader"] {
                background: rgba(7, 17, 29, 0.72);
                backdrop-filter: blur(12px);
            }

            /* ── Sidebar ──────────────────────────────────────── */
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(8, 15, 28, 0.98), rgba(15, 23, 42, 0.96));
                border-right: 1px solid rgba(148, 163, 184, 0.08);
            }
            [data-testid="stSidebar"] .stMarkdown h3 {
                font-size: 0.82rem;
                letter-spacing: 0.1em;
                text-transform: uppercase;
                color: #94a3b8;
                font-weight: 600;
            }

            /* ── Section Headers ─────────────────────────────── */
            .section-header {
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.14em;
                text-transform: uppercase;
                color: #64748b;
                padding-bottom: 0.35rem;
                margin-top: 0.6rem;
                margin-bottom: 0.25rem;
                border-bottom: 1px solid rgba(148, 163, 184, 0.08);
            }

            /* ── App Title ────────────────────────────────────── */
            .app-brand {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin-bottom: 0.1rem;
            }
            .app-brand-icon {
                width: 38px;
                height: 38px;
                border-radius: 12px;
                background: linear-gradient(135deg, #14b8a6, #6366f1);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 1.1rem;
                font-weight: 800;
                color: #fff;
                flex-shrink: 0;
            }
            .app-brand-text {
                font-size: 1.45rem;
                font-weight: 800;
                background: linear-gradient(135deg, #e2e8f0 0%, #94a3b8 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                line-height: 1.2;
            }
            .app-subtitle {
                font-size: 0.88rem;
                color: #64748b;
                margin-bottom: 1.1rem;
                margin-top: 0.15rem;
            }

            /* ── Cards ────────────────────────────────────────── */
            .hero-card, .intro-card, .mini-card, .empty-card, .form-shell, .avoid-card {
                border: 1px solid rgba(148, 163, 184, 0.12);
                border-radius: 16px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
                transition: border-color 0.2s ease, box-shadow 0.2s ease;
            }
            .mini-card:hover {
                border-color: rgba(20, 184, 166, 0.3);
                box-shadow: 0 8px 32px rgba(20, 184, 166, 0.06);
            }
            .intro-card, .form-shell, .empty-card, .mini-card, .avoid-card {
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.88), rgba(15, 23, 42, 0.68));
            }
            .hero-card {
                padding: 1.15rem 1.3rem;
                background: linear-gradient(135deg, rgba(13, 148, 136, 0.14), rgba(15, 23, 42, 0.95) 42%, rgba(99, 102, 241, 0.10));
            }
            .intro-card, .empty-card {
                padding: 1rem 1.2rem;
                margin-bottom: 0.8rem;
            }
            .form-shell {
                padding: 0.55rem 0.9rem 0.2rem 0.9rem;
                margin-bottom: 0.2rem;
            }
            .mini-card, .avoid-card {
                padding: 0.85rem 1rem;
                height: 100%;
            }
            .avoid-card {
                border-color: rgba(248, 113, 113, 0.14);
                background: linear-gradient(180deg, rgba(127, 29, 29, 0.16), rgba(15, 23, 42, 0.82));
                margin-bottom: 0.7rem;
            }

            /* ── Text styles ──────────────────────────────────── */
            .eyebrow {
                letter-spacing: 0.12em;
                text-transform: uppercase;
                font-size: 0.72rem;
                font-weight: 600;
                color: #5eead4;
            }
            .hero-title, .intro-title {
                color: #f1f5f9;
                font-weight: 700;
            }
            .hero-title {
                font-size: 1.55rem;
                margin: 0.25rem 0 0.5rem 0;
                line-height: 1.25;
            }
            .intro-title {
                font-size: 1.12rem;
                margin: 0.3rem 0 0.35rem 0;
                line-height: 1.35;
            }
            .mini-card-title {
                color: #f1f5f9;
                font-size: 0.95rem;
                font-weight: 700;
                margin-bottom: 0.25rem;
                line-height: 1.3;
            }
            .mini-card-score {
                color: #5eead4;
                font-size: 0.82rem;
                font-weight: 600;
                margin-bottom: 0.35rem;
            }
            .hero-subtitle, .muted {
                color: #94a3b8;
                font-size: 0.9rem;
                line-height: 1.5;
            }

            /* ── Chips & Badges ───────────────────────────────── */
            .chip-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.4rem;
                margin-top: 0.65rem;
            }
            .intro-chip, .score-badge, .tag-badge {
                display: inline-block;
                padding: 0.22rem 0.58rem;
                border-radius: 999px;
                font-size: 0.76rem;
                font-weight: 600;
                letter-spacing: 0.01em;
            }
            .intro-chip {
                background: rgba(99, 102, 241, 0.10);
                color: #a5b4fc;
                border: 1px solid rgba(99, 102, 241, 0.20);
            }
            .score-badge, .tag-badge {
                margin-right: 0.3rem;
                margin-bottom: 0.3rem;
            }
            .score-badge {
                background: rgba(20, 184, 166, 0.12);
                color: #5eead4;
                border: 1px solid rgba(20, 184, 166, 0.30);
            }
            .tag-badge {
                background: rgba(245, 158, 11, 0.10);
                color: #fcd34d;
                border: 1px solid rgba(245, 158, 11, 0.22);
            }

            /* ── Outcome badge ────────────────────────────────── */
            .outcome-badge {
                display: inline-block;
                padding: 0.18rem 0.5rem;
                border-radius: 6px;
                font-size: 0.78rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.06em;
            }
            .outcome-go {
                background: rgba(34, 197, 94, 0.14);
                color: #4ade80;
                border: 1px solid rgba(34, 197, 94, 0.3);
            }
            .outcome-caution {
                background: rgba(245, 158, 11, 0.14);
                color: #fbbf24;
                border: 1px solid rgba(245, 158, 11, 0.3);
            }
            .outcome-avoid {
                background: rgba(239, 68, 68, 0.14);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }

            /* ── Tabs ─────────────────────────────────────────── */
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.3rem;
                background: transparent;
            }
            .stTabs [data-baseweb="tab"] {
                background: rgba(15, 23, 42, 0.6);
                border: 1px solid rgba(148, 163, 184, 0.10);
                border-radius: 10px;
                color: #94a3b8;
                padding: 0.5rem 0.9rem;
                font-size: 0.85rem;
                font-weight: 500;
                transition: all 0.15s ease;
            }
            .stTabs [data-baseweb="tab"]:hover {
                color: #e2e8f0;
                border-color: rgba(148, 163, 184, 0.20);
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, rgba(20, 184, 166, 0.16), rgba(99, 102, 241, 0.10));
                border-color: rgba(20, 184, 166, 0.28);
                color: #f1f5f9;
                font-weight: 600;
            }

            /* ── Metrics ──────────────────────────────────────── */
            [data-testid="stMetricValue"] {
                color: #f1f5f9;
                font-weight: 700;
            }
            [data-testid="stMetricLabel"] {
                color: #64748b;
                font-size: 0.78rem;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }

            /* ── Expanders ────────────────────────────────────── */
            .stExpander {
                border: 1px solid rgba(148, 163, 184, 0.10);
                border-radius: 14px;
                background: rgba(15, 23, 42, 0.50);
                transition: border-color 0.2s ease;
            }
            .stExpander:hover {
                border-color: rgba(148, 163, 184, 0.20);
            }

            /* ── Insight cells (non-truncating metrics) ───────── */
            .insight-cell {
                padding: 0.3rem 0;
            }
            .insight-label {
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                color: #64748b;
                margin-bottom: 0.25rem;
            }
            .insight-value {
                font-size: 1.1rem;
                font-weight: 700;
                color: #f1f5f9;
                line-height: 1.3;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }

            /* ── Action plan cards ────────────────────────────── */
            .action-section {
                background: rgba(15, 23, 42, 0.40);
                border: 1px solid rgba(148, 163, 184, 0.08);
                border-radius: 10px;
                padding: 0.7rem 0.85rem;
                margin-bottom: 0.5rem;
            }
            .action-section-title {
                font-size: 0.72rem;
                font-weight: 600;
                letter-spacing: 0.10em;
                text-transform: uppercase;
                color: #5eead4;
                margin-bottom: 0.35rem;
            }
            .action-section ul {
                margin: 0;
                padding-left: 1.1rem;
                color: #cbd5e1;
                font-size: 0.88rem;
                line-height: 1.65;
            }

            /* ── Money summary bar ────────────────────────────── */
            .money-summary {
                background: rgba(15, 23, 42, 0.50);
                border: 1px solid rgba(148, 163, 184, 0.08);
                border-radius: 10px;
                padding: 0.6rem 0.85rem;
                margin-top: 0.4rem;
                font-size: 0.88rem;
                color: #94a3b8;
                display: flex;
                gap: 1.5rem;
                flex-wrap: wrap;
            }
            .money-summary strong {
                color: #e2e8f0;
            }

            /* ── Persona card ─────────────────────────────────── */
            .persona-card {
                background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(15, 23, 42, 0.70));
                border: 1px solid rgba(99, 102, 241, 0.16);
                border-radius: 10px;
                padding: 0.7rem 0.85rem;
                margin-bottom: 0.6rem;
            }
            .persona-label {
                font-weight: 700;
                color: #a5b4fc;
                font-size: 0.92rem;
            }
            .persona-pain {
                color: #94a3b8;
                font-size: 0.86rem;
                margin-top: 0.2rem;
            }

            /* ── Form buttons ─────────────────────────────────── */
            .stFormSubmitButton > button {
                background: linear-gradient(135deg, #0d9488, #4f46e5) !important;
                border: none !important;
                border-radius: 10px !important;
                font-weight: 600 !important;
                letter-spacing: 0.02em !important;
                transition: opacity 0.2s ease !important;
            }
            .stFormSubmitButton > button:hover {
                opacity: 0.9 !important;
            }

            /* ── Divider ──────────────────────────────────────── */
            .visual-divider {
                height: 1px;
                background: linear-gradient(90deg, transparent, rgba(148, 163, 184, 0.12), transparent);
                margin: 0.8rem 0;
            }

            /* ── Hide default Streamlit cruft ──────────────────── */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            [data-testid="stToolbar"] {display: none;}
        </style>
        """,
        unsafe_allow_html=True,
    )
