import streamlit as st
import time
import html
from typing import Dict, Any, Optional, List

from agent import HomeFinderAgent, run_agent
from charts import show_price_comparison, show_rating_chart
from display import show_property_card
from ui_state import (
    ensure_ui_state,
    find_property_item,
    selected_items,
    set_selected_property,
    toggle_property_id,
)


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================
st.set_page_config(
    page_title="NestFind - Find Your Dream Home",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================
def format_money(value: Optional[float]) -> str:
    """Format money value with proper currency display."""
    if value is None:
        return "Not set"
    try:
        if value >= 10_000_000:
            return f"₹ {value / 10_000_000:.2f} Cr"
        return f"₹ {value / 100_000:.0f} L"
    except (TypeError, ValueError):
        return "Not set"


def profile_value(value: Any) -> str:
    """Format profile values with proper display."""
    if value in (None, "", [], {}):
        return "—"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, list):
        return ", ".join(str(v) for v in value) if value else "—"
    return str(value)


# ============================================================================
# STATE MANAGEMENT
# ============================================================================
def ensure_state():
    """Initialize all session state variables."""
    ensure_ui_state(st.session_state)
    
    if "agent" not in st.session_state:
        st.session_state.agent = HomeFinderAgent()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    
    if "shortlist" not in st.session_state:
        st.session_state.shortlist = []
    
    if "compare" not in st.session_state:
        st.session_state.compare = []
    
    if "selected_property_id" not in st.session_state:
        st.session_state.selected_property_id = None
    
    if "show_tool_trace" not in st.session_state:
        st.session_state.show_tool_trace = False
    
    if "run_count" not in st.session_state:
        st.session_state.run_count = 0


def reset_demo_state():
    """Reset all session state to initial values."""
    st.session_state.messages = []
    st.session_state.last_result = None
    st.session_state.shortlist = []
    st.session_state.compare = []
    st.session_state.selected_property_id = None
    st.session_state.agent = HomeFinderAgent()
    st.session_state.run_count = 0


def handle_property_actions(actions: Dict[str, Any]) -> None:
    """Handle property card action buttons."""
    if not actions:
        return

    property_id = actions.get("property_id")
    if not property_id:
        return
    
    if actions.get("details"):
        set_selected_property(st.session_state, property_id)
        st.toast("📋 Property details opened", icon="📋")
    
    if actions.get("compare"):
        added = toggle_property_id(st.session_state, "compare", property_id, limit=3)
        if added:
            st.toast("➕ Added to comparison", icon="➕")
        else:
            st.toast("➖ Removed from comparison", icon="➖")
    
    if actions.get("shortlist"):
        added = toggle_property_id(st.session_state, "shortlist", property_id)
        if added:
            st.toast("⭐ Added to shortlist", icon="⭐")
        else:
            st.toast("🗑️ Removed from shortlist", icon="🗑️")


# ============================================================================
# CSS STYLING - Updated with RTL fixes
# ============================================================================
def inject_css():
    """Inject custom CSS for the application."""
    st.markdown(
        """
        <style>
        /* Force LTR and hide sidebar */
        .stApp, .stApp * {
            direction: ltr !important;
            text-align: left !important;
        }
        
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* Main container */
        .stApp {
            background: radial-gradient(circle at 20% 0%, rgba(100, 210, 255, 0.08), transparent 40rem),
                        linear-gradient(180deg, #07090f 0%, #0b0f18 100%);
            color: #f7f8fb;
        }

        .block-container {
            max-width: 1300px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }

        /* Hero Section */
        .hero {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 16px;
            padding: 2rem 2.5rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(12px);
        }

        .hero .logo {
            font-size: 2.5rem;
            font-weight: 800;
            margin: 0;
            background: linear-gradient(135deg, #64d2ff, #9ae6b4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .hero .logo-sub {
            font-size: 0.9rem;
            color: #9aa4b2;
            margin-left: 0.5rem;
            -webkit-text-fill-color: #9aa4b2;
        }

        .hero h1 {
            font-size: clamp(1.8rem, 3.5vw, 3rem);
            font-weight: 700;
            margin: 0.3rem 0 0;
            color: #f7f8fb;
        }

        .hero-copy {
            color: #c9d1dc;
            font-size: 1rem;
            line-height: 1.6;
            margin-top: 0.3rem;
            max-width: 600px;
        }

        .hero-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-top: 0.8rem;
        }

        .pill {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 999px;
            padding: 0.3rem 0.8rem;
            color: #dbe4ef;
            background: rgba(255, 255, 255, 0.04);
            font-size: 0.75rem;
        }

        /* Prompt suggestion box */
        .prompt-box {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 0.8rem 1.2rem;
            margin-bottom: 1.5rem;
        }

        .prompt-box .label {
            color: #9aa4b2;
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .prompt-box .text {
            color: #dbe4ef;
            font-family: monospace;
            font-size: 0.85rem;
            margin-top: 0.2rem;
            padding: 0.4rem 0.6rem;
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            border-left: 3px solid #64d2ff;
        }

        /* Professional Tabs */
        .tabs-container {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 0.5rem;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(12px);
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0;
            background: transparent;
            padding: 0;
            border: none;
            flex-wrap: wrap;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            background: transparent;
            color: #9aa4b2;
            font-weight: 500;
            font-size: 0.8rem;
            transition: all 0.2s;
            border: none;
            letter-spacing: 0.3px;
        }

        .stTabs [data-baseweb="tab"]:hover {
            color: #f7f8fb;
            background: rgba(255, 255, 255, 0.05);
        }

        .stTabs [aria-selected="true"] {
            background: rgba(100, 210, 255, 0.12);
            color: #f7f8fb;
            border: 1px solid rgba(100, 210, 255, 0.15);
            box-shadow: 0 2px 8px rgba(100, 210, 255, 0.1);
        }

        .stTabs [data-baseweb="tab-panel"] {
            padding-top: 1rem;
        }

        /* Chat */
        .chat-shell {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 1.2rem;
            min-height: 25rem;
            max-height: 35rem;
            overflow-y: auto;
            backdrop-filter: blur(12px);
        }

        .chat-shell::-webkit-scrollbar {
            width: 4px;
        }

        .chat-shell::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.02);
        }

        .chat-shell::-webkit-scrollbar-thumb {
            background: rgba(100, 210, 255, 0.3);
            border-radius: 2px;
        }

        .chat-message {
            padding: 0.7rem 1rem;
            border-radius: 10px;
            margin-bottom: 0.6rem;
            max-width: 85%;
            animation: fadeIn 0.3s ease;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .chat-message.user {
            background: rgba(100, 210, 255, 0.1);
            border: 1px solid rgba(100, 210, 255, 0.15);
            margin-left: auto;
            color: #f7f8fb;
        }

        .chat-message.assistant {
            background: rgba(255, 255, 255, 0.04);
            border: 1px solid rgba(255, 255, 255, 0.06);
            margin-right: auto;
            color: #f7f8fb;
        }

        .chat-role {
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
            color: #9aa4b2;
            margin-bottom: 0.2rem;
            letter-spacing: 0.5px;
        }

        .chat-role.user-role {
            color: #64d2ff;
        }

        .chat-role.assistant-role {
            color: #9ae6b4;
        }

        /* Professional Profile */
        .profile-card {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 1.5rem;
            backdrop-filter: blur(12px);
        }

        .profile-card .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.2rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .profile-card .header h3 {
            margin: 0;
            color: #f7f8fb;
            font-size: 1rem;
        }

        .profile-card .header .badge {
            background: rgba(100, 210, 255, 0.1);
            border: 1px solid rgba(100, 210, 255, 0.15);
            border-radius: 999px;
            padding: 0.2rem 0.8rem;
            font-size: 0.7rem;
            color: #64d2ff;
        }

        .profile-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.8rem;
        }

        .profile-item {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.04);
            border-radius: 8px;
            padding: 0.7rem;
        }

        .profile-item label {
            display: block;
            color: #9aa4b2;
            font-size: 0.6rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.2rem;
        }

        .profile-item .value {
            color: #f7f8fb;
            font-size: 0.9rem;
            font-weight: 500;
        }

        /* Buttons */
        .stButton > button {
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(255, 255, 255, 0.04);
            color: #f7f8fb;
            padding: 0.4rem 1.2rem;
            transition: all 0.2s;
            font-size: 0.8rem;
            font-weight: 500;
        }

        .stButton > button:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.15);
        }

        /* Input */
        div[data-testid="stChatInput"] {
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            background: rgba(17, 21, 32, 0.8);
            backdrop-filter: blur(12px);
            padding: 0.2rem;
        }

        div[data-testid="stChatInput"] > div {
            background: transparent;
            border-radius: 10px;
        }

        div[data-testid="stChatInput"] textarea {
            color: #f7f8fb;
        }

        /* Metrics */
        .metric-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1rem;
            margin: 1rem 0;
        }

        .metric-box {
            background: rgba(17, 21, 32, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.06);
            border-radius: 12px;
            padding: 1.2rem;
            text-align: center;
            backdrop-filter: blur(8px);
        }

        .metric-box .number {
            font-size: 2rem;
            font-weight: 700;
            color: #f7f8fb;
        }

        .metric-box .label {
            color: #9aa4b2;
            font-size: 0.75rem;
            font-weight: 500;
            margin-top: 0.2rem;
        }

        /* Responsive */
        @media (max-width: 860px) {
            .chat-message {
                max-width: 95%;
            }
            .hero {
                padding: 1.2rem;
            }
            .profile-grid {
                grid-template-columns: repeat(2, 1fr);
            }
            .metric-grid {
                grid-template-columns: 1fr;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.4rem 0.8rem;
                font-size: 0.7rem;
            }
            .chat-shell {
                min-height: 20rem;
                max-height: 25rem;
            }
        }

        @media (max-width: 480px) {
            .block-container {
                padding: 0.5rem;
            }
            .hero .logo {
                font-size: 1.8rem;
            }
            .profile-grid {
                grid-template-columns: 1fr;
            }
            .stTabs [data-baseweb="tab"] {
                padding: 0.3rem 0.5rem;
                font-size: 0.65rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================================
# PROPERTY CARD RENDERER - Fixed with RTL support
# ============================================================================
PROPERTY_VISUALS = [
    ("#172033", "#2f80ed", "#9ae6b4"),
    ("#1d2233", "#a855f7", "#64d2ff"),
    ("#16251f", "#22c55e", "#facc15"),
    ("#241d2b", "#fb7185", "#38bdf8"),
    ("#202033", "#818cf8", "#f8fafc"),
]

def _money(value):
    if value is None:
        return "N/A"
    if value >= 10_000_000:
        return f"₹ {value / 10_000_000:.2f} Cr"
    return f"₹ {value / 100_000:.0f} L"

def _list_items(items):
    if not items:
        return "<li>Recommendation generated from available market signals.</li>"
    return "".join(f"<li>{html.escape(str(item))}</li>" for item in items)

def show_property_card(item, rank=None, key_prefix="property"):
    """Render a premium property recommendation card with RTL fixes."""

    property_data = item["property"]
    score = item.get("score", 0)
    match = item.get("match", f"{score}%")
    confidence = item.get("confidence", 90)
    reasons = item.get("reason", [])
    cons = item.get("cons", [])
    tradeoffs = item.get("tradeoffs", [])
    affordability = item.get("affordability", {})
    commute = item.get("commute", {})
    schools = item.get("schools", [])
    neighbourhood = item.get("neighbourhood", {})
    ai_summary = item.get("ai_summary", "AI summary will appear after ranking completes.")

    price_per_sqft = property_data["price"] / property_data["area_sqft"]
    affordable = affordability.get("affordable")
    budget_text = (
        f"✅ Within budget, {_money(affordability.get('remaining_budget'))} buffer"
        if affordable
        else f"⚠️ {_money(affordability.get('shortfall'))} shortfall"
    )

    commute_text = commute.get("time_min", "N/A")
    if commute_text != "N/A":
        commute_text = f"{commute_text} min"

    safety = neighbourhood.get("safety", property_data.get("crime_score", "N/A"))
    metro = "✅ Yes" if neighbourhood.get("metro") else f"{property_data.get('metro_distance', 'N/A')} m"
    title_prefix = f"#{rank} " if rank else ""
    visual = PROPERTY_VISUALS[property_data["id"] % len(PROPERTY_VISUALS)]

    # Determine status badge color
    if confidence >= 85:
        status_badge = "🟢 Excellent"
        status_color = "#10b981"
    elif confidence >= 60:
        status_badge = "🟡 Good"
        status_color = "#f59e0b"
    else:
        status_badge = "🔴 Needs Review"
        status_color = "#ef4444"

    st.markdown(
        f"""
        <style>
        /* Property card styles - force LTR */
        .property-card {{
            direction: ltr !important;
            text-align: left !important;
            background: rgba(17, 21, 32, 0.82);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 12px;
            padding: 1.2rem;
            margin-bottom: 1rem;
            transition: all 0.3s ease;
            backdrop-filter: blur(12px);
        }}
        .property-card:hover {{
            transform: translateY(-2px);
            border-color: rgba(100, 210, 255, 0.3);
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.3);
        }}
        .property-visual {{
            min-height: 10rem;
            border-radius: 8px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            overflow: hidden;
            position: relative;
            margin-bottom: 1rem;
            background: linear-gradient(135deg, {visual[0]}, {visual[1]} 56%, {visual[2]});
        }}
        .property-visual-overlay {{
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            background: linear-gradient(180deg, transparent, rgba(0,0,0,0.7));
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
        }}
        .property-visual-overlay span {{
            color: rgba(255,255,255,0.9);
            font-size: 0.85rem;
            font-weight: 600;
        }}
        .property-visual-overlay strong {{
            color: white;
            font-size: 1.2rem;
        }}
        .property-top {{
            display: grid !important;
            grid-template-columns: 1fr auto !important;
            gap: 1rem !important;
            align-items: start !important;
            margin-bottom: 0.5rem !important;
            direction: ltr !important;
        }}
        .property-name {{
            font-size: 1.15rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            color: #f7f8fb !important;
            text-align: left !important;
        }}
        .property-location {{
            color: #9aa4b2 !important;
            font-size: 0.85rem !important;
            margin-top: 0.15rem !important;
            text-align: left !important;
        }}
        .score-badge {{
            text-align: right !important;
            color: #9ae6b4 !important;
            font-weight: 800 !important;
            font-size: 1.3rem !important;
            white-space: nowrap !important;
        }}
        .status-badge {{
            display: inline-block !important;
            padding: 0.15rem 0.6rem !important;
            border-radius: 999px !important;
            font-size: 0.65rem !important;
            font-weight: 600 !important;
            background: rgba(100, 210, 255, 0.15) !important;
            color: {status_color} !important;
            margin-left: 0.5rem !important;
        }}
        .card-metrics {{
            display: grid !important;
            grid-template-columns: repeat(4, 1fr) !important;
            gap: 0.5rem !important;
            margin: 0.7rem 0 !important;
        }}
        .card-metric {{
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 8px !important;
            padding: 0.5rem !important;
            text-align: center !important;
            background: rgba(255, 255, 255, 0.02) !important;
        }}
        .card-metric small {{
            color: #9aa4b2 !important;
            display: block !important;
            font-size: 0.6rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.5px !important;
        }}
        .card-metric strong {{
            font-size: 0.9rem !important;
            color: #f7f8fb !important;
        }}
        .pill-row {{
            display: flex !important;
            flex-wrap: wrap !important;
            gap: 0.4rem !important;
            margin: 0.5rem 0 !important;
            direction: ltr !important;
        }}
        .pill {{
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 999px !important;
            padding: 0.25rem 0.6rem !important;
            color: #dbe4ef !important;
            background: rgba(255, 255, 255, 0.04) !important;
            font-size: 0.7rem !important;
            display: inline-block !important;
        }}
        .pill.trade-off {{
            border-color: rgba(255, 200, 50, 0.2) !important;
            background: rgba(255, 200, 50, 0.05) !important;
            color: #facc15 !important;
        }}
        .pill.watch {{
            border-color: rgba(255, 100, 100, 0.2) !important;
            background: rgba(255, 100, 100, 0.05) !important;
            color: #fb7185 !important;
        }}
        .reason-list {{
            margin: 0.5rem 0 0 !important;
            padding-left: 1.2rem !important;
            color: #d9e2ee !important;
            font-size: 0.85rem !important;
            line-height: 1.6 !important;
            text-align: left !important;
        }}
        .reason-list li {{
            text-align: left !important;
        }}
        .ai-summary {{
            margin-top: 0.8rem !important;
            padding: 0.8rem !important;
            border: 1px solid rgba(255, 255, 255, 0.06) !important;
            border-radius: 8px !important;
            background: rgba(255, 255, 255, 0.02) !important;
        }}
        .ai-summary small {{
            display: block !important;
            color: #64d2ff !important;
            font-weight: 700 !important;
            text-transform: uppercase !important;
            font-size: 0.65rem !important;
            letter-spacing: 0.5px !important;
            margin-bottom: 0.2rem !important;
        }}
        .ai-summary p {{
            margin: 0 !important;
            color: #dbe4ef !important;
            font-size: 0.85rem !important;
            line-height: 1.5 !important;
            text-align: left !important;
        }}
        @media (max-width: 640px) {{
            .property-card {{
                padding: 0.8rem !important;
            }}
            .card-metrics {{
                grid-template-columns: repeat(2, 1fr) !important;
            }}
            .property-top {{
                grid-template-columns: 1fr !important;
            }}
            .score-badge {{
                text-align: left !important;
            }}
            .property-name {{
                font-size: 1rem !important;
            }}
        }}
        </style>
        
        <article class="property-card" style="direction: ltr !important;">
            <div class="property-visual">
                <div class="property-visual-overlay">
                    <span>{html.escape(property_data["location"])}</span>
                    <strong>{property_data["bhk"]} BHK</strong>
                </div>
            </div>
            <div class="property-top" style="direction: ltr !important;">
                <div>
                    <p class="property-name" style="direction: ltr !important;">
                        {title_prefix}{html.escape(property_data["name"])}
                        <span class="status-badge">{status_badge}</span>
                    </p>
                    <div class="property-location" style="direction: ltr !important;">
                        {html.escape(property_data["location"])} | {property_data["bhk"]} BHK | {property_data["area_sqft"]} sqft
                    </div>
                </div>
                <div class="score-badge" style="text-align: right !important;">{match}</div>
            </div>
            <div class="card-metrics">
                <div class="card-metric">
                    <small>Price</small>
                    <strong>{_money(property_data["price"])}</strong>
                </div>
                <div class="card-metric">
                    <small>Confidence</small>
                    <strong>{confidence}%</strong>
                </div>
                <div class="card-metric">
                    <small>Rating</small>
                    <strong>{property_data["rating"]}/5</strong>
                </div>
                <div class="card-metric">
                    <small>Price/sqft</small>
                    <strong>₹ {price_per_sqft:,.0f}</strong>
                </div>
                <div class="card-metric">
                    <small>Metro</small>
                    <strong>{metro}</strong>
                </div>
                <div class="card-metric">
                    <small>Commute</small>
                    <strong>{commute_text}</strong>
                </div>
                <div class="card-metric">
                    <small>Safety</small>
                    <strong>{safety}</strong>
                </div>
                <div class="card-metric">
                    <small>ROI</small>
                    <strong>{property_data.get("roi", "N/A")}%</strong>
                </div>
            </div>
            <div class="pill-row" style="direction: ltr !important;">
                {"".join(f'<span class="pill">{html.escape(str(a))}</span>' for a in property_data.get("amenities", [])[:6])}
            </div>
            <ul class="reason-list" style="direction: ltr !important;">{_list_items(reasons)}</ul>
            <div class="pill-row" style="direction: ltr !important;">
                <span class="pill">{budget_text}</span>
                <span class="pill">🏫 Schools: {len(schools) if schools else property_data.get("school_rating", "N/A")}</span>
                <span class="pill">📈 Growth: {property_data.get("price_growth", "N/A")}%</span>
            </div>
            <div class="pill-row" style="direction: ltr !important;">
                {"".join(f'<span class="pill trade-off">⚖️ {html.escape(str(t))}</span>' for t in tradeoffs[:2])}
                {"".join(f'<span class="pill watch">⚠️ {html.escape(str(c))}</span>' for c in cons[:2])}
            
        </article>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    prop_id = property_data["id"]
    return {
        "property_id": prop_id,
        "details": c1.button("📋 Details", key=f"{key_prefix}_view_{prop_id}", use_container_width=True),
        "compare": c2.button("⚖️ Compare", key=f"{key_prefix}_compare_{prop_id}", use_container_width=True),
        "shortlist": c3.button("⭐ Save", key=f"{key_prefix}_save_{prop_id}", use_container_width=True),
    }


# ============================================================================
# RENDER FUNCTIONS
# ============================================================================
def render_hero():
    """Render the hero section with branding."""
    st.markdown(
        """
        <div class="hero">
            <div>
                <span class="logo">NestFind</span>
                <span class="logo-sub">🏠</span>
            </div>
            <h1>Find Your Dream Home</h1>
            <p class="hero-copy">
                AI-powered real estate consultant for Bangalore. Build your buyer profile,
                search listings, check neighbourhoods, schools, commute, and price history.
            </p>
            <div class="hero-pills">
                <span class="pill">📍 Bangalore</span>
                <span class="pill">🤖 AI Assistant</span>
                <span class="pill">📊 Smart Ranking</span>
                <span class="pill">💡 Investment Insights</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_prompt_suggestion():
    """Render the prompt suggestion box."""
    st.markdown(
        """
        <div class="prompt-box">
            <div class="label">💡 Try saying</div>
            <div class="text">"I need a 3 BHK apartment in Electronic City under 90 lakh with schools nearby"</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_profile(profile: Dict[str, Any]) -> None:
    """Render the buyer profile card."""
    if not any(profile.values()):
        st.markdown("""
        <div class="profile-card">
            <div class="header">
                <h3>📋 Buyer Profile</h3>
                <span class="badge">Incomplete</span>
            </div>
            <p style="color: #9aa4b2; text-align: center; padding: 2rem 0;">
                Start a conversation to build your profile
            </p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    fields = [
        ("Budget", format_money(profile.get("budget"))),
        ("BHK", profile_value(profile.get("bhk"))),
        ("Locations", profile_value(profile.get("preferred_locations"))),
        ("Property Type", profile_value(profile.get("property_type"))),
        ("Schools", profile_value(profile.get("school_priority"))),
        ("Metro", profile_value(profile.get("metro_priority"))),
        ("Investment", profile_value(profile.get("investment_priority"))),
    ]
    
    html = '<div class="profile-card"><div class="header"><h3>📋 Buyer Profile</h3><span class="badge">Active</span></div><div class="profile-grid">'
    for label, value in fields:
        html += f'<div class="profile-item"><label>{label}</label><div class="value">{value}</div></div>'
    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)


def render_chat() -> None:
    """Render the chat interface."""
    st.markdown('<div class="chat-shell">', unsafe_allow_html=True)
    
    if not st.session_state.messages:
        st.markdown(
            """
            <div class="chat-message assistant">
                <div class="chat-role assistant-role">🏠 NestFind</div>
                Tell me what you're looking for in Bangalore.<br>
                <span style="color: #9aa4b2; font-size: 0.85rem;">
                    Example: "3 BHK near Electronic City under 90 lakh with schools nearby"
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    for message in st.session_state.messages:
        role_class = "user" if message["role"] == "user" else "assistant"
        role_label = "You" if message["role"] == "user" else "NestFind"
        role_style = "user-role" if message["role"] == "user" else "assistant-role"
        
        st.markdown(
            f"""
            <div class="chat-message {role_class}">
                <div class="chat-role {role_style}">{role_label}</div>
                {message["content"]}
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("</div>", unsafe_allow_html=True)


def render_results(result: Optional[Dict[str, Any]]) -> None:
    """Render property results."""
    if not result or result.get("type") != "recommendation":
        st.info("Start a conversation to see property recommendations.")
        return

    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; align-items: center; margin: 0.5rem 0 1rem;">
            <div>
                <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">🏠 Property Results</h2>
                <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Ranked recommendations with confidence scores</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    results = result.get("results", [])
    if not results:
        st.warning("No properties matched. Try adjusting your criteria.")
        return

    st.caption(
        f"⭐ Shortlisted: {len(st.session_state.shortlist)} | "
        f"⚖️ Comparing: {len(st.session_state.compare)}/3"
    )

    for rank, item in enumerate(results, start=1):
        actions = show_property_card(item, rank=rank, key_prefix="results")
        handle_property_actions(actions)


def render_property_details(result: Optional[Dict[str, Any]]) -> None:
    """Render property details view."""
    results = result.get("results", []) if result else []
    if not results:
        st.info("Search for properties to see details.")
        return

    item = find_property_item(result, st.session_state.selected_property_id) or results[0]
    
    col1, col2 = st.columns([1, 1])
    with col1:
        actions = show_property_card(item, rank=1, key_prefix="details")
        handle_property_actions(actions)
    with col2:
        st.markdown('<div style="background: rgba(17,21,32,0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 12px; padding: 1.2rem; backdrop-filter: blur(12px);">', unsafe_allow_html=True)
        st.subheader("🤖 AI Summary")
        st.write(item.get("ai_summary", "No summary available."))
        
        st.subheader("✅ Strengths")
        for value in item.get("pros", []) or ["None listed"]:
            st.success(value)
        
        st.subheader("⚠️ Trade-offs")
        for value in item.get("tradeoffs", []) or ["None listed"]:
            st.info(value)
        st.markdown("</div>", unsafe_allow_html=True)


def render_comparison(result: Optional[Dict[str, Any]]) -> None:
    """Render property comparison view."""
    results = result.get("results", []) if result else []
    selected = selected_items(result, st.session_state.compare)
    items = selected or results[:3]
    
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">⚖️ Compare Properties</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Side-by-side comparison of selected properties</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if not items:
        st.info("Select properties to compare using the compare button on property cards.")
        return

    rows = []
    for item in items[:5]:
        prop = item.get("property", {})
        rows.append({
            "Property": prop.get("name", "N/A"),
            "Location": prop.get("location", "N/A"),
            "Price": format_money(prop.get("price")),
            "BHK": prop.get("bhk", "N/A"),
            "Rating": f"{prop.get('rating', 0):.1f}",
            "ROI": f"{prop.get('roi', 0)}%",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_analytics(result: Optional[Dict[str, Any]]) -> None:
    """Render analytics view."""
    results = result.get("results", []) if result else []
    
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">📊 Analytics</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Market intelligence from your search results</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    if not results:
        st.info("Analytics available after search.")
        return

    properties = [item.get("property", {}) for item in results if item.get("property")]
    if not properties:
        st.info("No property data available for analytics.")
        return
    
    avg_price = sum(p.get("price", 0) for p in properties) / len(properties)
    avg_rating = sum(p.get("rating", 0) for p in properties) / len(properties)
    
    st.markdown(f"""
    <div class="metric-grid">
        <div class="metric-box">
            <div class="number">{len(properties)}</div>
            <div class="label">Properties Found</div>
        </div>
        <div class="metric-box">
            <div class="number">{format_money(avg_price)}</div>
            <div class="label">Average Price</div>
        </div>
        <div class="metric-box">
            <div class="number">{avg_rating:.1f}</div>
            <div class="label">Average Rating</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        show_rating_chart(properties)
    with col2:
        show_price_comparison(properties)


def render_shortlist(result: Optional[Dict[str, Any]]) -> None:
    """Render shortlist view."""
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">⭐ Shortlist</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Your saved properties</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    items = selected_items(result, st.session_state.shortlist)
    if not items:
        st.info("Use the shortlist button on property cards to save properties here.")
        return

    rows = []
    for item in items:
        prop = item.get("property", {})
        rows.append({
            "Property": prop.get("name", "N/A"),
            "Location": prop.get("location", "N/A"),
            "Price": format_money(prop.get("price")),
            "Match": item.get("match", "N/A"),
            "Confidence": f"{item.get('confidence', 0)}%",
        })
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_settings() -> None:
    """Render settings view."""
    st.markdown(
        """
        <div style="margin: 0.5rem 0 1rem;">
            <h2 style="font-size: 1.2rem; margin: 0; color: #f7f8fb;">⚙️ Settings</h2>
            <p style="color: #9aa4b2; margin: 0; font-size: 0.85rem;">Manage your session and preferences</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 New Conversation", use_container_width=True):
            reset_demo_state()
            st.rerun()
    with col2:
        st.markdown("""
        <div style="background: rgba(17,21,32,0.6); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px; padding: 0.8rem 1rem; backdrop-filter: blur(8px);">
            <div style="color: #9aa4b2; font-size: 0.7rem;">Session Status</div>
            <div style="color: #9ae6b4; font-size: 0.8rem; font-weight: 600;">● Active</div>
        </div>
        """, unsafe_allow_html=True)


# ============================================================================
# MAIN APPLICATION
# ============================================================================
def main():
    """Main application entry point."""
    # Initialize state
    ensure_state()
    
    # Inject CSS
    inject_css()
    
    # Render header and prompt
    render_hero()
    render_prompt_suggestion()
    
    # Professional tabs
    st.markdown('<div class="tabs-container">', unsafe_allow_html=True)
    tabs = st.tabs([
        "💬 Chat",
        "📋 Profile", 
        "🏠 Results",
        "📄 Details",
        "⚖️ Compare",
        "📊 Analytics",
        "⭐ Shortlist",
        "⚙️ Settings"
    ])
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Get data
    last_result = st.session_state.last_result
    profile = st.session_state.agent.conversation.get_profile()
    if last_result:
        profile = last_result.get("buyer") or last_result.get("profile") or {}
    
    # Render tabs
    with tabs[0]:
        render_chat()
    
    with tabs[1]:
        render_profile(profile)
    
    with tabs[2]:
        render_results(last_result)
    
    with tabs[3]:
        render_property_details(last_result)
    
    with tabs[4]:
        render_comparison(last_result)
    
    with tabs[5]:
        render_analytics(last_result)
    
    with tabs[6]:
        render_shortlist(last_result)
    
    with tabs[7]:
        render_settings()
    
    # Chat input
    prompt = st.chat_input("💬 Describe what you're looking for...")
    
    if prompt:
        # Increment run count
        st.session_state.run_count += 1
        
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Process with status
        with st.status("🔍 Searching...", expanded=True) as status:
            st.write("🧠 Understanding buyer intent")
            st.write("📋 Planning tool calls")
            st.write("🔎 Searching and enriching properties")
            
            try:
                result = run_agent(prompt, agent=st.session_state.agent)
                status.update(label="✅ Done", state="complete", expanded=False)
            except Exception as e:
                st.error(f"Error: {str(e)}")
                status.update(label="❌ Failed", state="error", expanded=False)
                return
        
        # Store result
        st.session_state.last_result = result
        
        # Build response
        if result.get("type") == "question":
            assistant_text = result.get("message", "I need more information to help you.")
        else:
            count = len(result.get("results", []))
            explanation = result.get("explanation", "")
            assistant_text = explanation or f"I found {count} matching properties."
        
        # Add assistant message
        st.session_state.messages.append({"role": "assistant", "content": assistant_text})
        
        # Rerun to update UI
        st.rerun()


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    main()