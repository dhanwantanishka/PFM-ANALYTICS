"""Global CSS helpers and optional light-theme overrides."""

from __future__ import annotations

import streamlit as st


def inject_global_styles(light_mode: bool = False) -> None:
    """Inject app-wide styling for cards, metrics, and premium UI polish."""
    st.markdown(
        """
        <style>
        /* Import premium fonts */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');
        
        :root {
            --bg-color: #0b0f19;
            --surface-color: rgba(30, 41, 59, 0.7);
            --surface-hover: rgba(45, 55, 72, 0.9);
            --text-primary: #f8fafc;
            --text-muted: #94a3b8;
            --accent-primary: #8b5cf6;
            --accent-secondary: #3b82f6;
            --border-color: rgba(255, 255, 255, 0.08);
            --glass-blur: blur(12px);
            --shadow-subtle: 0 4px 20px -2px rgba(0,0,0,0.4);
            --shadow-hover: 0 8px 30px -4px rgba(0,0,0,0.6);
        }

        /* Base Typography */
        html, body, [class*="css"] {
            font-family: 'Outfit', sans-serif !important;
        }
        
        h1, h2, h3 {
            font-weight: 700 !important;
            letter-spacing: -0.02em;
        }

        /* Glassmorphism Cards */
        .pfm-card, div[data-testid="stMetric"], div[data-testid="stExpander"] details {
            background: var(--surface-color) !important;
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--border-color) !important;
            border-radius: 16px !important;
            box-shadow: var(--shadow-subtle) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        }
        
        .pfm-card:hover, div[data-testid="stMetric"]:hover {
            transform: translateY(-4px);
            box-shadow: var(--shadow-hover) !important;
            border-color: rgba(139, 92, 246, 0.3) !important;
            background: var(--surface-hover) !important;
        }

        /* Metrics Styling */
        [data-testid="stMetric"] {
            padding: 1.25rem 1.5rem !important;
            position: relative;
            overflow: hidden;
        }
        [data-testid="stMetric"]::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 4px; height: 100%;
            background: linear-gradient(to bottom, var(--accent-primary), var(--accent-secondary));
            border-radius: 4px 0 0 4px;
        }
        [data-testid="stMetricLabel"] { 
            color: var(--text-muted) !important; 
            font-size: 0.9rem !important; 
            text-transform: uppercase;
            letter-spacing: 0.05em;
            font-weight: 500;
        }
        [data-testid="stMetricValue"] { 
            color: var(--text-primary) !important; 
            font-size: 2.2rem !important; 
            font-weight: 700 !important; 
            letter-spacing: -0.02em;
        }

        /* Premium Buttons */
        button[data-testid="baseButton-primary"] {
            background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            color: white !important;
            font-weight: 600 !important;
            padding: 0.5rem 1.5rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba(139, 92, 246, 0.4) !important;
        }
        button[data-testid="baseButton-primary"]:hover {
            transform: translateY(-2px) scale(1.02) !important;
            box-shadow: 0 8px 25px rgba(139, 92, 246, 0.6) !important;
        }
        
        /* Hero Section */
        .pfm-hero {
            background: linear-gradient(135deg, rgba(139, 92, 246, 0.15) 0%, rgba(59, 130, 246, 0.15) 100%);
            border: 1px solid rgba(139, 92, 246, 0.2);
            color: var(--text-primary);
            padding: 2.5rem;
            border-radius: 20px;
            margin-bottom: 2rem;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
        }
        
        .pfm-hero::after {
            content: '';
            position: absolute;
            top: -50%; right: -10%; width: 50%; height: 200%;
            background: radial-gradient(circle, rgba(139,92,246,0.1) 0%, transparent 70%);
            transform: rotate(30deg);
            pointer-events: none;
        }

        /* Section Headers */
        .pfm-section-header {
            font-size: 1.5rem;
            font-weight: 700;
            background: linear-gradient(90deg, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }

        /* Sidebar Styling */
        [data-testid="stSidebar"] {
            background: #0b0f19 !important;
            border-right: 1px solid var(--border-color) !important;
        }
        
        /* Input Fields */
        .stTextInput input, .stSelectbox > div > div {
            background: rgba(30, 41, 59, 0.5) !important;
            border: 1px solid var(--border-color) !important;
            border-radius: 10px !important;
            color: var(--text-primary) !important;
            transition: all 0.3s ease !important;
        }
        .stTextInput input:focus, .stSelectbox > div > div:focus-within {
            border-color: var(--accent-primary) !important;
            box-shadow: 0 0 0 2px rgba(139, 92, 246, 0.2) !important;
        }
        
        /* Dataframes */
        [data-testid="stDataFrame"] {
            border: 1px solid var(--border-color);
            border-radius: 12px;
            overflow: hidden;
        }
        
        /* Typography overrides */
        .pfm-card-title {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-bottom: 0.25rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .pfm-card-value {
            color: var(--text-primary);
            font-size: 1.5rem;
            font-weight: 700;
        }
        .pfm-badge {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 600;
            background: rgba(139, 92, 246, 0.2);
            color: #d8b4fe;
            border: 1px solid rgba(139, 92, 246, 0.4);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
