from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(20, 184, 166, 0.12), transparent 32%),
                    radial-gradient(circle at top right, rgba(245, 158, 11, 0.10), transparent 28%),
                    linear-gradient(180deg, #07111d 0%, #0f172a 55%, #111827 100%);
                color: #e5eef8;
            }
            [data-testid="stHeader"] {
                background: rgba(7, 17, 29, 0.68);
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, rgba(8, 15, 28, 0.98), rgba(15, 23, 42, 0.94));
                border-right: 1px solid rgba(148, 163, 184, 0.10);
            }
            .hero-card, .intro-card, .mini-card, .empty-card, .form-shell, .avoid-card {
                border: 1px solid rgba(148, 163, 184, 0.16);
                border-radius: 18px;
                box-shadow: 0 18px 42px rgba(0, 0, 0, 0.18);
            }
            .intro-card, .form-shell, .empty-card, .mini-card, .avoid-card {
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.92), rgba(15, 23, 42, 0.72));
            }
            .hero-card {
                padding: 1rem 1.1rem;
                background: linear-gradient(135deg, rgba(13, 148, 136, 0.18), rgba(15, 23, 42, 0.96) 42%, rgba(217, 119, 6, 0.14));
            }
            .intro-card, .empty-card {
                padding: 1rem 1.1rem;
                margin-bottom: 0.9rem;
            }
            .form-shell {
                padding: 0.6rem 0.85rem 0.2rem 0.85rem;
                margin-bottom: 0.25rem;
            }
            .mini-card, .avoid-card {
                padding: 0.9rem 1rem;
                height: 100%;
            }
            .avoid-card {
                border-color: rgba(248, 113, 113, 0.18);
                background: linear-gradient(180deg, rgba(127, 29, 29, 0.22), rgba(15, 23, 42, 0.78));
                margin-bottom: 0.9rem;
            }
            .eyebrow {
                letter-spacing: 0.12em;
                text-transform: uppercase;
                font-size: 0.78rem;
                color: #94f1df;
            }
            .hero-title, .intro-title {
                color: #f8fafc;
                font-weight: 700;
            }
            .hero-title {
                font-size: 1.7rem;
                margin: 0.3rem 0 0.6rem 0;
            }
            .intro-title {
                font-size: 1.22rem;
                margin: 0.35rem 0 0.45rem 0;
            }
            .mini-card-title {
                color: #f8fafc;
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 0.3rem;
            }
            .mini-card-score {
                color: #94f1df;
                font-size: 0.86rem;
                font-weight: 600;
                margin-bottom: 0.45rem;
            }
            .hero-subtitle, .muted {
                color: #cbd5e1;
                font-size: 0.96rem;
            }
            .chip-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.45rem;
                margin-top: 0.8rem;
            }
            .intro-chip, .score-badge, .tag-badge {
                display: inline-block;
                padding: 0.26rem 0.62rem;
                border-radius: 999px;
                font-size: 0.82rem;
                font-weight: 600;
            }
            .intro-chip {
                background: rgba(56, 189, 248, 0.12);
                color: #bae6fd;
                border: 1px solid rgba(56, 189, 248, 0.22);
            }
            .score-badge, .tag-badge {
                margin-right: 0.35rem;
                margin-bottom: 0.35rem;
            }
            .score-badge {
                background: rgba(20, 184, 166, 0.16);
                color: #99f6e4;
                border: 1px solid rgba(20, 184, 166, 0.4);
            }
            .tag-badge {
                background: rgba(245, 158, 11, 0.14);
                color: #fde68a;
                border: 1px solid rgba(245, 158, 11, 0.3);
            }
            .stTabs [data-baseweb="tab-list"] {
                gap: 0.35rem;
            }
            .stTabs [data-baseweb="tab"] {
                background: rgba(15, 23, 42, 0.72);
                border: 1px solid rgba(148, 163, 184, 0.14);
                border-radius: 999px;
                color: #dbe7f5;
                padding: 0.55rem 0.95rem;
            }
            .stTabs [aria-selected="true"] {
                background: linear-gradient(135deg, rgba(20, 184, 166, 0.20), rgba(59, 130, 246, 0.14));
                border-color: rgba(20, 184, 166, 0.34);
            }
            [data-testid="stMetricValue"] {
                color: #f8fafc;
            }
            [data-testid="stMetricLabel"] {
                color: #9fb3c8;
            }
            .stExpander {
                border: 1px solid rgba(148, 163, 184, 0.14);
                border-radius: 18px;
                background: rgba(15, 23, 42, 0.58);
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
